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
import time
import threading
from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from config import (
    JWT_SECRET, JWT_ALGORITHM, JWT_ACCESS_EXPIRE_MINUTES, JWT_REFRESH_EXPIRE_DAYS,
    JWT_BLACKLIST_CACHE_TTL,
)
from app.database import query_one, execute

# OAuth2PasswordBearer：声明本应用用 Bearer token 鉴权。
# tokenUrl 指向登录端点（主要给 /docs 的"Authorize"按钮用，不影响前端 JSON 登录）
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# ===== token 黑名单进程内缓存（无 Redis 时的过渡方案）=====
# 每次鉴权都要查 token_blacklist 表，高频接口（如生成轮询）会产生 DB 热点。
# 这里缓存"该 jti 是否已拉黑"的判定结果，未命中才查 DB，可消除绝大多数查询。
# 缓存值：(is_blacklisted: bool, expires_at: epoch秒)。
#   - 判定"未拉黑"：缓存 JWT_BLACKLIST_CACHE_TTL 秒（短，刚登出的 token 最多 TTL 秒内仍可用）
#   - 判定"已拉黑"：缓存至该 token 的 exp（已拉黑不可逆，缓存到自然过期，避免重复打 DB）
# 已知权衡：多 worker 下，其他 worker 的本地缓存最多 TTL 秒内仍判"未拉黑"；
# 引入 Redis 后（见优化方案点 3/7）可改为全局黑名单，消除该窗口。
_blacklist_cache: dict[str, tuple[bool, float]] = {}
_blacklist_cache_lock = threading.Lock()


def _is_blacklisted(jti: str, exp: float) -> bool:
    """查询 jti 是否在黑名单，带进程内 TTL 缓存。"""
    now = time.time()
    # 1) 先查缓存：命中且未过期直接返回
    with _blacklist_cache_lock:
        cached = _blacklist_cache.get(jti)
        if cached is not None:
            is_bl, expires_at = cached
            if expires_at > now:
                return is_bl
            _blacklist_cache.pop(jti, None)   # 过期，淘汰
    # 2) 未命中或已过期 -> 查 DB
    blacklisted = query_one("SELECT jti FROM token_blacklist WHERE jti = %s", (jti,)) is not None
    # 3) 回填缓存：已拉黑缓存到 exp，未拉黑缓存 TTL 秒
    cache_until = exp if blacklisted else now + JWT_BLACKLIST_CACHE_TTL
    with _blacklist_cache_lock:
        _blacklist_cache[jti] = (blacklisted, cache_until)
    return blacklisted


def _evict_blacklist_cache(jti: str) -> None:
    """登出撤销 token 后，主动驱逐本进程缓存，使登出在本进程内即时生效。"""
    with _blacklist_cache_lock:
        _blacklist_cache.pop(jti, None)


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
        # 检查黑名单：已撤销的 token 不可用（带进程内 TTL 缓存，避免每次鉴权打 DB）
        jti = payload.get("jti")
        if jti:
            exp = payload.get("exp")
            if exp and _is_blacklisted(jti, float(exp)):
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
        # 主动驱逐本进程缓存，使登出在本进程内即时生效
        # （多 worker 下其他进程最多 JWT_BLACKLIST_CACHE_TTL 秒内仍放行，已知权衡）
        _evict_blacklist_cache(jti)
    except jwt.InvalidTokenError:
        pass  # token 无效则忽略


def cleanup_expired_tokens() -> int:
    """清理已过期的 token 黑名单记录，避免表无限膨胀拖慢每次鉴权的黑名单查询。

    token 过期后本身已不可用，黑名单里留着纯属浪费——每次鉴权都要在这张表上
    查一次 jti。应用启动时调用一次，返回已清理的行数。
    """
    deleted = execute("DELETE FROM token_blacklist WHERE expires_at < NOW()")
    # 启动清理后重置缓存，避免持有跨重启的陈旧判定
    with _blacklist_cache_lock:
        _blacklist_cache.clear()
    return deleted


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
