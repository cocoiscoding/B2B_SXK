# 神行库 · 后端文件清单

> 本文档面向 Python 初学者，按目录层级列出每个后端文件的作用、核心概念与对应需求。
> 前端代码不在本文档分析范围内。

## 目录结构总览

```
shenxing/
├── main.py                      # 启动入口（uvicorn 加载 ASGI 应用）
├── config.py                    # 全局配置（数据库、LLM、向量维度等）
├── requirements.txt             # Python 依赖清单
├── BACKEND_FILES.md             # 本文档
├── database/
│   └── init_postgresql.sql      # PostgreSQL 建库建表 + 模拟数据脚本
└── app/
    ├── __init__.py              # 包标识（空文件）
    ├── main.py                  # FastAPI 应用创建、CORS、生命周期事件
    ├── database.py              # 数据库连接池 + query/transaction 工具函数
    ├── models.py                # Pydantic 数据模型（请求/响应结构）
    ├── vector_search.py         # 向量检索核心模块（语义搜索）
    ├── seed_data.py             # 启动时自动灌入样例数据
    ├── routers/                 # API 路由层
    │   ├── __init__.py          # 包标识（空文件）
    │   ├── products.py          # 产品知识库 CRUD + 语义搜索
    │   ├── scenarios.py         # 场景模板 CRUD
    │   ├── generate.py          # 内容生成入口（5 个 Agent 编排）
    │   └── history.py           # 历史记录管理 + 文件导出
    └── agents/                  # 多 Agent 协作引擎
        ├── __init__.py          # 包标识（空文件）
        ├── base.py              # Agent 基类 + 上下文对象
        ├── llm_provider.py      # LLM 双模式提供者（Mock / OpenAI 兼容）
        ├── retrieval_agent.py   # ① 产品信息检索 Agent
        ├── competitor_agent.py  # ② 竞品分析 Agent
        ├── generation_agent.py  # ③ 内容生成 Agent
        ├── channel_agent.py     # ④ 渠道适配 Agent
        ├── validation_agent.py  # ⑤ 内容校验 Agent
        └── orchestrator.py      # Agent 编排器（串行执行 5 个 Agent）
```

---

## 一、项目根目录

### `main.py` —— 启动入口

- **作用**：整个程序的启动脚本，使用 `uvicorn` ASGI 服务器加载 `app/main.py` 中的 FastAPI 实例。
- **核心概念**：
  - `uvicorn.run()`：启动异步 Web 服务器
  - `reload=True`：开发模式，代码改动后自动重启
- **执行命令**：`python main.py` → 访问 http://127.0.0.1:8000

### `config.py` —— 全局配置

- **作用**：集中管理所有配置项（数据库连接、LLM 接口、向量维度等），通过环境变量可覆盖默认值。
- **核心概念**：
  - `os.getenv("KEY", "default")`：读取环境变量，不存在时用默认值
  - 配置项包括：`DB_HOST/PORT/NAME/USER/PASSWORD`、`LLM_API_KEY/BASE_URL/MODEL`、`EMBEDDING_DIM`
- **设计意图**：把"会变的东西"（密码、API Key）与"代码逻辑"分离，方便部署到不同环境。

### `requirements.txt` —— 依赖清单

- **作用**：列出项目所需的第三方 Python 库及版本。
- **安装命令**：`pip install -r requirements.txt`
- **主要依赖**：`fastapi`（Web 框架）、`uvicorn`（ASGI 服务器）、`psycopg2`（PostgreSQL 驱动）、`pydantic`（数据验证）。

### `database/init_postgresql.sql` —— 数据库初始化脚本

- **作用**：首次部署时执行的 SQL 脚本，完成"建库 → 建表 → 加注释 → 插入样例数据"全流程。
- **内容**：
  - 创建 `shenxingdb` 数据库
  - 创建 `products`（产品表，含 `embedding JSONB` 向量列）、`scenarios`（场景表）、`history`（历史表）
  - 每个字段都有 `COMMENT ON COLUMN` 注释
  - 插入 3 个示例产品 + 6 个内置场景模板
- **执行方式**：`psql -U postgres -h 127.0.0.1 -f database\init_postgresql.sql`
- **Windows 注意**：执行前需设置 `$env:PGCLIENTENCODING="UTF8"` 避免编码错误。

