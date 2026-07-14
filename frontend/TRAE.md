# B2B-SXK-ManageGF — 项目上下文

> 一句话定位：基于 Vue 3 + Element Plus + Vite 的「神行库」产品营销 AI 平台管理后台，为产品知识库管理、多 Agent 营销内容生成（含 SSE 流式）、竞品对比分析、成员管理与多渠道文案适配提供交互界面。
> 本文件由 `project-init-context` skill 基于代码现状自动生成（11 维度分析框架），供人类开发者与 AI Agent 共享。后端为独立部署的 FastAPI 服务（`B2B-SXK-FastApi`，端点 `/api/*`），BladeX 仅作社交登录兼容层保留（`/api/blade-*`）。本仓库仅含前端。

---

## 1. 技术栈

| 层 | 技术 | 版本（取自 [package.json](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/package.json)） |
|----|------|------|
| 框架 | Vue 3（Composition API，`<script setup>`） | ^3.5.13 |
| 路由 | Vue Router（Hash 模式） | ^4.5.0 |
| 状态管理 | Pinia（4 个 module：user / common / tags / logs） | ^2.3.0 |
| 国际化 | Vue I18n（zh / en，默认 zh） | ^10.0.5 |
| 构建 | Vite | ^6.0.5 |
| UI 库 | Element Plus + `@element-plus/icons-vue`（组件按需自动导入，图标显式 import） | ^2.9.1 / ^2.3.1 |
| HTTP | axios（统一封装拦截器） | ^1.7.9 |
| 流式通信 | 原生 `fetch` + `ReadableStream`（[util/sse-client.js](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/src/util/sse-client.js)，自实现 SSE 客户端） | — |
| 工具库 | `crypto-js`（AES-CBC）、`js-base64`、`js-cookie`、`js-md5`、`nprogress`、`@vueuse/core` | — |
| 样式 | SCSS（全局变量自动注入 `@/styles/variables.scss`） | sass ^1.83.0 |
| 自动导入 | `unplugin-auto-import` + `unplugin-vue-components`（仅 ElementPlusResolver） | — |
| Lint | ESLint 8 + `eslint-plugin-vue`（配置见 [.eslintrc.cjs](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/.eslintrc.cjs)） | ^8.57.1 / ^9.32.0 |
| 包管理器 | npm（仓库存在 `package-lock.json`） | — |
| 模块系统 | ES Module（`"type": "module"`） | — |
| 后端（独立部署） | **FastAPI**（`B2B-SXK-FastApi`），OAuth2 PasswordBearer，主前缀 `/api/*`；BladeX 仅遗留社交登录兼容（`/api/blade-auth/oauth/token`） | 待确认 |

> 未声明 Node 版本约束（无 `engines` / `.nvmrc`），Vite 6 要求 Node 18+，建议团队统一 Node 18+。

---

## 2. 项目结构

前端单体项目（前后端分离的前端部分），顶层结构如下：

