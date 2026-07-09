"""用户鉴权 API：注册、登录、个人资料。

对应需求：用户登录、注册、查看并修改个人信息、鉴权。

登录/注册成功返回 JWT，前端存 localStorage 并在每次请求带上 Authorization: Bearer。
其他路由通过 Depends(get_current_user) 校验令牌。
"""
import uuid
from fastapi import APIRouter, Depends, HTTPException, status, Request
from app.database import query_one, transaction
from app.models import RegisterRequest, LoginRequest, TokenResponse, User, UserUpdate
from app.auth import (
    hash_password, verify_password, create_access_token, create_refresh_token,
    decode_token, get_current_user, revoke_token,
)

router = APIRouter(prefix="/api/auth", tags=["用户鉴权"])


def _to_user(row: dict) -> dict:
    """从数据库行构造不含密码的用户字典（响应里永不出现 password_hash）。"""
    return {
        "id": row["id"],
        "name": row["name"],
        "color": row.get("color") or "#409eff",
        "username": row.get("username"),
        "email": row.get("email"),
        "is_admin": row.get("is_admin", False),
        "created_at": row["created_at"],
    }


@router.post("/register", response_model=TokenResponse)
def register(req: RegisterRequest):
    """注册新用户。用户名唯一；成功后返回双令牌（免再登录一次）。"""
    # 用户名唯一检查（DB 也有 UNIQUE 约束兜底）
    if query_one("SELECT id FROM members WHERE username = %s", (req.username,)):
        raise HTTPException(status.HTTP_409_CONFLICT, "用户名已被占用")
    uid = f"U{uuid.uuid4().hex[:6].upper()}"
    pw_hash = hash_password(req.password)
    with transaction() as cur:
        cur.execute(
            """INSERT INTO members (id, name, color, username, password_hash, email, is_admin)
               VALUES (%s,%s,%s,%s,%s,%s,%s)""",
            (uid, req.name, "#409eff", req.username, pw_hash, req.email or None, False),
        )
    row = query_one("SELECT * FROM members WHERE id = %s", (uid,))
    access_token = create_access_token(uid)
    refresh_token = create_refresh_token(uid)
    return TokenResponse(access_token=access_token, refresh_token=refresh_token, user=User(**_to_user(row)))


@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest):
    """登录：校验用户名 + 密码，返回双令牌。

    用户名不存在或密码错误都返回同一句"用户名或密码错误"，避免账号枚举。
    """
    row = query_one("SELECT * FROM members WHERE username = %s", (req.username,))
    if not row or not row.get("password_hash"):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "用户名或密码错误")
    if not verify_password(req.password, row["password_hash"]):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "用户名或密码错误")
    access_token = create_access_token(row["id"])
    refresh_token = create_refresh_token(row["id"])
    return TokenResponse(access_token=access_token, refresh_token=refresh_token, user=User(**_to_user(row)))


@router.post("/refresh")
def refresh(req: dict):
    """刷新 access token：用 refresh token 换取新的 access token。

    前端收到 401 时自动调用此接口，用 refresh token 换新 access token，然后重试原请求。
    """
    refresh_token = req.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "缺少 refresh_token")
    
    # 解码 refresh token（expected_type="refresh" 防止用 access token 刷新）
    payload = decode_token(refresh_token, expected_type="refresh")
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "refresh token 无效")
    
    # 检查用户是否还存在
    user = query_one("SELECT id FROM members WHERE id = %s", (user_id,))
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "用户不存在")
    
    # 签发新的 access token
    new_access_token = create_access_token(user_id)
    return {"access_token": new_access_token}


@router.post("/logout")
def logout(request: Request, user: dict = Depends(get_current_user)):
    """退出登录：将当前 access token 加入黑名单。

    前端调用此接口后，当前 token 立即失效，即使未过期也无法再使用。
    """
    # 从 Authorization 头提取 token
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        revoke_token(token, user["id"])
    
    return {"message": "退出成功"}


@router.get("/me", response_model=User)
def get_me(user: dict = Depends(get_current_user)):
    """查看当前登录用户的资料。"""
    return User(**_to_user(user))


@router.put("/me", response_model=User)
def update_me(body: UserUpdate, user: dict = Depends(get_current_user)):
    """修改个人资料：昵称 / 邮箱 / 头像色可直接改；改密码需验旧密码。"""
    uid = user["id"]

    # 改密码：必须同时提供 old + new，且旧密码正确
    if body.new_password:
        if not body.old_password:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "改密码需提供旧密码")
        if not (user.get("password_hash") and verify_password(body.old_password, user["password_hash"])):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "旧密码不正确")
        if len(body.new_password) < 6:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "新密码至少 6 位")

    # 动态拼 SET 子句，只更新传入的字段
    sets, args = [], []
    if body.name is not None:
        sets.append("name=%s"); args.append(body.name)
    if body.email is not None:
        sets.append("email=%s"); args.append(body.email)
    if body.color is not None:
        sets.append("color=%s"); args.append(body.color)
    if body.new_password:
        sets.append("password_hash=%s"); args.append(hash_password(body.new_password))

    if not sets:
        return User(**_to_user(user))    # 没字段要改，直接返回当前资料

    args.append(uid)
    with transaction() as cur:
        cur.execute(f"UPDATE members SET {', '.join(sets)} WHERE id=%s", tuple(args))
    row = query_one("SELECT * FROM members WHERE id = %s", (uid,))
    return User(**_to_user(row))
