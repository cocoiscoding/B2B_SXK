"""团队成员管理 API：成员列表 + 管理员增删改。

提供成员/用户列表供前端展示归属（创建人彩点与名字）。
管理员可创建/编辑/删除成员；查询不取 password_hash 列。
"""
import uuid
from fastapi import APIRouter, Depends, HTTPException
from app.database import query, query_one, transaction
from app.models import Member, MemberCreate, MemberUpdate
from app.auth import get_current_user, require_admin, hash_password

router = APIRouter(prefix="/api/members", tags=["团队成员"])


@router.get("", response_model=list[Member])
@router.get("/", response_model=list[Member], include_in_schema=False)
def list_members(user: dict = Depends(get_current_user)):
    """查询所有团队成员（按 id 排序）。任何登录用户可看。

    前端启动时拉取，用于顶栏的"当前成员"选择器与创建人展示。
    刻意不查 password_hash 列。
    """
    return query(
        "SELECT id, name, color, username, email, is_admin, created_at FROM members ORDER BY id"
    )


def _to_member(row: dict) -> dict:
    """从数据库行构造不含密码的成员字典。"""
    return {
        "id": row["id"],
        "name": row["name"],
        "color": row.get("color") or "#409eff",
        "username": row.get("username"),
        "email": row.get("email"),
        "is_admin": row.get("is_admin", False),
        "created_at": row["created_at"],
    }


@router.post("", response_model=Member)
@router.post("/", response_model=Member, include_in_schema=False)
def create_member(body: MemberCreate, user: dict = Depends(require_admin)):
    """管理员创建成员（区别于公开注册，可指定角色）。仅管理员可调用。

    用户名唯一（DB 也有 UNIQUE 约束兜底）。
    """
    if query_one("SELECT id FROM members WHERE username = %s", (body.username,)):
        raise HTTPException(409, "用户名已被占用")
    uid = f"U{uuid.uuid4().hex[:6].upper()}"
    pw_hash = hash_password(body.password)
    with transaction() as cur:
        cur.execute(
            """INSERT INTO members (id, name, color, username, password_hash, email, is_admin)
               VALUES (%s,%s,%s,%s,%s,%s,%s)""",
            (uid, body.name, "#409eff", body.username, pw_hash, body.email or None, body.is_admin),
        )
    row = query_one("SELECT * FROM members WHERE id = %s", (uid,))
    return _to_member(row)


@router.put("/{member_id}", response_model=Member)
def update_member(member_id: str, body: MemberUpdate, user: dict = Depends(require_admin)):
    """管理员修改成员资料：昵称/邮箱/头像色/角色/重置密码。仅管理员可调用。

    改密码无需旧密码（管理员重置）。所有字段可选，只更新传入的。
    """
    existing = query_one("SELECT id FROM members WHERE id = %s", (member_id,))
    if not existing:
        raise HTTPException(404, f"成员 {member_id} 不存在")

    sets, args = [], []
    if body.name is not None:
        sets.append("name=%s"); args.append(body.name)
    if body.email is not None:
        sets.append("email=%s"); args.append(body.email)
    if body.color is not None:
        sets.append("color=%s"); args.append(body.color)
    if body.is_admin is not None:
        sets.append("is_admin=%s"); args.append(body.is_admin)
    if body.new_password:
        if len(body.new_password) < 6:
            raise HTTPException(400, "新密码至少 6 位")
        sets.append("password_hash=%s"); args.append(hash_password(body.new_password))

    if sets:
        args.append(member_id)
        with transaction() as cur:
            cur.execute(f"UPDATE members SET {', '.join(sets)} WHERE id=%s", tuple(args))
    row = query_one("SELECT * FROM members WHERE id = %s", (member_id,))
    return _to_member(row)


@router.delete("/{member_id}")
def delete_member(member_id: str, user: dict = Depends(require_admin)):
    """管理员删除成员。仅管理员可调用。

    关联数据处理（保留业务数据，清理归属与临时数据）：
    - products.created_by -> NULL（产品保留，归属"未标记"）
    - history.created_by -> NULL（历史保留）
    - drafts -> 删除该用户的草稿（user_id NOT NULL，且草稿是临时数据）
    不允许删除自己。
    """
    if user["id"] == member_id:
        raise HTTPException(400, "不能删除自己")

    existing = query_one("SELECT id FROM members WHERE id = %s", (member_id,))
    if not existing:
        raise HTTPException(404, f"成员 {member_id} 不存在")

    with transaction() as cur:
        cur.execute("UPDATE products SET created_by=NULL WHERE created_by=%s", (member_id,))
        cur.execute("UPDATE history SET created_by=NULL WHERE created_by=%s", (member_id,))
        cur.execute("DELETE FROM drafts WHERE user_id=%s", (member_id,))
        cur.execute("DELETE FROM members WHERE id=%s", (member_id,))
    return {"message": f"成员 {member_id} 已删除，其产品与历史的创建人标记已清空，草稿已清理"}
