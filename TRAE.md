# 神行库 · Product Marketing AI — 项目上下文

> 一句话定位：基于产品知识库，通过多 Agent 协作（检索→竞品→生成→渠道→校验→配图）快速生成适配不同渠道和受众的 B2B 营销内容的 AI 平台。
> 本文件由 project-init-context skill 基于代码现状自动生成，供人类开发者与 AI Agent 共享。
> 前端专属上下文另见 [frontend/TRAE.md](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK/B2B_SXK/frontend/TRAE.md)，本文档覆盖全栈（以后端为重点，避免重复）。

---

## 1. 技术栈

### 后端（`backend/`）

| 类别 | 技术 | 版本约束 |
|------|------|---------|
| 语言 | Python | ≥ 3.13（待确认，见第 11 节） |
| Web 框架 | FastAPI | ≥ 0.110.0 |
| ASGI 服务器 | uvicorn[standard] | ≥ 0.27.0 |
| 数据校验 | Pydantic | ≥ 2.0.0（v2 语法） |
| 数据库 | PostgreSQL | 本地实例，库名 `shenxingdb` |
| 数据库驱动 | psycopg2-binary | ≥ 2.9.9（ThreadedConnectionPool，原生 SQL，无 ORM） |
| 鉴权 | PyJWT ≥ 2.8.0 + bcrypt ≥ 4.0.0 | JWT 双令牌 + bcrypt 密码哈希 |
| HTTP 客户端 | httpx | ≥ 0.27.0（调用 LLM / Tavily API） |
| 文档解析 | python-docx ≥ 1.1.0、pdfplumber ≥ 0.11.0 | 产品文档上传解析 |
| 图像处理 | Pillow | ≥ 10.0.0 |
| 联网搜索 | tavily | ≥ 1.1.0（竞品分析，可选） |
| 配置 | python-dotenv ≥ 1.0.0 | 从 `.env` 加载环境变量 |
| 文件上传 | python-multipart | ≥ 0.0.9 |

### 前端（`frontend/`）

| 类别 | 技术 | 版本 |
|------|------|------|
| 框架 | Vue 3（Composition API） | ^3.5.13 |
| UI 库 | Element Plus | ^2.9.1 |
| 构建工具 | Vite | ^6.0.5 |
| 状态管理 | Pinia | ^2.3.0 |
| 路由 | Vue Router（Hash 模式） | ^4.5.0 |
| HTTP | axios | ^1.7.9 |
| 国际化 | vue-i18n | ^10.0.5 |
| 加密 | crypto-js、js-md5、js-base64 | Token / 密码处理 |
| 工具 | @vueuse/core、nprogress、js-cookie | |
| 自动导入 | unplugin-auto-import、unplugin-vue-components | Element Plus 按需自动注册 |
| 样式 | sass | |
| Lint | eslint 8 + eslint-plugin-vue | |

### 中间件 / 外部服务

- **PostgreSQL**：唯一持久化存储，本地默认 `127.0.0.1:5432`
- **LLM API**（可选）：默认通义千问 `qwen-plus`，兼容 OpenAI API 协议；未配置 `LLM_API_KEY` 时降级为 Mock 模板引擎
- **Embedding API**（可选）：未配置时降级为 MD5 哈希伪向量（语义检索变弱但不崩）
- **Tavily 搜索 API**（可选）：竞品分析联网搜索，未配置时降级为 Mock 规则分析

### 工具链

- 包管理器：后端 `pip`，前端 `npm`
- 无 Dockerfile、无 docker-compose、无 CI/CD 配置（见第 8 节）

---

## 2. 项目结构

