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
from app.database import query


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
            "competitors": product.get("competitors", []),
        }

        # 用户指定的重点卖点优先标注
        highlight = params.get("highlight", "")
        if highlight:
            info["highlight"] = highlight

        # 查询该产品的历史用户反馈（点赞/踩），供生成 Agent 学习用户偏好
        ctx.feedback_examples = self._load_feedback_examples(product.get("id", ""))

        # 写入上下文，供下游 Agent 使用
        ctx.retrieved_info = info

        # 构建执行信息（展示给用户）
        feat_count = len(info.get("features", []))
        sp_count = len(info.get("selling_points", []))
        liked = len(ctx.feedback_examples.get("liked", []))
        disliked = len(ctx.feedback_examples.get("disliked", []))
        fb_note = f"；历史反馈 {liked} 赞/{disliked} 踩" if (liked or disliked) else ""

        return "success", (
            f"已获取产品信息：{info['product_name']}；"
            f"包含 {feat_count} 项功能、{sp_count} 个卖点{fb_note}"
        ), info

    @staticmethod
    def _load_feedback_examples(product_id: str) -> dict[str, list]:
        """从 history 表查询该产品的历史反馈样本（per-user 聚合）。

        - feedback_voters 中有 like 的记录 -> 取首个版本作为正例
        - feedback_voters 中有 dislike 的记录 -> 取首个版本作为反例
        - 兼容老数据：无 feedback_voters 时按 feedback 单值归类

        每类最多取 2 条，避免 prompt 过长。
        """
        if not product_id:
            return {"liked": [], "disliked": []}
        rows = query(
            "SELECT versions, feedback_voters, feedback FROM history "
            "WHERE product_id = %s AND (feedback_voters IS NOT NULL AND feedback_voters != '{}'::jsonb "
            "OR feedback IS NOT NULL) "
            "ORDER BY created_at DESC LIMIT 6",
            (product_id,),
        )
        liked: list[dict] = []
        disliked: list[dict] = []
        for r in rows:
            versions = r.get("versions") or []
            if not versions:
                continue
            sample = {"title": versions[0].get("title", ""), "body": versions[0].get("body", "")}
            # 优先读 feedback_voters（per-user 明细）：任一用户 like -> 正例，任一 dislike -> 反例
            voters = r.get("feedback_voters") or {}
            if isinstance(voters, dict) and voters:
                votes = set(voters.values())
                if "like" in votes and len(liked) < 2:
                    liked.append(sample)
                if "dislike" in votes and len(disliked) < 2:
                    disliked.append(sample)
            else:
                # 兼容老数据：feedback 单值
                fb = r.get("feedback")
                if fb == "like" and len(liked) < 2:
                    liked.append(sample)
                elif fb == "dislike" and len(disliked) < 2:
                    disliked.append(sample)
        return {"liked": liked, "disliked": disliked}