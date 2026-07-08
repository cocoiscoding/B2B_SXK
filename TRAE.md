# B2B-SXK-ManageGF — 项目上下文

> 一句话定位：基于 Vue 3 + Element Plus 的「神行库」产品营销 AI 平台前端，为产品知识库管理、多 Agent 营销内容生成、竞品对比分析及多渠道文案适配提供管理后台交互界面。
> 本文件由 `project-init-context` skill 基于代码现状自动生成，供人类开发者与 AI Agent 共享。后端为独立的 BladeX 框架服务，本仓库仅含前端。

---

## 1. 技术栈

| 层 | 技术 | 版本（取自 [package.json](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/package.json)） |
|----|------|------|
| 框架 | Vue 3（Composition API，`<script setup>`） | ^3.5.13 |
| 路由 | Vue Router（Hash 模式） | ^4.5.0 |
| 状态管理 | Pinia（4 个 module） | ^2.3.0 |
| 国际化 | Vue I18n（zh / en，默认 zh） | ^10.0.5 |
| 构建 | Vite | ^6.0.5 |
| UI 库 | Element Plus + `@element-plus/icons-vue`（按需自动导入） | ^2.9.1 / ^2.3.1 |
| HTTP | axios（统一封装拦截器） | ^1.7.9 |
| 工具库 | `crypto-js`、`js-base64`、`js-cookie`、`js-md5`、`nprogress`、`@vueuse/core` | — |
| 样式 | SCSS（全局变量自动注入 `@/styles/variables.scss`） | sass ^1.83.0 |
| 自动导入 | `unplugin-auto-import` + `unplugin-vue-components`（ElementPlusResolver） | — |
| Lint | ESLint + `eslint-plugin-vue` | ^8.57.1 / ^9.32.0 |
| 包管理器 | npm（仓库存在 `package-lock.json`） | — |
| 模块系统 | ES Module（`"type": "module"`） | — |
| 后端（独立部署） | BladeX（OAuth2，接口前缀 `/api/blade-*`，Token 头 `Blade-Auth`） | 待确认 |

> 未声明 Node 版本约束（无 `engines` / `.nvmrc`），建议使用 Node 18+ 以适配 Vite 6。

---

## 2. 项目结构

前端单体项目（前后端分离的前端部分），顶层结构如下：

```
B2B-SXK-ManageGF/
├── index.html               # HTML 入口（标题：管理系统）
├── package.json             # 依赖与脚本
├── vite.config.js           # Vite 配置（别名 @ → src、代理、按需导入、手动分包）
├── .env / .env.dev / .env.prod / .env.test   # 多环境变量
├── .editorconfig            # 编辑器统一配置
├── src/
│   ├── main.js              # 应用入口
│   ├── App.vue              # 根组件（仅 <router-view/>）
│   ├── permission.js        # 路由全局守卫（鉴权 + 标签页维护）
│   ├── cache.js             # keepAlive 缓存配置
│   ├── api/                 # API 请求封装（按业务域拆分）
│   │   ├── user.js          # 鉴权/用户（登录、刷新、登出、验证码、用户信息）
│   │   ├── common.js        # 通用 API（字典等示例）
│   │   └── system/menu.js   # 菜单（顶部菜单、动态路由、按钮权限）
│   ├── components/          # 全局基础组件（basic-container / basic-block / error-page / iframe）
│   ├── config/
│   │   ├── env.js           # baseUrl、iconfont、环境判定
│   │   └── website.js       # 全站常量（标题、clientId/Secret、租户、tokenHeader 等）
│   ├── lang/                # i18n（index.js + zh.js + en.js）
│   ├── page/                # 页面级布局与免鉴权页（index 布局 / login / register / lock）
│   ├── router/
│   │   ├── router.js        # 路由实例 + 动态路由注入 + 重置
│   │   ├── axios.js         # axios 实例与全局拦截器（重点文件）
│   │   ├── page/index.js    # 页面路由（登录/注册/锁屏/错误页/首页重定向）
│   │   └── views/index.js   # 业务视图路由
│   ├── store/               # Pinia
│   │   ├── index.js         # createPinia
│   │   └── modules/         # user / common / tags / logs
│   ├── styles/              # 全局 SCSS（variables / common / layout / login / normalize）
│   ├── util/                # 工具（auth / crypto / store / util / validate / date / admin）
│   └── views/               # 业务视图（system/userinfo、workbenches）
└── .trae/skills/            # Trae 技能定义（与业务代码无关）
```