```
B2B_SXK/
├── backend/                         # Python FastAPI 后端
│   ├── main.py                      # ★ 启动入口（python main.py）
│   ├── config.py                    # ★ 全局配置（所有环境变量集中管理）
│   ├── requirements.txt             # Python 依赖清单
│   ├── README.md                    # 后端说明文档
│   ├── BACKEND_FILES.md             # 面向初学者的文件清单
│   ├── .gitignore                   # 忽略 .env / __pycache__ / data/ / *.db
│   ├── app/
│   │   ├── main.py                  # ★ FastAPI 应用创建、路由注册、lifespan
│   │   ├── database.py              # ★ PostgreSQL 连接池 + 建表 + query/execute
│   │   ├── auth.py                  # ★ JWT 签发/解码 + bcrypt + 依赖注入
│   │   ├── models.py                # ★ Pydantic v2 模型（所有 DTO）
│   │   ├── seed_data.py             # 初始示例数据（3 产品 + 6 场景 + 4 用户）
│   │   ├── vector_search.py         # 向量检索（余弦相似度 + Embedding）
│   │   ├── seo_analyzer.py          # SEO 分析
│   │   ├── docx_parser.py           # docx/pdf 文档解析
│   │   ├── routers/                 # 11 个路由模块
│   │   │   ├── auth.py              #   /api/auth（登录/注册/刷新/登出/me）
│   │   │   ├── products.py          #   /api/products（产品 CRUD + 上传）
│   │   │   ├── scenarios.py         #   /api/scenarios（场景 CRUD）
│   │   │   ├── templates.py         #   /api/templates（模板 CRUD + 审核）
│   │   │   ├── generate.py          #   /api/generate（旧版一次性生成）
│   │   │   ├── drafts.py            #   /api/drafts（★ 草稿四阶段 + SSE 流式）
│   │   │   ├── history.py           #   /api/history（历史记录 + 反馈）
│   │   │   ├── members.py           #   /api/members（团队成员管理）
│   │   │   ├── seo.py               #   /api/seo（SEO 建议）
│   │   │   ├── channels.py          #   /api/channels（渠道管理）
│   │   │   └── competitors.py       #   /api/competitors（竞品分析）
│   │   └── agents/                  # 多 Agent 系统
│   │       ├── base.py              #   ★ AgentContext + BaseAgent（模板方法模式）
│   │       ├── orchestrator.py      #   ★ 编排器（串联 6 Agent + 草稿流程）
│   │       ├── retrieval_agent.py   #   ① 产品信息检索
│   │       ├── competitor_agent.py  #   ② 竞品分析（仅竞品场景激活）
│   │       ├── generation_agent.py  #   ③ 内容生成
│   │       ├── channel_agent.py     #   ④ 渠道适配
│   │       ├── validation_agent.py  #   ⑤ 内容校验
│   │       ├── image_agent.py       #   ⑥ 文生图配图
│   │       └── llm_provider.py      #   LLM Provider（Mock / OpenAI 兼容）
│   ├── database/
│   │   └── init_postgresql.sql      # ★ 完整建库建表脚本 + 索引 + 种子数据
│   ├── frontend/                    # 旧版 CDN 前端（已被根 frontend/ 取代）
│   │   └── index.html
│   └── tests/
│       ├── __init__.py
│       └── test_regressions.py      # unittest 回归测试
│
└── frontend/                        # Vue 3 前端（独立，当前主力）
    ├── package.json
    ├── vite.config.js               # ★ Vite 配置（别名 @、代理、分包）
    ├── .eslintrc.cjs                # ESLint 规则
    ├── .editorconfig                # 编辑器统一配置
    ├── .env                         # 基础环境变量（所有环境共享）
    ├── .env.dev                     # 开发环境
    ├── .env.prod                    # 生产环境
    ├── TRAE.md                      # 前端专属上下文文档
    └── src/                         # Vue 源码（详见 frontend/TRAE.md）
```

**拓扑类型**：前后端分离（`backend/` + `frontend/` 双顶层），无 monorepo 工具编排。

---

## 3. 常用命令（注意执行目录）

### 后端（在 `backend/` 目录执行）

```bash
# 安装依赖
cd backend
pip install -r requirements.txt

# 启动开发服务器（端口 8000，热重载）
python main.py
# 或：uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 运行测试（unittest，无需数据库连接）
python -m pytest tests/
# 或：python -m unittest tests.test_regressions

# 初始化数据库（首次部署，手动执行 SQL 脚本）
psql -U postgres -f database/init_postgresql.sql
```

### 前端（在 `frontend/` 目录执行）

```bash
# 安装依赖
cd frontend
npm install

# 本地开发（端口 53200，自动代理 /api → http://localhost:8000）
npm run dev

# 生产构建
npm run build
# 构建产物优化版
npm run build:prod

# 预览构建产物
npm run preview

# 代码检查
npm run lint
```

