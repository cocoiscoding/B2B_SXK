"""神行库全局配置。

所有可配置项集中在此文件管理，可通过环境变量覆盖默认值。
这样设计的好处：修改配置时只需改这一处，不用到处找散落的配置。

关键概念：
- os.getenv("变量名", "默认值")：读取环境变量，如果没有则用默认值
- Path(__file__)：当前文件的路径
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# BASE_DIR 是项目根目录（config.py 所在目录）
# __file__ 是 Python 内置变量，指向当前文件路径
# .resolve() 返回绝对路径，.parent 取上一级目录
BASE_DIR = Path(__file__).resolve().parent

# 从 .env 文件加载环境变量（如 LLM_API_KEY），key 不进代码仓库
# 见项目根的 .env（已 .gitignore）；真实环境变量优先级仍高于 .env
load_dotenv(BASE_DIR / ".env")

# FRONTEND_DIR 是前端静态文件目录（存放 index.html 等）
FRONTEND_DIR = BASE_DIR / "frontend"

# ===== PostgreSQL 数据库配置 =====
# 通过 .env 配置（.env 已 gitignore）；以下默认值仅作本地开发兜底，密码须在 .env 设置
# int(os.getenv(...)) 表示把读到的字符串环境变量转成整数
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")          # 数据库主机地址
DB_PORT = int(os.getenv("DB_PORT", "5432"))           # 数据库端口
DB_NAME = os.getenv("DB_NAME", "shenxingdb")          # 数据库名
DB_USER = os.getenv("DB_USER", "postgres")            # 数据库用户名
DB_PASSWORD = os.getenv("DB_PASSWORD", "")            # 数据库密码（须在 .env 配置，勿提交源码）
DB_CLIENT_ENCODING = os.getenv("DB_CLIENT_ENCODING", "UTF8")  # 数据库客户端编码，避免中文错误信息解码失败

# 数据库连接池大小
# 连接池：预先创建一批数据库连接放在一起复用，避免每次请求都新建连接（开销大）
DB_MIN_CONN = int(os.getenv("DB_MIN_CONN", "1"))      # 最小连接数（常驻）
DB_MAX_CONN = int(os.getenv("DB_MAX_CONN", "10"))     # 最大连接数（上限）

# ===== LLM 配置 =====
# 不配置 API_KEY 时自动使用 Mock 模板引擎（开箱即用，无需联网）
# LLM = Large Language Model，大语言模型（如通义千问、DeepSeek、GPT 等）
LLM_API_KEY = os.getenv("LLM_API_KEY", "")             # API 密钥，空字符串表示未配置
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")  # 通义千问 API 地址
LLM_MODEL = os.getenv("LLM_MODEL", "qwen-plus")        # 使用的模型名称
LLM_TIMEOUT = float(os.getenv("LLM_TIMEOUT", "30"))    # 请求超时时间（秒）
# bool("") = False，bool("任何非空字符串") = True
# 所以只有配置了 API_KEY，LLM_ENABLED 才为 True
LLM_ENABLED = bool(LLM_API_KEY)

# ===== Tavily 搜索 API 配置（竞品分析联网搜索）=====
# Tavily 是专为 AI Agent 设计的搜索引擎，中文搜索效果好。
# 不配置 API_KEY 时自动降级为 Mock 规则分析（不联网）。
# 注册获取 API Key：https://app.tavily.com
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")
TAVILY_ENABLED = bool(TAVILY_API_KEY)

# ===== JWT 鉴权配置（用户登录/注册）=====
# JWT = JSON Web Token：登录成功后签发的令牌，前端每次请求在 Authorization 头带上
# 密钥务必通过环境变量 JWT_SECRET 覆盖默认值（默认值仅供本地开发，不可用于生产）
JWT_SECRET = os.getenv("JWT_SECRET", "shenxing-dev-secret-change-me")
JWT_ALGORITHM = "HS256"                                     # 签名算法
# 启动安全校验：仍用默认密钥时大声告警。
# 默认值公开在源码里，任何拿到源码者都能伪造任意用户的 JWT（含管理员），等价于鉴权失效。
if JWT_SECRET == "shenxing-dev-secret-change-me":
    print(
        "⚠ [安全警告] JWT_SECRET 仍为默认值，任何拿到源码者均可伪造登录令牌。"
        "请在 .env 中设置随机强密钥，例如 secrets.token_urlsafe(48)。"
    )

# 双令牌机制：access token（短期）+ refresh token（长期）
# access token：每次 API 请求携带，有效期短，泄露风险小
# refresh token：仅用于刷新 access token，有效期长，存 localStorage
JWT_ACCESS_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_EXPIRE_MINUTES", "30"))   # access token 有效期（分钟），默认 30
JWT_REFRESH_EXPIRE_DAYS = int(os.getenv("JWT_REFRESH_EXPIRE_DAYS", "7"))        # refresh token 有效期（天），默认 7
# 种子演示账号的默认密码（仅用于 4 个预置用户）
DEFAULT_USER_PASSWORD = os.getenv("DEFAULT_USER_PASSWORD", "123456")

# ===== 应用元信息 =====
APP_NAME = "神行库 · Product Marketing AI"
APP_VERSION = "1.0.0"