"""神行库 · Product Marketing AI 启动入口。

这个文件是整个后端服务的启动点。执行 `python main.py` 即可启动 Web 服务。

用法：
    python main.py
    # 或使用 uvicorn 命令（开发模式，支持热重载）
    uvicorn main:app --reload --port 8000
"""
# uvicorn 是一个高性能的 ASGI 服务器，用于运行 FastAPI 应用
import uvicorn
# 从 app/main.py 导入 FastAPI 实例 app
# noqa: E402 表示忽略"import 应该在文件顶部"的 lint 警告（此处故意放在 import uvicorn 之后）
from app.main import app  # noqa: E402


# __name__ == "__main__" 表示这个文件是被直接运行的（而非被其他文件 import）
# 这是 Python 的惯用写法，确保只有直接运行此文件时才启动服务器
if __name__ == "__main__":
    # 启动 uvicorn 服务器：
    # - "app.main:app" 指向 app/main.py 文件中的 app 变量（FastAPI 实例）
    # - host="0.0.0.0" 表示监听所有网络接口（允许外部访问）
    # - port=8000 是服务监听的端口号
    # - reload=True 开启热重载：代码修改后自动重启服务（开发阶段常用）
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)