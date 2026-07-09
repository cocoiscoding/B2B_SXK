"""团队成员管理 API（用户列表）。

提供成员/用户列表供前端展示归属（创建人彩点与名字）。
为安全起见，查询不取 password_hash 列。
"""
from fastapi import APIRouter, Depends
from app.database import query
from app.models import Member
from app.auth import get_current_user

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