### 关键端口

| 服务 | 端口 | 说明 |
|------|------|------|
| 后端 FastAPI | 8000 | `python main.py` 启动 |
| 前端 Vite Dev | 53200 | `npm run dev` 启动 |
| PostgreSQL | 5432 | 默认数据库端口 |

---

## 4. 架构与代码组织

### 4.1 后端分层

```
main.py（启动入口）
  └─ app/main.py（FastAPI 应用 + lifespan 初始化）
       ├─ routers/（路由层 — 接收 HTTP 请求，参数校验，调用编排器/数据库）
       │    └─ 路由函数依赖注入 auth.get_current_user
       ├─ agents/orchestrator.py（业务编排层 — 多 Agent 串联）
       │    └─ agents/（Agent 层 — 各自完成独立任务）
       │         └─ agents/base.py（模板方法模式：execute() → _execute()）
       └─ database.py（数据访问层 — 原生 SQL，无 ORM）
            ├─ query() / query_one() / execute()
            └─ transaction()（上下文管理器，自动 commit/rollback）
```

### 4.2 多 Agent 串行链路

```
RetrievalAgent（检索）
  → CompetitorAgent（竞品分析，仅竞品场景激活）
  → GenerationAgent（生成，支持多版本 + 返工重试）
  → ChannelAgent（渠道适配）
  → ValidationAgent（校验，失败可回退到 GenerationAgent 重试）
  → ImageAgent（文生图配图）
```

- **编排器**：`Orchestrator`（单例，`get_orchestrator()`），定义在 [orchestrator.py](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK/B2B_SXK/backend/app/agents/orchestrator.py)
- **共享上下文**：`AgentContext`（@dataclass），在 Agent 间流转中间产物（retrieved_info / draft_versions / versions / competitor_info / feedback_issues / feedback_examples）
- **返工机制**：校验失败时，orchestrator 将问题写入 `feedback_issues`，重新调用 GenerationAgent（每版最多 2 次重试）

### 4.3 草稿四阶段状态机

草稿是核心业务流程，采用交互式四阶段设计（区别于旧版 `generate` 一次性生成）：

```
阶段1 draft    → POST /api/drafts（创建初稿）/ POST /api/drafts/stream（SSE 流式）
                  状态：drafting → editing
阶段2 select   → PUT /api/drafts/{id}/select（用户选定版本）
                  状态：editing → selected
阶段3 adapt    → POST /api/drafts/{id}/adapt（多渠道适配）
                  状态：selected → adapted
阶段4 finalize → POST /api/drafts/{id}/finalize（文生图 + 落 history）
                  状态：adapted → imaged → done
```

- 草稿数据存在 `drafts` 表，`stage` 字段驱动状态流转
- `finalize` 使用 CAS（Compare-And-Swap）占位防并发重复提交
- SSE 流式实现：`_draft_stream()` 后台线程跑 `run_draft`，通过 `queue` 推送事件（step / done / error）

### 4.4 前端入口与状态管理

- **入口**：`frontend/src/main.js` → `App.vue`
- **路由**：Vue Router（Hash 模式），路由定义在 `src/router/`
- **状态管理**：Pinia，store 定义在 `src/store/`
- **路径别名**：`@` → `./src`（[vite.config.js](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK/B2B_SXK/frontend/vite.config.js)）
- **HTTP 封装**：axios，统一拦截器在 `src/utils/`，请求前自动注入 `sxk-` 前缀的 Token

### 4.5 端到端示例链路（创建营销内容）

```
用户选择产品 + 场景，点击"生成"
  → 前端 POST /api/drafts/stream（SSE）
  → drafts.py: _draft_stream() 启动后台线程
  → orchestrator.run_draft()
    → RetrievalAgent.execute()     // 从 products 表检索 + 向量搜索
    → GenerationAgent.execute()    // 调用 LLM 生成多版本
    → ValidationAgent.execute()    // 校验内容
  → SSE 推送每个 Agent 的 step 事件到前端
  → 前端实时展示生成进度
  → 用户选定版本 → PUT /api/drafts/{id}/select
  → 多渠道适配 → POST /api/drafts/{id}/adapt
  → 文生图 + 落 history → POST /api/drafts/{id}/finalize
```

