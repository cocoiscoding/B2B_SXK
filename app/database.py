"""PostgreSQL 数据库管理：连接池、查询助手、事务。

本模块封装了所有数据库操作的基础设施，其他模块通过调用 query / query_one / transaction
等函数操作数据库，无需直接写 SQL 连接管理代码。

核心技术：
- psycopg2：Python 操作 PostgreSQL 的主流库
- ThreadedConnectionPool：线程安全的连接池，多线程环境下复用连接
- RealDictCursor：查询结果以字典形式返回（{"id": 1, "name": "xxx"}）而非元组 (1, "xxx")
- Json：把 Python 字典/列表序列化为 PostgreSQL 的 JSONB 类型

设计模式：
- @contextmanager：把"获取资源 + try/finally 释放资源"的样板代码封装成 with 语句
- 全局单例连接池：整个应用共享一个连接池，避免反复创建
"""
import os
import psycopg2
from psycopg2.extras import RealDictCursor, Json
from psycopg2.pool import ThreadedConnectionPool
from contextlib import contextmanager
from typing import Any, Iterator
# 从 config.py 导入数据库连接参数
from config import (
    DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD,
    DB_CLIENT_ENCODING, DB_MIN_CONN, DB_MAX_CONN,
)

# 全局连接池实例，初始为 None，首次使用时才创建（懒加载）
# ThreadedConnectionPool | None 是类型注解，表示变量可以是连接池或 None
_pool: ThreadedConnectionPool | None = None


def _get_pool() -> ThreadedConnectionPool:
    """获取连接池实例（单例模式）。

    如果连接池还未创建，则创建一个新的。
    这样设计避免应用启动时就连接数据库，延迟到首次使用时才连接。
    """
    # global 关键字声明我们要修改模块级变量 _pool，而非创建局部变量
    global _pool
    if _pool is None:
        # 强制设置客户端编码，避免数据库返回的中文错误信息被 psycopg2 以 UTF-8 解码失败
        os.environ.setdefault("PGCLIENTENCODING", DB_CLIENT_ENCODING)
        # 创建连接池：
        # - DB_MIN_CONN：常驻连接数（启动时就创建）
        # - DB_MAX_CONN：最大连接数（按需扩容到此上限）
        # - options：在连接上执行 SET client_encoding，确保中文错误信息可正确解码
        _pool = ThreadedConnectionPool(
            DB_MIN_CONN, DB_MAX_CONN,
            host=DB_HOST, port=DB_PORT, dbname=DB_NAME,
            user=DB_USER, password=DB_PASSWORD,
            options=f"-c client_encoding={DB_CLIENT_ENCODING}",
        )
    return _pool


# @contextmanager 装饰器：把函数变成可用 with 语句的上下文管理器
# Iterator[psycopg2.extensions.connection] 是返回值类型注解
@contextmanager
def get_conn() -> Iterator[psycopg2.extensions.connection]:
    """从连接池获取一个连接，使用完毕自动归还。

    用法：
        with get_conn() as conn:
            conn.execute("SELECT 1")

    无论中间是否出错，finally 块都会执行，确保连接被归还到池中。
    """
    pool = _get_pool()
    conn = pool.getconn()      # 从池中借出一个连接
    try:
        yield conn             # yield 把 conn 交给 with 语句块使用
    finally:
        pool.putconn(conn)     # 无论是否出错，都把连接还回池中


def query(sql: str, params: tuple | None = None) -> list[dict[str, Any]]:
    """执行查询 SQL，返回字典列表。

    参数：
        sql: SQL 语句，用 %s 作占位符（PostgreSQL 风格，注意不是 ?）
        params: SQL 参数元组，如 (name_value,) —— 末尾逗号表示单元素元组

    返回：[{"id": "P001", "name": "xxx"}, ...]

    为什么要用 %s 占位符而不是字符串拼接？
    → 防止 SQL 注入攻击。psycopg2 会自动处理转义。
    """
    with get_conn() as conn:
        # cursor_factory=RealDictCursor 让查询结果以字典形式返回
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, params)
            # fetchall() 取出所有结果行
            # dict(row) 把 RealDictRow 转成普通 dict
            return [dict(row) for row in cur.fetchall()]


