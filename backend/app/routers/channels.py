"""渠道配置管理 API：查询渠道列表。

渠道配置存储在数据库 channels 表中，用于驱动 ChannelAgent 的通用规则适配。
新增渠道只需 INSERT 一条记录，无需修改后端代码。
"""

from fastapi import APIRouter, Depends, Query
from app.database import query
from app.auth import get_current_user

router = APIRouter(prefix="/api/channels", tags=["渠道管理"])


@router.get("")
@router.get("/", include_in_schema=False)
def list_channels(
    keyword: str = Query("", description="关键词过滤"),
    user: dict = Depends(get_current_user),
):
    """获取所有渠道配置列表。需登录（与项目其他列表接口的鉴权策略一致）。"""
    if keyword:
        rows = query(
            "SELECT name, display_name, tone, emoji, format, description, is_builtin "
            "FROM channels WHERE name ILIKE %s OR display_name ILIKE %s ORDER BY name",
            (f"%{keyword}%", f"%{keyword}%"),
        )
    else:
        rows = query(
            "SELECT name, display_name, tone, emoji, format, description, is_builtin "
            "FROM channels ORDER BY name"
        )
    return rows