---

## 5. 编码规范

### 前端

| 项目 | 配置 |
|------|------|
| ESLint 规则集 | `eslint:recommended` + `plugin:vue/vue3-recommended` |
| 生产环境 | `no-console` 和 `no-debugger` 为 `error` |
| 未使用变量 | 下划线前缀（`_`）的参数/变量豁免 |
| Vue 组件名 | 关闭 `vue/multi-word-component-names`（允许单字组件名） |
| 缩进 | 2 空格（.editorconfig） |
| 换行符 | LF（.editorconfig） |
| 编码 | UTF-8 |
| 文件尾 | 插入换行，去除行尾空格（.md 除外） |
| Prettier | 未配置（无 .prettierrc） |
| 路径别名 | `@` → `./src`（vite.config.js resolve.alias） |
| SCSS | 自动注入 `@/styles/variables.scss`（additionalData） |
| 自动导入 | unplugin-auto-import（Vue/Vue Router/Pinia API 自动导入） |
| 组件注册 | unplugin-vue-components（Element Plus 组件按需自动注册） |

### 后端

| 项目 | 说明 |
|------|------|
| Lint | 无配置文件（无 ruff / flake8 / mypy），遵循 PEP 8 约定 |
| 类型注解 | Python 3 风格（`dict[str, Any]`、`str \| None`），Pydantic v2 模型 |
| 配置管理 | 所有配置集中在 [config.py](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK/B2B_SXK/backend/config.py)，环境变量覆盖 |
| 数据库访问 | 原生 SQL，统一通过 `database.query()` / `query_one()` / `execute()` / `transaction()` |
| JSONB 处理 | `_parse_json_fields()` 兼容旧 SQLite 数据（JSONB 已是 Python 对象） |

### 提交规范

- **无 commitlint / husky / .husky 配置**——提交信息无强制约束
- Git 远程信息：未检测到 `.git/config`（待确认）

---

## 6. 数据与 API

### 6.1 数据库设计

PostgreSQL 库名 `shenxingdb`，共 **9 张表**：

| 表名 | 职责 | 关键字段 |
|------|------|---------|
| `products` | 产品信息库 | id（主键）、name、category（JSONB）、features（JSONB）、tech_params（JSONB）、embedding（向量） |
| `scenarios` | 营销场景 | id、name、description、params（JSONB） |
| `templates` | 提示词模板 | id、scenario_id（外键）、content、constraints（JSONB）、status（draft/pending/approved/rejected） |
| `drafts` | 草稿（四阶段） | id、user_id、product_id、scenario_id、stage（状态机）、versions（JSONB）、history_id |
| `history` | 生成历史 | id、product_id、scenario_id、content（JSONB）、feedback（JSONB） |
| `members` | 团队成员 | id、username、password_hash（bcrypt）、is_admin（布尔） |
| `channels` | 渠道 | id、name、description |
| `token_blacklist` | JWT 黑名单 | token_id（jti）、user_id、expires_at |
| `competitor_analyses` | 竞品分析 | id、product_id、analysis（JSONB） |

- **索引**：products.name / category / features(GIN)、templates.scenario_id、history.product_id/scenario_id/created_at、token_blacklist.user_id/expires_at、competitor_analyses.product_id
- **建表脚本**：[database/init_postgresql.sql](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK/B2B_SXK/backend/database/init_postgresql.sql)（DROP + CREATE DATABASE + 建表 + COMMENT + 索引 + 种子数据）
- **迁移策略**：`database.py` 的 `init_db()` 使用 `CREATE TABLE IF NOT EXISTS` + `ALTER TABLE ADD COLUMN IF NOT EXISTS` 兼容老库（无正式迁移工具）
- **种子数据**：`seed_data.py` 首次启动时灌入 3 个产品 + 6 个场景 + 12 个模板 + 4 个成员（密码 `123456`）

### 6.2 API 风格与路由

