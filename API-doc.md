# 后端接口文档：产品知识库 & 模板管理

> **Base URL**: `http://127.0.0.1:8000`
> **鉴权方式**: 除健康检查外，所有接口均需在请求头携带 `Authorization: Bearer <access_token>`
> **Content-Type**: `application/json`（文件上传接口为 `multipart/form-data`）

---

## 一、产品知识库接口（10 个）

### 1.1 查询产品列表

| 项目 | 值 |
|------|-----|
| **URL** | `GET /api/products` |
| **鉴权** | ✅ 需登录 |

**Query 参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| keyword | string | 否 | 按名称/类别/描述模糊检索 |
| member | string | 否 | 按创建人 ID 筛选 |

两个参数可叠加，同时传时取交集。

**请求示例**：
```
GET /api/products?keyword=数据&member=zhang
```

**响应**：`200 OK` → `Product[]`

``json
[
  {
    "id": "P001",
    "name": "神行数据分析平台",
    "category": ["数据分析", "企业级"],
    "description": "一站式数据分析平台...",
    "features": [
      { "name": "可视化报表", "description": "拖拽式报表设计" }
    ],
    "target_customers": ["金融", "制造"],
    "pricing": "按需定价",
    "selling_points": ["零代码搭建", "实时计算"],
    "images": [
      { "url": "/uploads/products/P001/abc123.jpg", "name": "截图1.jpg", "size": 102400 }
    ],
    "documents": [
      { "url": "/uploads/products/P001/def456.pdf", "name": "白皮书.pdf", "size": 2048000, "type": "pdf" }
    ],
    "created_by": "zhang",
    "created_at": "2025-01-01T00:00:00",
    "updated_at": "2025-01-01T00:00:00"
  }
]
``

---

### 1.2 查询单个产品详情

| 项目 | 值 |
|------|-----|
| **URL** | `GET /api/products/{product_id}` |
| **鉴权** | ✅ 需登录 |

**Path 参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| product_id | string | 是 | 产品 ID，如 `P001` |

**响应**：`200 OK` → `Product`（结构同上单个对象）
**错误**：`404` → `{"detail": "产品 P001 不存在"}`

---

### 1.3 创建产品

| 项目 | 值 |
|------|-----|
| **URL** | `POST /api/products` |
| **鉴权** | ✅ 需登录 |

**请求体**：`ProductCreate`

``json
{
  "id": "PNEW01",
  "name": "新产品名称",
  "category": ["分类1", "分类2"],
  "description": "产品详细描述",
  "features": [
    { "name": "功能名称", "description": "功能描述" }
  ],
  "target_customers": ["目标行业1", "目标行业2"],
  "pricing": "定价信息",
  "selling_points": ["卖点1", "卖点2"],
  "images": [],
  "documents": []
}
``

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| id | string | 否 | 自动生成 `P` + 6位随机码 | 产品 ID |
| name | string | ✅ 是 | — | 产品名称 |
| category | string[] | 否 | `[]` | 分类列表 |
| description | string | 否 | `""` | 产品描述 |
| features | Feature[] | 否 | `[]` | 功能列表，每项 `{name, description}` |
| target_customers | string[] | 否 | `[]` | 目标客户行业 |
| pricing | string | 否 | `""` | 定价信息 |
| selling_points | string[] | 否 | `[]` | 核心卖点 |
| images | ImageItem[] | 否 | `[]` | 图片列表，每项 `{url, name, size}` |
| documents | DocumentItem[] | 否 | `[]` | 文档列表，每项 `{url, name, size, type}` |

> `created_by` 由后端从 JWT Token 中提取，前端无需（也不应）传入。

**响应**：`200 OK` → `Product`（含 `id`、`created_by`、`created_at`、`updated_at`）

---

### 1.4 更新产品

| 项目 | 值 |
|------|-----|
| **URL** | `PUT /api/products/{product_id}` |
| **鉴权** | ✅ 需登录，且为创建者或管理员 |

**Path 参数**：`product_id`（必填）

**请求体**：`ProductCreate`（结构同 1.3，所有字段全量提交）

**响应**：`200 OK` → `Product`
**错误**：`404` 产品不存在 / `403` 无权修改他人产品

> 更新时会自动重新生成向量嵌入。`created_by` 不可改。

---

### 1.5 删除产品

| 项目 | 值 |
|------|-----|
| **URL** | `DELETE /api/products/{product_id}` |
| **鉴权** | ✅ 需登录，且为创建者或管理员 |

**Path 参数**：`product_id`（必填）