---

## 二、`app/` —— 应用主目录

### `app/__init__.py` —— 包标识

- **作用**：空文件，告诉 Python 把 `app/` 目录当作一个"包"（package），可以通过 `from app.xxx import yyy` 导入。
- **Python 知识**：Python 3.3+ 的"命名空间包"机制下其实可省略，但保留它是为了兼容性和明确性。

### `app/main.py` —— FastAPI 应用创建

- **作用**：创建 FastAPI 应用实例，配置 CORS 跨域、注册路由、定义启动/关闭生命周期事件。
- **核心概念**：
  - `FastAPI(title=..., version=...)`：创建应用实例
  - `app.add_middleware(CORSMiddleware, ...)`：允许前端跨域访问
  - `@app.on_event("startup")`：启动时执行（初始化连接池、灌入种子数据）
  - `@app.on_event("shutdown")`：关闭时执行（释放连接池）
  - `app.include_router(...)`：把 routers 目录下的路由挂载到主应用
  - `GET /api/health`：健康检查端点，用于验证服务是否在线
- **对应需求**：F0 系统基础

### `app/database.py` —— 数据库连接与工具函数

- **作用**：封装 PostgreSQL 连接池（`ThreadedConnectionPool`）和三个核心工具函数，让其他文件不直接写 psycopg2 代码。
- **核心函数**：
  - `query(sql, params)`：执行 SELECT，返回字典列表（自动把行转为 dict）
  - `query_one(sql, params)`：执行 SELECT，返回单条字典或 None
  - `transaction()`：上下文管理器（`@contextmanager`），用于 INSERT/UPDATE/DELETE，自动提交/回滚
  - `_parse_json_fields(row, fields)`：把 PostgreSQL JSONB 字段从字符串还原为 Python dict/list
- **Python 知识点**：
  - `ThreadedConnectionPool`：线程安全的连接池，多请求并发时不阻塞
  - `RealDictCursor`：让查询结果返回字典而非元组
  - `psycopg2.extras.Json`：把 Python dict/list 包装为 PostgreSQL JSONB
  - `@contextmanager` 装饰器：让函数支持 `with transaction() as cur:` 语法
  - `%s` 占位符：PostgreSQL 参数化查询（注意不是 SQLite 的 `?`）
- **对应需求**：所有 F1~F4 的数据持久化基础

### `app/models.py` —— Pydantic 数据模型

- **作用**：定义所有 API 请求体和响应体的数据结构（Schema），FastAPI 会自动校验请求数据、生成 Swagger 文档。
- **核心模型**：
  - `Product` / `ProductCreate` / `ProductUpdate`：产品相关
  - `Scenario` / `ScenarioCreate`：场景模板
  - `GenerateRequest`：生成请求（产品ID、场景ID、渠道、版本数等）
  - `VersionItem`：单版本文案（标题、正文、标签）
  - `HistoryItem` / `HistoryUpdate`：历史记录
- **Python 知识点**：
  - `class XxxModel(BaseModel)`：继承 Pydantic 基类
  - `Field(..., description=...)`：字段定义，`...` 表示必填
  - 类型注解：`str | None`、`list[dict]`、`datetime`
  - `model_dump()`：把模型转为字典（Pydantic v2 方法，v1 是 `.dict()`）
  - 模型继承：`ProductCreate(Product)` 复用父类字段
- **设计意图**：类型安全 + 自动文档，避免手写参数校验代码。
- **重要教训**：`created_at` 字段用纯 `datetime` 而非 `datetime | str`，否则 Pydantic v2 会优先按字符串验证导致 500 错误。

### `app/vector_search.py` —— 向量检索核心模块

- **作用**：实现产品语义搜索的核心算法，让"适合金融行业的安全防护产品"这样的自然语言查询能匹配到相关产品。
- **核心函数**：
  - `cosine_similarity(a, b)`：计算两个向量的余弦相似度（越接近 1 越相似）
  - `build_product_text(product)`：把产品的名称/描述/功能/卖点等结构化信息拼接成一段文本
  - `embed_product(product)`：调用 LLM Provider 把产品文本转为向量
  - `search_products_by_vector(query_vector, top_k, threshold)`：在数据库中找最相似的产品
  - `search_products_by_text(query_text, top_k, threshold)`：文本 → 向量 → 检索
