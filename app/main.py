"""神行库 · Product Marketing AI — FastAPI 应用入口。

这个文件创建并配置 FastAPI 应用实例，注册所有路由、启动事件、静态资源。

FastAPI 核心概念：
- FastAPI() 是应用实例，所有功能都挂载在它上面
- 路由（Router）：处理 HTTP 请求的函数，通过 @app.get / @app.post 等装饰器定义
- 中间件（Middleware）：在请求处理前后执行的钩子，如 CORS、日志等
- 启动/关闭事件：应用启动时初始化资源（如数据库），关闭时释放资源
"""
from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
# 从 config.py 导入配置项
from config import APP_NAME, APP_VERSION, FRONTEND_DIR, LLM_ENABLED, DB_HOST, DB_PORT, DB_NAME
# 从 database.py 导入数据库初始化和关闭函数
from app.database import init_db, close_pool
# 从 seed_data.py 导入种子数据初始化函数
from app.seed_data import seed_if_empty
# 从 routers 包导入 4 个路由模块
from app.routers import products, scenarios, generate, history, members, seo, auth, channels, templates

# 创建 FastAPI 应用实例
# title 和 version 会显示在自动生成的 API 文档（/docs）中
app = FastAPI(title=APP_NAME, version=APP_VERSION)

# 添加 CORS 中间件：允许跨域请求
# CORS = Cross-Origin Resource Sharing，跨域资源共享
# 前端和后端不在同一域名/端口时，浏览器会拦截请求，CORS 中间件用于放行
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       # 允许所有来源（生产环境应限制为具体域名）
    allow_methods=["*"],       # 允许所有 HTTP 方法（GET/POST/PUT/DELETE 等）
    allow_headers=["*"],       # 允许所有请求头
)

# 注册路由：把每个路由模块的 router 挂载到主应用
# include_router 会把子路由的所有端点合并到主应用
app.include_router(products.router)    # 产品知识库管理
app.include_router(scenarios.router)   # 场景管理
app.include_router(templates.router)   # 模板管理
app.include_router(generate.router)    # 内容生成
app.include_router(history.router)     # 历史记录管理
app.include_router(members.router)     # 团队成员（加分项：团队协作）
app.include_router(seo.router)         # SEO 分析（加分项）
app.include_router(auth.router)        # 用户鉴权（登录/注册/资料）
app.include_router(channels.router)    # 渠道配置管理
app.include_router(templates._batch_router)  # 模板批量查询


# @app.on_event("startup") 是 FastAPI 的启动事件装饰器
# 应用启动时自动执行此函数
@app.on_event("startup")
def _startup():
    """应用启动时：初始化数据库表 + 灌入种子数据。"""
    init_db()           # 创建数据库表（如果不存在）
    seed_if_empty()     # 如果表为空，插入示例数据


@app.on_event("shutdown")
def _shutdown():
    """应用关闭时：释放数据库连接池。"""
    close_pool()


@app.get("/api/health")
def health():
    """健康检查接口：用于监测服务是否正常运行。

    访问 GET /api/health 返回应用状态信息。
    """
    return {
        "app": APP_NAME,
        "version": APP_VERSION,
        "llm_enabled": LLM_ENABLED,
        "database": f"postgresql://{DB_HOST}:{DB_PORT}/{DB_NAME}",
        "status": "running",
    }


# 前端静态资源挂载
# StaticFiles 用于托管静态文件（如 JS、CSS、图片）
# mount("/assets", ...) 表示访问 /assets/xxx 时去 FRONTEND_DIR 找对应文件
if FRONTEND_DIR.exists():
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIR)), name="assets")

# 上传文件静态服务挂载
# 产品图片和文档上传后保存在 uploads/products 目录
# 通过 /uploads/products/xxx 路径可访问上传的文件
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")


@app.get("/")
def index():
    """根路径：返回前端首页 index.html。

    如果前端文件不存在，返回 JSON 提示信息。
    """
    idx = FRONTEND_DIR / "index.html"
    if idx.exists():
        # FileResponse 把文件作为 HTTP 响应返回（自动设置 Content-Type）
        return FileResponse(str(idx))
    return {"message": "神行库 API 运行中，前端文件未找到。访问 /docs 查看 API 文档。"}