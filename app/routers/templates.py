"""模板管理 API：CRUD。

模板关联在场景之下，每个场景可包含多个模板。
模板定义了提示词/产出格式，供内容生成 Agent 使用。
"""
import uuid
from fastapi import APIRouter, HTTPException, Depends
from app.database import query, query_one, transaction
from psycopg2.extras import Json
from app.models import TemplateCreate, Template, TemplateReviewRequest, TemplateFeatureRequest
from app.auth import get_current_user, require_admin, is_owner_or_admin

router = APIRouter(prefix="/api/scenarios/{scenario_id}/templates", tags=["模板管理"])
_batch_router = APIRouter(prefix="/api/templates", tags=["模板管理（批量）"])


@_batch_router.get("/all")
def list_all_templates(user: dict = Depends(get_current_user)):
    """查询所有模板：已通过审核的 + 当前用户自建（待审/驳回也可见）；管理员看全部。

    按推荐 > 使用次数 > 时间排序，让优秀模板浮上来。
    """
    if user.get("is_admin"):
        rows = query(
            "SELECT * FROM templates ORDER BY is_featured DESC, use_count DESC, created_at DESC"
        )
    else:
        rows = query(
            "SELECT * FROM templates WHERE status='approved' OR created_by=%s "
            "ORDER BY is_featured DESC, use_count DESC, created_at DESC",
            (user["id"],),
        )
    return rows


@_batch_router.put("/{template_id}/review", response_model=Template)
def review_template(template_id: str, body: TemplateReviewRequest,
                    user: dict = Depends(require_admin)):
    """审核模板（仅管理员）：通过 approved / 驳回 rejected（带 note）。"""
    existing = query_one("SELECT id FROM templates WHERE id = %s", (template_id,))
    if not existing:
        raise HTTPException(404, f"模板 {template_id} 不存在")
    decision = (body.decision or "").strip()
    if decision not in ("approved", "rejected"):
        raise HTTPException(400, "decision 需为 approved / rejected")
    with transaction() as cur:
        cur.execute(
            """UPDATE templates SET status=%s, reviewed_by=%s, reviewed_at=NOW(), review_note=%s
               WHERE id=%s""",
            (decision, user["id"], body.note or "", template_id),
        )
    return query_one("SELECT * FROM templates WHERE id = %s", (template_id,))


@_batch_router.put("/{template_id}/feature", response_model=Template)
def feature_template(template_id: str, body: TemplateFeatureRequest,
                     user: dict = Depends(require_admin)):
    """切换模板推荐标记（仅管理员）。"""
    existing = query_one("SELECT id FROM templates WHERE id = %s", (template_id,))
    if not existing:
        raise HTTPException(404, f"模板 {template_id} 不存在")
    with transaction() as cur:
        cur.execute("UPDATE templates SET is_featured=%s WHERE id=%s", (body.featured, template_id))
    return query_one("SELECT * FROM templates WHERE id = %s", (template_id,))


@router.get("", response_model=list[Template])
@router.get("/", response_model=list[Template], include_in_schema=False)
def list_templates(scenario_id: str, user: dict = Depends(get_current_user)):
    """查询指定场景下的所有模板：已通过审核的 + 当前用户自建；管理员看全部。"""
    scenario = query_one("SELECT id FROM scenarios WHERE id = %s", (scenario_id,))
    if not scenario:
        raise HTTPException(404, f"场景 {scenario_id} 不存在")
    if user.get("is_admin"):
        rows = query(
            "SELECT * FROM templates WHERE scenario_id = %s "
            "ORDER BY is_featured DESC, use_count DESC, created_at DESC",
            (scenario_id,),
        )
    else:
        rows = query(
            "SELECT * FROM templates WHERE scenario_id = %s AND (status='approved' OR created_by=%s) "
            "ORDER BY is_featured DESC, use_count DESC, created_at DESC",
            (scenario_id, user["id"]),
        )
    return rows