- **核心概念**：
  - **Embedding 向量**：把文本转为一串数字（如 128 维数组），语义相近的文本向量也相近
  - **余弦相似度**：衡量两个向量方向的夹角，忽略长度，值域 [-1, 1]
  - **语义搜索 vs 关键词搜索**：关键词搜索只匹配字面，语义搜索能理解"金融行业"和"银行/证券/保险"的关联
- **对应需求**：F1-3 知识库检索（增强版）

### `app/seed_data.py` —— 种子数据初始化

- **作用**：应用启动时检查数据库是否为空，若空则插入预置的 3 个示例产品 + 6 个场景模板；同时检测 `embedding IS NULL` 的产品并自动补向量。
- **核心函数**：`seed_if_empty()`
- **两种触发场景**：
  1. 数据库完全为空 → 插入完整样例数据（含 embedding）
  2. 数据库已有产品但缺 embedding（如用 SQL 脚本初始化的情况）→ 仅补向量
- **Python 知识点**：列表推导式、字典推导式、`datetime.now()`、`psycopg2.extras.Json`
- **对应需求**：F1-4 初始数据

---

## 三、`app/routers/` —— API 路由层

### `app/routers/__init__.py` —— 包标识

- **作用**：空文件，标记 `routers/` 为 Python 包。

### `app/routers/products.py` —— 产品知识库 CRUD + 语义搜索

- **作用**：处理产品知识库的所有 HTTP 请求，包括增删改查和语义搜索。
- **API 端点**：
  - `GET /api/products`：产品列表（支持关键词搜索）
  - `POST /api/products`：新建产品（自动生成 embedding 向量）
  - `GET /api/products/{id}`：产品详情
  - `PUT /api/products/{id}`：更新产品（重新生成 embedding）
  - `DELETE /api/products/{id}`：删除产品
  - `POST /api/products/search`：语义搜索（向量检索）
  - `POST /api/products/reindex`：重建所有产品的向量
- **Python 知识点**：
  - `@router.get("/path")` 装饰器：定义路由
  - `response_model=list[Product]`：自动序列化响应
  - `HTTPException(404, "...")`：抛出 HTTP 错误
  - `Json([...])`：把 Python 列表存为 PostgreSQL JSONB
- **对应需求**：F1-1 信息录入、F1-2 信息管理、F1-3 知识库检索

### `app/routers/scenarios.py` —— 场景模板 CRUD

- **作用**：管理营销场景模板（如官网 Banner、产品介绍、竞品对比等）。
- **API 端点**：
  - `GET /api/scenarios`：场景列表
  - `POST /api/scenarios`：新建自定义场景
  - `GET /api/scenarios/{id}`：场景详情
  - `PUT /api/scenarios/{id}`：更新场景
  - `DELETE /api/scenarios/{id}`：删除场景（内置场景受保护不可删）
- **设计特点**：内置场景（S001~S006）通过 ID 前缀判断，禁止删除，保证系统基础功能可用。
- **对应需求**：F2-1 ~ F2-3 场景模板管理

### `app/routers/generate.py` —— 内容生成入口

- **作用**：接收用户的生成请求，调用 `Orchestrator` 编排器执行 5 个 Agent，返回最终的多版本文案 + 执行链路 + 校验报告。
- **API 端点**：
  - `POST /api/generate`：生成营销内容
- **请求参数**：产品ID、场景ID、渠道、风格、版本数、用户补充参数等
- **响应结构**：
  - `versions`：多版本文案（适配后）
  - `agent_trace`：每个 Agent 的执行状态、消息、耗时
  - `issues`：校验发现的问题列表
- **核心流程**：请求 → 构造 `GenerateRequest` → `Orchestrator.run(ctx)` → 保存到 history 表 → 返回结果
- **对应需求**：F3-6 编排器、F4-1 历史保存

### `app/routers/history.py` —— 历史记录管理 + 文件导出

- **作用**：管理生成历史，支持查看、编辑、删除、导出为 Markdown/TXT 文件。
- **API 端点**：
  - `GET /api/history`：历史列表（按时间倒序）
  - `GET /api/history/{id}`：历史详情
  - `PUT /api/history/{id}`：编辑内容版本
  - `DELETE /api/history/{id}`：删除历史
  - `GET /api/history/{id}/export?format=markdown|txt`：导出文件
