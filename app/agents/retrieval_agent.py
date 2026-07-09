"""产品信息检索 Agent：直接查库获取完整产品信息。

这是多 Agent 链路的第 1 个 Agent，负责从知识库中获取产品信息。

执行流程：
1. 前端已明确选择产品，直接按 product_id 从上下文获取完整产品信息
2. 将完整产品信息写入上下文，供下游 Agent 使用

优化说明：
- 去掉了 LLM 推理（前端已明确选择产品，无需再让 LLM 生成查询）
- 去掉了向量检索（直接查库，性能更快）
- 去掉了规则过滤（直接传完整信息，让下游 Agent 自己决定用哪些）
"""
from app.agents.base import BaseAgent, AgentContext


class RetrievalAgent(BaseAgent):
    """产品信息检索 Agent。"""

    name = "产品信息检索 Agent"
    description = "从产品知识库中获取完整产品信息。"

    def _execute(self, ctx: AgentContext) -> tuple[str, str, dict]:
        """执行检索。

        返回 (status, message, info_dict)
        """
        product = ctx.product
        params = ctx.params

        if not product:
            return "error", "未找到产品信息", {}

        # 直接获取完整产品信息
        info: dict = {
            "product_name": product.get("name", ""),
            "product_id": product.get("id", ""),
            "description": product.get("description", ""),
            "category": product.get("category", []),
            "features": product.get("features", []),
            "target_customers": product.get("target_customers", []),
            "pricing": product.get("pricing", ""),
            "selling_points": product.get("selling_points", []),
        }

        # 用户指定的重点卖点优先标注
        highlight = params.get("highlight", "")
        if highlight:
            info["highlight"] = highlight

        # 写入上下文，供下游 Agent 使用
        ctx.retrieved_info = info

        # 构建执行信息（展示给用户）
        feat_count = len(info.get("features", []))
        sp_count = len(info.get("selling_points", []))

        return "success", (
            f"已获取产品信息：{info['product_name']}；"
            f"包含 {feat_count} 项功能、{sp_count} 个卖点"
        ), info