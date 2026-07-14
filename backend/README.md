# 神行库 · Product Marketing AI

基于产品知识库，通过多 Agent 协作快速生成适配不同渠道和受众的营销内容平台。

## 快速开始

### 1. 初始化 PostgreSQL 数据库（首次运行）

```bash
# 设置密码环境变量（替换为你的 postgres 密码）
set PGPASSWORD=123456

# 执行建库建表 + 插入模拟数据脚本
psql -U postgres -h 127.0.0.1 -f database\init_postgresql.sql
```

SQL 文件包含：建库 → 建表（完备字段 COMMENT）→ 索引 → 插入 3 个产品 + 6 个场景模板。

### 2. 安装依赖

```bash
.venv\Scripts\pip install -r requirements.txt
```

### 3. 启动服务

```bash
python main.py
```

### 4. 打开浏览器

访问 http://127.0.0.1:8000

### 数据库连接配置

默认连接本地 PostgreSQL，可通过环境变量覆盖（见 `config.py`）：

| 环境变量 | 默认值 | 说明 |
|---------|--------|------|
| `DB_HOST` | 127.0.0.1 | 数据库地址 |
| `DB_PORT` | 5432 | 端口 |
| `DB_NAME` | shenxingdb | 库名 |
| `DB_USER` | postgres | 用户名 |
| `DB_PASSWORD` | 123456 | 密码 |

如需修改密码，编辑 `config.py` 中的 `DB_PASSWORD` 默认值，或设置环境变量。

## 架构总览

```
用户选择 场景 + 产品 + 渠道
          ↓
[产品信息检索 Agent]  从知识库获取相关产品信息
          ↓
[竞品分析 Agent]      竞品场景下构建对比框架（其他场景跳过）
          ↓
[内容生成 Agent]      基于场景模板 + 产品信息 → 生成多版本初稿
          ↓
[渠道适配 Agent]      根据目标渠道调整风格（官网/微信/LinkedIn/邮件/PPT）
          ↓
[内容校验 Agent]      验证参数一致性、检查敏感词、卖点覆盖
          ↓
      输出最终结果（多版本 + Agent 执行链路 + 校验报告）
```

## 功能模块

| 模块 | 功能 | 对应需求 |
|------|------|---------|
| 产品知识库 | 结构化录入/编辑/删除/检索产品信息 | F1-1 ~ F1-4 |
| 场景模板 | 6 个内置场景 + 自定义场景 | F2-1 ~ F2-3 |
| 多 Agent 生成 | 5 个 Agent 串行编排 | F3-1 ~ F3-6 |
| 内容输出 | 多版本展示/编辑/导出/历史 | F4-1 ~ F4-5 |

## 预置场景

| ID | 场景 | 说明 |
|----|------|------|
| S001 | 官网首页 Banner 文案 | 主标题+副标题+CTA |
| S002 | 产品介绍文案 | 面向不同受众的产品介绍文章 |
| S003 | 竞品对比分析报告 | 功能对比表+差异化卖点+话术建议 |
| S004 | 客户案例包装 | STAR 结构成功案例 |
| S005 | 演示 PPT 大纲 | 结构化 PPT 每页要点 |
| S006 | 社交媒体帖子 | 多语气风格短文案+话题标签 |

## 技术栈

- **后端**：Python 3.13 + FastAPI + PostgreSQL（psycopg2 连接池）
- **前端**：Vue 3 + Element Plus（CDN 引入，无需构建）
- **数据库**：PostgreSQL 12+（JSONB 存储 JSON 字段，GIN 索引加速检索）
- **LLM**：默认模板引擎模式；配置 API Key 后自动切换真实大模型

## 接入真实 LLM（可选）

默认使用内置模板引擎，无需联网即可运行。如需接入真实大模型获得更优生成效果：

```bash
# Windows PowerShell
$env:LLM_API_KEY = "你的API密钥"
$env:LLM_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"  # 通义千问
$env:LLM_MODEL = "qwen-plus"
python main.py
```

兼容所有 OpenAI 格式的 Chat Completions API（通义千问/DeepSeek/智谱GLM/Moonshot 等）。

## 目录结构

```
shenxing/
├── app/
│   ├── main.py              # FastAPI 应用入口
│   ├── database.py          # SQLite 数据库
│   ├── models.py            # Pydantic 数据模型
│   ├── seed_data.py         # 初始示例数据
│   ├── agents/              # 多 Agent 核心
│   │   ├── base.py          # Agent 基类 + 共享上下文
│   │   ├── llm_provider.py  # LLM 双模式 Provider
│   │   ├── retrieval_agent.py    # ① 产品信息检索
│   │   ├── competitor_agent.py   # ② 竞品分析
│   │   ├── generation_agent.py   # ③ 内容生成
│   │   ├── channel_agent.py      # ④ 渠道适配
│   │   ├── validation_agent.py   # ⑤ 内容校验
│   │   └── orchestrator.py       # Agent 编排器
│   └── routers/             # API 路由
│       ├── products.py      # 产品知识库 CRUD
│       ├── scenarios.py     # 场景模板 CRUD
│       ├── generate.py      # 内容生成
│       └── history.py       # 历史记录 + 导出
├── frontend/
│   └── index.html           # Vue 3 单页应用
├── config.py                # 全局配置
├── main.py                  # 启动入口
└── requirements.txt
```

## API 速览

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/health` | 健康检查 |
| GET/POST | `/api/products` | 产品列表/新增 |
| GET/PUT/DELETE | `/api/products/{id}` | 产品详情/编辑/删除 |
| GET/POST | `/api/scenarios` | 场景列表/新增 |
| POST | `/api/generate` | 生成营销内容 |
| GET | `/api/history` | 历史记录列表 |
| GET | `/api/history/{id}/export` | 导出（markdown/txt） |
| GET | `/docs` | Swagger API 文档 |