```
B2B-SXK-ManageGF/
├── index.html               # HTML 入口（标题：神行库 · 营销 AI）
├── package.json             # 依赖与 5 个脚本
├── vite.config.js           # Vite 配置（别名 @ → src、代理、按需导入、手动分包）
├── .env / .env.dev / .env.prod / .env.test   # 多环境变量
├── .editorconfig            # 编辑器统一配置（UTF-8 / 2 空格 / LF）
├── .eslintrc.cjs            # ESLint 配置（eslint:recommended + vue3-recommended）
├── .gitignore               # 忽略 node_modules/dist/.trae/.env.local/三份接口清单md
├── check-port.ps1           # Windows 端口占用检查脚本
├── kill-dev-servers.ps1     # 关闭占用 Vite 端口进程的脚本
└── src/
    ├── main.js              # 应用入口（装配 pinia/router/i18n/ElementPlus，注册全局组件）
    ├── App.vue              # 根组件（仅 <router-view/>）
    ├── permission.js        # 路由全局守卫（鉴权 + 标签页维护 + requiresAdmin）
    ├── cache.js             # keepAlive 缓存配置
    ├── api/                 # 鉴权/系统级 API 请求（带 Mock 开关）
    │   ├── user.js          # 鉴权/用户（登录/注册/刷新/登出/用户信息/查重/验证码）
    │   ├── common.js        # 通用 API（字典等示例）
    │   └── system/menu.js   # 菜单（顶部菜单、动态路由；当前短路返回空数组）
    ├── components/          # 全局基础组件（不自动注册，需显式 import）
    │   ├── basic-container/main.vue
    │   ├── basic-block/main.vue     # 扩展了 header/aside 插槽、hoverShadow/padding props
    │   ├── error-page/{403,404,500}.vue
    │   ├── iframe/main.vue
    │   └── tag-input/index.vue      # 通用标签输入器
    ├── config/
    │   ├── env.js           # baseUrl（dev='/api'，prod=''）、iconfont、环境判定
    │   └── website.js       # 全站常量（标题、clientId/Secret、租户、tokenHeader 等）
    ├── lang/                # i18n（index.js + zh.js + en.js）
    ├── mock/                # 业务 Mock 层（双轨开关 USE_MOCK_BIZ）
    │   ├── data.js          # 业务 Mock 数据集（产品/模板/生成/成员/竞品/Dashboard 统计等）
    │   └── sxkApi.js        # 业务 Mock API 封装 + 真实链路适配层（核心文件，2211 行）
    ├── page/                # 页面级布局与免鉴权页
    │   ├── index/           # 主布局（top + sidebar + tags + router-view）
    │   ├── login/           # 登录页
    │   ├── register/        # 注册页
    │   └── lock/            # 锁屏页
    ├── router/
    │   ├── router.js        # 路由实例 + 动态路由注入 + 重置
    │   ├── axios.js         # axios 实例与全局拦截器（**Bearer Token + 双格式响应**）
    │   ├── page/index.js    # 免鉴权页路由（登录/注册/锁屏/错误页/首页重定向）
    │   └── views/index.js   # 业务视图路由（7 个 SXK 业务页 + 2 个旧页）
    ├── store/               # Pinia
    │   ├── index.js         # createPinia
    │   └── modules/         # user / common / tags / logs
    ├── styles/              # 全局 SCSS（variables / common / layout / login / normalize）
    ├── util/                # 工具集
    │   ├── auth.js          # Cookie token 工具（key: sxk-access-token / sxk-refresh-token）
    │   ├── crypto.js        # AES-CBC 加解密（固定 key/iv，仅前端混淆）
    │   ├── store.js         # sessionStorage 工具（自动加 sxk- 前缀）
    │   ├── util.js          # 通用工具（serialize / deepClone / loadStyle）
    │   ├── validate.js      # 校验工具（validatenull / isURL）
    │   ├── date.js          # 日期工具
    │   ├── admin.js         # 管理员判定
    │   ├── svg-captcha.js   # 本地 SVG 验证码（仅 Mock 阶段）
    │   ├── scene-style.js   # 场景图标/配色共享（dashboard + templates 共用）
    │   └── sse-client.js    # **SSE 流式客户端**（fetch + ReadableStream，Agent 步骤推送）
    └── views/               # 业务视图
        ├── sxk/             # 神行库 7 大业务页面
        │   ├── dashboard/       # 首页：欢迎区 + 统计卡 + 常用模板 + 最近生成
        │   ├── knowledge/       # 产品知识库：CRUD + 关键词高亮 + Word/PDF 建库
        │   ├── generate/        # 内容生成：3 阶段草稿流程（draft→editing→adapted→done）
        │   ├── history/         # 生成历史：表格 + 详情/A/B 投票/反馈/导出
        │   ├── templates/       # 场景模板管理：场景 + 子模板 CRUD
        │   ├── members/         # 成员管理（requiresAdmin: true）
        │   └── competitors/     # 竞品分析
        ├── system/userinfo.vue   # 个人信息
        └── workbenches/index.vue # 旧工作台入口
```

---

## 3. 常用命令（执行目录：项目根）