- **风格**：REST，统一前缀 `/api/`
- **路由注册**：[app/main.py](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK/B2B_SXK/backend/app/main.py) 中 `include_router()` 注册 11 个路由模块
- **请求校验**：Pydantic v2，所有 DTO 定义在 [models.py](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK/B2B_SXK/backend/app/models.py)
- **接口文档**：FastAPI 自动生成，开发模式访问 `http://127.0.0.1:8000/docs`（Swagger UI）
- **CORS**：`allow_origins=["*"]`（允许所有来源）
- **健康检查**：`GET /api/health`

### 6.3 鉴权机制

- **方式**：JWT 双令牌（access + refresh）
- **实现**：[auth.py](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK/B2B_SXK/backend/app/auth.py)
- **密码哈希**：bcrypt（72 字节截断）
- **access token**：30 分钟有效期，每次 API 请求在 `Authorization: Bearer <token>` 头携带
- **refresh token**：7 天有效期，仅用于刷新 access token
- **令牌防伪**：payload 含 `type` 字段（access/refresh），`decode_token(expected_type=)` 防止类型混淆
- **登出撤销**：access + refresh token 加入 `token_blacklist` 表，`cleanup_expired_tokens()` 定期清理
- **FastAPI 依赖**：`get_current_user`（OAuth2PasswordBearer）、`require_admin`、`is_owner_or_admin`

### 6.4 前端数据获取

- **HTTP 封装**：axios，统一拦截器注入 Token（`sxk-` 前缀的 TokenKey）
- **状态管理**：Pinia（全局状态）
- **代理**：开发环境 Vite proxy 将 `/api` 转发到 `VITE_API_TARGET`（默认 `http://localhost:8000`）

---

## 7. 环境变量

### 7.1 后端环境变量（`backend/.env`，已 gitignore）

| 变量 | 说明 | 默认值 | 敏感 |
|------|------|--------|------|
| `DB_HOST` | 数据库主机 | `127.0.0.1` | |
| `DB_PORT` | 数据库端口 | `5432` | |
| `DB_NAME` | 数据库名 | `shenxingdb` | |
| `DB_USER` | 数据库用户 | `postgres` | |
| `DB_PASSWORD` | 数据库密码 | `123456` | ⚠ 敏感 |
| `DB_MIN_CONN` / `DB_MAX_CONN` | 连接池大小 | `1` / `10` | |
| `LLM_API_KEY` | LLM API 密钥（空→Mock 模板引擎） | `""` | ⚠ 敏感 |
| `LLM_BASE_URL` | LLM API 地址 | 通义千问 | |
| `LLM_MODEL` | LLM 模型名 | `qwen-plus` | |
| `LLM_TIMEOUT` | 请求超时（秒） | `30` | |
| `EMBEDDING_API_KEY` | Embedding API 密钥（空→Mock 哈希） | `""` | ⚠ 敏感 |
| `EMBEDDING_BASE_URL` | Embedding API 地址 | 通义千问 | |
| `EMBEDDING_MODEL` | Embedding 模型（空→降级 Mock） | `""` | |
| `EMBEDDING_DIM` | 向量维度（须与模型一致） | `128` | |
| `JWT_SECRET` | JWT 签名密钥 | `shenxing-dev-secret-change-me` | ⚠ 敏感（生产必须覆盖） |
| `JWT_ACCESS_EXPIRE_MINUTES` | access token 有效期（分钟） | `30` | |
| `JWT_REFRESH_EXPIRE_DAYS` | refresh token 有效期（天） | `7` | |
| `TAVILY_API_KEY` | Tavily 搜索密钥（空→Mock） | `""` | ⚠ 敏感 |
| `DEFAULT_USER_PASSWORD` | 种子用户默认密码 | `123456` | |

### 7.2 前端环境变量（Vite，必须 `VITE_` 前缀）

| 变量 | 文件 | 说明 |
|------|------|------|
| `VITE_APP_TITLE` | `.env` | 应用标题（所有环境共享） |
| `VITE_PORT` | `.env.dev` | 开发服务器端口（`53200`） |
| `VITE_API_TARGET` | `.env.dev` / `.env.prod` | 后端 API 地址（dev: `http://localhost:8000`，prod: 留空待配置） |
| `VITE_APP_USE_MOCK_AUTH` | `.env.dev` / `.env.prod` | Mock 登录开关（dev/prod 均为 `false`） |
| `VITE_APP_USE_MOCK_BIZ` | `.env.dev` | Mock 业务接口开关（`false`） |
| `VITE_APP_ENV` | `.env.prod` | 环境标识（`prod`） |