**响应**：`200 OK`
``json
{ "message": "产品 P001 已删除，清理了 2 个关联文件" }
``

**错误**：`404` / `403`

> 删除时会自动清理关联的上传文件（图片+文档）。

---

### 1.6 语义搜索（向量检索）

| 项目 | 值 |
|------|-----|
| **URL** | `POST /api/products/search` |
| **鉴权** | ✅ 需登录 |

**请求体**：`SemanticSearchRequest`

``json
{
  "query": "适合金融行业的数据分析产品",
  "top_k": 5,
  "threshold": 0.0
}
``

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| query | string | ✅ 是 | — | 自然语言查询 |
| top_k | int | 否 | 5 | 返回数量（1-20） |
| threshold | float | 否 | 0.0 | 相似度阈值（0.0-1.0） |

**响应**：`200 OK` → `SemanticSearchResult[]`

``json
[
  {
    "product_id": "P001",
    "product_name": "神行数据分析平台",
    "category": ["数据分析", "企业级"],
    "score": 0.8532,
    "description": "一站式数据分析平台..."
  }
]
``

> 与 `GET /api/products?keyword=` 的区别：keyword 是字符级模糊匹配（LIKE），语义搜索理解"意思"，能找到关键词不完全匹配但语义相近的产品。

---

### 1.7 重建向量索引

| 项目 | 值 |
|------|-----|
| **URL** | `POST /api/products/reindex` |
| **鉴权** | ✅ 仅管理员 |

**请求体**：无

**响应**：`200 OK`
``json
{ "message": "已重建 3 个产品的向量嵌入", "count": 3 }
``

---

### 1.8 上传 Word 手册解析

| 项目 | 值 |
|------|-----|
| **URL** | `POST /api/products/import-docx` |
| **鉴权** | ✅ 需登录 |
| **Content-Type** | `multipart/form-data` |

**请求体**：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| file | File | ✅ 是 | `.docx` 文件 |

**响应**：`200 OK` → `ImportDocxResponse`

``json
{
  "product": {
    "id": null,
    "name": "解析出的产品名",
    "category": ["分类1"],
    "description": "解析出的描述",
    "features": [{ "name": "功能1", "description": "描述" }],
    "target_customers": ["行业1"],
    "pricing": "",
    "selling_points": ["卖点1"],
    "images": [],
    "documents": []
  },
  "char_count": 3580,
  "extractor": "heuristic",
  "note": "部分字段未识别到，请手动补充"
}
``

| 字段 | 类型 | 说明 |
|------|------|------|
| product | ProductCreate | 解析出的产品草稿（**不入库**，需前端让用户确认后再调创建接口） |
| char_count | int | 文档纯文本字符数 |
| extractor | string | 提取器：`llm`（大模型）/ `heuristic`（启发式规则） |
| note | string | 解析说明 |

**错误**：`400` 非 .docx 文件 / 文件为空 / 解析失败

---

### 1.9 上传产品图片

| 项目 | 值 |
|------|-----|
| **URL** | `POST /api/products/{product_id}/upload-image` |
| **鉴权** | ✅ 需登录，且为创建者或管理员 |
| **Content-Type** | `multipart/form-data` |

**Path 参数**：`product_id`

**请求体**：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| file | File | ✅ 是 | 图片文件（JPG/PNG/GIF/WebP） |

**限制**：单张最大 5MB，每产品最多 10 张

**响应**：`200 OK`
``json
{
  "url": "/uploads/products/P001/abc12345.jpg",
  "name": "截图.jpg",
  "size": 102400
}
``

**错误**：`400` 格式不支持 / 超过大小限制 / 数量达上限 / `404` / `403`

---

### 1.10 上传产品文档

| 项目 | 值 |
|------|-----|
| **URL** | `POST /api/products/{product_id}/upload-document` |
| **鉴权** | ✅ 需登录，且为创建者或管理员 |
| **Content-Type** | `multipart/form-data` |

**Path 参数**：`product_id`

**请求体**：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| file | File | ✅ 是 | 文档文件（.pdf/.doc/.docx/.xls/.xlsx/.ppt/.pptx/.txt/.zip） |

**限制**：单个最大 50MB，每产品最多 5 个

**响应**：`200 OK`
``json
{
  "url": "/uploads/products/P001/def45678.pdf",
  "name": "白皮书.pdf",
  "size": 2048000,
  "type": "pdf"
}
``

**错误**：`400` 格式不支持 / 超过大小限制 / 数量达上限 / `404` / `403`

---

## 二、场景管理接口（5 个）

