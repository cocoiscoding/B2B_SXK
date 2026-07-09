"""竞品分析 Agent：在竞品对比场景下，组织我方与竞品的对比信息。

这是多 Agent 链路的第 2 个 Agent。

设计特点：
- 仅在竞品分析场景激活（场景名包含"竞品"）
- 其他场景直接跳过，不影响流程

对应需求：F3-2 竞品分析 Agent
"""
from app.agents.base import BaseAgent, AgentContext


class CompetitorAgent(BaseAgent):
    """竞品分析 Agent。"""

    name = "竞品分析 Agent"
    description = "对比我方产品与竞品，输出结构化差异信息供生成 Agent 使用。"

    def _execute(self, ctx: AgentContext) -> tuple[str, str, dict]:
        """执行竞品分析。

        如果不是竞品场景，直接跳过。
        """
        scenario_name = ctx.scenario.get("name", "")
        # 非竞品场景：跳过
        if "竞品" not in scenario_name:
            return "success", "非竞品分析场景，跳过", {}

        # 从上下文获取检索到的产品信息
        info = ctx.retrieved_info
        product_name = info.get("product_name", "")
        user_competitor = ctx.params.get("competitor", "")       # 用户输入的竞品名
        known_competitors = info.get("competitors", [])          # 知识库中的竞品列表

        # 竞品名称：优先用户输入，其次取知识库中记录的首个竞品
        competitor_name = user_competitor or (known_competitors[0] if known_competitors else "未知竞品")

        focus = ctx.params.get("focus", "功能全面性")            # 对比重点
        our_sp = info.get("selling_points", [])                  # 我方卖点
        our_feats = info.get("features", [])                     # 我方功能

        # 构建对比框架（供生成 Agent 使用）
        comparison = {
            "our_product": product_name,
            "competitor": competitor_name,
            "focus": focus,
            "our_strengths": our_sp,
            "our_features": [f["name"] for f in our_feats],      # 列表推导式提取功能名
            "competitor_known": competitor_name in known_competitors,  # 竞品是否在知识库中
            "competitor_estimated": {
                "定位": f"市场主要竞品（{focus}维度对比）",
                "备注": f"竞品「{competitor_name}」详细参数需销售团队补充，以下为我方差异化建议。",
            },
        }
        # 写入上下文
        ctx.competitor_info = comparison
        return "success", (
            f"已构建「{product_name} vs {competitor_name}」对比框架，"
            f"聚焦「{focus}」，我方 {len(our_sp)} 个差异化卖点已标注"
        ), comparison