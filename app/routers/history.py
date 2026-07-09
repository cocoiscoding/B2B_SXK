"""生成历史管理 API：列表、详情、编辑、删除、导出。

对应需求：F4-1 ~ F4-5

每次调用 /api/generate 生成的内容都会保存到 history 表，
用户可以回看历史、编辑内容、导出为 Markdown/TXT 文件。
"""
from fastapi import APIRouter, HTTPException, Response, Depends
from psycopg2.extras import Json
import base64
import io
import re
from app.database import query, query_one, transaction, _parse_json_fields
from app.models import HistoryItem, HistoryUpdate, FeedbackRequest, VoteRequest
from app.auth import get_current_user, is_owner_or_admin

router = APIRouter(prefix="/api/history", tags=["生成历史"])

# history 表中的 JSONB 字段
JSON_FIELDS = ["params", "versions", "agent_trace", "issues"]


@router.get("", response_model=list[HistoryItem])
@router.get("/", response_model=list[HistoryItem], include_in_schema=False)
def list_history(user: dict = Depends(get_current_user)):
    """查询历史记录列表（按时间倒序）。全员可见（共享）。"""
    rows = query("SELECT * FROM history ORDER BY created_at DESC")
    return [_parse_json_fields(r, JSON_FIELDS) for r in rows]


@router.get("/{history_id}", response_model=HistoryItem)
def get_history(history_id: str, user: dict = Depends(get_current_user)):
    """查询单条历史记录详情。"""
    row = query_one("SELECT * FROM history WHERE id = %s", (history_id,))
    if not row:
        raise HTTPException(404, f"历史记录 {history_id} 不存在")
    return _parse_json_fields(row, JSON_FIELDS)


@router.put("/{history_id}", response_model=HistoryItem)
def update_history(history_id: str, body: HistoryUpdate, user: dict = Depends(get_current_user)):
    """编辑历史记录中的内容版本。仅创建者或管理员可改。

    用户在前端手动修改生成的文案后，通过此接口保存。
    """
    existing = query_one("SELECT id, created_by FROM history WHERE id = %s", (history_id,))
    if not existing:
        raise HTTPException(404, f"历史记录 {history_id} 不存在")
    if not is_owner_or_admin(user, existing.get("created_by")):
        raise HTTPException(403, "无权编辑他人的历史记录")
    if body.versions is not None:
        with transaction() as cur:
            cur.execute(
                "UPDATE history SET versions = %s WHERE id = %s",
                (Json([v.model_dump() for v in body.versions]), history_id),
            )
    return get_history(history_id)


@router.delete("/{history_id}")
def delete_history(history_id: str, user: dict = Depends(get_current_user)):
    """删除历史记录。仅创建者或管理员可删。"""
    existing = query_one("SELECT id, created_by FROM history WHERE id = %s", (history_id,))
    if not existing:
        raise HTTPException(404, f"历史记录 {history_id} 不存在")
    if not is_owner_or_admin(user, existing.get("created_by")):
        raise HTTPException(403, "无权删除他人的历史记录")
    with transaction() as cur:
        cur.execute("DELETE FROM history WHERE id = %s", (history_id,))
    return {"message": f"历史记录 {history_id} 已删除"}


# ===== 导出辅助：图片 data URL 解析 + SVG 转 PNG + docx 构建 =====

def _parse_data_url(data_url: str):
    """解析 data URL，返回 (mime, 图片字节) 或 (None, None)。"""
    if not data_url or not data_url.startswith("data:"):
        return None, None
    m = re.match(r"data:([\w+\-.]+/[\w+\-.]+);base64,(.*)", data_url, re.S)
    if not m:
        return None, None
    try:
        return m.group(1), base64.b64decode(m.group(2))
    except Exception:
        return None, None


def _svg_to_png(svg_bytes: bytes):
    """SVG 转 PNG（svglib+reportlab），失败返回 None。"""
    try:
        from svglib.svglib import svg2rlg
        from reportlab.graphics import renderPM
        drawing = svg2rlg(io.BytesIO(svg_bytes))
        png_io = io.BytesIO()
        renderPM.drawToFile(drawing, png_io, fmt="PNG")
        return png_io.getvalue()
    except Exception:
        return None