---

## 3. 常用命令（执行目录：项目根）

| 场景 | 命令 | 说明 |
|------|------|------|
| 安装依赖 | `npm install` | 使用 npm（仓库带 `package-lock.json`） |
| 本地开发（默认 dev） | `npm run dev` | `vite --mode dev`，端口取 `VITE_PORT`（默认 52400），`/api` 代理到 `VITE_API_TARGET`（默认 `http://localhost:8080`） |
| 本地开发（local） | `npm run dev:local` | `vite --mode local`（**注意：仓库无 `.env.local`，待确认**） |
| 本地开发（gdccs） | `npm run dev:gdccs` | `vite --mode gdccs`（**注意：仓库无 `.env.gdccs`，待确认**） |
| 生产构建（默认） | `npm run build` | `vite build` |
| 生产构建（gdccs） | `npm run build:gdccs` | `vite build --mode gdccs` |
| 生产构建（prod） | `npm run build:prod` | `vite build --mode prod` |
| 预览构建产物 | `npm run preview` | `vite preview` |
| Lint 修复 | `npm run lint` | `eslint . --ext .vue,.js,.jsx,.cjs,.mjs --fix` |

构建产物输出到 `dist/`，手动分包：`vue`（vue+router+pinia）、`element`（element-plus+icons）。

---

## 4. 架构与代码组织

**分层**：典型的中后端驱动前端（Saber/Avue 风格）— `views/(业务视图) → api/(请求) → router/axios.js(统一 http) → 后端 BladeX`。

**入口与装配**（[src/main.js](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/src/main.js)）：
- `createApp(App)` → 依次 `use(pinia)`、`use(router)`、`use(i18n)`、`use(ElementPlus, { locale: zhCn })`
- 全局注册 `basicContainer`、`basicBlock` 组件
- 注入全局属性 `website`、`baseUrl`
- 动态加载阿里 iconfont
- 引入 `./permission` 启动路由守卫
- **注意**：`main.js` 引用了 `basicContainer` / `basicBlock` 但未显式 import（依赖自动导入或隐式全局），见「待确认项」。

**布局**（[src/page/index/index.vue](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/src/page/index/index.vue)）：`header(Top) + left(Sidebar) + Tags + router-view`，根据 `route.meta.keepAlive` 决定是否 `keep-alive`。

**路由**（[src/router/router.js](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/src/router/router.js)）：Hash 模式，由 `PageRouter`（免鉴权页）+ `ViewsRouter`（业务页）组成；提供 `addDynamicRoutes`（动态注入后端菜单）与 `resetRouter`（登出重置）。`meta` 约定：`keepAlive` / `isTab` / `isAuth` / `menu`。

**鉴权链路**（端到端示例）：
1. [login/index.vue](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/src/page/login/index.vue) 表单 → `userStore.loginByUsername()`
2. [store/modules/user.js](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/src/store/modules/user.js) → 调 [api/user.js](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/src/api/user.js) `loginByUsername`（密码经 `md5` 后再 AES 加密）
3. [router/axios.js](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/src/router/axios.js) 拦截器：自动拼 `baseUrl`、加 `Authorization: Basic <clientId:clientSecret>`、加 `Blade-Auth: <token>`
4. 成功 → `setToken`（Cookie `saber-access-token`）+ `setStore`（sessionStorage `saber-*`）
5. [permission.js](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/src/permission.js) `beforeEach`：无 token 跳 `/login`；有 token 但 store 中 token 空 → `fedLogOut`；否则维护 Tags 放行
6. 进入首页后 `getTopMenu` + `getRoutes` 拉取菜单，`addDynamicRoutes` 注入动态路由，`getButtons` 拉取按钮权限码

