"""草稿 API：多阶段交互式生成流程。

四阶段（draft_id 串联，最终确认才落 history，历史列表保持干净）：
  阶段1 POST   /api/drafts                  检索->生成->校验，产出 3 个初稿
        POST   /api/drafts/{id}/regenerate  重新生成初稿（可微调 params）
  阶段2 PUT    /api/drafts/{id}/select      用户选定+改动后的那一版
  阶段3 POST   /api/drafts/{id}/adapt       多选渠道 -> 每渠道 1 个适配版本
  阶段4 POST   /api/drafts/{id}/finalize    文生图 -> 落 history
        GET    /api/drafts/{id}             恢复草稿（前端刷新续作）

阶段2（用户选版+改内容）无 Agent 参与，由本路由直接写草稿。
"""
from fastapi import APIRouter, HTTPException, Depends
from psycopg2.extras import Json
import uuid
from app.database import query_one, transaction
from app.models import (
    Draft, CreateDraftRequest, RegenerateRequest, SelectVersionRequest, AdaptRequest,
    VersionContent,
)
from app.agents.orchestrator import get_orchestrator
from app.auth import get_current_user, is_owner_or_admin

router = APIRouter(prefix="/api/drafts", tags=["草稿-多阶段生成"])


def _row_to_draft(row: dict) -> Draft:
    """drafts 表行 -> Draft 响应模型。

    补空值后交给 Pydantic，list[dict] 自动转 list[VersionContent]/list[AgentStep]，
    selected_version 的 dict 自动转 VersionContent（None 保留）。
    """
    d = dict(row)
    for f in ("draft_versions", "agent_trace", "channels", "versions"):
        if d.get(f) is None:
            d[f] = []
    for f in ("params", "retrieved_info", "validation"):
        if d.get(f) is None:
            d[f] = {}
    return Draft(**d)


def _get_owned_draft(draft_id: str, user: dict) -> dict:
    """取草稿行并校验归属：不存在 404，非本人/非管理员 403。"""
    row = query_one("SELECT * FROM drafts WHERE id = %s", (draft_id,))
    if not row:
        raise HTTPException(404, f"草稿 {draft_id} 不存在")
    if not is_owner_or_admin(user, row.get("user_id")):
        raise HTTPException(403, "无权操作他人的草稿")
    return dict(row)


def _to_version_content(v: dict, i: int) -> VersionContent:
    """dict -> VersionContent，补默认字段（适配/配图阶段产出的 dict 字段不全）。"""
    return VersionContent(
        index=v.get("index", i + 1),
        title=v.get("title", ""),
        body=v.get("body", ""),
        tags=v.get("tags", []),
        channel=v.get("channel", ""),
        image=v.get("image"),
        images=v.get("images", []),
        votes=v.get("votes", {"like": 0, "dislike": 0}),
        voters=v.get("voters", {}),
    )


