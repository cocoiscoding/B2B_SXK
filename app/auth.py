"""鉴权核心：密码哈希、JWT 签发/解码、FastAPI 依赖。

技术：
- bcrypt：密码哈希（自带随机盐，同一密码每次哈希结果不同）。直接用 bcrypt 库，
  不经 passlib——passlib 1.7.4 与 bcrypt 4.1+ 存在已知不兼容。
- PyJWT：签发 / 解码 JWT 令牌
- FastAPI Depends：把"取当前登录用户"做成依赖，路由函数参数声明即可鉴权

设计原则：
- 密码永不明文存储，响应也永不返回 password_hash
- bcrypt 限制密码 ≤72 字节，超长则截断（标准做法）
- JWT 负载 {sub: user_id, exp: 过期时间}，HS256 签名
- get_current_user：解码 token → 查库 → 返回用户字典；失败抛 401
- require_admin：在 get_current_user 基础上要求 is_admin，否则 403
"""
import jwt
import bcrypt
import uuid
from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from config import JWT_SECRET, JWT_ALGORITHM, JWT_ACCESS_EXPIRE_MINUTES, JWT_REFRESH_EXPIRE_DAYS
from app.database import query_one, execute

# OAuth2PasswordBearer：声明本应用用 Bearer token 鉴权。
# tokenUrl 指向登录端点（主要给 /docs 的"Authorize"按钮用，不影响前端 JSON 登录）
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

def hash_password(plain: str) -> str:
    """明文密码 → bcrypt 哈希（返回 ascii 字符串便于存库）。"""
    pw = plain.encode("utf-8")[:72]    # bcrypt 上限 72 字节，超长截断
    return bcrypt.hashpw(pw, bcrypt.gensalt()).decode("ascii")


def verify_password(plain: str, hashed: str) -> bool:
    """校验明文密码是否与哈希匹配。"""
    try:
        pw = plain.encode("utf-8")[:72]
        return bcrypt.checkpw(pw, hashed.encode("ascii"))
    except Exception:
        return False


def create_access_token(user_id: str) -> str:
    """为用户签发访问令牌（access token）。负载 {sub, exp, iat, type, jti}。"""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,                                              # subject = 用户 id
        "exp": now + timedelta(minutes=JWT_ACCESS_EXPIRE_MINUTES),   # 短期有效
        "iat": now,                                                  # 签发时间
        "type": "access",                                            # 令牌类型
        "jti": str(uuid.uuid4()),                                    # JWT ID，用于黑名单
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def create_refresh_token(user_id: str) -> str:
    """为用户签发刷新令牌（refresh token）。负载 {sub, exp, iat, type, jti}。"""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,                                              # subject = 用户 id
        "exp": now + timedelta(days=JWT_REFRESH_EXPIRE_DAYS),        # 长期有效
        "iat": now,                                                  # 签发时间
        "type": "refresh",                                           # 令牌的类型
        "jti": str(uuid.uuid4()),                                    # JWT ID，用于黑名单
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str, expected_type: str = "access") -> dict:
    """解码并校验 JWT，返回负载字典；无效 / 过期 / 类型不匹配 / 已撤销抛 401。
    
    expected_type: "access" 或 "refresh"，用于防止令牌类型混淆攻击。
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        # 校验令牌类型，防止用 refresh token 当 access token 用
        if payload.get("type") != expected_type:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "令牌类型错误")
        # 检查黑名单：已撤销的 token 不可用
        jti = payload.get("jti")
        if jti:
            blacklisted = query_one("SELECT jti FROM token_blacklist WHERE jti = %s", (jti,))
            if blacklisted:
                raise HTTPException(status.HTTP_401_UNAUTHORIZED, "令牌已撤销")
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "令牌已过期，请重新登录")
    except jwt.InvalidTokenError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "令牌无效")


def revoke_token(token: str, user_id: str) -> None:
    """将 token 加入黑名单（退出登录时调用）。"""
    try:
        # 解码时不检查黑名单，避免循环依赖
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM], options={"verify_exp": False})
        jti = payload.get("jti")
        if not jti:
            return
        token_type = payload.get("type", "access")
        expires_at = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        execute(
            "INSERT INTO token_blacklist (jti, token_type, user_id, expires_at) VALUES (%s, %s, %s, %s) ON CONFLICT (jti) DO NOTHING",
            (jti, token_type, user_id, expires_at)
        )
    except jwt.InvalidTokenError:
        pass  # token 无效则忽略


def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    """依赖：从 token 取当前登录用户。

    无 token / 无效 / 用户不存在 → 401。
    返回的是数据库里的用户字典（含 password_hash，但路由响应模型不会序列化它）。
    """
    payload = decode_token(token)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "令牌无效")
    user = query_one("SELECT * FROM members WHERE id = %s", (user_id,))
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "用户不存在")
    return user


def require_admin(user: dict = Depends(get_current_user)) -> dict:
    """依赖：要求当前用户是管理员，否则 403。"""
    if not user.get("is_admin"):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "需要管理员权限")
    return user


def is_owner_or_admin(user: dict, created_by: str | None) -> bool:
    """判断用户是否可编辑 / 删除某条记录：是创建者，或是管理员。

    created_by 为 None（老记录）时，只允许管理员操作。
    """
    if user.get("is_admin"):
        return True
    if not created_by:
        return False
    return user.get("id") == created_by
