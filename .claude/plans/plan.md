# 神行库 Agent 流程改造：多阶段交互式向导

## 目标

把当前「一次请求串行跑完 5 个 Agent」改为**四阶段交互式流程**，用户在阶段间介入（选版本 / 改内容 / 选渠道）：

```
阶段1  检索 → 生成 → 校验        →  3 个初稿 + 校验报告
         （用户：重新生成 / 选定 1 个）
阶段2  渠道适配页                →  用户在选定版本上改动内容
         （用户：多选渠道 → 确认）
阶段3  多渠道适配                →  N 个渠道版本（每渠道 1 个）
阶段4  文生图                    →  对 N 个渠道版本配图 → 落 history
```

## 已确认的关键决策
- **跨阶段状态**：服务端 `drafts` 表，`draft_id` 串联，最终确认才落 `history`（历史列表保持干净，刷新可恢复）。
- **多渠道产出**：每渠道 1 个版本（用户选定的 1 版 → 适配成 N 个渠道版）。
- **校验**：只报告 `issues`，不自动返工；用户自行决定「重新生成」。

---

## 一、后端改动

### 1. `app/database.py` — 新增 drafts 表（init_db 内 CREATE IF NOT EXISTS）
```
drafts(
  id VARCHAR(20) PK,            -- D + uuid hex
  user_id VARCHAR(20) NOT NULL,
  product_id, product_name, scenario_id, scenario_name,
  template_id, template_name, style,
  params JSONB,
  stage VARCHAR(20) DEFAULT 'draft',   -- draft / editing / adapted / imaged / done
  retrieved_info JSONB,                -- 阶段1 检索产物
  draft_versions JSONB DEFAULT '[]',   -- 阶段1 3个初稿
  validation JSONB,                    -- {issues, validated}
  agent_trace JSONB DEFAULT '[]',
  selected_version JSONB,              -- 阶段2 用户选定+改动后的那1版
  channels JSONB DEFAULT '[]',         -- 阶段3 用户多选渠道
  versions JSONB DEFAULT '[]',         -- 阶段3 N个渠道版本(每版带 channel)
  history_id VARCHAR(20),              -- 阶段4 落库后回填
  created_at, updated_at
)
```

### 2. `app/models.py` — 新增 Draft 模型 + VersionContent 加字段
- `VersionContent` 增加 `channel: str = ""`（标识渠道版本归属）
- 新增：`DraftResponse`（完整草稿状态）、`CreateDraftRequest`、`SelectVersionRequest`、`AdaptRequest`
- `CreateDraftRequest` 与现有 `GenerateRequest` 字段相近，但**去掉 channel**（渠道后置），`version_count` 固定 3

### 3. `app/routers/drafts.py` — 新增 6 个端点
| 方法 | 路径 | 阶段 | 作用 |
|------|------|------|------|
| POST | `/api/drafts` | 1 | 检索+生成+校验 → 返回 draft_id + 3 初稿 + 校验 + trace |
| POST | `/api/drafts/{id}/regenerate` | 1 | 重新生成（可微调 params），替换 draft_versions |
| PUT  | `/api/drafts/{id}/select` | 2 | 提交用户选定+改动后的那 1 版，stage→editing |
| POST | `/api/drafts/{id}/adapt` | 3 | 多选渠道 → 产出 N 个渠道版本，stage→adapted |
| POST | `/api/drafts/{id}/finalize` | 4 | 文生图 → 写 history → 返回 history_id，stage→done |
| GET  | `/api/drafts/{id}` | — | 恢复草稿（前端刷新续作） |

所有写操作校验 `user_id` 归属（复用 `get_current_user` + `is_owner_or_admin`）。

### 4. `app/agents/orchestrator.py` — 新增分阶段方法（保留旧 `run()` 兼容）
- `run_draft(product, scenario, style, params)` → `(retrieved_info, draft_versions, validation, trace)`：调 RetrievalAgent → GenerationAgent → ValidationAgent（**只跑 1 次，不返工**）
- `run_adapt(selected_version, channels, scenario)` → `N 个渠道版本`：调 ChannelAgent 新方法
- `run_images(versions, scenario)` → `配图后的 versions`：调 ImageAgent
- 现有 `run()`（旧一次性流程）保留不动，供旧 `/api/generate` 兼容

### 5. `app/agents/channel_agent.py` — 新增 `adapt_to_channels(version, channels, scenario)`
- 现有 `_execute` 是「一批版本 → 单渠道」；新方法是「单版本 → 多渠道」
- 对每个渠道复用 `_adapt_with_llm` / `_adapt_rule`，产出版本带 `channel` 字段
- 未知渠道跳过并在返回信息中标注

### 6. `app/main.py` — 挂载 `drafts.router`

---

## 二、前端改动（`frontend/index.html`「内容生成」tab）

改为 `el-steps` 向导，`draft_id` 贯穿全程：

- **Step 1「生成」**：配置表单（**移除渠道单选**，渠道后置到 Step2）→ `POST /api/drafts` → 展示 3 初稿（Tab）+ 校验 issues + Agent 链路 + 按钮【重新生成】【选定此版本】
- **Step 2「渠道适配」**：展示选定版本（可编辑 title/body，复用现有编辑模式）→ `el-checkbox-group` 多选渠道 →【确认适配】`POST /adapt`
- **Step 3「多渠道版本」**：展示 N 个渠道版本（Tab 按渠道）→【生成配图并保存】`POST /finalize` → 文生图 loading → 完成提示
- 顶部 `el-steps` 显示进度；刷新时 `GET /api/drafts/{id}` 按 `stage` 恢复到对应步
- 复用现有 `renderArticle`、编辑模式、投票、SEO、导出逻辑

---

## 三、历史记录形态
- 一条 `history`，`versions` 含 N 个渠道版本，每版带 `channel` 字段
- 导出（docx/md/txt）、A/B 投票、反馈按 version index 自然兼容
- history 列表「渠道」列改为展示「多渠道(N)」或首个渠道

---

## 四、兼容性 & 风险
- 旧 `/api/generate` + `orchestrator.run()` 保留，不破坏现有 history 数据与导出
- `drafts` 为新增表，`init_db` 用 `CREATE IF NOT EXISTS` + `ALTER ADD COLUMN IF NOT EXISTS` 幂等
- LLM/Mock 双模式在各阶段均保留（生成 / 适配 / 配图）
- `finalize` 对 N 个渠道版本配图，N 大时耗时增加 → 前端 loading + 后端逐版本生成（失败不阻断）
- 草稿归属校验：他人草稿 403，不存在 404

---

## 五、实施顺序
1. `database.py`：drafts 建表 + init_db
2. `models.py`：Draft 模型 + `VersionContent.channel`
3. `channel_agent.py`：`adapt_to_channels`
4. `orchestrator.py`：`run_draft` / `run_adapt` / `run_images`
5. `routers/drafts.py`：6 个端点
6. `app/main.py`：挂载 router
7. `frontend/index.html`：el-steps 向导 + 三步页面 + draft_id 恢复
8. 联调：Mock 模式先通，再切 LLM 模式验证