> 模板挂载在场景之下，前端"模板管理"页面需要先获取场景列表。

### 2.1 查询所有场景

| 项目 | 值 |
|------|-----|
| **URL** | `GET /api/scenarios` |
| **鉴权** | ✅ 需登录 |

**响应**：`200 OK` → `Scenario[]`

``json
[
  {
    "id": "S001",
    "name": "官网文案",
    "description": "官网产品介绍页面文案",
    "parameters": [
      { "name": "audience", "description": "目标受众" },
      { "name": "tone", "description": "语气风格" }
    ],
    "created_at": "2025-01-01T00:00:00"
  }
]
``

---

### 2.2 查询单个场景

| 项目 | 值 |
|------|-----|
| **URL** | `GET /api/scenarios/{scenario_id}` |
| **鉴权** | ✅ 需登录 |

**响应**：`200 OK` → `Scenario`（结构同上单个对象）
**错误**：`404`

---

### 2.3 创建场景

| 项目 | 值 |
|------|-----|
| **URL** | `POST /api/scenarios` |
| **鉴权** | ✅ 需登录 |

**请求体**：`ScenarioCreate`

``json
{
  "id": "SNEW01",
  "name": "新场景",
  "description": "场景描述",
  "parameters": [
    { "name": "param1", "description": "参数说明" }
  ]
}
``

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| id | string | 否 | 自动生成 `S` + 6位随机码 | 场景 ID |
| name | string | ✅ 是 | — | 场景名称 |
| description | string | 否 | `""` | 场景描述 |
| parameters | ScenarioParam[] | 否 | `[]` | 参数列表，每项 `{name, description}` |

**响应**：`200 OK` → `Scenario`

---

### 2.4 更新场景

| 项目 | 值 |
|------|-----|
| **URL** | `PUT /api/scenarios/{scenario_id}` |
| **鉴权** | ✅ 需登录 |

**请求体**：`ScenarioCreate`（结构同 2.3，全量提交）

**响应**：`200 OK` → `Scenario`
**错误**：`404`

---

### 2.5 删除场景

| 项目 | 值 |
|------|-----|
| **URL** | `DELETE /api/scenarios/{scenario_id}` |
| **鉴权** | ✅ 需登录 |

**响应**：`200 OK`
``json
{ "message": "场景 S001 已删除" }
``

> 关联的模板会级联删除。

---

## 三、模板管理接口（6 个）

### 3.1 查询所有模板（批量加载）

| 项目 | 值 |
|------|-----|
| **URL** | `GET /api/templates/all` |
| **鉴权** | ✅ 需登录 |

**响应**：`200 OK` → `Template[]`

``json
[
  {
    "id": "T001",
    "scenario_id": "S001",
    "name": "官网产品介绍-标准版",
    "tag": "标准",
    "description": "适用于官网产品介绍页的标准模板",
    "prompt": "你是一位专业的产品文案撰写师...",
    "constraints": {
      "title_max_chars": 30,
      "body_chars": [500, 1500],
      "must_include_params": ["audience"],
      "min_selling_points": 3
    },
    "structure": "钩子→痛点→方案→功能→CTA",
    "examples": [
      { "title": "示例标题", "body": "示例正文..." }
    ],
    "differentiation_dims": ["价格", "限时", "赠品"],
    "applicable_channels": ["官网", "微信公众号"],
    "tags": ["标准", "长文案", "官网"],
    "created_at": "2025-01-01T00:00:00"
  }
]
``

> 前端初始化时调用此接口一次性加载全部模板，避免按场景逐个请求。

---

### 3.2 查询场景下的模板列表

| 项目 | 值 |
|------|-----|
| **URL** | `GET /api/scenarios/{scenario_id}/templates` |
| **鉴权** | ✅ 需登录 |

**Path 参数**：`scenario_id`

**响应**：`200 OK` → `Template[]`
**错误**：`404` 场景不存在

---

### 3.3 查询单个模板详情

| 项目 | 值 |
|------|-----|
| **URL** | `GET /api/scenarios/{scenario_id}/templates/{template_id}` |
| **鉴权** | ✅ 需登录 |

**响应**：`200 OK` → `Template`
**错误**：`404`

---

### 3.4 创建模板

| 项目 | 值 |
|------|-----|
| **URL** | `POST /api/scenarios/{scenario_id}/templates` |
| **鉴权** | ✅ 需登录 |

**Path 参数**：`scenario_id`

**请求体**：`TemplateCreate`

