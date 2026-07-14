"""竞品分析管理 API：查看与删除已入库的竞品分析。

竞品分析结果由 CompetitorAgent 自动入库（按 产品+竞品 维度缓存，见 competitor_agent）。
本路由提供查看与删除（强制下次生成时重新分析）能力，让缓存可见、可控。
"""
from fastapi import APIRouter, HTTPException, Depends
from app.database import query, query_one, transaction
from app.auth import get_current_user, is_owner_or_admin
from config import COMPETITOR_CACHE_DAYS

router = APIRouter(prefix="/api/products", tags=["竞品分析"])


@router.get("/{product_id}/competitors")
def list_competitor_analyses(product_id: str, user: dict = Depends(get_current_user)):
    """列出某产品的所有已入库竞品分析（按更新时间倒序）。任何登录用户可看。

    返回字段：id / competitor_name / analysis(完整分析 JSON) / source / updated_at / expires_at
    expires_at = updated_at + COMPETITOR_CACHE_DAYS，据此判断缓存是否仍新鲜。
    """
    if not query_one("SELECT id FROM products WHERE id = %s", (product_id,)):
        raise HTTPException(404, f"产品 {product_id} 不存在")
    return query(
        """SELECT id, competitor_name, analysis, source, updated_at,
                  updated_at + %s * interval '1 day' AS expires_at
           FROM competitor_analyses WHERE product_id = %s
           ORDER BY updated_at DESC""",
        (COMPETITOR_CACHE_DAYS, product_id),
    )


@router.delete("/{product_id}/competitors/{competitor_name}")
def delete_competitor_analysis(
    product_id: str,
    competitor_name: str,
    user: dict = Depends(get_current_user),
):
    """删除某条竞品分析（强制下次生成时重新分析）。仅产品创建者或管理员可删。"""
    prod = query_one("SELECT id, created_by FROM products WHERE id = %s", (product_id,))
    if not prod:
        raise HTTPException(404, f"产品 {product_id} 不存在")
    if not is_owner_or_admin(user, prod.get("created_by")):
        raise HTTPException(403, "无权删除该产品的竞品分析")
    with transaction() as cur:
        cur.execute(
            "DELETE FROM competitor_analyses WHERE product_id = %s AND competitor_name = %s",
            (product_id, competitor_name),
        )
        deleted = cur.rowcount
    if not deleted:
        raise HTTPException(404, f"竞品「{competitor_name}」的分析不存在")
    return {"message": f"已删除竞品「{competitor_name}」的分析，下次生成将重新分析"}
