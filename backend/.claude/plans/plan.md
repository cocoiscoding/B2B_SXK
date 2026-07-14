# 竞品分析自动入库

## 背景
竞品分析结果（comparison_table / SWOT / 优劣 / 销售话术）目前只存在 `ctx.competitor_info`，用一次即弃。
虽 `agent_trace` 里留存了一份，但埋在 JSONB 里、不可查询、不可复用。
每次竞品场景生成都要重跑 Tavily 搜索 + LLM 分析（5-10s + API 成本）。

## 目标
竞品分析结果自动入库，按 (产品, 竞品) 复用，避免重复分析；并结构化可查询、可管理。

## 改动

### 1. 新表 `competitor_analyses`（`app/database.py` init_db + `database/init_postgresql.sql`）
```sql
CREATE TABLE IF NOT EXISTS competitor_analyses (
    id              VARCHAR(20)  PRIMARY KEY,
    product_id      VARCHAR(20)  NOT NULL,
    competitor_name VARCHAR(200) NOT NULL,
    analysis        JSONB        NOT NULL,      -- 完整分析结果（competitor_agent 产出）
    source          VARCHAR(50),                -- tavily / llm / mock
    created_at      TIMESTAMPTZ  DEFAULT NOW(),
    updated_at      TIMESTAMPTZ  DEFAULT NOW(),
    UNIQUE (product_id, competitor_name)
);
```
沿用项目 `CREATE/ALTER IF NOT EXISTS` 幂等模式，启动自动建表。

### 2. `app/agents/competitor_agent.py` `_execute`（核心：自动入库 + 缓存复用）
- 取 `product_id = ctx.product.get("id", "")`
- **分析前先查缓存**：`SELECT analysis, source, updated_at FROM competitor_analyses WHERE product_id=%s AND competitor_name=%s`
  - 命中且新鲜（`updated_at > NOW() - INTERVAL '7 days'`）→ 直接复用 `analysis`，跳过 Tavily+LLM，message 标注「复用已入库分析（N 天前，source）」
  - 未命中 / 过期 / 无 product_id → 走原分析逻辑
- **分析后 UPSERT 入库**：`INSERT ... ON CONFLICT (product_id, competitor_name) DO UPDATE SET analysis=EXCLUDED.analysis, source=EXCLUDED.source, updated_at=NOW()`
- 新增导入：`uuid`、`query_one, execute`、`Json`；模块常量 `COMPETITOR_CACHE_DAYS = 7`
- 无 product_id 时只分析不入库（容错，不阻断）

### 3. 竞品分析查看/管理 API（新 `app/routers/competitors.py`，挂到 `app/main.py`）
- `GET /api/products/{product_id}/competitors` — 列出该产品所有竞品分析（id/competitor_name/source/updated_at + analysis）
- `DELETE /api/products/{product_id}/competitors/{competitor_name}` — 删除单条（强制下次重新分析）
- 鉴权：查看需登录；删除限产品创建者或管理员（复用 `is_owner_or_admin`）

## 不做（控制范围）
- 不改生成响应结构：`competitor_info` 仍只注入 prompt；查看走新 API
- 不加前端 UI（后续可补）
- 缓存维度 `(product_id, competitor_name)`，忽略 `focus`（分析本身覆盖多维度，足够复用）
- 不保留历史快照：同一产品+竞品反复分析只留最新一条（UPSERT）

## 取舍说明
- **7 天新鲜度**：平衡成本与时效。竞品定位不会周级变化，7 天合理；过期自动重分析。常量可调。
- **UPSERT 而非追加**：避免同竞品堆积大量历史快照；如需审计可后续加 `competitor_analysis_history` 表。
- **复用而非每次重算**：这是本功能主要收益——二次生成竞品场景从 5-10s 降到毫秒级。
