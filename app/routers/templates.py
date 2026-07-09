"""模板管理 API：CRUD。

模板关联在场景之下，每个场景可包含多个模板。
模板定义了提示词/产出格式，供内容生成 Agent 使用。
"""
import uuid
from fastapi import APIRouter, HTTPException, Depends
from app.database import query, query_one, transaction
from psycopg2.extras import Json
from app.models import TemplateCreate, Template
from app.auth import get_current_user

router = APIRouter(prefix="/api/scenarios/{scenario_id}/templates", tags=["模板管理"])
_batch_router = APIRouter(prefix="/api/templates", tags=["模板管理（批量）"])


@_batch_router.get("/all")
def list_all_templates(user: dict = Depends(get_current_user)):
    """查询所有模板（供前端一次性加载）。"""
    rows = query("SELECT * FROM templates ORDER BY scenario_id, created_at DESC")
    return rows


@router.get("", response_model=list[Template])
@router.get("/", response_model=list[Template], include_in_schema=False)
def list_templates(scenario_id: str, user: dict = Depends(get_current_user)):
    """查询指定场景下的所有模板。"""
    # 检查场景是否存在
    scenario = query_one("SELECT id FROM scenarios WHERE id = %s", (scenario_id,))
    if not scenario:
        raise HTTPException(404, f"场景 {scenario_id} 不存在")
    rows = query(
        "SELECT * FROM templates WHERE scenario_id = %s ORDER BY created_at DESC",
        (scenario_id,),
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
    return row


@router.post("", response_model=Template)
@router.post("/", response_model=Template, include_in_schema=False)
def create_template(scenario_id: str, body: TemplateCreate, user: dict = Depends(get_current_user)):
    """在指定场景下创建模板。"""
    # 检查场景是否存在
    scenario = query_one("SELECT id FROM scenarios WHERE id = %s", (scenario_id,))
    if not scenario:
        raise HTTPException(404, f"场景 {scenario_id} 不存在")
    tid = body.id or f"T{uuid.uuid4().hex[:6].upper()}"
    with transaction() as cur:
        cur.execute(
            """INSERT INTO templates (id, scenario_id, name, tag, description, prompt, constraints, structure, examples, differentiation_dims, applicable_channels, tags)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (tid, scenario_id, body.name, body.tag, body.description, body.prompt,
             Json(body.constraints), body.structure, Json(body.examples), Json(body.differentiation_dims),
             Json(body.applicable_channels), Json(body.tags)),
        )
    row = query_one("SELECT * FROM templates WHERE id = %s", (tid,))
    return row


@router.put("/{template_id}", response_model=Template)
def update_template(scenario_id: str, template_id: str, body: TemplateCreate,
                    user: dict = Depends(get_current_user)):
    """更新模板。"""
    existing = query_one(
        "SELECT id FROM templates WHERE id = %s AND scenario_id = %s",
        (template_id, scenario_id),
    )
    if not existing:
        raise HTTPException(404, f"模板 {template_id} 不存在")
    with transaction() as cur:
        cur.execute(
            """UPDATE templates SET
            name=%s, tag=%s, description=%s, prompt=%s, constraints=%s, structure=%s, examples=%s, differentiation_dims=%s, applicable_channels=%s, tags=%s
            WHERE id=%s""",
            (body.name, body.tag, body.description, body.prompt, Json(body.constraints),
             body.structure, Json(body.examples), Json(body.differentiation_dims),
             Json(body.applicable_channels), Json(body.tags), template_id),
        )
    row = query_one("SELECT * FROM templates WHERE id = %s", (template_id,))
    return row


@router.delete("/{template_id}")
def delete_template(scenario_id: str, template_id: str, user: dict = Depends(get_current_user)):
    """删除模板。"""
    existing = query_one(
        "SELECT id FROM templates WHERE id = %s AND scenario_id = %s",
        (template_id, scenario_id),
    )
    if not existing:
        raise HTTPException(404, f"模板 {template_id} 不存在")
    with transaction() as cur:
        cur.execute("DELETE FROM templates WHERE id = %s", (template_id,))
    return {"message": f"模板 {template_id} 已删除"}