- **技术细节**：
  - 中文文件名需要 RFC 5987 编码（`filename*=UTF-8''...`），否则浏览器下载乱码
  - `urllib.parse.quote`：URL 编码中文文件名
  - `Response(content=..., media_type=..., headers=...)`：自定义 HTTP 响应
- **对应需求**：F4-1 ~ F4-5 历史管理

---

## 四、`app/agents/` —— 多 Agent 协作引擎

### `app/agents/__init__.py` —— 包标识

- **作用**：空文件，标记 `agents/` 为 Python 包。

### `app/agents/base.py` —— Agent 基类与上下文

- **作用**：定义所有 Agent 的公共基类 `BaseAgent` 和共享上下文 `AgentContext`，是整个多 Agent 系统的基石。
- **核心组件**：
  - `AgentContext`（`@dataclass`）：在 5 个 Agent 之间传递数据的"容器"，包含产品ID、场景、渠道、检索结果、初稿、最终版本、执行链路等
  - `BaseAgent`：抽象基类，定义 `run(ctx)` 模板方法，子类只需实现 `_execute(ctx)`
  - `AgentTrace`：记录每个 Agent 的执行状态（success/warning/error）、消息、耗时
- **设计模式**：
  - **模板方法模式**：`run()` 是模板（固定流程：记录开始 → 执行 → 记录结束），`_execute()` 是可变部分
  - **上下文对象模式**：用 `AgentContext` 在多个对象间传递数据，避免方法参数爆炸
- **Python 知识点**：
  - `@dataclass`：自动生成 `__init__`、`__repr__` 等方法
  - `ABCMeta` + `@abstractmethod`：定义抽象类
  - `tuple[str, str, ...]`：返回值类型注解
  - `time.time()`：计算耗时
- **对应需求**：F3 多 Agent 系统基础

### `app/agents/llm_provider.py` —— LLM 双模式提供者

- **作用**：封装大语言模型（LLM）的调用，支持两种模式无缝切换——不配 API Key 时用 Mock 模板引擎（离线可用），配置后用真实大模型。
- **核心类**：
  - `LLMProvider`（抽象基类）：定义 `chat()` 和 `embed()` 接口
  - `MockLLMProvider`：离线模式
    - `chat()`：返回固定占位文本
    - `embed()`：基于 MD5 哈希的 2-gram 伪向量 + L2 归一化（让无 API Key 时语义搜索也能跑）
  - `OpenAICompatibleProvider`：真实 LLM 模式
    - `chat()`：调用 `/chat/completions` 端点
    - `embed()`：调用 `/embeddings` 端点
  - `get_llm_provider()`：工厂函数，根据环境变量自动选择
- **Python 知识点**：
  - `urllib.request`：标准库 HTTP 请求（不依赖 requests）
  - `json.loads()`：解析 JSON 响应
  - `hashlib.md5()`：生成哈希
  - `numpy`（可选）：向量运算
- **对应需求**：F3 系统的 LLM 接入层

### `app/agents/retrieval_agent.py` —— ① 产品信息检索 Agent

- **作用**：根据用户选择的场景和参数，从知识库中检索相关的产品信息。这是多 Agent 链路的**第 1 个** Agent，也是质量基石。
- **三段式流程**（重写后引入 LLM 推理 + 向量检索）：
  1. **LLM 推理**：让 LLM 根据场景名和用户参数生成搜索关键词 + 判断需要哪些字段
  2. **向量检索**：用关键词的 embedding 在数据库中找最相似的产品（余弦相似度）
  3. **智能字段选取**：根据场景类型选择相关字段写入 `ctx.retrieved_info`
- **回退策略**：LLM 不可用时用 `_default_fields()` 按场景名关键词选字段
- **对应需求**：F3-1 产品信息检索 Agent

### `app/agents/competitor_agent.py` —— ② 竞品分析 Agent

- **作用**：在竞品对比场景下，组织我方产品与竞品的对比信息，输出结构化差异框架供生成 Agent 使用。
- **设计特点**：
  - 只在竞品场景激活（场景名包含"竞品"）
  - 其他场景直接跳过，返回空字典，不影响流程