**状态管理分工**：
- `user`：token / refreshToken / userInfo / roles / menu / menuAll / permission（按钮权限码 map）
- `common`：语言、主题、锁屏、折叠、全屏、屏幕尺寸等 UI 状态
- `tags`：标签页导航（增删、当前标签）
- `logs`：前端日志列表

**路径别名**：`@` → `./src`（定义于 [vite.config.js](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/vite.config.js#L18)）。**所有 import 必须使用 `@/`，禁止相对路径硬编码。**

**数据持久化**：token/refreshToken 存 Cookie（[util/auth.js](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/src/util/auth.js)）；其余状态存 sessionStorage，key 统一加前缀 `saber-`（[util/store.js](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/src/util/store.js)）。

---

## 5. 编码规范

- **Linter / Formatter**：`npm run lint`（ESLint 8 + eslint-plugin-vue，`--fix` 自动修复）。**仓库未发现 `.eslintrc*` 配置文件，lint 实际生效规则待确认**（见待确认项）。
- **缩进 / 引号 / 分号**：依 [.editorconfig](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/.editorconfig) — UTF-8、2 空格缩进、LF 换行、文件尾插入空行、去除行尾空白（`.md` 除外）。代码普遍使用单引号、无分号（抽样既有代码得出）。
- **样式**：SCSS，组件内 `<style lang="scss" scoped>`；全局样式入口 `src/styles/common.scss` / `layout.scss` / `login.scss`，变量文件 `variables.scss` 由 Vite 自动 `@use` 注入，**无需在各文件手动 import**。
- **组件**：Element Plus 组件通过 `unplugin-vue-components` **按需自动注册**，模板中直接使用 `<el-*>`，无需手动 import；`@element-plus/icons-vue` 图标需显式 import。
- **命名约定**（抽样观察）：
  - 目录与 `.vue` / `.js` 文件：小写（`login/index.vue`、`basic-container/main.vue`）
  - 全局组件注册名：camelCase（`basicContainer`、`basicBlock`）
  - Store 模块：小写单词（`user`、`common`、`tags`、`logs`）
  - API 函数：camelCase（`loginByUsername`、`getTopMenu`）
  - 业务常量：camelCase 对象（`website`）
- **注释语言**：中文（`/** ... */` 与行内注释）。
- **提交规范**：仓库未配置 `commitlint` / `husky`，无强制约定。

---

## 6. 数据与 API

- **前端无数据库**；所有数据来自后端 BladeX 服务。
- **API 风格**：REST，统一前缀 `/api/blade-*`。
  - 鉴权：`/api/blade-auth/oauth/{token, captcha, user-info, logout}`
  - 系统：`/api/blade-system/menu/{top-menu, routes, buttons}`、`/api/blade-system/dict/dictionary`
- **请求封装**：所有请求经 [src/router/axios.js](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/src/router/axios.js) 默认 axios 实例，约定：
  - 超时 60s，`withCredentials` 开启
  - 请求拦截：自动加 `baseUrl`、`Authorization: Basic`、`Blade-Auth` token（除非 `config.meta.isToken === false`）
  - 响应拦截：`status !== 200` 统一 `ElMessage` 报错；`401` 触发 `refreshToken`，失败则 `fedLogOut` 跳 `/login`
  - 自定义 `config.meta`：`isToken`（是否带 token）、`isSerialize`（表单序列化）；`config.text === true` 设 `Content-Type: text/plain`
- **DTO 校验**：前端用 Element Plus `el-form` rules（如登录页 [user/password required](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/src/page/login/index.vue#L83-L86)），无 zod/joi/class-validator。
- **接口文档**：前端仓库内未发现 Swagger/OpenAPI；需查阅后端 BladeX 服务。
- **加密**：密码经 `js-md5` 后再 AES-CBC 加密（固定 key/iv，见 [util/crypto.js](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/src/util/crypto.js#L6-L7)）。

---

## 7. 环境变量

Vite 环境变量必须以 `VITE_` 为前缀才能注入前端。文件分布：

| 变量 | 来源 | 示例 / 默认 | 说明 |
|------|------|------------|------|
| `VITE_APP_TITLE` | [.env](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/.env) | `管理系统` | 全站标题（基础共享） |
| `VITE_APP_ENV` | .env.dev/prod/test | `dev` / `prod` / `test` | 环境标识 |
| `VITE_PORT` | [.env.dev](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/.env.dev) | `52400` | dev server 端口 |
| `VITE_API_TARGET` | .env.dev/prod/test | dev=`http://localhost:8080` | dev 代理目标；**prod/test 当前为空**（待确认） |

- 开发态 `baseUrl = '/api'`（走 Vite proxy）；生产态 `baseUrl = ''`（同源直连，见 [config/env.js](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/src/config/env.js)）。
- 全局敏感常量集中在 [config/website.js](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/src/config/website.js)：`clientId='saber'`、`clientSecret='saber_secret'`、`tokenHeader='Blade-Auth'`、`tenantId='000000'`、`captchaMode=true`。**`clientSecret` 硬编码在前端，属安全隐患，建议核实后端是否启用公私钥或网关层加固。**

---

## 8. 部署

- **容器化**：仓库未发现 `Dockerfile` / `docker-compose.yml`。
- **CI/CD**：未发现 `.github/workflows/` / `.gitlab-ci.yml` / `Jenkinsfile`。
- **目标环境**：构建为静态资源（`dist/`），部署到任意静态服务器 / 反向代理；生产态请求需由部署层（nginx 等）将 `/api/blade-*` 转发到后端 BladeX 服务（因 `baseUrl` 生产为空，需同源或网关统一）。
- **多环境构建模式**：`dev` / `local` / `gdccs` / `prod` / `test`，但 `local` 与 `gdccs` 对应的 `.env.*` 文件缺失（待确认）。

---

## 9. 业务领域（简要）

- **产品定位**：「神行库」产品营销 AI 平台管理后台。
- **规划能力**（依 [README.md](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/README.md)）：产品知识库管理、多 Agent 营销内容生成、竞品对比分析、多渠道文案适配。
- **当前实现进度**：仅完成框架与基础页面——登录/注册/锁屏、首页布局、工作台仪表盘（[workbenches/index.vue](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/src/views/workbenches/index.vue)）、个人信息（[system/userinfo.vue](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/src/views/system/userinfo.vue)）。README 所述核心业务视图尚未落地。
- **领域术语**：租户（tenant）、部门（dept）、角色（role）、菜单（menu，含 top-menu/routes）、按钮权限（buttons/permission code）、验证码（captcha）、租户模式 / 部门切换模式 / 验证码模式。
- **权限模型**：RBAC + 按钮级权限码（`userStore.permission[code] === true`，通过 `getButtons` 拉取）+ 多租户（`tenantId`，`website.tenantMode` 当前关闭）。
- **关键流程**：登录（账密/验证码）→ 下发 access_token + refresh_token → 拉顶部菜单 → 拉路由菜单 → 动态注册路由 → 拉按钮权限 → 进入业务页。

---

## 9.x 神行库业务前端实现（Phase 4 — Mock 数据驱动）

> **背景**：后端 BladeX 服务尚未开发，前端采用 Mock 数据驱动开发。接口命名、字段、错误码均与《神行库_接口设计文档 v1.1》保持一致，后端就绪后仅替换 `src/mock/sxkApi.js` 实现即可。
> **配套文档**（仓库外）：
> - 原型 `SXK.html`
> - `神行库_产品需求文档.md`
> - `神行库_接口设计文档.md`
> - `神行库_数据库设计文档.md`

### 9.x.1 业务路由表（已注册）

| 路径 | 文件 | 说明 |
|------|------|------|
| `/dashboard/index` | [views/sxk/dashboard/index.vue](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/src/views/sxk/dashboard/index.vue) | 首页：4 张统计卡 + 常用模板 + 最近生成 |
| `/knowledge/index` | [views/sxk/knowledge/index.vue](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/src/views/sxk/knowledge/index.vue) | 产品知识库：CRUD + 关键词高亮 |
| `/generate/index` | [views/sxk/generate/index.vue](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/src/views/sxk/generate/index.vue) | 内容生成：左配置 + 右 4 Tab（编辑/Agent/渠道/对比） |
| `/history/index` | [views/sxk/history/index.vue](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/src/views/sxk/history/index.vue) | 生成历史：表格 + 详情/重编辑/删除 |
| `/templates/index` | [views/sxk/templates/index.vue](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/src/views/sxk/templates/index.vue) | 模板管理：列表 + 详情/创建 |

### 9.x.2 关键基础设施

- **Mock 数据集**：[src/mock/data.js](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/src/mock/data.js)
  - 6 个产品 / 7 个模板 / 5 条生成历史 / 单版本内容 / Agent 思考链 / 校验问题 / Dashboard 统计
- **Mock API 封装**：[src/mock/sxkApi.js](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/src/mock/sxkApi.js)
  - 方法命名严格对齐接口文档资源路径（`getDashboardStats` / `listProducts` / `triggerGeneration` 等）
  - 全部返回 `{ code, msg, data, trace_id }`，兼容现有 axios 拦截器
  - 业务校验示例：`4091 重名` / `4006 内容块为空` / `4042 已删除`
- **登录后菜单注入**：[store/modules/user.js](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/src/store/modules/user.js) `initSxkMenu()`
  - 绕过 `/blade-system/menu/routes`，直接写入 5 个 SXK 业务菜单
- **可复用组件**：
  - [components/basic-block/main.vue](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/src/components/basic-block/main.vue) — 扩展了 `header`/`aside` 插槽与 `hoverShadow`/`padding` props
  - [components/tag-input/index.vue](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/src/components/tag-input/index.vue) — 通用标签输入器（回车/失焦提交、删除、backspace）

### 9.x.3 业务字段规范

- **统一响应壳**：`{ code: 0, msg: 'ok', data, trace_id }`
- **API 路径前缀**：`/api/sxk/...`（按接口文档 2.6 白名单约定）
- **业务规则代号**：BR-K-XX（产品）/ BR-G-XX（生成）/ BR-H-XX（历史）/ BR-T-XX（模板）/ BR-A-XX（认证）
- **场景代号**：`product_intro` / `competitor` / `channel_adapt` / `email` / `event` / `other` / `custom`
- **Agent 协作流（默认 4 节点）**：retrieval → generation → channel_adapt → validation
- **Agent 协作流（竞品 4 节点）**：retrieval → competitor_analysis → generation → validation

---

## 10. AI 协作约定（写给 AI Agent）

### 10.1 已知陷阱（Known Pitfalls）

以下为本项目实际踩过/已确认的风险点，AI Agent 编写代码前必须先确认是否命中：

1. **自定义全局组件不会自动导入**：`unplugin-vue-components` 仅配置了 `ElementPlusResolver`，对 `src/components/` 下的自定义组件（`basic-container`、`basic-block` 等）**不会自动注册**。在 `main.js` 中如需 `app.component('basicContainer', ...)`，必须先显式 `import` 对应的 `.vue` 文件，否则启动报「Unknown custom element」。
2. **生产/测试 `VITE_API_TARGET` 为空**：`prod` / `test` / `gdccs` 模式下 `VITE_API_TARGET` 仅为占位空值，`baseUrl` 生产态又为空，**请求会发往同源**。任何新增/修改的接口默认走 `/api`，必须由部署层（nginx / 网关）将 `/api/blade-*` 反代到 BladeX，否则 404。不要在代码里假设后端域名。
3. **`sessionStorage` 不跨标签页共享**：所有非 token 状态（userInfo / menu / permission / language）存于 `sessionStorage`，新标签页打开会触发「有 cookie 但 store 为空 → fedLogOut」分支。若 AI 需要「跨标签同步」逻辑，请改用 `localStorage` 或 `BroadcastChannel`，不要硬塞进 `util/store.js`。
4. **`userStore.delAllTag()` / `clearLock()` 历史上为空实现**：早期版本这两个方法只占位未真正调用 `tags` / `common` store。若 AI 在 `permission.js` 里直接调用会看似生效、实则不生效。当前已通过动态 `import` 委托修复，新增登出/锁屏流程时**必须沿用动态 import 写法**，不要 `import` 静态 store 模块（避免循环依赖）。
5. **`crypto-js` 的 AES key/iv 是固定常量**：见 `src/util/crypto.js` 中的硬编码 key/iv，**仅用于前端密码传输的二次混淆**，不是安全存储。任何「把 token / refreshToken 用 AES 加密再存」的需求都属过度设计，直接复用 `util/auth.js` 的 Cookie 工具即可。
6. **按钮权限判定依赖后端下发的 `permission` map**：UI 上 `v-if="$store.state.user.permission['btn_xxx']"` 仅当 `getButtons` 接口被调用且返回该 code 时才生效。AI 不要在前端硬编码权限码，权限码以 `website.js` / `api/system/menu.js` 的契约为准。
7. **不要新增 `.env.*` 文件而不补 `.gitignore`**：本仓库 `.env.local` / `.env.gdccs` 等已确认由部署/CI 注入；若 AI 必须新增，请同步在 `.gitignore` 中忽略，避免真实后端域名泄露到公开仓库。
8. **菜单路径必须含 `/index` 后缀**：`src/store/modules/user.js` 的 `initSxkMenu()` 写入的 5 个菜单项均为 `/dashboard/index` / `/knowledge/index` / `/generate/index` / `/history/index` / `/templates/index`，与 [src/router/views/index.js](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/src/router/views/index.js) 中注册的 `child.path` 一致。**不要省略 `/index`，否则侧边栏点击会跳到 `/dashboard` 但 router 找不到匹配路由而落到 `redirect: /workbenches/index` 的旧逻辑。**
9. **`sxkApi` 返回的是「AxiosResponse 形态」而不是裸 `data`**：Mock 实现中每个方法 `return delay().then(() => ok(...))`，其中 `ok()` 是 `{code, msg, data, trace_id}`，**业务页面必须读取 `resp.data.xxx`**（即 `resp.data.items` / `resp.data.total`），不要直接 `resp.items`。
10. **Generate 页用了 `document.execCommand` 做轻量富文本**：仅用于演示阶段，生产可替换为 Tiptap / Quill。**注意**：`execCmd('formatBlock', 'H2')` 第二个参数必须是字符串字面量，**不能** 走 reactive 变量（浏览器不会动态解析）。另外 `editorRef` 是 `<div contenteditable>`，赋值请用 `innerHTML` 而不是 `v-model`，否则 Vue 会把 HTML 当文本。
11. **Agent 协作轮询为前端模拟**：[views/sxk/generate/index.vue](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/src/views/sxk/generate/index.vue) `startAgentPolling()` 用 `setTimeout` 把每个 Agent 节点从 `pending → running → success` 推进，仅为视觉演示。**真实实现应改为 SSE / WebSocket**（按接口文档 4.6.8 `GET /generations/{id}/agents` 长连接），不要在生产代码里保留这个轮询。
12. **`getSceneSchemas()` 返回的 `params` 字段是「字段定义」而不是「字段值」**：`mockSceneSchemas` 中 `params[i].default` 是默认值，业务页面要遍历 schema 渲染表单，**不要把整个 `params` 数组直接 `v-model`**。当前 Generate 页使用 `applySceneDefaults()` 把 schema 默认值复制到 `form.params` 后再双向绑定。
13. **模板 `is_custom` 默认 `false`**：系统预置模板（`mockTemplates` 中前 6 条）均为 `is_custom: false`，仅当用户通过 `sxkApi.createTemplate()` 创建时才置 `true`。**模板列表页筛选「我的模板」时务必传 `is_custom: true`**，不要把系统模板一并返回。
14. **Phase 4 登录链路 Mock 短路**：[.env.dev](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/.env.dev) 中 `VITE_APP_USE_MOCK_AUTH=true` 时，[store/modules/user.js](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/src/store/modules/user.js) `loginByUsername()` 会**完全跳过** BladeX `/api/blade-auth/oauth/token`，仅做"用户名+密码非空"和"验证码与本地缓存一致"校验后伪造 `access_token` 直接进入业务页。**生产环境务必移除该环境变量或置 `false`**，否则鉴权完全失效。
   - 配套短路：[api/user.js](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/src/api/user.js) 中 `loginByUsername` / `loginBySocial` / `refreshToken` / `getButtons` / `logout` / `getUserInfo` 共 6 个函数均在 `MOCK_AUTH` 开启时返回本地 `ok()` 响应壳，避免任何路径意外触发 `/api/blade-auth/*` 或 `/api/blade-system/*` 导致 ECONNREFUSED。
   - 配套短路：[api/system/menu.js](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/src/api/system/menu.js) 中 `getTopMenu` / `getRoutes` 同样在 `MOCK_AUTH` 开启时短路返回空数组（真实菜单由 `initSxkMenu()` 注入）。
15. **本地 SVG 验证码仅前端演示**：[util/svg-captcha.js](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/src/util/svg-captcha.js) 把生成时的正确答案返回到 login 页并写入 `sessionStorage('sxk-captcha-text')`，**客户端比对 = 0 安全意义**。后端就绪后应删除整个文件 + 恢复 `api/user.js` 中的真实 `getCaptcha` 实现，并在后端做权威校验。
16. **`vite.config.js` 已关闭全局组件自动注册**：`Components({ dirs: [], deep: false, dts: false })` 仅按需注册 ElementPlus。**所有 `src/components/*` 下的组件必须显式 `import` 后再使用**，不要在模板里直接写 `<basic-block>` 而不 import（不会被自动注册，会报「Unknown custom element」）。
17. **端口冲突 → 52400 报 404**：开发期 `localhost:52400` 出现 404 时，**优先检查端口是否被占用**（Vite 启动日志 `Port 52400 is in use, trying another one...` 会自动落到 52401+），不是 vite.config / 路由问题。需 `netstat -ano | findstr 52400` + `taskkill /PID <pid> /F` 后重启 `npm run dev`。其他可能：浏览器缓存（强刷）、网络代理拦截。
18. **项目独立性约束**：神行库独立部署，使用 `sxk` 前缀（`clientId='sxk'`、`TokenKey='sxk-access-token'`、`ssoUrl/authUrl` 指向 SXK 自己的 BladeX 服务）。**严禁再把其他同源业务系统（B2B-HGSH 等）的 clientId / tokenKey / 注释直接复制进来**；新增 `.env.*` 时只保留 `dev / test / prod` 三套，不引入 `local / gdccs` 等业务无关的 mode。

### 10.2 编码与工程约束（Operational Rules）

1. **import 必须使用 `@/` 别名**，禁止 `../../` 相对路径（别名见 [vite.config.js](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/vite.config.js#L17-L19)）。
2. **新增 API**：在 `src/api/<业务域>.js` 内导出函数，统一调用 `@/router/axios` 的 `request`；URL 以 `/api/blade-*` 开头；不要在业务组件里直接 `import axios`。
3. **新增业务视图**：放在 `src/views/<模块>/`，并在 [src/router/views/index.js](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/src/router/views/index.js) 注册路由，使用 `Layout` 父级；`meta` 必填语义（`keepAlive` / `isTab` / `isAuth`）。
4. **Element Plus 组件**：模板直接写 `<el-*>`，**不要**手动 import 组件；图标 `@element-plus/icons-vue` 需显式 import。
5. **状态管理**：跨页共享状态写 Pinia store（`src/store/modules/`），不要滥用全局属性；持久化用 `@/util/store`（sessionStorage，自动加 `saber-` 前缀），token 类用 `@/util/auth`（Cookie）。
6. **样式**：组件内 `<style lang="scss" scoped>`；变量直接使用 `variables.scss` 中的值（已自动注入），不要再 `@import`。
7. **鉴权**：免 token 请求需在 request 配置里加 `meta: { isToken: false }`；新增需登录的页面**不要**加 `meta.isAuth = false`。
8. **密码 / 敏感数据**：复用 [util/crypto.js](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/src/util/crypto.js) 与 [util/auth.js](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/src/util/auth.js)，不要自造加密逻辑；不要把 `clientSecret` 等常量复制到业务文件，统一引用 `@/config/website`。
9. **代码风格**：2 空格、单引号、无分号、文件尾空行、中文注释；改动完成后执行 `npm run lint` 自检。
10. **不确定处先问**：不要臆造后端接口、菜单字段或环境变量；后端契约以 [api/](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/src/api) 现有调用与 [website.js](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/src/config/website.js) `menu.props` 字段映射为准。

---

## 11. 待确认项（基于假设，需人工核实）

1. **`.env.prod` / `.env.test` 的 `VITE_API_TARGET` 为空**：生产/测试构建后请求路径如何路由到后端（同源？网关？）需部署方确认。当前两文件 `VITE_API_TARGET` 留空，由部署/CI 注入或经 nginx 网关反代 `/api/blade-*`。
2. **`.env.dev` 中 `VITE_API_TARGET=http://localhost:8080`**：仅为本地 BladeX 服务占位值，启动 BladeX 后端前请勿提交实际域名。
3. **ESLint 规则**：仓库使用 [eslint-plugin-vue v9](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/.eslintrc.cjs) + `vue3-recommended`，`vue/multi-word-component-names: 'off'`（sxk 模块下含单/双字业务组件，如 `basic-block`）。生产环境禁 `console`/`debugger`。
4. **Node 版本未约束**：无 `engines` / `.nvmrc`，Vite 6 要求 Node 18+，请确认团队统一版本。
5. **后端版本与契约**：BladeX 后端版本、是否启用租户模式、`clientSecret` 是否为前端可见值，需后端确认。当前 `clientSecret='sxk_secret'` 为本地占位，生产前必须由部署/CI 注入或移至网关鉴权。
6. **测试体系缺失**：未检测到任何测试框架（jest/vitest/cypress）与 `*.test.*` 文件，`package.json` 也无 `test` 脚本。若需补测试，建议引入 Vitest。
7. **Phase 4 残留**：`src/mock/*` 与 `VITE_APP_USE_MOCK_AUTH=true` 仅用于后端未启阶段。后端 BladeX 服务就绪后应：删除 `src/mock/` 目录 + 还原 `api/user.js` / `api/system/menu.js` 真实 `request()` 链路 + `.env.dev` 中 `VITE_APP_USE_MOCK_AUTH` 置 `false`。
8. **CI/CD 与容器化**：仓库无相关配置，部署链路需运维确认。
9. **`permission.js` 中 `userStore.delAllTag()` / `clearLock()` 在 user store 内为空实现**（[store/modules/user.js:260-265](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/src/store/modules/user.js#L260-L265)），登录后清标签/清锁屏实际未生效。**已修**：使用动态 `import('@/store/modules/tags')` / `import('@/store/modules/common')` 跨模块委托，避免循环依赖。
10. **登录页验证码 URL 重复拼接 `/api`**：[login/index.vue:90](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/src/page/login/index.vue#L90) 原写 `${baseUrl}/api/blade-auth/...`，而 `baseUrl` 开发态本身就是 `/api`，导致路径变成 `/api/api/...`，被 Vite proxy 转发到 `http://localhost:8080/api/api/...`（无此端点）→ `ECONNREFUSED`。**已修**：去掉重复 `/api`，改为 `${baseUrl}/blade-auth/...`。同类问题需在所有"模板字符串直接拼 baseUrl"处警惕。