``json
{
  "id": "TNEW01",
  "name": "新模板名称",
  "tag": "标准",
  "description": "模板描述",
  "prompt": "你是一位专业的产品文案撰写师...",
  "constraints": {
    "title_max_chars": 30,
    "body_chars": [500, 1500],
    "must_include_params": ["audience"],
    "min_selling_points": 3
  },
  "structure": "钩子→痛点→方案→功能→CTA",
  "examples": [
    { "title": "示例标题", "body": "示例正文..." }
  ],
  "differentiation_dims": ["价格", "限时"],
  "applicable_channels": ["官网"],
  "tags": ["标准", "官网"]
}
``

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| id | string | 否 | 自动生成 `T` + 6位随机码 | 模板 ID |
| name | string | ✅ 是 | — | 模板名称 |
| tag | string | 否 | `""` | 标签（单个） |
| description | string | 否 | `""` | 模板描述 |
| prompt | string | 否 | `""` | 提示词/产出格式 |
| constraints | object | 否 | `{}` | 结构化硬约束 |
| structure | string | 否 | `""` | 产出骨架 |
| examples | object[] | 否 | `[]` | 参考范例（few-shot） |
| differentiation_dims | string[] | 否 | `[]` | 多版本差异化维度 |
| applicable_channels | string[] | 否 | `[]` | 适用渠道列表 |
| tags | string[] | 否 | `[]` | 多维标签 |

**constraints 常用字段**：

| 字段 | 类型 | 说明 |
|------|------|------|
| title_max_chars | int | 标题最大字符数 |
| body_chars | [int, int] | 正文字符数范围 [min, max] |
| must_include_params | string[] | 必须包含的参数名 |
| min_selling_points | int | 最少卖点数量 |

**响应**：`200 OK` → `Template`
**错误**：`404` 场景不存在

---

### 3.5 更新模板

| 项目 | 值 |
|------|-----|
| **URL** | `PUT /api/scenarios/{scenario_id}/templates/{template_id}` |
| **鉴权** | ✅ 需登录 |

**Path 参数**：`scenario_id`、`template_id`

**请求体**：`TemplateCreate`（结构同 3.4，全量提交）

**响应**：`200 OK` → `Template`
**错误**：`404`

---

### 3.6 删除模板

| 项目 | 值 |
|------|-----|
| **URL** | `DELETE /api/scenarios/{scenario_id}/templates/{template_id}` |
| **鉴权** | ✅ 需登录 |

**Path 参数**：`scenario_id`、`template_id`

**响应**：`200 OK`
``json
{ "message": "模板 T001 已删除" }
``

**错误**：`404`

---

## 四、通用错误响应格式

所有接口在出错时返回统一格式：

``json
{ "detail": "错误描述信息" }
``

| HTTP 状态码 | 含义 |
|-------------|------|
| 400 | 请求参数错误 / 文件格式不支持 / 解析失败 |
| 401 | 未登录（Token 缺失或过期） |
| 403 | 无权限（非创建者/非管理员） |
| 404 | 资源不存在 |
| 422 | 请求体校验失败（Pydantic 自动返回） |

---

## 五、前端调用关系总结

| 页面 | 操作 | 调用的接口 |
|------|------|-----------|
| **产品知识库** | 加载产品列表 | `GET /api/products` |
| | 按创建人筛选 | `GET /api/products?member=xxx` |
| | 关键词搜索 | `GET /api/products?keyword=xxx` |
| | 新建产品 | `POST /api/products` |
| | 编辑产品 | `PUT /api/products/{id}` |
| | 删除产品 | `DELETE /api/products/{id}` |
| | 上传图片 | `POST /api/products/{id}/upload-image` |
| | 上传文档 | `POST /api/products/{id}/upload-document` |
| | 导入 Word 手册 | `POST /api/products/import-docx` |
| **模板管理** | 加载全部模板 | `GET /api/templates/all` |
| | 加载场景列表 | `GET /api/scenarios` |
| | 新建场景 | `POST /api/scenarios` |
| | 编辑场景 | `PUT /api/scenarios/{id}` |
| | 删除场景 | `DELETE /api/scenarios/{id}` |
| | 新建模板 | `POST /api/scenarios/{sid}/templates` |
| | 编辑模板 | `PUT /api/scenarios/{sid}/templates/{tid}` |
| | 删除模板 | `DELETE /api/scenarios/{sid}/templates/{tid}` |

> 📌 `POST /api/products/search` 和 `POST /api/products/reindex` 是后端已实现但前端未调用的接口，供后续扩展使用。
﻿
---

## 六、用户鉴权接口（6 个）

### 6.1 注册