- **输出结构**：`our_product`、`competitor`、`focus`、`our_strengths`、`our_features`、`competitor_known`、`competitor_estimated`
- **Python 知识点**：列表推导式 `[f["name"] for f in our_feats]`、`in` 成员判断、`or` 短路求值
- **对应需求**：F3-2 竞品分析 Agent

### `app/agents/generation_agent.py` —— ③ 内容生成 Agent（核心）

- **作用**：基于检索到的产品信息 + 场景模板生成多版本营销文案。这是整个系统的**核心 Agent**。
- **双模式**：
  - **LLM 模式**：为每个风格变体调用一次 LLM，`temperature` 随版本号递增让后面的版本更有创意
  - **Mock 模式**：内置 6 种场景模板函数
    - `_gen_banner`：官网 Banner（主标题+副标题+CTA）
    - `_gen_intro`：产品介绍文章
    - `_gen_competitor`：竞品对比报告（含 Markdown 表格）
    - `_gen_case`：客户案例（STAR 结构：背景-任务-方案-成果）
    - `_gen_ppt`：PPT 大纲（每页标题+要点）
    - `_gen_social`：社交媒体帖子（4 种语气）
- **风格变体**：`STYLE_VARIANTS` 定义"专业严谨""激情澎湃""亲和走心"3 种语气，通过 prefix/suffix 修饰
- **Python 知识点**：
  - `enumerate(list, 1)`：带起始索引的遍历
  - `f-string` 格式化字符串
  - `json.dumps(ensure_ascii=False)`：保留中文
  - `try/except` 异常处理
  - 列表推导式 + 字典推导式
- **对应需求**：F3-3 内容生成 Agent

### `app/agents/channel_agent.py` —— ④ 渠道适配 Agent

- **作用**：将生成的内容按目标渠道调整风格与排版，让同一份文案在不同平台都有最佳呈现。
- **5 种渠道适配**：
  - **官网**：保持 Markdown，专业正式
  - **微信公众号**：短段落 + emoji 点缀（✨ 标题、👉 列表）
  - **LinkedIn**：精简 + 英文话题标签 `#ProductMarketing #Tech`
  - **邮件营销**：主题 + 要点 + CTA（立即申请试用）
  - **内部培训PPT**：bullet 要点化（■ 标题、· 内容）
- **设计特点**：`CHANNEL_STYLES` 配置表驱动，新增渠道只需加一行配置
- **Python 知识点**：`@staticmethod` 静态方法、`set()` 去重、字符串 `split/join/strip`
- **对应需求**：F3-4 渠道适配 Agent

### `app/agents/validation_agent.py` —— ⑤ 内容校验 Agent

- **作用**：检查生成内容的参数一致性与完整性，是质量把关的最后一道防线。
- **4 项校验**：
  1. **产品名称一致性**：内容中是否出现正确的产品名
  2. **定价一致性**：用正则提取价格，检查是否与知识库一致
  3. **敏感词检查**：过滤"第一""最""国家级"等绝对化用词（违反《广告法》）
  4. **卖点覆盖**：内容是否包含至少 1 个核心卖点
- **输出**：`{"issues": [...], "validated": bool}`，状态为 `success`（无问题）或 `warning`（有问题但不阻断）
- **Python 知识点**：
  - `re.findall(pattern, text)`：正则提取
  - `all(...)` / `any(...)`：全量/存在性判断
  - 列表推导式 + `in` 关键字
- **对应需求**：F3-5 内容校验 Agent

### `app/agents/orchestrator.py` —— Agent 编排器

- **作用**：把 5 个 Agent 串行编排起来，按顺序执行并收集每个 Agent 的执行轨迹。是整个多 Agent 系统的"指挥官"。
- **7 步编排流程**：
  1. 加载产品数据（从数据库）
  2. 加载场景模板
  3. 初始化 `AgentContext`
  4. 实例化 5 个 Agent（注入 LLM Provider）
  5. 顺序执行：检索 → 竞品分析 → 生成 → 渠道适配 → 校验
  6. 收集每个 Agent 的执行轨迹 `agent_trace`
  7. 返回最终结果（多版本 + 链路 + 校验报告）
- **设计模式**：
  - **责任链模式**：5 个 Agent 像流水线一样依次处理
  - **单例模式**：`get_orchestrator()` 全局只创建一个实例，避免重复初始化