> **注意**：前端环境变量前缀必须是 `VITE_`，否则运行时取不到值。

---

## 8. 部署

### 当前状态

- **无 Dockerfile / docker-compose**：未检测到容器化配置
- **无 CI/CD**：未检测到 GitHub Actions / GitLab CI / Jenkins 配置
- **无 Makefile / Taskfile**：无聚合命令

### 本地开发部署

1. **PostgreSQL**：本地安装，执行 `backend/database/init_postgresql.sql` 初始化
2. **后端**：`cd backend && pip install -r requirements.txt && python main.py`
3. **前端**：`cd frontend && npm install && npm run dev`
4. 访问前端 `http://localhost:53200`，后端 API `http://localhost:8000`

### 生产部署（推测）

- 前端 `npm run build` 产出 `dist/`，可由后端静态挂载（`app/main.py` 已挂载 `/assets`）或 nginx 反代
- 后端通过 `uvicorn` 启动（`python main.py` 内置 `reload=True`，**生产应关闭 reload**）
- `.env.prod` 中 `VITE_API_TARGET` 留空，注释提示由 CI / 网关注入或 nginx 同源反代

### 静态资源挂载

- `/assets` → `backend/frontend/`（旧版前端目录）
- `/uploads` → `backend/uploads/`（用户上传文件）

---

## 9. 业务领域

### 9.1 核心业务实体

| 实体 | 对应表 | 说明 |
|------|--------|------|
| 产品（Product） | `products` | 营销内容的对象，含功能列表、技术参数、图片、文档 |
| 场景（Scenario） | `scenarios` | 营销场景（官网 Banner / 产品介绍 / 竞品对比 / 客户案例 / PPT 大纲 / 社交媒体） |
| 模板（Template） | `templates` | 提示词模板，含约束、结构、示例、差异化维度、适用渠道 |
| 草稿（Draft） | `drafts` | 四阶段交互式内容生成流程的载体 |
| 历史（History） | `history` | 最终生成的营销内容归档，支持点赞/踩反馈 |
| 成员（Member） | `members` | 团队成员，admin / user 两级权限 |
| 渠道（Channel） | `channels` | 目标投放渠道（官网 / 微信 / 邮件等） |
| 竞品分析（CompetitorAnalysis） | `competitor_analyses` | 联网搜索竞品信息并分析 |

### 9.2 关键业务流程

**核心流程**：选择产品 → 选择场景 → 创建草稿（多 Agent 生成多版本）→ 用户选定版本 → 多渠道适配 → 文生图配图 → 归档为历史

**6 个预置场景**：
- S001 官网 Banner
- S002 产品介绍
- S003 竞品对比
- S004 客户案例
- S005 PPT 大纲
- S006 社交媒体

### 9.3 权限模型

- **RBAC 两级**：`admin`（`members.is_admin = true`）/ `user`（`is_admin = false`）
- **数据隔离**：草稿、模板等通过 `created_by` 字段归属用户，`is_owner_or_admin` 依赖校验
- **保护规则**：最后一个 admin 不可降级（`test_last_admin_cannot_be_demoted`）

### 9.4 领域术语表

| 术语 | 含义 |
|------|------|
| 神行库 | 项目代号（Shenxing） |
| Agent | 能独立完成某项任务的智能体（检索/竞品/生成/渠道/校验/配图） |
| Orchestrator | Agent 编排器，串联多 Agent 执行 |
| 草稿（Draft） | 交互式内容生成的中间态，四阶段状态机驱动 |
| 版本（Version） | 单次生成产出多个文案版本供用户选择 |
| 渠道适配（Adapt） | 将选定版本适配到多个目标渠道 |
| Mock 模式 | 未配置 API Key 时的降级模式（LLM / Embedding / Tavily 均有 Mock 兜底） |

---

## 10. AI 协作约定

### 后端开发约定