| 项目 | 值 |
|------|-----|
| **URL** | ``POST /api/auth/register`` |
| **鉴权** | ❌ 无需登录 |

**请求体**：``RegisterRequest``

```json
{
  "username": "newuser",
  "password": "123456",
  "name": "新用户",
  "email": "user@example.com"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| username | string | ✅ 是 | 登录用户名（3-50 位） |
| password | string | ✅ 是 | 密码（至少 6 位） |
| name | string | ✅ 是 | 昵称（1-50 位） |
| email | string | 否 | 邮箱（默认空字符串） |

**响应**：``200 OK`` → ``TokenResponse``

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "user": {
    "id": "U1A2B3",
    "name": "新用户",
    "color": "#409eff",
    "username": "newuser",
    "email": "user@example.com",
    "is_admin": false,
    "created_at": "2025-01-01T00:00:00"
  }
}
```

> 注册成功后直接返回双令牌，无需再调登录接口。

**错误**：``409`` 用户名已被占用

---

### 6.2 登录

| 项目 | 值 |
|------|-----|
| **URL** | ``POST /api/auth/login`` |
| **鉴权** | ❌ 无需登录 |

**请求体**：``LoginRequest``

```json
{
  "username": "zhang",
  "password": "123456"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| username | string | ✅ 是 | 登录用户名 |
| password | string | ✅ 是 | 密码 |

**响应**：``200 OK`` → ``TokenResponse``（结构同 6.1）

**错误**：``401`` 用户名或密码错误

> 用户名不存在和密码错误返回相同提示，防止账号枚举攻击。

---

### 6.3 刷新令牌

| 项目 | 值 |
|------|-----|
| **URL** | ``POST /api/auth/refresh`` |
| **鉴权** | ❌ 无需登录（需提供 refresh_token） |

**请求体**：

```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| refresh_token | string | ✅ 是 | 刷新令牌（登录/注册时返回的） |

**响应**：``200 OK``

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

**错误**：``400`` 缺少 refresh_token / ``401`` refresh token 无效或已过期

> 前端收到 401 时自动调用此接口，用 refresh token 换新 access token，然后重试原请求。不能用 access token 来刷新（类型校验）。

---

### 6.4 退出登录

| 项目 | 值 |
|------|-----|
| **URL** | ``POST /api/auth/logout`` |
| **鉴权** | ✅ 需登录 |

**请求体**：无

**响应**：``200 OK``

```json
{ "message": "退出成功" }
```

> 退出后当前 access token 立即失效（加入黑名单），即使未过期也无法再使用。

---

### 6.5 查看当前用户资料

| 项目 | 值 |
|------|-----|
| **URL** | ``GET /api/auth/me`` |
| **鉴权** | ✅ 需登录 |

**请求体**：无

**响应**：``200 OK`` → ``User``

```json
{
  "id": "U1A2B3",
  "name": "张三",
  "color": "#409eff",
  "username": "zhang",
  "email": "zhang@example.com",
  "is_admin": true,
  "created_at": "2025-01-01T00:00:00"
}
```

---

### 6.6 修改个人资料

| 项目 | 值 |
|------|-----|
| **URL** | ``PUT /api/auth/me`` |
| **鉴权** | ✅ 需登录 |

**请求体**：``UserUpdate``

```json
{
  "name": "新昵称",
  "email": "new@example.com",
  "color": "#67c23a",
  "old_password": "123456",
  "new_password": "654321"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | string | 否 | 新昵称 |
| email | string | 否 | 新邮箱 |
| color | string | 否 | 头像颜色（如 ``#409eff``） |
| old_password | string | 改密码时必填 | 旧密码 |
| new_password | string | 改密码时必填 | 新密码（至少 6 位） |

> 只改资料时无需传密码字段；改密码时必须同时提供 ``old_password`` 和 ``new_password``。所有字段均为可选，只更新传入的字段。

**响应**：``200 OK`` → ``User``（结构同 6.5）

**错误**：``400`` 改密码需提供旧密码 / 新密码至少 6 位 / ``403`` 旧密码不正确

---

### 令牌机制说明

| 项目 | Access Token | Refresh Token |
|------|-------------|---------------|
| 用途 | 每次请求携带鉴权 | 仅用于刷新 access token |
| 有效期 | 短期（分钟级） | 长期（天级） |
| 请求头 | ``Authorization: Bearer <token>`` | 不放请求头，放请求体 |
| 存储 | 前端 localStorage | 前端 localStorage |
| 失效方式 | 过期 / 退出加入黑名单 | 过期 / 退出加入黑名单 |
