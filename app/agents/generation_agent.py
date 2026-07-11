"""内容生成 Agent：基于完整产品信息 + 场景模板生成营销文案。

这是多 Agent 链路的第 2 个 Agent，是整个系统的核心。

生成依据：
1. 完整产品信息（来自 RetrievalAgent）
2. 用户选中的场景模板中定义的参数和格式（来自 scenario["template"]）

双模式：
- LLM 启用时：单次调用批量生成多版本（同一上下文天然差异化，且只需 1 次 HTTP），
  若返回版本数不足（截断/解析失败）则并发补齐
- Mock 模式：用模板 prompt 做参数替换生成

对应需求：F3-3 内容生成 Agent
"""
import json
from concurrent.futures import ThreadPoolExecutor
from app.agents.base import BaseAgent, AgentContext
from app.agents.llm_provider import LLMProvider
from app.agents.validation_agent import SENSITIVE_WORDS_HINT


class GenerationAgent(BaseAgent):
    """内容生成 Agent。"""

    name = "内容生成 Agent"
    description = "基于产品信息与场景模板，生成营销文案。"

    def __init__(self, llm: LLMProvider | None = None):
        super().__init__(llm)

    def _execute(self, ctx: AgentContext) -> tuple[str, str, list]:
        """执行内容生成，返回多个版本。"""
        info = ctx.retrieved_info
        if not info:
            return "error", "无可用产品信息，无法生成", []

        scenario_name = ctx.scenario.get("name", "")
        template_name = ctx.scenario.get("template_name", "默认模板")
        version_count = ctx.version_count or 1

        versions = []
        if self._llm and self._llm.name != "mock-engine":
            # LLM 模式：一次生成多个版本
            versions = self._generate_with_llm_multi(ctx, version_count)
        else:
            # Mock 模式：循环生成多个版本
            for i in range(version_count):
                version = self._generate_mock(ctx, version_index=i)
                versions.append(version)

        ctx.draft_versions = versions
        return "success", f"已基于模板「{template_name}」生成「{scenario_name}」{len(versions)}个版本", versions

    # ===== LLM 生成模式 =====

    def _generate_with_llm_multi(self, ctx: AgentContext, version_count: int) -> list:
        """使用真实 LLM 生成多个版本：单次批量 + 不足并发补齐。

        主路径是一次调用让 LLM 在同一上下文里产出全部版本——同一推理内天然
        保证各版本互异，且只需 1 次 HTTP（替代原先 N 次串行调用）。
        若返回数量不足（输出被截断或解析失败），用并发补齐缺口。
        """
        versions = self._generate_batch_with_llm(ctx, version_count)
        if len(versions) < version_count:
            missing = version_count - len(versions)
            versions.extend(
                self._generate_versions_concurrent(ctx, start_index=len(versions), count=missing)
            )
        # 保证 index 连续（1..N）并截断到目标数量
        for i, v in enumerate(versions):
            v["index"] = i + 1
        return versions[:version_count]

    def _generate_batch_with_llm(self, ctx: AgentContext, version_count: int) -> list:
        """单次调用 LLM 生成多版本（主路径）。失败/不足时返回已解析部分。"""
        sys_prompt = (
            "你是资深产品营销文案专家，擅长根据产品信息和模板要求生成高质量营销内容。"
            "严格遵循模板的格式和参数要求，使用产品知识库中的信息，不得编造数据。"
            "本次需一次性产出多个差异化版本，输出 JSON 数组。"
        )
        user_prompt = self._build_batch_prompt(ctx, version_count)
        raw = self._llm.chat(sys_prompt, user_prompt, temperature=0.8)
        return self._parse_llm_batch_output(raw)

    def _generate_versions_concurrent(self, ctx: AgentContext, start_index: int, count: int) -> list:
        """并发生成指定数量版本（batch 不足时补齐用）。

        httpx.Client 线程安全，多线程共享同一 provider 的 client 即可。
        workers 上限 4，避免对 LLM API 造成过大并发压力。
        """
        if count <= 0:
            return []
        workers = min(count, 4)

        def gen(offset: int) -> dict:
            # 复用单版本生成：每个 offset 对应不同 style hint，保证补齐版本间也有差异
            return self._generate_with_llm(ctx, version_index=start_index + offset)

        with ThreadPoolExecutor(max_workers=workers) as ex:
            return list(ex.map(gen, range(count)))

    def _format_prompt_extras(self, scenario: dict) -> str:
        """构造模板的产出骨架 + 参考范例增强段（无则返回空串）。

        两段都是 prompt 侧增强：骨架稳定产出结构，范例（few-shot）引导语气，
        都不改变产出格式（仍是 title/body/tags）。
        """
        parts = []
        structure = scenario.get("template_structure", "")
        if structure:
            parts.append(f"【产出骨架】\n{structure}")
        examples = scenario.get("template_examples", [])
        if examples:
            parts.append(
                "【参考范例】（学习其结构与语气，勿照抄具体内容）\n"
                + self._format_examples(examples)
            )
        return ("\n\n".join(parts) + "\n\n") if parts else ""

    @staticmethod
    def _format_examples(examples: list) -> str:
        """把范例列表格式化为可读文本。"""
        blocks = []
        for i, ex in enumerate(examples, 1):
            title = ex.get("title", "")
            body = ex.get("body", "")
            tags = "、".join(ex.get("tags", []))
            blocks.append(f"范例{i}：\n标题：{title}\n正文：{body}\n标签：{tags}")
        return "\n---\n".join(blocks)

    def _format_feedback(self, ctx: AgentContext) -> str:
        """构造返工反馈段：上次校验的问题，提示本次规避（无则返回空串）。

        orchestrator 在校验失败时把 issues 写入 ctx.feedback_issues，
        本方法将其注入 prompt，让 LLM 下次生成时主动避免同类问题。
        """
        issues = ctx.feedback_issues
        if not issues:
            return ""
        items = "\n".join(f"- {i}" for i in issues)
        return "【上次生成存在以下问题，本次务必避免】\n" + items + "\n\n"

    def _format_user_feedback(self, ctx: AgentContext) -> str:
        """构造用户历史偏好反馈段：注入点赞/踩样本，让 LLM 学习用户偏好。

        - 点赞的内容作为正例，引导 LLM 向其风格/结构靠拢
        - 踩的内容作为反例，提示 LLM 避免类似风格
        无反馈数据时返回空串，不影响生成。
        """
        examples = ctx.feedback_examples or {}
        liked = examples.get("liked", [])
        disliked = examples.get("disliked", [])
        if not liked and not disliked:
            return ""
        parts = ["【用户历史偏好参考】（基于该产品过往生成的点赞/踩反馈，请学习用户偏好）"]
        if liked:
            parts.append("用户认可的范例（请在风格、结构、语气上参考借鉴，勿照抄内容）：")
            for i, ex in enumerate(liked, 1):
                body = (ex.get("body") or "")[:200]
                parts.append(f"  范例{i} 标题：{ex.get('title', '')}\n  范例{i} 正文：{body}...")
        if disliked:
            parts.append("用户不认可的反例（请避免类似风格和写法）：")
            for i, ex in enumerate(disliked, 1):
                body = (ex.get("body") or "")[:150]
                parts.append(f"  反例{i} 标题：{ex.get('title', '')}\n  反例{i} 正文：{body}...")
        parts.append("")
        return "\n".join(parts) + "\n"

    def _format_competitor_block(self, ctx: AgentContext) -> str:
        """构造竞品分析信息段（仅竞品场景有值，其他场景返回空串）。

        供 _build_batch_prompt 与 _build_llm_prompt 共用，避免逻辑重复。
        """
        comp = ctx.competitor_info or {}
        if not comp.get("competitor_name"):
            return ""
        comp_lines = [f"竞品名称：{comp.get('competitor_name','')}"]
        if comp.get("competitor_positioning"):
            comp_lines.append(f"竞品定位：{comp['competitor_positioning']}")
        if comp.get("source_note"):
            comp_lines.append(f"信息来源：{comp['source_note']}")
        if comp.get("comparison_table"):
            comp_lines.append("对比表：")
            for row in comp["comparison_table"]:
                dim = row.get("dimension", "")
                us = row.get("us", "")
                them = row.get("them", "")
                adv = row.get("advantage", "")
                comp_lines.append(f"  - {dim}：我方={us}，竞品={them}，优势方={adv}")
        if comp.get("our_advantages"):
            comp_lines.append(f"我方优势：{'、'.join(comp['our_advantages'])}")
        if comp.get("their_advantages"):
            comp_lines.append(f"竞品优势：{'、'.join(comp['their_advantages'])}")
        if comp.get("swot"):
            swot = comp["swot"]
            comp_lines.append(f"SWOT-优势：{'、'.join(swot.get('strengths',[]))}")
            comp_lines.append(f"SWOT-劣势：{'、'.join(swot.get('weaknesses',[]))}")
        if comp.get("sales_tips"):
            comp_lines.append("销售话术建议：")
            for tip in comp["sales_tips"]:
                comp_lines.append(f"  - {tip}")
        return "\n".join(comp_lines) + "\n\n"

    def _format_hard_requirements(self, ctx: AgentContext) -> str:
        """把校验 Agent 的校验项转成生成时的硬性要求，前置注入 prompt。

        与 ValidationAgent 的校验逻辑一一对应：让 LLM 在生成阶段就知晓所有硬性
        边界（产品名/定价/敏感词/卖点覆盖/模板字数与参数约束），显著提高一次校验
        通过率，避免"待完善"反复返工。
        注意：敏感词列表须与 validation_agent.SENSITIVE_WORDS 保持一致。
        """
        info = ctx.retrieved_info
        params = ctx.params
        constraints = ctx.scenario.get("template_constraints") or {}
        lines: list[str] = []

        product_name = info.get("product_name", "")
        if product_name:
            lines.append(f"正文或标题中必须出现正确的产品名称「{product_name}」")

        pricing = info.get("pricing", "")
        if pricing:
            lines.append(f"定价须与知识库一致（{pricing}），不得编造或出现其他价格数字")

        # 敏感/绝对化用词（广告法违禁），与 validation_agent.SENSITIVE_PATTERNS 同步
        lines.append(f"严禁使用绝对化/违禁用词：{SENSITIVE_WORDS_HINT}")

        sp = info.get("selling_points", [])
        if sp:
            min_sp = constraints.get("min_selling_points")
            need = min_sp if isinstance(min_sp, int) and min_sp > 0 else 1
            lines.append(f"必须原样包含以下核心卖点中的至少 {need} 个（照搬原词，不得改写）：{'、'.join(sp)}")

        title_max = constraints.get("title_max_chars")
        if isinstance(title_max, int) and title_max > 0:
            lines.append(f"标题不超过 {title_max} 字")

        body_range = constraints.get("body_chars")
        if isinstance(body_range, list) and len(body_range) == 2:
            lo, hi = body_range
            parts = []
            if isinstance(lo, int) and lo > 0:
                parts.append(f"不少于 {lo}")
            if isinstance(hi, int) and hi > 0:
                parts.append(f"不超过 {hi}")
            if parts:
                lines.append(f"正文纯文字字数{'、'.join(parts)} 字（不含 markdown 符号与空白）")

        must_params = constraints.get("must_include_params", [])
        if must_params and params:
            for name in must_params:
                val = params.get(name)
                if val and len(str(val)) <= 50:
                    lines.append(f"必须原样包含用户指定的「{name}」：{val}")

        if not lines:
            return ""
        return "【硬性要求（必须全部满足，否则校验不通过）】\n" + "\n".join(f"- {l}" for l in lines) + "\n\n"

    def _build_batch_prompt(self, ctx: AgentContext, version_count: int) -> str:
        """构造单次批量生成多版本的提示词。"""
        info = ctx.retrieved_info
        scenario = ctx.scenario
        params = ctx.params
        template_prompt = scenario.get("template", "")

        product_info = (
            f"产品名称：{info.get('product_name','')}\n"
            f"产品描述：{info.get('description','')}\n"
            f"产品分类：{json.dumps(info.get('category',[]), ensure_ascii=False)}\n"
            f"核心功能：{json.dumps(info.get('features',[]), ensure_ascii=False)}\n"
            f"卖点：{json.dumps(info.get('selling_points',[]), ensure_ascii=False)}\n"
            f"目标客户：{json.dumps(info.get('target_customers',[]), ensure_ascii=False)}\n"
            f"定价：{info.get('pricing','')}\n"
        )
        params_text = json.dumps(params, ensure_ascii=False) if params else "无"

        # 竞品分析信息（仅竞品场景有值，其他场景为空）
        comp_block = self._format_competitor_block(ctx)

        # 多版本差异化维度：优先用模板指定，否则回退默认风格锚点
        dims = scenario.get("template_diff_dims") or []
        if not dims:
            dims = ["专业严谨", "活泼有趣", "情感共鸣", "创新独特"]
        style_lines = []
        for i in range(version_count):
            dim = dims[i] if i < len(dims) else dims[-1]
            style_lines.append(f"{i + 1}. {dim}")
        style_block = "\n".join(style_lines)

        extras = self._format_prompt_extras(scenario)
        feedback = self._format_feedback(ctx)
        user_fb = self._format_user_feedback(ctx)
        hard_req = self._format_hard_requirements(ctx)
        return (
            f"场景：{scenario.get('name','')}\n"
            f"渠道：{ctx.channel}\n"
            f"风格：{ctx.style}\n\n"
            f"【产品信息】\n{product_info}\n"
            f"【用户填写的参数】\n{params_text}\n\n"
            f"{comp_block}"
            f"【模板要求】\n{template_prompt}\n\n"
            f"{hard_req}"
            f"{extras}"
            f"{user_fb}"
            f"{feedback}"
            f"【需生成 {version_count} 个差异化版本，各版本差异化方向如下】\n{style_block}\n\n"
            "各版本必须在标题切入角度、行文语气、结构侧重上形成明显差异，不得雷同。"
            "严格遵循模板要求，使用产品知识库信息，不得编造数据。\n\n"
            f"输出 JSON 数组，恰好 {version_count} 个元素，每个元素格式："
            "{\"title\":\"...\",\"body\":\"...\",\"tags\":[\"...\"]}。"
            "body 中可用 markdown 格式。只输出 JSON 数组，不要附加解释文字。"
        )

    @staticmethod
    def _parse_llm_batch_output(raw: str) -> list:
        """解析 LLM 返回的 JSON 数组（多版本）。

        兼容 ```json 代码块包裹、以及 LLM 偶发返回单对象的情况。
        解析失败返回空列表，由调用方触发并发补齐。
        """
        text = raw.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        try:
            obj = json.loads(text)
        except (json.JSONDecodeError, IndexError):
            return []
        # 兼容：LLM 返回单个对象而非数组
        if isinstance(obj, dict):
            obj = [obj]
        if not isinstance(obj, list):
            return []
        versions = []
        for item in obj:
            if not isinstance(item, dict):
                continue
            versions.append({
                "index": len(versions) + 1,
                "title": item.get("title", "生成内容"),
                "body": item.get("body", ""),
                "tags": item.get("tags", []),
            })
        return versions

    def _generate_with_llm(self, ctx: AgentContext, version_index: int = 0) -> dict:
        """使用真实 LLM 生成单个版本。"""
        sys_prompt = (
            "你是资深产品营销文案专家，擅长根据产品信息和模板要求生成高质量营销内容。"
            "严格遵循模板的格式和参数要求，使用产品知识库中的信息，不得编造数据。输出 JSON。"
        )
        user_prompt = self._build_llm_prompt(ctx, version_index)
        raw = self._llm.chat(sys_prompt, user_prompt, temperature=0.7)
        result = self._parse_llm_output(raw)
        result["index"] = version_index + 1
        return result

    def generate_one(self, ctx: AgentContext, version_index: int = 0) -> dict:
        """生成单个版本（含特色 feature 字段），供 orchestrator 逐版本调用。

        根据是否启用 LLM 选择真实生成或 Mock，并把该版本的差异化特色（dim）
        写入返回结果的 feature 字段，供前端展示。
        """
        if self._llm and self._llm.name != "mock-engine":
            version = self._generate_with_llm(ctx, version_index)
        else:
            version = self._generate_mock(ctx, version_index)
        version["feature"] = self.dim_for_version(ctx.scenario, version_index)
        return version

    @staticmethod
    def dim_for_version(scenario: dict, version_index: int) -> str:
        """取指定版本的差异化特色：优先用模板 template_diff_dims，否则回退默认风格锚点。"""
        dims = scenario.get("template_diff_dims") or []
        if not dims:
            dims = ["专业严谨", "活泼有趣", "情感共鸣", "创新独特"]
        return dims[version_index] if version_index < len(dims) else dims[-1]

    def _build_llm_prompt(self, ctx: AgentContext, version_index: int = 0) -> str:
        """构造发给 LLM 的提示词。"""
        info = ctx.retrieved_info
        scenario = ctx.scenario
        params = ctx.params
        template_prompt = scenario.get("template", "")

        # 构建产品信息部分
        product_info = (
            f"产品名称：{info.get('product_name','')}\n"
            f"产品描述：{info.get('description','')}\n"
            f"产品分类：{json.dumps(info.get('category',[]), ensure_ascii=False)}\n"
            f"核心功能：{json.dumps(info.get('features',[]), ensure_ascii=False)}\n"
            f"卖点：{json.dumps(info.get('selling_points',[]), ensure_ascii=False)}\n"
            f"目标客户：{json.dumps(info.get('target_customers',[]), ensure_ascii=False)}\n"
            f"定价：{info.get('pricing','')}\n"
        )

        # 构建用户参数部分
        params_text = json.dumps(params, ensure_ascii=False) if params else "无"

        # 多版本差异化提示：优先用模板指定维度，否则回退默认风格
        dim = self.dim_for_version(scenario, version_index)
        version_hint = f"这是第 {version_index + 1} 个版本，请侧重「{dim}」，与前面版本形成差异。"

        extras = self._format_prompt_extras(scenario)
        feedback = self._format_feedback(ctx)
        user_fb = self._format_user_feedback(ctx)
        comp_block = self._format_competitor_block(ctx)
        hard_req = self._format_hard_requirements(ctx)
        return (
            f"场景：{scenario.get('name','')}\n"
            f"渠道：{ctx.channel}\n"
            f"风格：{ctx.style}\n\n"
            f"【产品信息】\n{product_info}\n"
            f"【用户填写的参数】\n{params_text}\n\n"
            f"{comp_block}"
            f"【模板要求】\n{template_prompt}\n\n"
            f"{hard_req}"
            f"{extras}"
            f"{user_fb}"
            f"{feedback}"
            f"【版本要求】\n{version_hint}\n\n"
            "请严格按照模板要求生成内容，输出 JSON 格式：{\"title\":\"...\",\"body\":\"...\",\"tags\":[\"...\"]}。"
            "body 中可用 markdown 格式。"
        )

    @staticmethod
    def _parse_llm_output(raw: str) -> dict:
        """解析 LLM 返回的 JSON。"""
        try:
            text = raw.strip()
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
            obj = json.loads(text)
            return {
                "index": 1,
                "title": obj.get("title", "生成内容"),
                "body": obj.get("body", raw),
                "tags": obj.get("tags", []),
            }
        except (json.JSONDecodeError, IndexError):
            return {"index": 1, "title": "生成内容", "body": raw, "tags": []}

    # ===== Mock 模板生成模式 =====

    def _generate_mock(self, ctx: AgentContext, version_index: int = 0) -> dict:
        """Mock 模式：基于模板 prompt 生成内容，支持多版本。"""
        info = ctx.retrieved_info
        scenario = ctx.scenario
        params = ctx.params

        # 获取模板 prompt
        template_prompt = scenario.get("template", "")
        if not template_prompt:
            # 模板为空时使用通用模板
            template_prompt = "根据产品信息生成营销内容"

        # 替换模板中的占位符（如 {highlight}、{cta}）
        filled_prompt = template_prompt
        for key, value in params.items():
            filled_prompt = filled_prompt.replace(f"{{{key}}}", str(value))

        # 构建内容
        product_name = info.get("product_name", "")
        description = info.get("description", "")
        features = info.get("features", [])
        selling_points = info.get("selling_points", [])

        # 构建功能列表文本
        features_text = "\n".join(
            f"- **{f.get('name', '')}**：{f.get('description', '')}"
            for f in features[:5]
        ) if features else "暂无功能信息"

        # 构建卖点文本
        sp_text = "、".join(selling_points[:4]) if selling_points else "高效可靠"

        # 根据版本索引生成不同风格的内容
        body = self._build_body_from_template(
            filled_prompt, product_name, description, features_text, sp_text, info, version_index
        )

        # 生成标题
        title = self._build_title_from_template(filled_prompt, product_name, version_index)

        # 生成标签
        tags = [scenario.get("name", "营销内容")]

        return {
            "index": version_index + 1,
            "title": title,
            "body": body,
            "tags": tags,
        }

    def _build_title_from_template(self, template_prompt: str, product_name: str, version_index: int = 0) -> str:
        """根据模板生成标题，支持多版本差异化。"""
        # 版本后缀
        version_suffix = f"（版本{version_index + 1}）" if version_index > 0 else ""

        # 简单规则：如果模板提到"Banner"，生成简短标题
        if "Banner" in template_prompt or "banner" in template_prompt.lower():
            return f"{product_name} · 核心亮点{version_suffix}"

        # 如果模板提到"案例"或"成功"
        if "案例" in template_prompt or "成功" in template_prompt:
            return f"{product_name} · 客户成功案例{version_suffix}"

        # 如果模板提到"对比"或"竞品"
        if "对比" in template_prompt or "竞品" in template_prompt:
            return f"{product_name} · 竞品分析{version_suffix}"

        # 如果模板提到"PPT"或"大纲"
        if "PPT" in template_prompt or "大纲" in template_prompt:
            return f"{product_name} · 演示大纲{version_suffix}"

        # 默认标题
        return f"{product_name} · 营销内容{version_suffix}"

    def _build_body_from_template(
        self, template_prompt: str, product_name: str,
        description: str, features_text: str, sp_text: str, info: dict,
        version_index: int = 0
    ) -> str:
        """根据模板 prompt 生成 body 内容，支持多版本差异化风格。"""
        # 根据版本索引调整风格
        style_hints = {
            0: "专业严谨",
            1: "活泼有趣",
            2: "情感共鸣",
            3: "创新独特"
        }
        style = style_hints.get(version_index, "专业严谨")
        
        # 如果模板提到"Banner"或"主标题"
        if "Banner" in template_prompt or "主标题" in template_prompt:
            if style == "活泼有趣":
                return f"## 🎉 {product_name} 来啦！\n\n{description}\n\n✨ **{sp_text}** ✨"
            elif style == "情感共鸣":
                return f"## {product_name}，与你同行\n\n{description}\n\n💪 **{sp_text}**"
            else:
                return f"## {product_name}\n\n{description}\n\n**{sp_text}**"

        # 如果模板提到"案例"或"STAR"
        if "案例" in template_prompt or "STAR" in template_prompt:
            if style == "活泼有趣":
                return (
                    f"## 🌟 {product_name} 的奇妙之旅\n\n"
                    f"### 故事开始\n\n有个客户遇到了大麻烦！🤔\n\n"
                    f"### 解决方案\n\n他们选择了 **{product_name}**，看看有多棒：\n{features_text}\n\n"
                    f"### 完美结局\n\n效率飞起，老板笑开花！😄\n\n"
                    f"> 「太棒了！」—— 开心到飞的客户"
                )
            elif style == "情感共鸣":
                return (
                    f"## {product_name} 的温暖故事\n\n"
                    f"### 困境\n\n每个企业都会遇到挑战，这个客户也不例外。\n\n"
                    f"### 转折\n\n直到遇见 **{product_name}**：\n{features_text}\n\n"
                    f"### 收获\n\n不仅是效率提升，更是信心的重建。\n\n"
                    f"> 「感谢 {product_name}，让我们重新找到了方向。」—— 客户心声"
                )
            else:
                return (
                    f"## {product_name} 客户成功案例\n\n"
                    f"### 背景\n\n客户面临业务挑战，需要高效解决方案。\n\n"
                    f"### 方案\n\n引入 **{product_name}**，核心能力：\n{features_text}\n\n"
                    f"### 成果\n\n客户业务效率显著提升，投资回报超预期。\n\n"
                    f"> 「{product_name} 让我们的业务更上一层楼。」—— 客户负责人"
                )

        # 如果模板提到"对比"或"竞品"
        if "对比" in template_prompt or "竞品" in template_prompt:
            if style == "活泼有趣":
                return (
                    f"## 🥊 {product_name} VS 竞品\n\n"
                    f"### 为什么选我们？\n\n{product_name} 超厉害：{sp_text}\n\n"
                    f"### 实力对比\n\n{features_text}\n\n"
                    f"### 结论\n\n选 {product_name}，不后悔！👍"
                )
            else:
                return (
                    f"## {product_name} 竞品对比分析\n\n"
                    f"### 核心优势\n\n{product_name} 的核心优势：{sp_text}\n\n"
                    f"### 功能对比\n\n{features_text}\n\n"
                    f"### 总结\n\n{product_name} 在功能全面性、性价比、服务支持等方面领先。"
                )

        # 如果模板提到"PPT"或"大纲"
        if "PPT" in template_prompt or "大纲" in template_prompt:
            if style == "活泼有趣":
                return (
                    f"## 🎬 {product_name} 精彩演示\n\n"
                    f"### 第 1 页：开场\n- {product_name}\n- {description[:50]}...\n\n"
                    f"### 第 2 页：超能力\n{features_text}\n\n"
                    f"### 第 3 页：为什么选我\n- {sp_text}\n\n"
                    f"### 第 4 页：行动\n- 定价：{info.get('pricing', '联系销售')}\n- 快来试试吧！"
                )
            else:
                return (
                    f"## {product_name} 演示大纲\n\n"
                    f"### 第 1 页：封面\n- {product_name}\n- {description[:50]}...\n\n"
                    f"### 第 2 页：核心功能\n{features_text}\n\n"
                    f"### 第 3 页：核心优势\n- {sp_text}\n\n"
                    f"### 第 4 页：总结\n- 定价：{info.get('pricing', '联系销售')}"
                )

        # 默认：产品介绍格式
        if style == "活泼有趣":
            return (
                f"## 🎉 {product_name} 闪亮登场！\n\n{description}\n\n"
                f"### 超能力清单\n{features_text}\n\n"
                f"### 为什么选我\n{sp_text}\n\n"
                f"> 定价：{info.get('pricing', '详见官网')} | 快来体验吧！"
            )
        elif style == "情感共鸣":
            return (
                f"## {product_name}，懂你的选择\n\n{description}\n\n"
                f"### 我们能帮你\n{features_text}\n\n"
                f"### 我们的承诺\n{sp_text}\n\n"
                f"> 定价：{info.get('pricing', '详见官网')} | 与我们同行"
            )
        else:
            return (
                f"## {product_name}\n\n{description}\n\n"
                f"### 核心功能\n{features_text}\n\n"
                f"### 核心优势\n{sp_text}\n\n"
                f"> 定价：{info.get('pricing', '详见官网')}"
            )