1. **新增 API**：先在 [models.py](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK/B2B_SXK/backend/app/models.py) 定义 Pydantic v2 模型（请求 DTO + 响应 DTO），再写 router 函数，最后在 [app/main.py](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK/B2B_SXK/backend/app/main.py) 注册 `include_router()`。
2. **数据库操作**：必须使用 `database.py` 的 `query()` / `query_one()` / `execute()` / `transaction()`，禁止直接创建 psycopg2 连接。
3. **鉴权**：需要登录的路由函数加 `current_user = Depends(get_current_user)`；需要管理员权限加 `Depends(require_admin)`；涉及归属校验用 `is_owner_or_admin`。
4. **草稿修改**：注意四阶段状态机（draft → editing → selected → adapted → done），`stage` 字段流转必须按序，`finalize` 已有 CAS 防并发。
5. **Agent 扩展**：新增 Agent 需继承 `BaseAgent`，实现 `_execute()` 方法（返回 status/message/output 三元组），并在 `Orchestrator.__init__()` 中注册。
6. **配置项**：新增配置在 [config.py](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK/B2B_SXK/backend/config.py) 集中添加，使用 `os.getenv()` 支持环境变量覆盖。
7. **LLM 调用**：通过 `llm_provider.get_provider()` 获取 Provider，不要直接 import httpx 调用 LLM API。
8. **降级思维**：所有外部 API（LLM / Embedding / Tavily）都应有 Mock 兜底，`_ENABLED` 标志控制开关。
9. **测试**：新增关键逻辑需在 [tests/test_regressions.py](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK/B2B_SXK/backend/tests/test_regressions.py) 补充 unittest（使用 mock，不依赖数据库）。

### 前端开发约定

10. **import 路径**：必须使用 `@/` 别名（如 `@/components/`、`@/utils/`），禁止相对路径穿越。
11. **组件命名**：Element Plus 组件由 unplugin-vue-components 自动注册，无需手动 import；Vue/Vue Router/Pinia API 由 unplugin-auto-import 自动导入。
12. **SCSS 变量**：`@/styles/variables.scss` 由 Vite additionalData 全局注入，无需在组件中手动 import。
13. **API 请求**：通过 `src/utils/` 中的 axios 封装发送请求，Token 自动注入。
14. **生产代码**：禁止 `console.log` / `debugger`（ESLint 生产环境为 error）。
15. **环境变量**：前端变量必须以 `VITE_` 为前缀。

### 通用约定

16. **不确定处先问**：不要臆造不存在的 API / 配置 / 文件路径。
17. **保持双 TRAE.md**：根目录 TRAE.md 覆盖全栈，`frontend/TRAE.md` 覆盖前端细节，修改时注意同步。

---

## 11. 待确认项

| 序号 | 待确认内容 | 当前假设 | 出处 |
|------|-----------|---------|------|
| 1 | Python 版本 | 假设 ≥ 3.13（使用了 `dict[str, Any]`、`str \| None` 语法） | `requirements.txt` 未声明 `requires-python` |
| 2 | 生产部署方式 | 无 Dockerfile，推测 nginx 反代 + uvicorn 直接部署 | 未检测到容器化配置 |
| 3 | 生产 `VITE_API_TARGET` | `.env.prod` 留空，注释提示由 CI / 网关注入 | `.env.prod` |
| 4 | Git 远程仓库 | 未检测到 `.git/config` | 本地仓库 |
| 5 | `main.py` 中 `reload=True` | 生产环境应关闭热重载 | [backend/main.py](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK/B2B_SXK/backend/main.py) 第 25 行 |
| 6 | CORS `allow_origins=["*"]` | 生产环境应限制为具体域名 | [app/main.py](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK/B2B_SXK/backend/app/main.py) |
| 7 | `JWT_SECRET` 默认值 | 仅供开发，生产必须通过环境变量覆盖（源码已有安全告警） | [config.py](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK/B2B_SXK/backend/config.py) 第 83-87 行 |

---

> **前端深度上下文**：如需前端详细架构（23 条已知陷阱、路由守卫、Mock 机制、Pinia store 设计等），请参阅 [frontend/TRAE.md](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK/B2B_SXK/frontend/TRAE.md)。
