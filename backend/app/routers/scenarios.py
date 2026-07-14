"""场景管理 API：CRUD。

场景定义了不同的营销创作场景（如官网文案、竞品分析、客户案例等），
每个场景包含参数定义。模板关联在场景之下。

对应需求：F2-1 ~ F2-3
"""
import uuid
from fastapi import APIRouter, HTTPException, Depends
from psycopg2.extras import Json
from app.database import query, query_one, transaction, _parse_json_fields
from app.models import ScenarioCreate, Scenario
from app.auth import get_current_user, is_owner_or_admin

router = APIRouter(prefix="/api/scenarios", tags=["场景管理"])

# scenarios 表中的 JSONB 字段
JSON_FIELDS = ["parameters"]


@router.get("", response_model=list[Scenario])
@router.get("/", response_model=list[Scenario], include_in_schema=False)
def list_scenarios(user: dict = Depends(get_current_user)):
    """查询所有场景。"""
    rows = query("SELECT * FROM scenarios ORDER BY created_at DESC")
    return [_parse_json_fields(r, JSON_FIELDS) for r in rows]


@router.get("/{scenario_id}", response_model=Scenario)
def get_scenario(scenario_id: str, user: dict = Depends(get_current_user)):
    """查询单个场景详情。"""
    row = query_one("SELECT * FROM scenarios WHERE id = %s", (scenario_id,))
    if not row:
        raise HTTPException(404, f"场景 {scenario_id} 不存在")
    return _parse_json_fields(row, JSON_FIELDS)


@router.post("", response_model=Scenario)
@router.post("/", response_model=Scenario, include_in_schema=False)
def create_scenario(body: ScenarioCreate, user: dict = Depends(get_current_user)):
    """创建自定义场景。"""
    sid = body.id or f"S{uuid.uuid4().hex[:6].upper()}"
    if query_one("SELECT id FROM scenarios WHERE id = %s", (sid,)):
        raise HTTPException(409, f"场景 ID {sid} 已存在")
    with transaction() as cur:
        cur.execute(
            """INSERT INTO scenarios (id, name, description, parameters, created_by)
            VALUES (%s,%s,%s,%s,%s)""",
            (
                sid, body.name, body.description,
                Json([p.model_dump() for p in body.parameters]),
                user["id"],
            ),
        )
    return get_scenario(sid)


@router.put("/{scenario_id}", response_model=Scenario)
def update_scenario(scenario_id: str, body: ScenarioCreate, user: dict = Depends(get_current_user)):
    """更新场景。

    若场景参数名发生变化，自动同步更新该场景下所有模板提示词中的
    {旧参数名} 引用为 {新参数名}（按位置索引匹配）。
    """
    existing = query_one("SELECT id, created_by, parameters FROM scenarios WHERE id = %s", (scenario_id,))
    if not existing:
        raise HTTPException(404, f"场景 {scenario_id} 不存在")
    if not is_owner_or_admin(user, existing.get("created_by")):
        raise HTTPException(403, "无权修改该场景；内置场景仅管理员可修改")

    # 对比新旧参数，找出改名的（按位置索引匹配）
    old_params = existing.get("parameters") or []
    new_params = [p.model_dump() for p in body.parameters]
    renames = {}  # {old_name: new_name}
    max_len = min(len(old_params), len(new_params))
    for i in range(max_len):
        old_name = (old_params[i] or {}).get("name", "")
        new_name = (new_params[i] or {}).get("name", "")
        if old_name and new_name and old_name != new_name:
            renames[old_name] = new_name

    with transaction() as cur:
        cur.execute(
            """UPDATE scenarios SET
            name=%s, description=%s, parameters=%s
            WHERE id=%s""",
            (
                body.name, body.description,
                Json(new_params),
                scenario_id,
            ),
        )
        # 同步更新关联模板提示词中的 {旧参数名} → {新参数名}
        if renames:
            cur.execute(
                "SELECT id, prompt FROM templates WHERE scenario_id = %s",
                (scenario_id,),
            )
            rows = cur.fetchall()
            for row in rows:
                tpl_id, prompt = row[0], row[1]
                if not prompt:
                    continue
                updated = prompt
                for old_name, new_name in renames.items():
                    updated = updated.replace(f"{{{old_name}}}", f"{{{new_name}}}")
                if updated != prompt:
                    cur.execute(
                        "UPDATE templates SET prompt = %s WHERE id = %s",
                        (updated, tpl_id),
                    )

    return get_scenario(scenario_id)


@router.delete("/{scenario_id}")
def delete_scenario(scenario_id: str, user: dict = Depends(get_current_user)):
    """删除场景（关联的模板也会级联删除）。"""
    existing = query_one("SELECT id, created_by FROM scenarios WHERE id = %s", (scenario_id,))
    if not existing:
        raise HTTPException(404, f"场景 {scenario_id} 不存在")
    if not is_owner_or_admin(user, existing.get("created_by")):
        raise HTTPException(403, "无权删除该场景；内置场景仅管理员可删除")
    with transaction() as cur:
        cur.execute("DELETE FROM scenarios WHERE id = %s", (scenario_id,))
    return {"message": f"场景 {scenario_id} 已删除"}