def query_one(sql: str, params: tuple | None = None) -> dict[str, Any] | None:
    """执行查询 SQL，返回单条字典或 None。

    用于按 ID 查询等只期望一条结果的场景。
    返回 None 表示未找到记录。
    """
    with get_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, params)
            row = cur.fetchone()    # 只取第一条
            return dict(row) if row else None


def execute(sql: str, params: tuple | None = None) -> int:
    """执行 INSERT/UPDATE/DELETE 语句，返回受影响行数。

    自动 commit（提交事务），调用方无需手动提交。
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            conn.commit()           # 提交事务，使修改生效
            return cur.rowcount     # 返回受影响的行数


@contextmanager
def transaction() -> Iterator[psycopg2.extensions.cursor]:
    """事务上下文管理器：自动 commit / rollback。

    用法：
        with transaction() as cur:
            cur.execute("INSERT INTO ...")
            cur.execute("UPDATE ...")
        # 退出 with 块时：全部成功 → commit；任意失败 → rollback

    事务的好处：要么所有操作都成功，要么都失败回滚，保证数据一致性。
    """
    with get_conn() as conn:
        cur = conn.cursor()
        try:
            yield cur               # 把 cursor 交给 with 语句块
            conn.commit()           # 全部成功 → 提交
        except Exception:
            conn.rollback()         # 出错 → 回滚所有操作
            raise                   # 重新抛出异常，让调用方知道
        finally:
            cur.close()             # 无论成败，关闭 cursor


def init_db() -> None:
    """建表（IF NOT EXISTS）。

    应用启动时调用。与 init_postgresql.sql 保持一致。
    IF NOT EXISTS 表示表已存在则跳过，不会报错。
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS products (
                    id               VARCHAR(20)  PRIMARY KEY,
                    name             VARCHAR(200) NOT NULL,
                    category         JSONB        NOT NULL DEFAULT '[]'::jsonb,
                    description      TEXT,
                    features         JSONB        NOT NULL DEFAULT '[]'::jsonb,
                    target_customers JSONB        NOT NULL DEFAULT '[]'::jsonb,
                    pricing          VARCHAR(500),
                    selling_points   JSONB        NOT NULL DEFAULT '[]'::jsonb,
                    images           JSONB        NOT NULL DEFAULT '[]'::jsonb,
                    documents        JSONB        NOT NULL DEFAULT '[]'::jsonb,
                    embedding        JSONB,
                    created_at       TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at       TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );

                CREATE TABLE IF NOT EXISTS scenarios (
                    id          VARCHAR(20)  PRIMARY KEY,
                    name        VARCHAR(200) NOT NULL,
                    description TEXT,
                    parameters  JSONB        NOT NULL DEFAULT '[]'::jsonb,
                    created_at  TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );

                CREATE TABLE IF NOT EXISTS templates (
                    id          VARCHAR(20)  PRIMARY KEY,
                    scenario_id VARCHAR(20)  NOT NULL REFERENCES scenarios(id) ON DELETE CASCADE,
                    name        VARCHAR(200) NOT NULL,
                    tag         VARCHAR(100),
                    description TEXT,
                    prompt      TEXT,
                    constraints JSONB        NOT NULL DEFAULT '{}'::jsonb,
                    structure   TEXT,
                    examples    JSONB        NOT NULL DEFAULT '[]'::jsonb,
                    differentiation_dims JSONB NOT NULL DEFAULT '[]'::jsonb,
                    applicable_channels JSONB NOT NULL DEFAULT '[]'::jsonb,
                    tags                 JSONB NOT NULL DEFAULT '[]'::jsonb,
                    created_at  TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );

                CREATE TABLE IF NOT EXISTS history (
                    id            VARCHAR(20)  PRIMARY KEY,
                    product_id    VARCHAR(20),
                    product_name  VARCHAR(200),
                    scenario_id   VARCHAR(20),
                    scenario_name VARCHAR(200),
                    channel       VARCHAR(100),
                    style         VARCHAR(100),
                    params        JSONB        NOT NULL DEFAULT '{}'::jsonb,
                    versions      JSONB        NOT NULL DEFAULT '[]'::jsonb,
                    agent_trace   JSONB        NOT NULL DEFAULT '[]'::jsonb,
                    validated     BOOLEAN      NOT NULL DEFAULT FALSE,
                    issues        JSONB        NOT NULL DEFAULT '[]'::jsonb,
                    feedback      VARCHAR(20),    -- 用户反馈：like / dislike / NULL
                    feedback_voters JSONB      NOT NULL DEFAULT '{}'::jsonb,  -- 每个成员的反馈 {member_id: like/dislike}，per-user 不覆盖
                    created_at    TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );

                -- 草稿表：多阶段交互式生成流程的中间状态
                -- 检索生成校验 -> 用户选版改内容 -> 多渠道适配 -> 文生图 -> 落 history
                CREATE TABLE IF NOT EXISTS drafts (
                    id               VARCHAR(20)  PRIMARY KEY,        -- D + uuid hex
                    user_id          VARCHAR(20)  NOT NULL,
                    product_id       VARCHAR(20)  NOT NULL,
                    product_name     VARCHAR(200),
                    scenario_id      VARCHAR(20)  NOT NULL,
                    scenario_name    VARCHAR(200),
                    template_id      VARCHAR(20),
                    template_name    VARCHAR(200),
                    style            VARCHAR(100),
                    params           JSONB        NOT NULL DEFAULT '{}'::jsonb,
                    stage            VARCHAR(20)  NOT NULL DEFAULT 'draft',  -- draft/editing/adapted/imaged/done
                    retrieved_info   JSONB,                              -- 阶段1 检索产物
                    draft_versions   JSONB        NOT NULL DEFAULT '[]'::jsonb,  -- 阶段1 三个初稿
                    validation       JSONB,                              -- {issues, validated}
                    agent_trace      JSONB        NOT NULL DEFAULT '[]'::jsonb,
                    selected_version JSONB,                              -- 阶段2 用户选定+改动后的那一版
                    channels         JSONB        NOT NULL DEFAULT '[]'::jsonb,  -- 阶段3 用户多选渠道
                    versions         JSONB        NOT NULL DEFAULT '[]'::jsonb,  -- 阶段3 N 个渠道版本(每版带 channel)
                    history_id       VARCHAR(20),                         -- 阶段4 落库后回填
                    created_at       TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at       TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
                """
            )
        conn.commit()
        # 兼容老库：如果 history 表在新增 feedback 列之前就已创建，
        # 上面的 CREATE TABLE IF NOT EXISTS 会跳过，这里用 ALTER 补列。
        # ADD COLUMN IF NOT EXISTS 是 PostgreSQL 9.6+ 语法，已存在则跳过，幂等安全。
        with conn.cursor() as cur:
            cur.execute(
                "ALTER TABLE history ADD COLUMN IF NOT EXISTS feedback VARCHAR(20)"
            )
            # 团队协作：每个成员的反馈 {member_id: like/dislike}，per-user 不互相覆盖
            cur.execute(
                "ALTER TABLE history ADD COLUMN IF NOT EXISTS feedback_voters JSONB NOT NULL DEFAULT '{}'::jsonb"
            )
            # 加分项：团队协作——产品与历史记录加"创建人"列
            cur.execute(
                "ALTER TABLE products ADD COLUMN IF NOT EXISTS created_by VARCHAR(20)"
            )
            # 老库兼容：早期 products 表可能没有 images/documents 列，补上（IF NOT EXISTS 幂等）
            cur.execute(
                "ALTER TABLE products ADD COLUMN IF NOT EXISTS images JSONB NOT NULL DEFAULT '[]'::jsonb"
            )
            cur.execute(
                "ALTER TABLE products ADD COLUMN IF NOT EXISTS documents JSONB NOT NULL DEFAULT '[]'::jsonb"
            )
            # 竞品列表：供竞品分析 Agent 自动识别（docx 解析可抽取，前端可维护）
            cur.execute(
                "ALTER TABLE products ADD COLUMN IF NOT EXISTS competitors JSONB NOT NULL DEFAULT '[]'::jsonb"
            )
            cur.execute(
                "ALTER TABLE history ADD COLUMN IF NOT EXISTS created_by VARCHAR(20)"
            )
            # 模板结构化约束列：老库 templates 表在新增 constraints 列前已创建，这里幂等补列
            cur.execute(
                "ALTER TABLE templates ADD COLUMN IF NOT EXISTS constraints JSONB NOT NULL DEFAULT '{}'::jsonb"
            )
            # 第二步增强：产出骨架 + 参考范例（few-shot），供 GenerationAgent 构造 prompt
            cur.execute(
                "ALTER TABLE templates ADD COLUMN IF NOT EXISTS structure TEXT"
            )
            cur.execute(
                "ALTER TABLE templates ADD COLUMN IF NOT EXISTS examples JSONB NOT NULL DEFAULT '[]'::jsonb"
            )
            # 第三步：多版本差异化维度，驱动 GenerationAgent 各版本的差异方向
            cur.execute(
                "ALTER TABLE templates ADD COLUMN IF NOT EXISTS differentiation_dims JSONB NOT NULL DEFAULT '[]'::jsonb"
            )
            # 第四步：适用渠道（ChannelAgent 适配性告警）+ 多维标签（前端筛选）
            cur.execute(
                "ALTER TABLE templates ADD COLUMN IF NOT EXISTS applicable_channels JSONB NOT NULL DEFAULT '[]'::jsonb"
            )
            cur.execute(
                "ALTER TABLE templates ADD COLUMN IF NOT EXISTS tags JSONB NOT NULL DEFAULT '[]'::jsonb"
            )
            # 模板审核制 + 复用：status(审核状态)/created_by/审核留痕/use_count(使用次数)/is_featured(推荐)
            cur.execute(
                "ALTER TABLE templates ADD COLUMN IF NOT EXISTS status VARCHAR(20) NOT NULL DEFAULT 'approved'"
            )
            cur.execute(
                "ALTER TABLE templates ADD COLUMN IF NOT EXISTS created_by VARCHAR(20)"
            )
            cur.execute(
                "ALTER TABLE templates ADD COLUMN IF NOT EXISTS reviewed_by VARCHAR(20)"
            )
            cur.execute(
                "ALTER TABLE templates ADD COLUMN IF NOT EXISTS reviewed_at TIMESTAMP WITH TIME ZONE"
            )
            cur.execute(
                "ALTER TABLE templates ADD COLUMN IF NOT EXISTS review_note TEXT"
            )
            cur.execute(
                "ALTER TABLE templates ADD COLUMN IF NOT EXISTS use_count INT NOT NULL DEFAULT 0"
            )
            cur.execute(
                "ALTER TABLE templates ADD COLUMN IF NOT EXISTS is_featured BOOLEAN NOT NULL DEFAULT FALSE"
            )
            # 加分项：团队成员表（演进为用户表，含登录鉴权字段）
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS members (
                    id            VARCHAR(20)  PRIMARY KEY,
                    name          VARCHAR(50)  NOT NULL,
                    color         VARCHAR(20)  DEFAULT '#409eff',
                    username      VARCHAR(50)  UNIQUE,
                    password_hash VARCHAR(255),
                    email         VARCHAR(100),
                    is_admin      BOOLEAN      NOT NULL DEFAULT FALSE,
                    created_at    TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
                """
            )
            # 兼容老库：上一轮的 members 表没有鉴权列，这里补上（幂等）
            cur.execute("ALTER TABLE members ADD COLUMN IF NOT EXISTS username      VARCHAR(50) UNIQUE")
            cur.execute("ALTER TABLE members ADD COLUMN IF NOT EXISTS password_hash VARCHAR(255)")
            cur.execute("ALTER TABLE members ADD COLUMN IF NOT EXISTS email         VARCHAR(100)")
            cur.execute("ALTER TABLE members ADD COLUMN IF NOT EXISTS is_admin      BOOLEAN NOT NULL DEFAULT FALSE")
            # 渠道配置表：驱动 ChannelAgent 的通用规则适配
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS channels (
                    name           VARCHAR(50)  PRIMARY KEY,
                    display_name   VARCHAR(100) NOT NULL,
                    tone           VARCHAR(100) NOT NULL DEFAULT '专业正式',
                    emoji          BOOLEAN      NOT NULL DEFAULT FALSE,
                    format         VARCHAR(50)  NOT NULL DEFAULT 'markdown',
                    description    TEXT,
                    is_builtin     BOOLEAN      NOT NULL DEFAULT FALSE
                );
                """
            )
            # Token 黑名单表：用于退出登录时撤销 Token
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS token_blacklist (
                    jti          VARCHAR(100) PRIMARY KEY,
                    token_type   VARCHAR(20)  NOT NULL,
                    user_id      VARCHAR(20)  NOT NULL,
                    expires_at   TIMESTAMP WITH TIME ZONE NOT NULL,
                    revoked_at   TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
                """
            )
            # 竞品分析入库：按 (产品, 竞品) 缓存分析结果，避免每次生成重跑 Tavily+LLM
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS competitor_analyses (
                    id              VARCHAR(20)  PRIMARY KEY,
                    product_id      VARCHAR(20)  NOT NULL,
                    competitor_name VARCHAR(200) NOT NULL,
                    analysis        JSONB        NOT NULL,
                    source          VARCHAR(50),
                    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    UNIQUE (product_id, competitor_name)
                );
                """
            )
        conn.commit()


def close_pool() -> None:
    """关闭连接池（应用退出时调用）。

    释放所有数据库连接，避免连接泄漏。
    """
    global _pool
    if _pool is not None:
        _pool.closeall()    # 关闭池中所有连接
        _pool = None        # 重置为 None，下次使用时会重新创建


# ===== 兼容旧接口的适配层 =====
# JSONB 字段读取时已是 Python 对象，无需 json.loads
def _parse_json_fields(row: dict, fields: list[str]) -> dict:
    """兼容旧接口：JSONB 字段在 PostgreSQL 中已是 Python 对象，此处只做空值补全和类型兼容。

    早期 SQLite 版本需要 json.loads 反序列化，迁移到 PostgreSQL 后 JSONB 字段
    由 psycopg2 自动转为 Python 对象，此函数仅保留用于空值处理。

    兼容性处理：
    - category 字段：旧数据可能是字符串，需转为数组
    - images/documents 字段：旧数据可能是空对象 {}，需转为空数组 []
    """
    if row is None:
        return {}
    d = dict(row)
    # 这些字段是列表类型，如果为 None 则补成空列表
    list_fields = {"features", "target_customers", "category", "selling_points",
                   "parameters", "versions", "agent_trace", "issues",
                   "competitors", "images", "documents"}
    for f in fields:
        val = d.get(f)
        if val is None:
            d[f] = [] if f in list_fields else {}
        # 兼容旧数据：category 可能是字符串，需转为数组
        elif f == "category" and isinstance(val, str):
            d[f] = [val] if val else []
        # 兼容旧数据：images/documents 可能是非数组类型，需转为空数组
        elif f in ("images", "documents") and not isinstance(val, list):
            d[f] = []
    return d