@router.post("", response_model=Draft)
@router.post("/", response_model=Draft, include_in_schema=False)
def create_draft(req: CreateDraftRequest, user: dict = Depends(get_current_user)):
    """阶段1：检索 -> 生成 -> 校验，创建草稿并产出 3 个初稿。"""
    try:
        orch = get_orchestrator()
        result = orch.run_draft(
            product_id=req.product_id,
            scenario_id=req.scenario_id,
            template_id=req.template_id or None,
            style=req.style,
            params=req.params,
            version_count=req.version_count,
        )
    except ValueError as e:
        raise HTTPException(400, str(e))

    draft_id = f"D{uuid.uuid4().hex[:8]}"
    with transaction() as cur:
        cur.execute(
            """INSERT INTO drafts
            (id, user_id, product_id, product_name, scenario_id, scenario_name,
             template_id, template_name, style, params, stage,
             retrieved_info, draft_versions, validation, agent_trace)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (
                draft_id, user["id"], req.product_id, result["product_name"],
                req.scenario_id, result["scenario_name"],
                req.template_id or None, result.get("template_name"),
                req.style, Json(req.params), "draft",
                Json(result["retrieved_info"]),
                Json(result["draft_versions"]),
                Json(result["validation"]),
                Json(result["agent_trace"]),
            ),
        )
    row = query_one("SELECT * FROM drafts WHERE id = %s", (draft_id,))
    return _row_to_draft(row)


@router.post("/{draft_id}/regenerate", response_model=Draft)
def regenerate_draft(draft_id: str, body: RegenerateRequest, user: dict = Depends(get_current_user)):
    """阶段1内：重新生成初稿。可微调 params；重置后续阶段（选版/渠道/版本）。"""
    d = _get_owned_draft(draft_id, user)
    params = body.params if body.params is not None else (d.get("params") or {})
    try:
        orch = get_orchestrator()
        result = orch.run_draft(
            product_id=d["product_id"],
            scenario_id=d["scenario_id"],
            template_id=d.get("template_id"),
            style=d.get("style", "专业严谨"),
            params=params,
            version_count=3,
        )
    except ValueError as e:
        raise HTTPException(400, str(e))

    with transaction() as cur:
        cur.execute(
            """UPDATE drafts SET
                 params=%s, retrieved_info=%s, draft_versions=%s, validation=%s,
                 agent_trace=%s, selected_version=NULL, channels='[]'::jsonb,
                 versions='[]'::jsonb, stage='draft', history_id=NULL, updated_at=NOW()
               WHERE id=%s""",
            (
                Json(params),
                Json(result["retrieved_info"]),
                Json(result["draft_versions"]),
                Json(result["validation"]),
                Json(result["agent_trace"]),
                draft_id,
            ),
        )
    row = query_one("SELECT * FROM drafts WHERE id = %s", (draft_id,))
    return _row_to_draft(row)


@router.put("/{draft_id}/select", response_model=Draft)
def select_version(draft_id: str, body: SelectVersionRequest, user: dict = Depends(get_current_user)):
    """阶段2：提交用户选定+改动后的那一版。"""
    d = _get_owned_draft(draft_id, user)
    if not d.get("draft_versions"):
        raise HTTPException(400, "尚无初稿，请先生成")
    version = body.version or {}
    norm = {
        "index": version.get("index", 1),
        "title": version.get("title", ""),
        "body": version.get("body", ""),
        "tags": version.get("tags", []),
    }
    with transaction() as cur:
        cur.execute(
            """UPDATE drafts SET selected_version=%s, stage='editing', updated_at=NOW()
               WHERE id=%s""",
            (Json(norm), draft_id),
        )
    row = query_one("SELECT * FROM drafts WHERE id = %s", (draft_id,))
    return _row_to_draft(row)


@router.post("/{draft_id}/adapt", response_model=Draft)
def adapt_draft(draft_id: str, body: AdaptRequest, user: dict = Depends(get_current_user)):
    """阶段3：多选渠道 -> 每渠道 1 个适配版本。"""
    d = _get_owned_draft(draft_id, user)
    selected = d.get("selected_version")
    if not selected:
        raise HTTPException(400, "尚未选定版本，请先在阶段2确认")
    # 渠道去重保序
    channels = body.channels or []
    seen = set()
    channels = [c for c in channels if not (c in seen or seen.add(c))]
    if not channels:
        raise HTTPException(400, "未选择任何渠道")

    try:
        orch = get_orchestrator()
        result = orch.run_adapt(
            selected_version=selected,
            channels=channels,
            scenario_id=d["scenario_id"],
            template_id=d.get("template_id"),
        )
    except ValueError as e:
        raise HTTPException(400, str(e))

    versions = result["versions"]
    skipped = result["skipped"]
    # 追加渠道适配步骤到 agent_trace（供最终落 history 时链路完整）
    trace = list(d.get("agent_trace") or [])
    trace.append({
        "agent": "渠道适配 Agent",
        "status": "warning" if skipped else "success",
        "message": f"已将选定版本适配至 {len(versions)} 个渠道"
                   + (f"；跳过未知渠道：{','.join(skipped)}" if skipped else ""),
        "duration_ms": 0,
        "output": {"channels": channels, "skipped": skipped},
    })

    with transaction() as cur:
        cur.execute(
            """UPDATE drafts SET channels=%s, versions=%s, agent_trace=%s,
                 stage='adapted', updated_at=NOW() WHERE id=%s""",
            (Json(channels), Json(versions), Json(trace), draft_id),
        )
    row = query_one("SELECT * FROM drafts WHERE id = %s", (draft_id,))
    return _row_to_draft(row)


@router.post("/{draft_id}/finalize", response_model=Draft)
def finalize_draft(draft_id: str, user: dict = Depends(get_current_user)):
    """阶段4：对多渠道版本配图 -> 写 history -> 回填 history_id。"""
    d = _get_owned_draft(draft_id, user)
    versions = d.get("versions") or []
    if not versions:
        raise HTTPException(400, "尚无渠道版本，请先完成阶段3适配")

    try:
        orch = get_orchestrator()
        result = orch.run_images(
            versions=versions,
            scenario_id=d["scenario_id"],
            retrieved_info=d.get("retrieved_info") or {},
        )
    except ValueError as e:
        raise HTTPException(400, str(e))

    versions = result["versions"]
    image_step = result["image_step"]
    trace = list(d.get("agent_trace") or []) + [image_step]

    validation = d.get("validation") or {}
    issues = validation.get("issues", []) if isinstance(validation, dict) else []
    validated = validation.get("validated", False) if isinstance(validation, dict) else False
    channels = d.get("channels") or []
    channel_str = ",".join(channels) if channels else "多渠道"

    version_objs = [_to_version_content(v, i) for i, v in enumerate(versions)]
    history_id = f"H{uuid.uuid4().hex[:8]}"
    with transaction() as cur:
        cur.execute(
            """INSERT INTO history
            (id, product_id, product_name, scenario_id, scenario_name,
             channel, style, params, versions, agent_trace, validated, issues, created_by)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (
                history_id, d["product_id"], d.get("product_name", ""),
                d["scenario_id"], d.get("scenario_name", ""),
                channel_str, d.get("style", ""), Json(d.get("params") or {}),
                Json([v.model_dump() for v in version_objs]),
                Json(trace), validated, Json(issues), user["id"],
            ),
        )
        cur.execute(
            """UPDATE drafts SET versions=%s, agent_trace=%s, history_id=%s,
                 stage='done', updated_at=NOW() WHERE id=%s""",
            (Json(versions), Json(trace), history_id, draft_id),
        )
    row = query_one("SELECT * FROM drafts WHERE id = %s", (draft_id,))
    return _row_to_draft(row)


@router.get("/{draft_id}", response_model=Draft)
def get_draft(draft_id: str, user: dict = Depends(get_current_user)):
    """恢复草稿（前端刷新续作）。"""
    row = _get_owned_draft(draft_id, user)
    return _row_to_draft(row)