def _build_docx(data: dict) -> bytes:
    """把历史记录导出为 docx（含配图），返回字节。

    配图是 data URL（SVG/PNG），SVG 需转 PNG 才能插入 docx；
    转换或插入失败则跳过该图，不影响文案导出。
    markdown 标题/列表转为 docx 对应样式，表格按行原样输出。
    """
    from docx import Document
    from docx.shared import Inches

    doc = Document()
    doc.add_heading(f"{data['product_name']} - {data['scenario_name']}", level=0)
    doc.add_paragraph(f"渠道：{data['channel']} | 风格：{data['style']} | 生成时间：{data['created_at']}")

    for v in data.get("versions", []):
        doc.add_heading(f"版本 {v.get('index', 1)}：{v.get('title', '')}", level=1)
        # 正文：markdown 标题/列表转 docx 样式，其余按段落
        for line in (v.get("body") or "").split("\n"):
            s = line.strip()
            if not s:
                continue
            if s.startswith("###"):
                doc.add_heading(s.lstrip("# ").strip(), level=3)
            elif s.startswith("##"):
                doc.add_heading(s.lstrip("# ").strip(), level=2)
            elif s.startswith("#"):
                doc.add_heading(s.lstrip("# ").strip(), level=1)
            elif s.startswith("- ") or s.startswith("• "):
                doc.add_paragraph(s.lstrip("-• ").strip(), style="List Bullet")
            else:
                doc.add_paragraph(s)
        # 配图：SVG 转 PNG，PNG/JPEG 直接插入
        img = v.get("image")
        if img:
            mime, img_bytes = _parse_data_url(img)
            if img_bytes:
                insert = _svg_to_png(img_bytes) if (mime and "svg" in mime) else img_bytes
                if insert:
                    try:
                        doc.add_picture(io.BytesIO(insert), width=Inches(5.5))
                        doc.add_paragraph()
                    except Exception:
                        doc.add_paragraph("（配图插入失败）")
        if v.get("tags"):
            doc.add_paragraph(f"标签：{', '.join(v['tags'])}")

    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


@router.get("/{history_id}/export")
def export_history(history_id: str, format: str = "markdown", user: dict = Depends(get_current_user)):
    """导出历史记录为文件。

    GET /api/history/H001/export?format=markdown → 下载 .md 文件
    GET /api/history/H001/export?format=txt      → 下载 .txt 文件

    中文文件名需要特殊处理（Content-Disposition 编码），
    否则浏览器下载时中文会乱码。
    """
    row = query_one("SELECT * FROM history WHERE id = %s", (history_id,))
    if not row:
        raise HTTPException(404, f"历史记录 {history_id} 不存在")
    data = _parse_json_fields(row, JSON_FIELDS)
    versions = data.get("versions", [])

    # docx 导出（含配图，二进制，单独返回）
    if format == "docx":
        content_bytes = _build_docx(data)
        from urllib.parse import quote
        safe_name = data["product_name"].replace(" ", "_")
        filename = f"{safe_name}_{history_id}.docx"
        ascii_fallback = f"shenxing_{history_id}.docx"
        return Response(
            content=content_bytes,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={
                "Content-Disposition": (
                    f"attachment; filename={ascii_fallback}; "
                    f"filename*=UTF-8''{quote(filename)}"
                )
            },
        )

    if format == "txt":
        # 纯文本格式
        lines = []
        for v in versions:
            lines.append(f"=== 版本 {v.get('index', 1)}：{v.get('title', '')} ===\n")
            lines.append(v.get("body", ""))
            lines.append("\n")
        content = "\n".join(lines)
        media_type = "text/plain"
        ext = "txt"
    else:
        # Markdown 格式
        parts = [f"# {data['product_name']} - {data['scenario_name']}\n"]
        parts.append(f"> 渠道：{data['channel']} | 风格：{data['style']} | 生成时间：{data['created_at']}\n")
        for v in versions:
            parts.append(f"\n## 版本 {v.get('index', 1)}：{v.get('title', '')}\n")
            parts.append(v.get("body", ""))
            if v.get("tags"):
                parts.append(f"\n\n**标签：** {', '.join(v['tags'])}")
            parts.append("\n")
        content = "\n".join(parts)
        media_type = "text/markdown"
        ext = "md"

    # 中文文件名编码处理
    # RFC 5987 规定：filename* 用于非 ASCII 文件名，格式为 UTF-8''编码后的文件名
    from urllib.parse import quote
    safe_name = data["product_name"].replace(" ", "_")
    filename = f"{safe_name}_{history_id}.{ext}"
    ascii_fallback = f"shenxing_{history_id}.{ext}"  # ASCII 兜底文件名
    return Response(
        content=content.encode("utf-8"),
        media_type=media_type,
        headers={
            "Content-Disposition": (
                f"attachment; filename={ascii_fallback}; "
                f"filename*=UTF-8''{quote(filename)}"
            )
        },
    )