- **Python 知识点**：
  - 类变量 vs 实例变量
  - `None` 作为类变量的默认值实现单例
  - `for agent in [agent1, agent2, ...]: agent.run(ctx)`
  - `trace.append(...)` 收集执行记录
- **对应需求**：F3-6 Agent 编排器

---

## 五、文件间调用关系（数据流）

```
用户请求
   ↓
main.py (启动) → app/main.py (FastAPI)
   ↓
routers/generate.py (POST /api/generate)
   ↓
agents/orchestrator.py (编排)
   ↓
   ├─→ retrieval_agent.py   ← vector_search.py ← llm_provider.py
   ├─→ competitor_agent.py
   ├─→ generation_agent.py  ← llm_provider.py
   ├─→ channel_agent.py
   └─→ validation_agent.py
   ↓
database.py (保存到 history 表)
   ↓
返回 JSON 响应
```

---

## 六、Python 知识点速查（针对初学者）

| 概念 | 出现位置 | 简要说明 |
|------|---------|---------|
| `@dataclass` | `base.py` | 自动生成 `__init__` 等方法，减少样板代码 |
| `@contextmanager` | `database.py` | 让函数支持 `with` 语法，自动管理资源 |
| 装饰器 `@router.get(...)` | `routers/*.py` | FastAPI 路由定义 |
| 类型注解 `str \| None` | `models.py`、`base.py` | Python 3.10+ 联合类型语法 |
| 列表推导式 `[x for x in ...]` | 多处 | 简洁地生成列表 |
| 字典推导式 `{k: v for ...}` | 多处 | 简洁地生成字典 |
| `f-string` `f"Hello {name}"` | 多处 | 字符串格式化 |
| `enumerate(list, 1)` | `generation_agent.py` | 带索引遍历 |
| `try/except` | `generation_agent.py`、`database.py` | 异常处理 |
| `@staticmethod` | `channel_agent.py` | 静态方法，不需要 self |
| `@abstractmethod` | `base.py` | 抽象方法，子类必须实现 |
| `model_dump()` | `models.py` | Pydantic v2 模型转字典 |
| `os.getenv("KEY", "default")` | `config.py` | 读取环境变量 |
| `ThreadedConnectionPool` | `database.py` | 线程安全的数据库连接池 |
| `Json([...])` | `database.py`、`routers/*.py` | psycopg2 的 JSONB 包装器 |

---

## 七、需求对应关系总表

| 需求编号 | 功能描述 | 实现文件 |
|---------|---------|---------|
| F1-1 | 产品信息录入 | `routers/products.py` (POST) |
| F1-2 | 产品信息管理 | `routers/products.py` (GET/PUT/DELETE) |
| F1-3 | 知识库检索 | `routers/products.py` (search) + `vector_search.py` + `retrieval_agent.py` |
| F1-4 | 初始数据 | `seed_data.py` + `database/init_postgresql.sql` |
| F2-1~F2-3 | 场景模板管理 | `routers/scenarios.py` |
| F3-1 | 产品信息检索 Agent | `agents/retrieval_agent.py` |
| F3-2 | 竞品分析 Agent | `agents/competitor_agent.py` |
| F3-3 | 内容生成 Agent | `agents/generation_agent.py` |
| F3-4 | 渠道适配 Agent | `agents/channel_agent.py` |
| F3-5 | 内容校验 Agent | `agents/validation_agent.py` |
| F3-6 | Agent 编排器 | `agents/orchestrator.py` + `routers/generate.py` |
| F4-1~F4-5 | 历史记录管理 | `routers/history.py` |

---

## 八、学习建议

如果你是 Python 初学者，建议按以下顺序阅读代码：

1. **先读 `config.py` 和 `main.py`** —— 了解配置和启动流程
2. **再读 `app/models.py`** —— 理解数据结构（最直观）
3. **接着读 `app/database.py`** —— 理解数据库交互模式
4. **然后读 `app/agents/base.py`** —— 理解多 Agent 系统的基石
5. **之后读各个 Agent**（按 ① → ⑤ 顺序）—— 理解业务逻辑
6. **最后读 `routers/` 下的文件** —— 理解 HTTP API 层

每个文件顶部都有详细的模块级 docstring 说明用途和核心概念，关键代码行都有中文注释解释 Python 语法和设计思路。