> 实际 scripts 取自 [package.json](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/package.json#L6-L12)，仅以下 5 个。

| 场景 | 命令 | 说明 |
|------|------|------|
| 安装依赖 | `npm install` | 使用 npm（仓库带 `package-lock.json`） |
| 本地开发 | `npm run dev` | `vite --mode dev`，端口取 `VITE_PORT`（**当前 `.env.dev` 配置为 53200**，vite.config 默认 fallback 52400），`/api` 代理到 `VITE_API_TARGET`（当前 `http://localhost:8000`） |
| 生产构建（默认） | `npm run build` | `vite build` |
| 生产构建（prod） | `npm run build:prod` | `vite build --mode prod` |
| 预览构建产物 | `npm run preview` | `vite preview` |
| Lint 修复 | `npm run lint` | `eslint . --ext .vue,.js,.jsx,.cjs,.mjs --fix --ignore-path .gitignore` |

**辅助脚本（PowerShell）**：
- `./check-port.ps1`：检查 53200 端口占用
- `./kill-dev-servers.ps1`：杀掉占用 Vite 端口的进程

构建产物输出到 `dist/`，手动分包：`vue`（vue+router+pinia）、`element`（element-plus+icons）。

---

## 4. 架构与代码组织

**分层**：典型中后端驱动前端（Saber/Avue 风格） — `views/(业务视图) → api/ 或 mock/sxkApi(请求) → router/axios.js(统一 http) → 后端 FastAPI`。

**入口与装配**（[src/main.js](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/src/main.js)）：
- `createApp(App)` → 依次 `use(pinia)`、`use(router)`、`use(i18n)`、`use(ElementPlus, { locale: zhCn })`
- 显式 `import` 后注册全局组件 `basicContainer`、`basicBlock`
- 注入全局属性 `website`、`baseUrl`
- 动态加载阿里 iconfont
- 引入 `./permission` 启动路由守卫

**布局**（[src/page/index/index.vue](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/src/page/index/index.vue)）：`header(Top) + left(Sidebar) + Tags + router-view`，根据 `route.meta.keepAlive` 决定是否 `keep-alive`。

**路由**（[src/router/router.js](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/src/router/router.js)）：Hash 模式，由 `PageRouter`（免鉴权页）+ `ViewsRouter`（业务页）组成；提供 `addDynamicRoutes`（动态注入后端菜单）与 `resetRouter`（登出重置）。`meta` 约定：`keepAlive` / `isTab` / `isAuth` / `menu` / `title` / `requiresAdmin`。

**业务路由**（[src/router/views/index.js](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/src/router/views/index.js)）：7 个 SXK 业务页 + 2 个旧页，均以 `Layout` 为父级，`child.path` 统一为 `index`：
- `/dashboard/index`、`/knowledge/index`、`/generate/index`、`/history/index`、`/templates/index`
- `/members/index`（**`meta.requiresAdmin: true`**）、`/competitors/index`
- `/workbenches/index`（旧入口）、`/info/index`（个人信息）

**鉴权链路（端到端示例）**：
1. [login/index.vue](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/src/page/login/index.vue) 表单 → `userStore.loginByUsername()`
2. [store/modules/user.js](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/src/store/modules/user.js)：
   - `VITE_APP_USE_MOCK_AUTH === 'true'` 时走本地 Mock 登录（非空校验 + 验证码 + 伪造 token，**Mock 阶段所有用户视为管理员 `is_admin=true`**）
   - 否则调 [api/user.js](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/src/api/user.js) `loginByUsername` → `POST /api/auth/login`
3. [router/axios.js](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/src/router/axios.js) 请求拦截器：自动拼 `baseUrl`、加 **`Authorization: Bearer <token>`**（FastAPI 标准 OAuth2；与既有 BladeX `Blade-Auth` 头不同）
4. 响应拦截器**双格式兼容**：
   - 有 `code` 字段（Mock/SXK 壳）：`code === 0` 成功，业务错误码正常 return 由页面处理
   - 无 `code` 字段（FastAPI 裸响应）：按 HTTP status 判断，错误消息优先读 `res.data.detail`
   - `401` 触发 `refreshToken`，失败则 `fedLogOut` 跳 `/login`
5. 成功 → `setToken`（Cookie `sxk-access-token`）+ `setStore`（sessionStorage `sxk-*`）
6. [permission.js](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/src/permission.js) `beforeEach`：无 token 跳 `/login`；有 token 但 store 中 token 空 → `fedLogOut`；否则按 `meta.requiresAdmin` 校验管理员（非管理员访问跳 `/dashboard/index`）后维护 Tags 放行
7. 登录后 `initSxkMenu()` 注入菜单（绕过后端菜单接口）

**状态管理分工**：
- `user`：token / refreshToken / tenantId / userInfo / roles / menu / menuAll / permission（按钮权限码 map）
- `common`：语言、主题、锁屏、折叠、全屏、屏幕尺寸等 UI 状态
- `tags`：标签页导航（增删、当前标签）
- `logs`：前端日志列表

**菜单注入**（[store/modules/user.js](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/src/store/modules/user.js#L396-L448) `initSxkMenu()`）：登录后与 `setUserInfo` 时都会触发，写入 7 个一级菜单（首页 / 产品知识库 / 内容生成 / 生成历史 / 场景模板管理 / 竞品分析 + **管理员可见的成员管理**）。

**路径别名**：`@` → `./src`（定义于 [vite.config.js](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/vite.config.js#L23-L26)）。**所有 import 必须使用 `@/`，禁止相对路径硬编码。**

**数据持久化**：
- token / refreshToken → Cookie（[util/auth.js](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/src/util/auth.js)，key `sxk-access-token` / `sxk-refresh-token`）
- 其他状态 → sessionStorage（[util/store.js](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/src/util/store.js)，key 自动加 `sxk-` 前缀，主键来自 `website.key = 'sxk'`）

**关键基础设施**：
- [util/sse-client.js](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/src/util/sse-client.js)：自实现 SSE 客户端，用于 [mock/sxkApi.js](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/src/mock/sxkApi.js) `createDraftStream` / `regenerateDraftStream` 接收 Agent 步骤推送。事件协议：`step`/`done`/`error`，与后端 `B2B-SXK-FastApi/app/routers/drafts.py` 一致。dev 模式直连 `VITE_API_TARGET` 绕过 Vite proxy 的 SSE 缓冲。
- [util/scene-style.js](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/src/util/scene-style.js)：场景图标/配色共享工具（dashboard 与 templates 共用 `getSceneStyle()`，匹配优先级：sceneCode 精确匹配 → 名称关键词匹配 → 兜底）。

---

## 5. 编码规范

- **Linter / Formatter**：`npm run lint`（ESLint 8 + eslint-plugin-vue，`--fix` 自动修复）。配置 [.eslintrc.cjs](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/.eslintrc.cjs)：
  - 继承 `eslint:recommended` + `plugin:vue/vue3-recommended`
  - `vue/multi-word-component-names: 'off'`（sxk 模块下含单/双字业务组件）
  - 生产环境 `no-console` / `no-debugger` 为 `error`，开发环境为 `off`
  - `no-unused-vars`：下划线前缀参数/变量视为有意保留
- **缩进 / 引号 / 分号**：依 [.editorconfig](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/.editorconfig) — UTF-8、2 空格缩进、LF 换行、文件尾插入空行、去除行尾空白（`.md` 除外）。代码普遍使用单引号、无分号。
- **样式**：SCSS，组件内 `<style lang="scss" scoped>`；全局样式入口 `src/styles/common.scss` / `layout.scss` / `login.scss`；变量 `variables.scss` 由 Vite 自动 `@use` 注入，**无需在各文件手动 import**。
- **组件**：Element Plus 组件通过 `unplugin-vue-components` **按需自动注册**，模板直接使用 `<el-*>`，无需手动 import；`@element-plus/icons-vue` 图标需显式 import。**`src/components/*` 下的自定义组件不会自动注册**，必须显式 import（见 10.1 陷阱 1）。
- **命名约定**：
  - 目录与 `.vue` / `.js` 文件：小写（`login/index.vue`、`basic-container/main.vue`）
  - 全局组件注册名：camelCase（`basicContainer`、`basicBlock`）
  - Store 模块：小写单词（`user`、`common`、`tags`、`logs`）
  - API 函数：camelCase（`loginByUsername`、`getDashboardStats`、`createDraftStream`）
  - 业务常量：camelCase 对象（`website`）
- **注释语言**：中文（`/** ... */` 与行内注释）。
- **提交规范**：仓库未配置 `commitlint` / `husky`，无强制约定。

---

## 6. 数据与 API

- **前端无数据库**；所有数据来自后端服务（FastAPI）。
- **后端真实路径清单**（取自 [mock/sxkApi.js](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/src/mock/sxkApi.js) 真实链路分支）：

| 域 | 方法 + 路径 |
|----|------------|
| 鉴权 | `POST /api/auth/login`、`POST /api/auth/register`、`POST /api/auth/refresh`、`POST /api/auth/logout`、`GET /api/auth/me` |
| 用户名查重 | `GET /api/sxk/auth/check-username` |
| 产品 | `GET /api/products`、`POST /api/products`、`GET/PUT/DELETE /api/products/{id}`、`POST /api/products/{id}/upload-image`、`POST /api/products/{id}/upload-document`、`POST /api/products/import-docx`（Word/PDF 建库）、`POST /api/products/search`（语义搜索）、`POST /api/products/reindex`（管理员） |
| 场景 | `GET /api/scenarios`、`POST /api/scenarios`、`PUT/DELETE /api/scenarios/{id}` |
| 模板 | `GET /api/templates/all`、`GET /api/scenarios/{sid}/templates`、`POST /api/scenarios/{sid}/templates`、`GET/PUT/DELETE /api/scenarios/{sid}/templates/{tid}` |
| 生成 | `POST /api/generate` |
| 草稿 | `POST /api/drafts`、`POST /api/drafts/stream`（**SSE**）、`POST /api/drafts/{id}/regenerate/stream`（**SSE**）、`PUT /api/drafts/{id}/select`、`POST /api/drafts/{id}/adapt`、`POST /api/drafts/{id}/finalize`、`GET /api/drafts/{id}`、`POST /api/drafts/{id}/regenerate` |
| 历史 | `GET /api/history`、`GET/PUT/DELETE /api/history/{id}`、`PUT /api/history/{id}/vote`、`PUT /api/history/{id}/feedback`、`GET /api/history/{id}/export?format=docx\|markdown\|txt` |
| 成员 | `GET /api/members`、`POST /api/members`、`PUT/DELETE /api/members/{id}` |
| 竞品 | `GET /api/products/{pid}/competitors`、`DELETE /api/products/{pid}/competitors/{name}` |
| 渠道/SEO | `GET /api/channels`、`POST /api/seo/analyze` |
| BladeX 遗留 | `POST /api/blade-auth/oauth/token`（社交登录）、`GET /api/blade-system/menu/{top-menu,routes,buttons}`（基本已不调用） |

- **请求封装**（[src/router/axios.js](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/src/router/axios.js)）：
  - 超时 60s，`withCredentials` 开启
  - 请求拦截：自动加 `baseUrl`、加 `Authorization: Bearer <token>`（除非 `config.meta.isToken === false`）
  - 响应拦截：**优先读 `res.data.code`**（SXK 约定 `code === 0` 成功，业务错误码 return 由页面处理）；无 `code` 字段时按 HTTP status 判断，错误消息优先 `res.data.detail`（FastAPI 风格）后 `msg`；`401` 触发 `refreshToken`，失败 `fedLogOut` 跳 `/login`
  - 自定义 `config.meta`：`isToken`（是否带 token）、`isSerialize`（表单序列化）；`config.text === true` 设 `Content-Type: text/plain`
- **Mock 双轨开关**：
  - `VITE_APP_USE_MOCK_AUTH`：控制鉴权/系统级接口（[api/user.js](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/src/api/user.js) + [api/system/menu.js](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/src/api/system/menu.js)）
  - `VITE_APP_USE_MOCK_BIZ`：控制业务域全部接口（[mock/sxkApi.js](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/src/mock/sxkApi.js)，每个方法内 `if (!USE_MOCK_BIZ) return real(...)` 自动切换）。真实链路 `real()` 已提取 `res.data`，与 Mock `ok()` 返回形态完全一致，调用方无感知
- **后端字段适配层**：[mock/sxkApi.js](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/src/mock/sxkApi.js) 内置 `adaptProduct` / `adaptTemplate` / `adaptScene` / `adaptHistory` / `adaptVersion` / `adaptProductToBackend`，**业务页面只看到前端统一字段（snake_case 但带 `product_id`/`template_id`/`scene_code` 等 ID 命名）**，无需关心后端 `id`/`scenario_id`/`parameters`/`constraints` 等差异。
- **DTO 校验**：前端用 Element Plus `el-form` rules，无 zod/joi/class-validator。
- **接口文档**：前端仓库内未发现 Swagger/OpenAPI；本地有 3 份后端接口清单 md（已被 `.gitignore` 忽略）。
- **加密**：AES-CBC（固定 key/iv，见 [util/crypto.js](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/src/util/crypto.js#L6-L7)），仅用于前端敏感数据二次混淆，非安全存储。

---

## 7. 环境变量

Vite 环境变量必须以 `VITE_` 为前缀才能注入前端。文件分布（实测值）：

| 变量 | 来源 | 当前值 | 说明 |
|------|------|--------|------|
| `VITE_APP_TITLE` | [.env](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/.env) | `神行库 · 营销 AI` | 全站标题（基础共享） |
| `VITE_APP_ENV` | .env.dev/prod/test | `dev` / `prod` / `test` | 环境标识 |
| `VITE_PORT` | [.env.dev](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/.env.dev) | **`53200`** | dev server 端口（vite.config fallback 为 52400） |
| `VITE_API_TARGET` | .env.dev | `http://localhost:8000` | dev 代理目标（本地后端 FastAPI） |
| `VITE_API_TARGET` | .env.prod / .env.test | （空） | 生产/测试由 CI/网关注入或 nginx 反代 |
| `VITE_APP_USE_MOCK_AUTH` | .env.dev | `false` | 鉴权域 Mock 开关（当前已关闭） |
| `VITE_APP_USE_MOCK_BIZ` | .env.dev | `false` | 业务域 Mock 开关（当前已关闭） |
| `VITE_APP_USE_MOCK_AUTH` | .env.prod / .env.test | `false` | 生产/测试强制关闭 Mock Auth |

- 开发态 `baseUrl = '/api'`（走 Vite proxy）；生产态 `baseUrl = ''`（同源直连，见 [config/env.js](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/src/config/env.js)）。
- 全局常量集中在 [config/website.js](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/src/config/website.js)：`clientId='sxk'`、`clientSecret='sxk_secret'`、`tokenHeader='Blade-Auth'`、`tenantId='000000'`、`captchaMode=true`、`key='sxk'`。**`clientSecret` 硬编码在前端，属安全隐患，生产前必须由部署/CI 注入或移至网关鉴权。**
- 已知小漂移：[website.js](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/src/config/website.js#L53) 的 `redirectUri: 'http://localhost:52400'` 与 `.env.dev` 实际端口 `53200` 不一致（社交登录未启用，影响小，但建议同步）。

---

## 8. 部署

- **容器化**：仓库未发现 `Dockerfile` / `docker-compose.yml`。
- **CI/CD**：未发现 `.github/workflows/` / `.gitlab-ci.yml` / `Jenkinsfile`。
- **目标环境**：构建为静态资源（`dist/`），部署到任意静态服务器 / 反向代理；生产态请求需由部署层（nginx 等）将 `/api/*` 转发到后端 FastAPI 服务（因 `baseUrl` 生产为空，需同源或网关统一）。
- **构建模式**：仅 `dev` / `prod` / `test` 三套（无 `local` / `gdccs`）。

---

## 9. 业务领域

### 9.1 产品定位与能力
- **产品定位**：「神行库」产品营销 AI 平台管理后台。
- **核心能力**：产品知识库管理、多 Agent 营销内容生成（含 SSE 流式 Agent 协作）、竞品对比分析、成员管理、多渠道文案适配。
- **当前实现**：7 大业务页面已落地（dashboard / knowledge / generate / history / templates / members / competitors）+ 登录/注册/锁屏 + 个人信息 + 旧工作台。

### 9.2 领域术语
- 租户（tenant）、部门（dept）、角色（role，admin/user）、菜单（menu）、按钮权限（permission code）、验证码（captcha）、产品（product）、模板（template）、场景（scenario，前后端字段映射 `scene_code ↔ scenario_id`）、生成（generation）、历史（history）、草稿（draft，状态机 `draft → editing → adapted → done`）、版本（version，A/B/C…）、Agent 协作（agent_trace / agent_run）、投票（vote，like/dislike）、反馈（feedback）、成员（member）、竞品（competitor）。

### 9.3 权限模型
- RBAC：`is_admin` 布尔字段（后端 `User.is_admin` / Mock 强制 true）+ 按钮级权限码（`userStore.permission[code] === true`）+ 多租户（`tenantId`，`website.tenantMode` 当前关闭）。
- 前端路由级：`meta.requiresAdmin: true` 由 [permission.js](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/src/permission.js#L42-L47) 校验，非管理员访问跳 `/dashboard/index`。
- 菜单级：`initSxkMenu()` 仅当 `userInfo.is_admin === true` 时注入"成员管理"。

### 9.4 关键业务流程
- **登录流程**：登录（账密 + 可选验证码）→ 下发 access_token（+ 可选 refresh_token）→ `setUserInfo` 写入 store → `initSxkMenu()` 注入菜单 → 进入业务页。
- **内容生成 3 阶段流程**（[views/sxk/generate/index.vue](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/src/views/sxk/generate/index.vue)）：
  - **Step 0（draft）**：触发生成 → 多版本初稿（SSE 流式推送 Agent 步骤 `retrieval → generation → validation`，或同步 `createDraft`）
  - **Step 1（editing）**：选定一个版本 → 编辑内容 + 多选渠道（`selectDraftVersion`）
  - **Step 2（adapted→done）**：多渠道适配（`adaptDraft`）→ 文生图 + 落历史（`finalizeDraft`）

### 9.5 后端真实场景代号（取自 [util/scene-style.js](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/src/util/scene-style.js#L32-L38)）
- `S001` 线下展会物料、`S002` 产品介绍文案、`S003` 竞品对比分析报告、`S004` 客户案例包装、`S005` 演讲 PPT 大纲、`S006` 社交媒体帖子。
- Mock 旧版 code（向后兼容）：`product_intro` / `competitor` / `channel_adapt` / `email` / `event` / `other` / `custom_*`。

### 9.6 业务规则代号
- BR-K-XX（产品）/ BR-G-XX（生成）/ BR-H-XX（历史）/ BR-T-XX（模板/场景）/ BR-A-XX（认证）。常见错误码：`4001` 必填、`4006` 内容块为空、`4030` 预置不可删、`4041` 不存在、`4042` 已删除、`4091` 重名、`4092` 场景下重名。

---

## 10. AI 协作约定（写给 AI Agent）

### 10.1 已知陷阱（Known Pitfalls）

以下为本项目实际踩过/已确认的风险点，AI Agent 编写代码前必须先确认是否命中：

1. **自定义全局组件不会自动导入**：`unplugin-vue-components` 仅配置了 `ElementPlusResolver`（`dirs: []`, `deep: false`），对 `src/components/` 下的自定义组件（`basic-container`、`basic-block`、`tag-input` 等）**不会自动注册**。[main.js](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/src/main.js) 中已显式 import 注册 `basicContainer` / `basicBlock`；其他自定义组件使用前必须先显式 `import`，否则报「Unknown custom element」。
2. **鉴权头已切换为 Bearer Token**：[router/axios.js](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/src/router/axios.js#L44-L46) 现在用 `Authorization: Bearer <token>`（FastAPI 标准 OAuth2），**不再是 BladeX 的 `Blade-Auth` + `Authorization: Basic`**。新增鉴权相关代码不要回退到旧风格。
3. **鉴权 API 路径是 `/api/auth/*` 而非 `/api/sxk/auth/*`**：登录/注册/刷新/登出/用户信息都在 `/api/auth/`，只有用户名查重是 `/api/sxk/auth/check-username`（混用，注意区分）。
4. **生产/测试 `VITE_API_TARGET` 为空**：`prod` / `test` 模式下 `VITE_API_TARGET` 留空，`baseUrl` 生产态又为空，**请求会发往同源**。任何新增/修改的接口默认走 `/api`，必须由部署层（nginx / 网关）将 `/api/*` 反代到后端，否则 404。不要在代码里假设后端域名。
5. **`sessionStorage` 不跨标签页共享**：所有非 token 状态（userInfo / menu / permission / language）存于 `sessionStorage`（前缀 `sxk-`），新标签页打开会触发「有 cookie 但 store 为空 → fedLogOut」分支。若 AI 需要「跨标签同步」逻辑，请改用 `localStorage` 或 `BroadcastChannel`。
6. **`userStore.delAllTag()` / `clearLock()` 已用动态 import 修复**：这两个方法通过动态 `import('@/store/modules/tags')` / `import('@/store/modules/common')` 跨模块委托实现（避免循环依赖）。新增登出/锁屏流程时**必须沿用动态 import 写法**。[store/modules/user.js](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/src/store/modules/user.js#L370-L381)
7. **`crypto-js` 的 AES key/iv 是固定常量**：见 [util/crypto.js](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/src/util/crypto.js#L6-L7)，**仅用于前端密码传输的二次混淆**，不是安全存储。任何「把 token / refreshToken 用 AES 加密再存」的需求都属过度设计，直接复用 `util/auth.js` 的 Cookie 工具即可。
8. **按钮权限判定依赖后端下发的 `permission` map**：UI 上 `userStore.permission['btn_xxx']` 仅当 `getButtons` 接口被调用且返回该 code 时才生效。AI 不要在前端硬编码权限码；当前 `getButtons` 实际未调用，权限码机制基本未启用。
9. **不要新增 `.env.*` 文件而不补 `.gitignore`**：本仓库 `.env.local` / `.env.*.local` 已被 `.gitignore` 忽略；若 AI 必须新增环境文件，请同步在 `.gitignore` 中忽略。
10. **菜单路径必须含 `/index` 后缀**：`initSxkMenu()` 写入的菜单项均为 `/dashboard/index` / `/knowledge/index` / `/generate/index` / `/history/index` / `/templates/index` / `/competitors/index` / `/members/index`，与 [router/views/index.js](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/src/router/views/index.js) 中注册的 `child.path` 一致。**不要省略 `/index`**，否则侧边栏点击会跳到无匹配路由的路径。
11. **`sxkApi` Mock 与真实返回形态完全对齐**：[mock/sxkApi.js](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/src/mock/sxkApi.js) 中 Mock 方法 `return delay().then(() => ok(...))`，`ok()` 返回 `{code, msg, data, trace_id}`；真实链路 `real()` 已做 `res.data` 提取对齐。业务页面调用 sxkApi 后**直接读 `resp.data.xxx`**（如 `resp.data.items` / `resp.data.total`）。**注意**：[api/user.js](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/src/api/user.js) 的 Mock `ok()` 多包了一层 AxiosResponse（`{status, data}`），与 sxkApi 不同。
12. **响应拦截双格式分支**：[router/axios.js](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/src/router/axios.js#L85-L127) 当 `res.data.code !== undefined` 时用 `code` 判定（SXK 约定 `0` 成功，业务错误码如 `4091` 正常 return 由页面处理）；无 `code` 字段才回退 HTTP status，错误消息优先 `res.data.detail`（FastAPI 风格）。新增接口若返回壳含 `code`，业务错误不会触发全局 ElMessage，需在页面自行处理。
13. **`requiresAdmin` 路由守卫已生效**：[permission.js](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/src/permission.js#L42-L47) 对 `meta.requiresAdmin: true` 的路由校验 `userStore.userInfo.is_admin`，非管理员访问会被 ElMessage 报错并跳 `/dashboard/index`。新增管理员专属页面必须加此 meta。
14. **Mock 双轨开关独立**：`VITE_APP_USE_MOCK_AUTH`（鉴权域）与 `VITE_APP_USE_MOCK_BIZ`（业务域）是两个独立开关。当前 `.env.dev` 两者均为 `false`（已切真实链路）。开启 Mock Auth 时，`loginByUsername()` 会**完全跳过**后端登录，仅做本地校验后伪造 token，且 `is_admin` 强制为 `true`。**生产环境务必确保两者为 `false`**。
15. **本地 SVG 验证码仅前端演示**：[util/svg-captcha.js](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/src/util/svg-captcha.js) 把生成时的正确答案返回到 login 页并写入 `sessionStorage('sxk-captcha-text')`，**客户端比对 = 0 安全意义**。后端就绪后应删除整个文件 + 恢复真实 `getCaptcha` 实现。
16. **SSE 直连后端绕过 Vite proxy**：[util/sse-client.js](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/src/util/sse-client.js#L63-L69) dev 模式下用 `${VITE_API_TARGET}${url}` 直连后端（如 `http://localhost:8000/api/drafts/stream`），**不走 axios 的 `/api` 代理**，因为 Vite proxy 对 `text/event-stream` 有缓冲问题。生产模式才用 `baseUrl + url`。
17. **SSE Mock 阶段抛错**：[mock/sxkApi.js](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/src/mock/sxkApi.js#L1796-L1824) `createDraftStream` / `regenerateDraftStream` 在 `USE_MOCK_BIZ=true` 时抛 `MOCK_UNSUPPORTED` 错误，调用方需 try/catch 后回退到同步 `createDraft`。
18. **后端字段适配层在 sxkApi 内**：[mock/sxkApi.js](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/src/mock/sxkApi.js) 内置 `adaptProduct`/`adaptTemplate`/`adaptScene`/`adaptHistory`/`adaptVersion` 函数，所有真实链路返回都经过适配。**业务页面 import 的字段是前端格式（`product_id`/`template_id`/`scene_code`），不要直接使用后端字段（`id`/`scenario_id`/`parameters`）**。
19. **模板/场景预置判定靠 ID 正则**：[mock/sxkApi.js](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/src/mock/sxkApi.js#L112) `isPresetTemplate(id)` 用 `/^T\d{3}$/.test(id)` 检测（后端预置模板 ID 为 T001~T008）；场景则用 `!sceneCode.startsWith('custom_')` 判定预置。预置项不可删除（返回 `4030`）。
20. **Word/PDF 建库（importDocx）在 Mock 阶段返回 `mock_unavailable: true`**：[mock/sxkApi.js](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/src/mock/sxkApi.js#L758-L780) 让前端用 `ElMessage.warning` 区别对待，**不要把它当普通错误处理**。
21. **文件上传禁用 serialize**：[mock/sxkApi.js](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/src/mock/sxkApi.js#L730) `uploadProductImage` / `uploadProductDocument` / `importDocx` 必须传 `meta: { isSerialize: false }`，否则 multipart FormData 会被错误序列化。
22. **端口冲突 → 自动落到 53201+**：开发期 `localhost:53200` 出现 404 时，**优先检查端口是否被占用**（Vite 启动日志 `Port 53200 is in use, trying another one...` 会自动落到 53201+）。需 `netstat -ano | findstr 53200` + `taskkill /PID <pid> /F` 后重启 `npm run dev`，或直接运行 `./kill-dev-servers.ps1`。
23. **项目独立性约束**：神行库独立部署，使用 `sxk` 前缀（`clientId='sxk'`、`TokenKey='sxk-access-token'`、sessionStorage 前缀 `sxk-`、`website.key='sxk'`）。**严禁再把其他同源业务系统的 clientId / tokenKey / 注释直接复制进来**；新增 `.env.*` 时只保留 `dev / test / prod` 三套。

### 10.2 编码与工程约束（Operational Rules）

1. **import 必须使用 `@/` 别名**，禁止 `../../` 相对路径（别名见 [vite.config.js](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/vite.config.js#L23-L26)）。
2. **新增 API**：业务接口统一加到 [src/mock/sxkApi.js](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/src/mock/sxkApi.js)（双轨写法：`if (!USE_MOCK_BIZ) return real({...})` + Mock 分支），URL 以 `/api/` 开头；鉴权/系统级接口加到 `src/api/<域>.js`。**不要在业务组件里直接 `import axios`**。
3. **新增业务视图**：放在 `src/views/<模块>/`，并在 [src/router/views/index.js](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/src/router/views/index.js) 注册路由，使用 `Layout` 父级，`child.path` 用 `index`；`meta` 必填语义（`keepAlive` / `isTab` / `isAuth` / `title`，管理员专属加 `requiresAdmin: true`）。
4. **新增菜单项**：在 [store/modules/user.js](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/src/store/modules/user.js#L396-L448) `initSxkMenu()` 中追加，path 必须含 `/index` 后缀；管理员专属菜单要包在 `if (isAdmin)` 分支内。
5. **Element Plus 组件**：模板直接写 `<el-*>`，**不要**手动 import 组件；图标 `@element-plus/icons-vue` 需显式 import。
6. **状态管理**：跨页共享状态写 Pinia store（`src/store/modules/`），不要滥用全局属性；持久化用 `@/util/store`（sessionStorage，自动加 `sxk-` 前缀），token 类用 `@/util/auth`（Cookie）。
7. **样式**：组件内 `<style lang="scss" scoped>`；变量直接使用 `variables.scss` 中的值（已自动注入），不要再 `@import`。
8. **鉴权**：免 token 请求需在 request 配置里加 `meta: { isToken: false }`；新增需登录的页面**不要**加 `meta.isAuth = false`。
9. **密码 / 敏感数据**：复用 [util/crypto.js](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/src/util/crypto.js) 与 [util/auth.js](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/src/util/auth.js)，不要自造加密逻辑；不要把 `clientSecret` 等常量复制到业务文件，统一引用 `@/config/website`。
10. **场景图标/配色**：必须复用 [util/scene-style.js](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/src/util/scene-style.js) `getSceneStyle(sceneCode, sceneName)`，保证 dashboard / templates / generate 等页面展示一致。
11. **SSE 流式**：新增流式接口复用 [util/sse-client.js](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/src/util/sse-client.js)，事件协议与后端对齐（`step`/`done`/`error`）；Mock 阶段抛 `MOCK_UNSUPPORTED` 由调用方回退。
12. **代码风格**：2 空格、单引号、无分号、文件尾空行、中文注释；改动完成后执行 `npm run lint` 自检。
13. **不确定处先问**：不要臆造后端接口、菜单字段或环境变量；后端契约以 [mock/sxkApi.js](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/src/mock/sxkApi.js) 真实链路分支与 [website.js](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/src/config/website.js) 为准。

---

## 11. 待确认项（基于假设，需人工核实）

1. **`.env.prod` / `.env.test` 的 `VITE_API_TARGET` 为空**：生产/测试构建后请求路径如何路由到后端（同源？网关？）需部署方确认。当前两文件 `VITE_API_TARGET` 留空，由部署/CI 注入或经 nginx 网关反代 `/api/*`。
2. **`.env.dev` 中 `VITE_API_TARGET=http://localhost:8000`**：为本地后端 FastAPI 服务地址，启动后端服务前请勿提交实际域名。
3. **Node 版本未约束**：无 `engines` / `.nvmrc`，Vite 6 要求 Node 18+，请确认团队统一版本。
4. **后端版本与契约**：后端 FastAPI 服务版本、字段完整契约（如 `User.is_admin`、`agent_trace` 元素结构、`issues` 字符串数组）需后端确认。当前前端通过 [mock/sxkApi.js](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/src/mock/sxkApi.js) 的 `adapt*` 函数对齐，后续字段变更需同步更新适配层。
5. **测试体系缺失**：未检测到任何测试框架（jest/vitest/cypress）与 `*.test.*` 文件，`package.json` 也无 `test` 脚本。若需补测试，建议引入 Vitest。
6. **Mock 残留**：`src/mock/*` 与 `VITE_APP_USE_MOCK_AUTH` / `VITE_APP_USE_MOCK_BIZ` 用于后端未启阶段。当前 `.env.dev` 均已置 `false`（切真实链路），但 `src/mock/` 目录仍保留作为双轨兜底。后端稳定后可考虑移除。
7. **CI/CD 与容器化**：仓库无相关配置，部署链路需运维确认。
8. **`refresh_token` 管理方式**：[util/auth.js](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/src/util/auth.js) 用 js-cookie 存储 `sxk-refresh-token`；生产是否应改为 HttpOnly Cookie 由后端 `Set-Cookie` 管理，需安全团队确认。
9. **`website.redirectUri` 端口不一致**：[website.js](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/src/config/website.js#L53) 写的是 `http://localhost:52400`，但 `.env.dev` 实际端口已改为 `53200`，社交登录未启用，建议同步。
10. **`getButtons()` 实际未调用**：[store/modules/user.js](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/src/store/modules/user.js#L314-L322) 定义了按钮权限获取，但 `initSxkMenu()` 路径未调用 `getMenu()` → `getButtons()`，导致 `userStore.permission` 实际始终为空。按钮级权限是否启用需产品确认。