# ===== 加分项：用户反馈（赞 / 踩）=====

@router.put("/{history_id}/feedback", response_model=HistoryItem)
def set_feedback(history_id: str, body: FeedbackRequest, user: dict = Depends(get_current_user)):
    """标记用户对某条生成内容的反馈（点赞 / 踩 / 取消）。任何登录用户可操作。

    PUT /api/history/H001/feedback
    {"feedback": "like"}      → 点赞
    {"feedback": "dislike"}   → 踩
    {"feedback": ""}          → 取消标记
    """
    existing = query_one("SELECT id FROM history WHERE id = %s", (history_id,))
    if not existing:
        raise HTTPException(404, f"历史记录 {history_id} 不存在")

    # 规范化取值：去空格；空字符串表示取消
    fb = (body.feedback or "").strip()
    if fb and fb not in ("like", "dislike"):
        raise HTTPException(400, "feedback 取值需为 like / dislike / 空字符串")
    # 空字符串 → 写入 NULL（数据库里用 NULL 表示"未标记"）
    value = fb if fb else None

    with transaction() as cur:
        cur.execute(
            "UPDATE history SET feedback = %s WHERE id = %s",
            (value, history_id),
        )
    return get_history(history_id)


# ===== 加分项：A/B 测试（按版本投票，对比哪个版本更受欢迎）=====

@router.put("/{history_id}/vote", response_model=HistoryItem)
def vote_version(history_id: str, body: VoteRequest, user: dict = Depends(get_current_user)):
    """对某条历史的指定版本投票（A/B 测试）。任何登录用户可投。

    PUT /api/history/H001/vote
    {"version_index": 1, "vote": "like"}

    投票人由登录令牌决定（user.id），同一用户再次投票=改票，vote 为空=取消。
    body.member_id 已弃用（不再信任前端传入）。
    """
    row = query_one("SELECT * FROM history WHERE id = %s", (history_id,))
    if not row:
        raise HTTPException(404, f"历史记录 {history_id} 不存在")

    data = _parse_json_fields(row, JSON_FIELDS)
    versions = data.get("versions", [])

    # 找到目标版本（按 index 匹配）
    target = next((v for v in versions if v.get("index") == body.version_index), None)
    if target is None:
        raise HTTPException(404, f"版本 {body.version_index} 不存在")

    vote = (body.vote or "").strip()
    if vote and vote not in ("like", "dislike"):
        raise HTTPException(400, "vote 取值需为 like / dislike / 空字符串")

    votes = target.get("votes") or {"like": 0, "dislike": 0}
    voters = target.get("voters") or {}

    # 投票人 = 当前登录用户（来自令牌，不可伪造）
    member_id = user["id"]
    # 先撤销该用户的旧票（如有），再计新票
    old = voters.get(member_id)
    if old:
        votes[old] = max(0, votes.get(old, 0) - 1)
    if vote:
        voters[member_id] = vote
        votes[vote] = votes.get(vote, 0) + 1
    else:
        voters.pop(member_id, None)    # 取消投票

    target["votes"] = votes
    target["voters"] = voters

    # 整个 versions 数组写回（JSONB）
    with transaction() as cur:
        cur.execute(
            "UPDATE history SET versions = %s WHERE id = %s",
            (Json(versions), history_id),
        )
    return get_history(history_id)