@router.get("/{template_id}", response_model=Template)
def get_template(scenario_id: str, template_id: str, user: dict = Depends(get_current_user)):
    """查询单个模板详情。"""
    row = query_one(
        "SELECT * FROM templates WHERE id = %s AND scenario_id = %s",
        (template_id, scenario_id),
    )
    if not row:
        raise HTTPException(404, f"模板 {template_id} 不存在")
    if (
        not user.get("is_admin")
        and row.get("status") != "approved"
        and row.get("created_by") != user.get("id")
    ):
        # 与列表接口保持同一可见性规则，也避免通过猜测 ID 查看他人的待审模板
        raise HTTPException(404, f"模板 {template_id} 不存在")
    return row


@router.post("", response_model=Template)
@router.post("/", response_model=Template, include_in_schema=False)
def create_template(scenario_id: str, body: TemplateCreate, user: dict = Depends(get_current_user)):
    """在指定场景下创建模板。用户创建的模板初始为 pending（待审核），需管理员通过后才能在生成中使用。"""
    # 检查场景是否存在
    scenario = query_one("SELECT id FROM scenarios WHERE id = %s", (scenario_id,))
    if not scenario:
        raise HTTPException(404, f"场景 {scenario_id} 不存在")
    tid = body.id or f"T{uuid.uuid4().hex[:6].upper()}"
    if query_one("SELECT id FROM templates WHERE id = %s", (tid,)):
        raise HTTPException(409, f"模板 ID {tid} 已存在")
    with transaction() as cur:
        cur.execute(
            """INSERT INTO templates (id, scenario_id, name, tag, description, prompt, constraints, structure, examples, differentiation_dims, applicable_channels, tags, status, created_by)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (tid, scenario_id, body.name, body.tag, body.description, body.prompt,
             Json(body.constraints), body.structure, Json(body.examples), Json(body.differentiation_dims),
             Json(body.applicable_channels), Json(body.tags), "pending", user["id"]),
        )
    row = query_one("SELECT * FROM templates WHERE id = %s", (tid,))
    return row


@router.put("/{template_id}", response_model=Template)
def update_template(scenario_id: str, template_id: str, body: TemplateCreate,
                    user: dict = Depends(get_current_user)):
    """更新模板。仅创建者或管理员可改；非管理员编辑被驳回的模板会回到 pending 重审。"""
    existing = query_one(
        "SELECT id, created_by, status FROM templates WHERE id = %s AND scenario_id = %s",
        (template_id, scenario_id),
    )
    if not existing:
        raise HTTPException(404, f"模板 {template_id} 不存在")
    if not is_owner_or_admin(user, existing.get("created_by")):
        raise HTTPException(403, "无权编辑他人的模板")
    # 非管理员编辑被驳回的模板 -> 回 pending 重审；否则保持原 status
    new_status = "pending" if (not user.get("is_admin") and existing.get("status") == "rejected") else (existing.get("status") or "approved")
    with transaction() as cur:
        cur.execute(
            """UPDATE templates SET
            name=%s, tag=%s, description=%s, prompt=%s, constraints=%s, structure=%s, examples=%s, differentiation_dims=%s, applicable_channels=%s, tags=%s, status=%s
            WHERE id=%s""",
            (body.name, body.tag, body.description, body.prompt, Json(body.constraints),
             body.structure, Json(body.examples), Json(body.differentiation_dims),
             Json(body.applicable_channels), Json(body.tags), new_status, template_id),
        )
    row = query_one("SELECT * FROM templates WHERE id = %s", (template_id,))
    return row


@router.delete("/{template_id}")
def delete_template(scenario_id: str, template_id: str, user: dict = Depends(get_current_user)):
    """删除模板。仅创建者或管理员可删。"""
    existing = query_one(
        "SELECT id, created_by FROM templates WHERE id = %s AND scenario_id = %s",
        (template_id, scenario_id),
    )
    if not existing:
        raise HTTPException(404, f"模板 {template_id} 不存在")
    if not is_owner_or_admin(user, existing.get("created_by")):
        raise HTTPException(403, "无权删除他人的模板")
    with transaction() as cur:
        cur.execute("DELETE FROM templates WHERE id = %s", (template_id,))
    return {"message": f"模板 {template_id} 已删除"}
