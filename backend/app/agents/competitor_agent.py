"""竞品分析 Agent：通过 Tavily 联网搜索获取真实竞品信息，构建结构化对比框架。

这是多 Agent 链路的第 2 个 Agent。

设计特点：
- 仅在竞品分析场景激活（场景名包含"竞品"）
- 其他场景直接跳过，不影响流程
- LLM 模式：Tavily 搜索竞品信息 → LLM 提炼结构化对比
- Mock 模式：回退规则化对比框架（不联网）
- Tavily 未配置 Key / 搜索失败自动降级，不阻断流程

对应需求：F3-2 竞品分析 Agent
"""
import json
import uuid
from app.agents.base import BaseAgent, AgentContext
from app.agents.llm_provider import LLMProvider
from app.database import query_one, execute
from psycopg2.extras import Json
from config import TAVILY_API_KEY, COMPETITOR_CACHE_DAYS


class CompetitorAgent(BaseAgent):
    """竞品分析 Agent。"""

    name = "竞品分析 Agent"
    description = "搜索竞品信息并输出结构化差异分析供生成 Agent 使用。"

    def __init__(self, llm: LLMProvider | None = None):
        super().__init__(llm)

    def _execute(self, ctx: AgentContext) -> tuple[str, str, dict]:
        """执行竞品分析。

        如果不是竞品场景，直接跳过。
        分析结果自动入库（按 产品+竞品 维度），新鲜缓存直接复用，避免重复跑 Tavily+LLM。
        """
        scenario_name = ctx.scenario.get("name", "")
        # 非竞品场景：跳过
        if "竞品" not in scenario_name:
            return "success", "非竞品分析场景，跳过", {}

        # 从上下文获取检索到的产品信息
        info = ctx.retrieved_info
        product_name = info.get("product_name", "")
        product_id = ctx.product.get("id", "")
        user_competitor = ctx.params.get("competitor", "")       # 用户输入的竞品名
        known_competitors = info.get("competitors", [])          # 知识库中的竞品列表

        # 竞品名称：优先用户输入，其次取知识库中记录的首个竞品
        competitor_name = user_competitor or (known_competitors[0] if known_competitors else "未知竞品")

        focus = ctx.params.get("focus", "功能全面性")            # 对比重点

        # 1) 缓存命中且新鲜 -> 直接复用已入库分析，跳过昂贵的 Tavily 搜索 + LLM
        cached = self._load_cached_analysis(product_id, competitor_name)
        if cached:
            comparison, src = cached
            method = f"复用已入库分析（{self._method_label(src)}）"
        else:
            # 2) 未命中 / 过期 -> 执行分析
            comparison, source = self._analyze(info, competitor_name, focus)
            method = self._method_label(source)
            # 3) 入库（UPSERT），下次直接复用
            self._store_analysis(product_id, competitor_name, comparison, source)

        # 写入上下文
        ctx.competitor_info = comparison
        our_sp = info.get("selling_points", [])
        return "success", (
            f"已构建「{product_name} vs {competitor_name}」对比框架（{method}），"
            f"聚焦「{focus}」，我方 {len(our_sp)} 个差异化卖点已标注"
        ), comparison

    @staticmethod
    def _method_label(source: str) -> str:
        """分析来源 -> 展示标签。"""
        return {
            "tavily": "Tavily 搜索 + LLM 分析",
            "llm_common_sense": "LLM 分析（联网未果，基于常识）",
            "llm": "LLM 分析（未联网）",   # 兼容旧存量行
            "mock": "规则分析",
        }.get(source, "规则分析")

    def _analyze(self, info: dict, competitor_name: str, focus: str) -> tuple[dict, str]:
        """执行竞品分析，返回 (analysis, source)。source: tavily / llm_common_sense / mock。

        source 由 _analyze_with_llm 按实际是否用到联网数据 / 是否降级 mock 如实回传，
        不在此处凭 TAVILY_API_KEY 是否配置来猜（否则 Tavily 失败/空时仍误标 tavily）。
        """
        use_llm = self._use_llm
        if use_llm:
            return self._analyze_with_llm(info, competitor_name, focus)   # (analysis, actual_source)
        return self._mock_analyze(info, competitor_name, focus), "mock"

    @staticmethod
    def _load_cached_analysis(product_id: str, competitor_name: str):
        """查询已入库且未过期的竞品分析，返回 (analysis, source) 或 None。

        无 product_id / 未命中 / 已过期 / 数据损坏 都返回 None，由调用方触发重新分析。
        """
        if not product_id:
            return None
        row = query_one(
            """SELECT analysis, source FROM competitor_analyses
               WHERE product_id = %s AND competitor_name = %s
               AND updated_at > NOW() - %s::interval""",
            (product_id, competitor_name, f"{COMPETITOR_CACHE_DAYS} days"),
        )
        if not row:
            return None
        analysis = row.get("analysis")
        if not isinstance(analysis, dict) or not analysis:
            return None
        return analysis, row.get("source", "")

    @staticmethod
    def _store_analysis(product_id: str, competitor_name: str, analysis: dict, source: str) -> None:
        """UPSERT 竞品分析结果（按 产品+竞品 唯一，反复分析只留最新一条）。无 product_id 时跳过。"""
        if not product_id or not analysis:
            return
        ca_id = f"CA{uuid.uuid4().hex[:10]}"
        execute(
            """INSERT INTO competitor_analyses (id, product_id, competitor_name, analysis, source, updated_at)
               VALUES (%s, %s, %s, %s, %s, NOW())
               ON CONFLICT (product_id, competitor_name) DO UPDATE
               SET analysis = EXCLUDED.analysis,
                   source = EXCLUDED.source,
                   updated_at = NOW()""",
            (ca_id, product_id, competitor_name, Json(analysis), source),
        )

    # ===== Tavily 搜索 + LLM 分析（LLM 模式）=====

    def _search_competitor(self, name: str, focus: str, max_results: int = 5) -> list[dict]:
        """用 Tavily 搜索竞品信息。

        Tavily 是专为 AI Agent 设计的搜索引擎：
        - 返回结构化结果（title/url/content）
        - 中文搜索质量好
        - 需要 API Key（config.TAVILY_API_KEY）

        搜索失败或未配置 Key 时返回空列表，由调用方降级。
        """
        if not TAVILY_API_KEY:
            return []
        try:
            from tavily import TavilyClient
            client = TavilyClient(api_key=TAVILY_API_KEY)
            # 搜竞品产品信息，中文关键词
            query = f"{name} 产品 功能 价格 优势 2025 2026"
            resp = client.search(query, max_results=max_results)
            results = resp.get("results", [])
            # focus 有具体维度时补搜一轮
            if focus and focus not in ("功能全面性",):
                query2 = f"{name} {focus} 对比 评测"
                resp2 = client.search(query2, max_results=3)
                results.extend(resp2.get("results", []))
            # 去重（按 title 去重）
            seen = set()
            deduped = []
            for r in results:
                t = r.get("title", "")
                if t not in seen:
                    seen.add(t)
                    deduped.append(r)
            return deduped
        except Exception as e:
            print(f"[competitor] Tavily 搜索失败: {e}")
            return []

    def _analyze_with_llm(self, info: dict, competitor_name: str, focus: str) -> tuple[dict, str]:
        """用 LLM 分析搜索到的竞品信息，输出 (结构化对比框架, source)。

        source 如实反映本次分析的实际来源：
        - "tavily"：Tavily 搜到结果且 LLM 解析成功（用到了联网数据）
        - "llm_common_sense"：Tavily 未配 / 失败 / 空，LLM 基于行业常识解析成功
        - "mock"：LLM 解析失败，降级到规则分析
        Tavily 有 Key 时先搜索再分析；无 Key 时纯靠 LLM 行业知识。
        """
        if TAVILY_API_KEY:
            search_results = self._search_competitor(competitor_name, focus)
        else:
            search_results = []
        used_web = bool(search_results)   # 是否真正用到联网数据，决定 source

        # 构建搜索结果文本
        if search_results:
            search_text = "\n".join(
                f"- [{r.get('title', '')}]({r.get('url', '')})\n  {r.get('content', '')}"
                for r in search_results[:8]
            )
            source_note = "来自 Tavily 网络搜索"
        else:
            search_text = f"（未搜索到「{competitor_name}」的详细信息，请基于行业常识进行分析）"
            source_note = "基于行业常识分析（未联网）" if TAVILY_API_KEY else "LLM 行业知识分析（未配置 Tavily API Key）"

        product_name = info.get("product_name", "")
        features = info.get("features", [])
        selling_points = info.get("selling_points", [])
        pricing = info.get("pricing", "")
        target_customers = info.get("target_customers", [])

        user_prompt = f"""你是一位资深 B2B 行业分析师。基于以下信息，输出结构化竞品对比分析。

【我方产品】
名称：{product_name}
核心功能：{json.dumps([f.get("name") for f in features], ensure_ascii=False)}
功能详情：{json.dumps(features, ensure_ascii=False)}
核心卖点：{json.dumps(selling_points, ensure_ascii=False)}
目标客户：{json.dumps(target_customers, ensure_ascii=False)}
定价：{pricing}
对比重点：{focus}

【关于「{competitor_name}」的信息】
{search_text}

请输出 JSON 格式（严格 JSON，不要 markdown 代码块包裹）：
{{
  "competitor_name": "竞品名称",
  "competitor_positioning": "竞品的市场定位一句话概括",
  "source_note": "信息来源说明（如'{source_note}'）",
  "comparison_table": [
    {{"dimension": "对比维度", "us": "我方情况", "them": "竞品情况", "advantage": "我方/竞品/持平"}}
  ],
  "our_advantages": ["我方相对竞品的核心优势列表"],
  "their_advantages": ["竞品的优势/威胁列表"],
  "swot": {{
    "strengths": ["我方优势"],
    "weaknesses": ["我方劣势"],
    "opportunities": ["市场机会"],
    "threats": ["竞品威胁"]
  }},
  "sales_tips": ["针对竞品弱点的销售话术建议"]
}}

要求：
1. comparison_table 至少包含 4-6 个维度（功能、价格、目标客户、技术架构、服务等）
2. 每个维度需标注 advantage（我方/竞品/持平）
3. 不要编造数据，搜索结果不足时标注"信息不足，需核实"
4. 如完全无搜索结果，基于「{focus}」维度做合理的行业通用对比"""
        try:
            raw = self._llm.chat(
                "你是有10年经验的B2B产品与竞品分析师。输出严格 JSON，不要附加文字。",
                user_prompt,
                temperature=0.3,
            )
            parsed = self._parse_llm_json(raw)
            if parsed and isinstance(parsed, dict) and "competitor_name" in parsed:
                return parsed, ("tavily" if used_web else "llm_common_sense")
        except Exception as e:
            print(f"[competitor] LLM 分析失败: {e}")

        # 降级：mock 分析
        return self._mock_analyze(info, competitor_name, focus), "mock"

    @staticmethod
    def _parse_llm_json(raw: str) -> dict | None:
        """解析 LLM 返回的 JSON，兼容 ```json 包裹。"""
        try:
            text = raw.strip()
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
            return json.loads(text)
        except Exception:
            return None

    # ===== Mock 分析（无 LLM 模式 / LLM 降级）=====

    def _mock_analyze(self, info: dict, competitor_name: str, focus: str) -> dict:
        """Mock 模式：基于知识库信息做规则化对比。

        注意：竞品数据是估计的（无联网信息），生成 Agent 需在文案中注明。
        """
        our_sp = info.get("selling_points", [])
        our_feats = info.get("features", [])
        product_name = info.get("product_name", "")
        known_competitors = info.get("competitors", [])

        # 构建对比表：基于我方功能维度，逐项标注
        table = []
        for f in our_feats[:6]:
            table.append({
                "dimension": f.get("name", ""),
                "us": f.get("description", "支持"),
                "them": "待核实",
                "advantage": "我方",
            })
        # 补充通用维度
        common_dims = [
            {"dimension": "价格", "us": info.get("pricing", "待确认"), "them": "待核实", "advantage": "待核实"},
            {"dimension": "目标客户", "us": "、".join(info.get("target_customers", [])), "them": "待核实", "advantage": "待核实"},
        ]
        table.extend(common_dims)

        return {
            "competitor_name": competitor_name,
            "competitor_positioning": f"市场主要竞品（{focus}维度对比）",
            "source_note": f"基于知识库信息分析，竞品「{competitor_name}」详细参数需销售团队补充",
            "comparison_table": table,
            "our_advantages": our_sp,
            "their_advantages": [f"竞品在{f.get('name','')}方面可能有独特优势，需进一步调研" for f in our_feats[:2]],
            "swot": {
                "strengths": our_sp,
                "weaknesses": ["品牌知名度待提升", "需更多客户案例积累"],
                "opportunities": [f"在{focus}维度上存在差异化机会"],
                "threats": [f"竞品「{competitor_name}」在市场上已有一定影响力"],
            },
            "sales_tips": [
                f"强调我方在{focus}上的差异化优势",
                "准备竞品功能对比表，用数据说话",
                "针对竞品弱点，提前准备阻击话术",
            ],
        }
