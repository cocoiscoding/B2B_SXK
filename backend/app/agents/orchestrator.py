"""Agent 编排器：串联 检索 → 生成 → 渠道适配 → 校验。

这是多 Agent 系统的指挥中心，负责：
1. 从数据库加载产品和场景数据
2. 按顺序执行 4 个 Agent
3. 收集每个 Agent 的执行步骤
4. 持久化结果到 history 表
5. 返回完整的生成响应

对应需求：F3-6 多 Agent 编排

设计模式：
- 责任链模式：4 个 Agent 串行执行，前一个的输出是后一个的输入
- 单例模式：整个应用只创建一个 Orchestrator 实例
"""
import uuid
from typing import Callable
from psycopg2.extras import Json
from app.agents.base import AgentContext, BaseAgent
from app.agents.retrieval_agent import RetrievalAgent
from app.agents.competitor_agent import CompetitorAgent
from app.agents.generation_agent import GenerationAgent
from app.agents.channel_agent import ChannelAgent
from app.agents.validation_agent import ValidationAgent
from app.agents.llm_provider import get_provider
from app.database import query_one, transaction, _parse_json_fields, execute
from app.models import GenerateResponse, VersionContent, AgentStep
from app.seo_analyzer import analyze as seo_analyze


class Orchestrator:
    """多 Agent 串行编排器。"""

    def __init__(self):
        """初始化：创建 LLM Provider 和 5 个 Agent 实例。"""
        llm = get_provider()
        # 5 个 Agent：检索单跑；生成->渠道->校验可返工重试；文生图最后
        self.retrieval = RetrievalAgent(llm)        # ① 产品信息检索
        self.competitor = CompetitorAgent(llm)      # ② 竞品分析（仅竞品场景激活）
        self.generation = GenerationAgent(llm)      # ③ 内容生成
        self.channel = ChannelAgent(llm)            # ④ 渠道适配
        self.validation = ValidationAgent(llm)      # ⑤ 内容校验
        self.image = self._build_image_agent(llm)   # ⑥ 文生图配图（加分项，缺失时降级为 noop）
        # 保留 agents 列表便于外部遍历/展示
        self.agents = [self.retrieval, self.competitor, self.generation, self.channel, self.validation, self.image]

    def _build_image_agent(self, llm):
        """兼容旧版本代码：若 image agent 模块不存在，使用 no-op 退化实现。"""
        try:
            from app.agents.image_agent import ImageAgent  # type: ignore
        except ModuleNotFoundError:
            class ImageAgentFallback(BaseAgent):
                name = "文生图配图 Agent"
                description = "图片生成模块未启用时的降级实现"

                def _execute(self, ctx: AgentContext) -> tuple[str, str, dict]:
                    return "success", "图片生成模块未启用，跳过配图", {"image": None, "images": []}

            return ImageAgentFallback(llm)
        return ImageAgent(llm)

    def run(self, product_id: str, scenario_id: str, channel: str,
            style: str, params: dict, version_count: int = 3,
            created_by: str | None = None, template_id: str | None = None) -> GenerateResponse:
        """执行完整的 Agent 链路。

        参数：
            product_id: 产品 ID
            scenario_id: 场景 ID
            channel: 目标渠道
            style: 文案风格
            params: 用户填写的参数
            version_count: 生成版本数
            template_id: 模板 ID（可选，用于加载模板提示词）

        返回：GenerateResponse 对象
        """
        # ===== 第 1 步：从数据库加载产品、场景和模板 =====
        prod_row = query_one("SELECT * FROM products WHERE id = %s", (product_id,))
        if not prod_row:
            raise ValueError(f"产品 {product_id} 不存在")
        # _parse_json_fields 处理 JSONB 字段的空值
        product = _parse_json_fields(prod_row, ["features", "target_customers", "selling_points", "competitors"])

        sce_row = query_one("SELECT * FROM scenarios WHERE id = %s", (scenario_id,))
        if not sce_row:
            raise ValueError(f"场景 {scenario_id} 不存在")
        scenario = _parse_json_fields(sce_row, ["parameters"])

        # 加载模板（如果有）
        if template_id:
            tmpl_row = query_one(
                "SELECT * FROM templates WHERE id = %s AND scenario_id = %s",
                (template_id, scenario_id),
            )
            if tmpl_row and tmpl_row.get("status") == "approved":
                # 将模板的 prompt 注入到 scenario 中，供后续 Agent 使用
                scenario["template"] = tmpl_row["prompt"]
                scenario["template_name"] = tmpl_row["name"]
                # 模板结构化约束：供 ValidationAgent 机械校验（字数/必含参数/卖点覆盖等）
                scenario["template_constraints"] = tmpl_row.get("constraints") or {}
                # 产出骨架 + 参考范例：供 GenerationAgent 注入 prompt，稳定产出结构
                scenario["template_structure"] = tmpl_row.get("structure") or ""
                scenario["template_examples"] = tmpl_row.get("examples") or []
                # 多版本差异化维度：供 GenerationAgent 驱动各版本差异方向（留空用默认风格锚点）
                scenario["template_diff_dims"] = tmpl_row.get("differentiation_dims") or []
                # 适用渠道：供 ChannelAgent 做适配性告警（留空表示不限渠道）
                scenario["template_applicable_channels"] = tmpl_row.get("applicable_channels") or []
            elif tmpl_row:
                print(f"[orchestrator] 模板 {template_id} 未通过审核（{tmpl_row.get('status')}），使用场景默认逻辑")
            else:
                print(f"[orchestrator] 模板 {template_id} 不存在，使用场景默认逻辑")
        # 模板被采用 -> 使用次数 +1（仅 approved 模板会加载成功，scenario 带 template_name）
        if template_id and scenario.get("template_name"):
            self._bump_template_use(template_id)
        # 兼容旧数据：如果 scenario 本身没有 template 字段，提供一个默认值
        if "template" not in scenario or not scenario.get("template"):
            scenario["template"] = f"根据场景「{scenario['name']}」生成内容，用户参数：{params}"

        # ===== 第 2 步：构建共享上下文 =====
        ctx = AgentContext(
            product=product,
            scenario=scenario,
            channel=channel,
            style=style,
            params=params,
            version_count=version_count,
        )

        # ===== 第 3 步：执行 Agent 链路（生成->渠道->校验 可返工重试） =====
        trace: list[dict] = []    # 执行链路追踪

        # ① 检索
        trace.append(self.retrieval.execute(ctx))

        # ② 竞品分析（仅竞品场景激活，其他场景跳过）
        trace.append(self.competitor.execute(ctx))

        # ③④⑤⑥ 生成 -> 渠道适配 -> 校验：校验失败则带反馈返工，最多重试 MAX_REGEN 次
        MAX_REGEN = 2    # 返工上限（总生成次数 = 1 + MAX_REGEN = 3）
        validated = False
        issues: list[str] = []
        for attempt in range(1 + MAX_REGEN):
            trace.append(self.generation.execute(ctx))
            trace.append(self.channel.execute(ctx))
            val_step = self.validation.execute(ctx)
            trace.append(val_step)

            val_output = val_step.get("output") or {}
            if isinstance(val_output, dict):
                issues = val_output.get("issues", [])
                validated = val_output.get("validated", False)
            else:
                issues, validated = [], False

            if validated or attempt >= MAX_REGEN:
                break
            # 返工：把上次校验问题反馈给下次生成（GenerationAgent 会注入 prompt 规避）
            ctx.feedback_issues = list(issues)

        # ⑤ 文生图（校验通过或重试用尽后配图，避免对失败版本白做）
        trace.append(self.image.execute(ctx))

        # ===== 第 4 步：汇总校验结果（issues/validated 已在循环中取得） =====

        # ===== 第 5 步：提取最终版本内容 =====
        # 优先用适配后的 versions，没有则用初稿 draft_versions
        versions = ctx.versions or ctx.draft_versions or []

        # SEO 分析（自动执行，不阻断流程）
        self._enrich_seo(versions)
        seo_scores = [v.get("seo", {}).get("score", 0) for v in versions if v.get("seo")]
        if seo_scores:
            trace.append({
                "agent": "SEO 分析",
                "status": "success",
                "message": f"已完成 {len(seo_scores)} 个版本的 SEO 分析，评分：{'/'.join(str(s) for s in seo_scores)}",
                "duration_ms": 0,
                "output": {"scores": seo_scores},
            })

        version_objs = [
            VersionContent(
                index=v.get("index", i + 1),
                title=v.get("title", ""),
                body=v.get("body", ""),
                tags=v.get("tags", []),
                image=v.get("image"),                                           # 文生图配图（首图，向后兼容）
                images=v.get("images", []),                                      # 全部配图（前端按小节穿插展示）
                votes=v.get("votes", {"like": 0, "dislike": 0}),                # A/B 测试票数
                voters=v.get("voters", {}),                                     # 已投票成员 {id: 方向}
                seo=v.get("seo"),                                                # SEO 分析结果
            )
            for i, v in enumerate(versions)
        ]

        # ===== 第 6 步：持久化到 history 表 =====
        history_id = f"H{uuid.uuid4().hex[:8]}"
        with transaction() as cur:
            cur.execute(
                """INSERT INTO history
                (id, product_id, product_name, scenario_id, scenario_name,
                 channel, style, params, versions, agent_trace, validated, issues, created_by)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                (
                    history_id,
                    product_id,
                    product["name"],
                    scenario_id,
                    scenario["name"],
                    channel,
                    style,
                    Json(params),
                    Json([v.model_dump() for v in version_objs]),
                    Json(trace),
                    validated,
                    Json(issues),
                    created_by,
                ),
            )

        # ===== 第 7 步：返回生成响应 =====
        return GenerateResponse(
            history_id=history_id,
            product_name=product["name"],
            scenario_name=scenario["name"],
            channel=channel,
            style=style,
            versions=version_objs,
            agent_trace=[AgentStep(**t) for t in trace],    # **t 把字典展开为关键字参数
            validated=validated,
            issues=issues,
        )

    # ===== SEO 分析富化（深度集成：自动执行，不阻断流程）=====

    def _enrich_seo(self, versions: list[dict]) -> list[dict]:
        """为每个版本计算 SEO 分析结果，写入 v['seo']。

        纯规则引擎，无 LLM 调用，毫秒级完成。异常不阻断生成流程。
        """
        for v in versions:
            try:
                v["seo"] = seo_analyze(v.get("title", ""), v.get("body", ""))
            except Exception:
                v["seo"] = None
        return versions

    # ===== 多阶段交互式流程（新流程）=====
    # 阶段1 run_draft：检索->生成->校验（只跑一次，不返工）
    # 阶段3 run_adapt：单版本->多渠道适配
    # 阶段4 run_images：对多渠道版本配图
    # 阶段2（用户选版+改内容）无 Agent 参与，由 router 直接写草稿

    def _load_product(self, product_id: str) -> dict:
        """加载产品（含 JSONB 字段解析）。不存在抛 ValueError。"""
        row = query_one("SELECT * FROM products WHERE id = %s", (product_id,))
        if not row:
            raise ValueError(f"产品 {product_id} 不存在")
        return _parse_json_fields(
            row, ["features", "target_customers", "selling_points", "competitors"]
        )

    def _load_scenario(self, scenario_id: str, template_id: str | None) -> dict:
        """加载场景并注入模板字段（与 run() 一致）。不存在抛 ValueError。"""
        row = query_one("SELECT * FROM scenarios WHERE id = %s", (scenario_id,))
        if not row:
            raise ValueError(f"场景 {scenario_id} 不存在")
        scenario = _parse_json_fields(row, ["parameters"])
        if template_id:
            tmpl = query_one(
                "SELECT * FROM templates WHERE id = %s AND scenario_id = %s",
                (template_id, scenario_id),
            )
            if tmpl and tmpl.get("status") == "approved":
                scenario["template"] = tmpl["prompt"]
                scenario["template_name"] = tmpl["name"]
                scenario["template_constraints"] = tmpl.get("constraints") or {}
                scenario["template_structure"] = tmpl.get("structure") or ""
                scenario["template_examples"] = tmpl.get("examples") or []
                scenario["template_diff_dims"] = tmpl.get("differentiation_dims") or []
                scenario["template_applicable_channels"] = tmpl.get("applicable_channels") or []
            elif tmpl:
                # 模板未通过审核 -> 不采用，回退场景默认（前端选择器已只显示 approved，这是兜底）
                print(f"[orchestrator] 模板 {template_id} 未通过审核（{tmpl.get('status')}），使用场景默认逻辑")
        if "template" not in scenario or not scenario.get("template"):
            scenario["template"] = f"根据场景「{scenario['name']}」生成内容"
        return scenario

    def _bump_template_use(self, template_id: str | None) -> None:
        """模板被用于生成时使用次数 +1。仅 approved 模板会加载成功（非 approved 不计）。

        计数失败不影响生成流程。
        """
        if not template_id:
            return
        try:
            execute("UPDATE templates SET use_count = use_count + 1 WHERE id = %s", (template_id,))
        except Exception:
            pass

    def run_draft(self, product_id: str, scenario_id: str, template_id: str | None,
                  style: str, params: dict, version_count: int = 3,
                  on_step: Callable[[dict], None] | None = None) -> dict:
        """阶段1：检索 -> 生成 -> 校验（只跑一次，不返工）。

        渠道适配与文生图不在本阶段。校验问题交由前端展示，用户决定是否重新生成。
        返回 {retrieved_info, draft_versions, validation, agent_trace}。

        on_step：可选的流式回调，每个 Agent 执行前/后各推送一次步骤事件
        （执行前推 {agent, status:"running"}，执行后推完整 step dict）。
        不传时按原同步行为执行，不影响调用方。
        """
        product = self._load_product(product_id)
        scenario = self._load_scenario(scenario_id, template_id)
        # 模板被采用 -> 使用次数 +1（仅 approved 模板会加载成功）
        if template_id and scenario.get("template_name"):
            self._bump_template_use(template_id)

        ctx = AgentContext(
            product=product,
            scenario=scenario,
            style=style,
            params=params,
            version_count=version_count,
        )

        trace: list[dict] = []

        def _emit(step: dict) -> None:
            """把单个步骤事件推给流式订阅者（无订阅者时为空操作）。"""
            if on_step:
                try:
                    on_step(step)
                except Exception:
                    pass    # 回调异常不得影响生成主流程

        def _run(agent: BaseAgent) -> dict:
            """执行一个 Agent：先推送 running，再执行，最后推送实际步骤。"""
            _emit({"agent": agent.name, "status": "running"})
            step = agent.execute(ctx)
            trace.append(step)
            _emit(step)
            return step

        # ① 检索
        _run(self.retrieval)
        if not ctx.retrieved_info:
            raise ValueError("产品信息检索失败，无法生成")
        # ② 竞品分析（仅竞品场景激活，其他场景跳过）
        _run(self.competitor)
        # ③④ 逐版本生成 + 单版本校验 + 重试（每版 1 初试 + 最多 2 次重试）
        val_output = self._generate_versions_with_retry(ctx, trace, _emit)
        if not ctx.draft_versions:
            raise ValueError("内容生成失败，未产出任何版本")

        # SEO 分析（初稿阶段自动执行；纯规则引擎，毫秒级）
        _emit({"agent": "SEO 分析", "status": "running"})
        self._enrich_seo(ctx.draft_versions)
        seo_scores = [v.get("seo", {}).get("score", 0) for v in ctx.draft_versions if v.get("seo")]
        if seo_scores:
            seo_step = {
                "agent": "SEO 分析",
                "status": "success",
                "message": f"已完成 {len(seo_scores)} 个初稿版本的 SEO 分析，评分：{'/'.join(str(s) for s in seo_scores)}",
                "duration_ms": 0,
                "output": {"scores": seo_scores},
            }
            trace.append(seo_step)
            _emit(seo_step)

        return {
            "retrieved_info": ctx.retrieved_info,
            "draft_versions": ctx.draft_versions,
            "validation": val_output,
            "agent_trace": trace,
            "product_name": product["name"],
            "scenario_name": scenario["name"],
            "template_name": scenario.get("template_name"),
        }

    def _generate_versions_with_retry(self, ctx: AgentContext, trace: list, emit) -> dict:
        """逐版本生成：每版独立 生成->校验->重试(最多2次)，结果累加到 ctx.draft_versions。

        每版开始/完成各 emit 一次版本事件，供前端流式展示"版本N·特色 已生成"。
        返回汇总 {"issues","validated"} 并把校验步骤写入 trace。
        """
        version_count = ctx.version_count or 1
        all_issues: list[str] = []
        all_validated = True
        for i in range(version_count):
            dim = self.generation.dim_for_version(ctx.scenario, i)
            emit({"kind": "version_start", "index": i + 1, "dim": dim})
            version, attempts, issues = self._gen_one_with_retry(ctx, i, emit)
            ctx.draft_versions.append(version)
            if issues:
                all_validated = False
                all_issues.extend(issues)
            emit({
                "kind": "version_done", "index": i + 1, "dim": dim,
                "attempts": attempts, "validated": not issues, "issues": issues,
            })
        trace.append({
            "agent": "内容校验 Agent",
            "status": "success" if all_validated else "warning",
            "message": "全部版本校验通过" if all_validated else f"发现 {len(all_issues)} 项需关注的问题",
            "duration_ms": 0,
            "output": {"issues": all_issues, "validated": all_validated},
        })
        return {"issues": all_issues, "validated": all_validated}

    def _gen_one_with_retry(self, ctx: AgentContext, version_index: int, emit) -> tuple[dict, int, list[str]]:
        """单个版本：生成->校验，失败带 feedback 重试，最多 3 次尝试（1 初试 + 2 重试）。

        返回 (version, attempts, issues)；issues 为空表示该版本校验通过。
        """
        max_attempts = 3
        last_issues: list[str] = []
        version: dict = {}
        for attempt in range(1, max_attempts + 1):
            ctx.feedback_issues = list(last_issues) if attempt > 1 else []
            if attempt > 1:
                emit({"kind": "version_attempt", "index": version_index + 1, "attempt": attempt})
            version = self.generation.generate_one(ctx, version_index)
            result = self.validation.validate_single(version, ctx)
            if result["validated"]:
                return version, attempt, []
            last_issues = result["issues"]
        return version, max_attempts, last_issues

    def run_adapt(self, selected_version: dict, channels: list[str],
                  scenario_id: str, template_id: str | None) -> dict:
        """阶段3：把用户选定的 1 个版本适配到多个渠道，每渠道 1 版。

        返回 {versions, skipped}。skipped 为未知渠道列表。
        """
        if not selected_version:
            raise ValueError("未选定版本，无法适配")
        if not channels:
            raise ValueError("未选择任何渠道")
        scenario = self._load_scenario(scenario_id, template_id)
        versions, skipped = self.channel.adapt_to_channels(selected_version, channels, scenario)
        if not versions:
            raise ValueError("渠道适配失败：所选渠道均无效")
        # SEO 分析（适配后的各渠道版本重新评估：渠道适配改变了正文语气/排版，必须重算）
        self._enrich_seo(versions)
        return {"versions": versions, "skipped": skipped}

    def run_images(self, versions: list[dict], scenario_id: str,
                   retrieved_info: dict) -> dict:
        """阶段4：对多渠道版本逐个配图。

        返回 {versions, image_step}。配图失败不阻断（图片字段留空）。
        """
        scenario = self._load_scenario(scenario_id, None)
        ctx = AgentContext(scenario=scenario, retrieved_info=retrieved_info or {})
        ctx.versions = versions
        image_step = self.image.execute(ctx)
        return {"versions": ctx.versions, "image_step": image_step}

    # ===== 单版本微调（初稿阶段）=====
    def run_rewrite(self, draft: dict, version_index: int, instruction: str) -> dict:
        """微调初稿中指定版本：重写 -> 重校验 -> 重算 SEO。不落库（由路由层持久化）。

        返回 {"version": 重写后的版本, "issues": [...], "validated": bool}。
        """
        versions = draft.get("draft_versions") or []
        target = next((v for v in versions if v.get("index") == version_index), None)
        if target is None:
            raise ValueError(f"版本 {version_index} 不存在")
        scenario = self._load_scenario(draft["scenario_id"], draft.get("template_id"))
        ctx = AgentContext(
            scenario=scenario,
            retrieved_info=draft.get("retrieved_info") or {},
            params=draft.get("params") or {},
        )
        rewritten = self.generation.rewrite_one(target, instruction, ctx)
        val = self.validation.validate_single(rewritten, ctx)
        rewritten["seo"] = seo_analyze(rewritten.get("title", ""), rewritten.get("body", ""))
        return {"version": rewritten, "issues": val["issues"], "validated": val["validated"]}


# 单例模式：全局只创建一个 Orchestrator 实例
_orchestrator: Orchestrator | None = None


def get_orchestrator() -> Orchestrator:
    """获取 Orchestrator 单例。

    第一次调用时创建，后续调用返回同一个实例。
    避免每次请求都重新创建 Agent 实例。
    """
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = Orchestrator()
    return _orchestrator