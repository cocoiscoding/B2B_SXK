# B2B-SXK-ManageGF — 项目上下文

> 一句话定位：基于 Vue 3 + Element Plus 的「神行库」产品营销 AI 平台前端，为产品知识库管理、多 Agent 营销内容生成、竞品对比分析及多渠道文案适配提供管理后台交互界面。
> 本文件由 `project-init-context` skill 基于代码现状自动生成，供人类开发者与 AI Agent 共享。后端为独立服务（SXK 原生 `/api/sxk/*` + BladeX 兼容层 `/api/blade-*`），本仓库仅含前端。

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
| Lint | ESLint 8 + `eslint-plugin-vue`（配置见 [.eslintrc.cjs](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/.eslintrc.cjs)） | ^8.57.1 / ^9.32.0 |
| 包管理器 | npm（仓库存在 `package-lock.json`） | — |
| 模块系统 | ES Module（`"type": "module"`） | — |
| 后端（独立部署） | SXK 原生 API（`/api/sxk/*`，统一响应壳 `{code,msg,data,trace_id}`）+ BladeX 兼容层（`/api/blade-*`，Token 头 `Blade-Auth`） | 待确认 |

> 未声明 Node 版本约束（无 `engines` / `.nvmrc`），Vite 6 要求 Node 18+，建议团队统一 Node 18+。

---

## 2. 项目结构

前端单体项目（前后端分离的前端部分），顶层结构如下：

```
B2B-SXK-ManageGF/
├── index.html               # HTML 入口（标题：神行库 · 营销 AI）
├── package.json             # 依赖与脚本
├── vite.config.js           # Vite 配置（别名 @ → src、代理、按需导入、手动分包）
├── .env / .env.dev / .env.prod / .env.test   # 多环境变量
├── .editorconfig            # 编辑器统一配置
├── .eslintrc.cjs            # ESLint 配置（eslint:recommended + vue3-recommended）
├── .gitignore               # 忽略 node_modules/dist/.trae/.env.local/接口清单md 等
├── src/
│   ├── main.js              # 应用入口（装配 pinia/router/i18n/ElementPlus，注册全局组件）
│   ├── App.vue              # 根组件（仅 <router-view/>）
│   ├── permission.js        # 路由全局守卫（鉴权 + 标签页维护）
│   ├── cache.js             # keepAlive 缓存配置
│   ├── api/                 # API 请求封装（按业务域拆分）
│   │   ├── user.js          # 鉴权/用户（登录、注册、刷新、登出、验证码、用户信息）
│   │   ├── common.js        # 通用 API（字典等示例）
│   │   └── system/menu.js   # 菜单（顶部菜单、动态路由、按钮权限）
│   ├── components/          # 全局基础组件（basic-container / basic-block / error-page / iframe / tag-input）
│   ├── config/
│   │   ├── env.js           # baseUrl、iconfont、环境判定
│   │   └── website.js       # 全站常量（标题、clientId/Secret、租户、tokenHeader 等）
│   ├── lang/                # i18n（index.js + zh.js + en.js）
│   ├── mock/                # Mock 数据层（后端未启期间短路）
│   │   ├── data.js          # 业务 Mock 数据集（产品/模板/生成/Agent 等）
│   │   └── sxkApi.js        # 业务 Mock API 封装（双轨开关 USE_MOCK_BIZ）
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
│   ├── util/                # 工具（auth / crypto / store / util / validate / date / admin / svg-captcha）
│   └── views/               # 业务视图
│       ├── sxk/             # 神行库 5 大业务页面（dashboard/generate/history/knowledge/templates）
│       ├── system/userinfo.vue   # 个人信息
│       └── workbenches/index.vue # 旧工作台入口
└── .trae/skills/            # Trae 技能定义（与业务代码无关）
```

---

## 3. 常用命令（执行目录：项目根）

> 实际 scripts 取自 [package.json](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/package.json#L6-L12)，仅以下 5 个，**无** `dev:local` / `dev:gdccs` / `build:gdccs`。

| 场景 | 命令 | 说明 |
|------|------|------|
| 安装依赖 | `npm install` | 使用 npm（仓库带 `package-lock.json`） |
| 本地开发 | `npm run dev` | `vite --mode dev`，端口取 `VITE_PORT`（默认 52400），`/api` 代理到 `VITE_API_TARGET`（当前 `http://localhost:8000`） |
| 生产构建（默认） | `npm run build` | `vite build` |
| 生产构建（prod） | `npm run build:prod` | `vite build --mode prod` |
| 预览构建产物 | `npm run preview` | `vite preview` |
| Lint 修复 | `npm run lint` | `eslint . --ext .vue,.js,.jsx,.cjs,.mjs --fix --ignore-path .gitignore` |

构建产物输出到 `dist/`，手动分包：`vue`（vue+router+pinia）、`element`（element-plus+icons）。

---

## 4. 架构与代码组织

**分层**：典型的中后端驱动前端（Saber/Avue 风格）— `views/(业务视图) → api/ 或 mock/(请求) → router/axios.js(统一 http) → 后端`。

**入口与装配**（[src/main.js](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/src/main.js)）：
- `createApp(App)` → 依次 `use(pinia)`、`use(router)`、`use(i18n)`、`use(ElementPlus, { locale: zhCn })`
- 显式 `import` 后注册全局组件 `basicContainer`、`basicBlock`
- 注入全局属性 `website`、`baseUrl`
- 动态加载阿里 iconfont
- 引入 `./permission` 启动路由守卫

**布局**（[src/page/index/index.vue](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/src/page/index/index.vue)）：`header(Top) + left(Sidebar) + Tags + router-view`，根据 `route.meta.keepAlive` 决定是否 `keep-alive`。

**路由**（[src/router/router.js](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/src/router/router.js)）：Hash 模式，由 `PageRouter`（免鉴权页）+ `ViewsRouter`（业务页）组成；提供 `addDynamicRoutes`（动态注入后端菜单）与 `resetRouter`（登出重置）。`meta` 约定：`keepAlive` / `isTab` / `isAuth` / `menu` / `title`。

**业务路由**（[src/router/views/index.js](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/src/router/views/index.js)）：5 个 SXK 业务页 + 2 个旧页，均以 `Layout` 为父级，`child.path` 统一为 `index`：
- `/dashboard/index`、`/knowledge/index`、`/generate/index`、`/history/index`、`/templates/index`
- `/workbenches/index`（旧入口）、`/info/index`（个人信息）

**鉴权链路**（端到端示例）：
1. [login/index.vue](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/src/page/login/index.vue) 表单 → `userStore.loginByUsername()`
2. [store/modules/user.js](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/src/store/modules/user.js)：
   - `VITE_APP_USE_MOCK_AUTH === 'true'` 时走本地 Mock 登录（校验用户名/密码/验证码非空后伪造 token）
   - 否则调 [api/user.js](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/src/api/user.js) `loginByUsername` → `POST /api/sxk/auth/login`
3. [router/axios.js](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/src/router/axios.js) 拦截器：自动拼 `baseUrl`、加 `Authorization: Basic <clientId:clientSecret>`、加 `Blade-Auth: <token>`
4. 成功 → `setToken`（Cookie `sxk-access-token`）+ `setStore`（sessionStorage `sxk-*`）
5. [permission.js](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/src/permission.js) `beforeEach`：无 token 跳 `/login`；有 token 但 store 中 token 空 → `fedLogOut`；否则维护 Tags 放行
6. 登录后 `initSxkMenu()` 注入 5 个一级菜单（绕过后端菜单接口）

**状态管理分工**：
- `user`：token / refreshToken / userInfo / roles / menu / menuAll / permission（按钮权限码 map）
- `common`：语言、主题、锁屏、折叠、全屏、屏幕尺寸等 UI 状态
- `tags`：标签页导航（增删、当前标签）
- `logs`：前端日志列表

**路径别名**：`@` → `./src`（定义于 [vite.config.js](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/vite.config.js#L23-L26)）。**所有 import 必须使用 `@/`，禁止相对路径硬编码。**

**数据持久化**：token/refreshToken 存 Cookie（[util/auth.js](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/src/util/auth.js)，key 为 `sxk-access-token` / `sxk-refresh-token`）；其余状态存 sessionStorage，key 统一加前缀 `sxk-`（[util/store.js](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/src/util/store.js)，`keyName = website.key + '-'`，`website.key = 'sxk'`）。

---

## 5. 编码规范

- **Linter / Formatter**：`npm run lint`（ESLint 8 + eslint-plugin-vue，`--fix` 自动修复）。配置文件 [.eslintrc.cjs](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/.eslintrc.cjs)：
  - 继承 `eslint:recommended` + `plugin:vue/vue3-recommended`
  - `vue/multi-word-component-names: 'off'`（sxk 模块下含单/双字业务组件，如 `basic-block`）
  - 生产环境 `no-console` / `no-debugger` 为 `error`，开发环境为 `off`
- **缩进 / 引号 / 分号**：依 [.editorconfig](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/.editorconfig) — UTF-8、2 空格缩进、LF 换行、文件尾插入空行、去除行尾空白（`.md` 除外）。代码普遍使用单引号、无分号（抽样既有代码得出）。
- **样式**：SCSS，组件内 `<style lang="scss" scoped>`；全局样式入口 `src/styles/common.scss` / `layout.scss` / `login.scss`，变量文件 `variables.scss` 由 Vite 自动 `@use` 注入，**无需在各文件手动 import**。
- **组件**：Element Plus 组件通过 `unplugin-vue-components` **按需自动注册**，模板中直接使用 `<el-*>`，无需手动 import；`@element-plus/icons-vue` 图标需显式 import。**`src/components/*` 下的自定义组件不会自动注册**，必须显式 import（见 10.1 陷阱 1/16）。
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

- **前端无数据库**；所有数据来自后端服务。
- **API 风格**：REST，双前缀：
  - **SXK 原生**（主要）：`/api/sxk/*`，统一响应壳 `{ code: 0, msg, data, trace_id }`
    - 鉴权：`/api/sxk/auth/{login, register, refresh, logout, check-username}`
    - 业务：`/api/sxk/{products, templates, scenes, generations, history, users, stats}/*`
  - **BladeX 兼容层**（遗留，部分接口仍沿用）：`/api/blade-*`，Token 头 `Blade-Auth`
    - `/api/blade-system/menu/{top-menu, routes, buttons}`
    - `/api/blade-auth/oauth/{token, user-info}`（社交登录等）
- **请求封装**：所有请求经 [src/router/axios.js](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/src/router/axios.js) 默认 axios 实例，约定：
  - 超时 60s，`withCredentials` 开启
  - 请求拦截：自动加 `baseUrl`、`Authorization: Basic`、`Blade-Auth` token（除非 `config.meta.isToken === false`）
  - 响应拦截：**优先读取 `res.data.code`**（SXK 约定 `code === 0` 成功）；无 `code` 字段时回退 HTTP status；`401` 触发 `refreshToken`，失败则 `fedLogOut` 跳 `/login`；白名单状态码自行 catch
  - 自定义 `config.meta`：`isToken`（是否带 token）、`isSerialize`（表单序列化）；`config.text === true` 设 `Content-Type: text/plain`
- **Mock 双轨开关**：
  - `VITE_APP_USE_MOCK_AUTH`：控制鉴权/系统级 6 个接口（[api/user.js](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/src/api/user.js) + [api/system/menu.js](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/src/api/system/menu.js)）
  - `VITE_APP_USE_MOCK_BIZ`：控制业务域全部接口（[mock/sxkApi.js](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/src/mock/sxkApi.js)，每个方法内 `if (!USE_MOCK_BIZ) return real(...)` 自动切换）
- **DTO 校验**：前端用 Element Plus `el-form` rules，无 zod/joi/class-validator。
- **接口文档**：前端仓库内未发现 Swagger/OpenAPI；需查阅后端服务。本地有 3 份后端接口清单 md（已被 `.gitignore` 忽略）。
- **加密**：AES-CBC（固定 key/iv，见 [util/crypto.js](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/src/util/crypto.js#L6-L7)），仅用于前端敏感数据二次混淆，非安全存储。

---

## 7. 环境变量

Vite 环境变量必须以 `VITE_` 为前缀才能注入前端。文件分布（实测值）：

| 变量 | 来源 | 当前值 | 说明 |
|------|------|--------|------|
| `VITE_APP_TITLE` | [.env](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/.env) | `神行库 · 营销 AI` | 全站标题（基础共享） |
| `VITE_APP_ENV` | .env.dev/prod/test | `dev` / `prod` / `test` | 环境标识 |
| `VITE_PORT` | [.env.dev](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/.env.dev) | `52400` | dev server 端口 |
| `VITE_API_TARGET` | .env.dev | `http://localhost:8000` | dev 代理目标（本地后端） |
| `VITE_API_TARGET` | .env.prod / .env.test | （空） | 生产/测试由 CI/网关注入或 nginx 反代 |
| `VITE_APP_USE_MOCK_AUTH` | .env.dev | `false` | 鉴权域 Mock 开关（当前已关闭） |
| `VITE_APP_USE_MOCK_BIZ` | .env.dev | `false` | 业务域 Mock 开关（当前已关闭） |
| `VITE_APP_USE_MOCK_AUTH` | .env.prod / .env.test | `false` | 生产/测试强制关闭 Mock |

- 开发态 `baseUrl = '/api'`（走 Vite proxy）；生产态 `baseUrl = ''`（同源直连，见 [config/env.js](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/src/config/env.js)）。
- 全局常量集中在 [config/website.js](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/src/config/website.js)：`clientId='sxk'`、`clientSecret='sxk_secret'`、`tokenHeader='Blade-Auth'`、`tenantId='000000'`、`captchaMode=true`、`key='sxk'`（sessionStorage 前缀主键）。**`clientSecret` 硬编码在前端，属安全隐患，生产前必须由部署/CI 注入或移至网关鉴权。**

---

## 8. 部署

- **容器化**：仓库未发现 `Dockerfile` / `docker-compose.yml`。
- **CI/CD**：未发现 `.github/workflows/` / `.gitlab-ci.yml` / `Jenkinsfile`。
- **目标环境**：构建为静态资源（`dist/`），部署到任意静态服务器 / 反向代理；生产态请求需由部署层（nginx 等）将 `/api/*` 转发到后端服务（因 `baseUrl` 生产为空，需同源或网关统一）。
- **构建模式**：仅 `dev` / `prod` / `test` 三套（无 `local` / `gdccs`）。

---

## 9. 业务领域

### 9.1 产品定位与能力
- **产品定位**：「神行库」产品营销 AI 平台管理后台。
- **核心能力**（依 [README.md](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/README.md)）：产品知识库管理、多 Agent 营销内容生成、竞品对比分析、多渠道文案适配。
- **当前实现**：5 大业务页面已落地（dashboard / knowledge / generate / history / templates）+ 登录/注册/锁屏 + 个人信息 + 旧工作台。

### 9.2 领域术语
- 租户（tenant）、部门（dept）、角色（role）、菜单（menu，含 top-menu/routes）、按钮权限（buttons/permission code）、验证码（captcha）、产品（product）、模板（template）、场景（scene）、生成（generation）、版本（version）、Agent 协作（agent run）。

### 9.3 权限模型
- RBAC + 按钮级权限码（`userStore.permission[code] === true`，通过 `getButtons` 拉取）+ 多租户（`tenantId`，`website.tenantMode` 当前关闭）。

### 9.4 关键流程
- 登录（账密/验证码）→ 下发 access_token（+ 可选 refresh_token）→ `initSxkMenu()` 注入 5 个菜单 → 进入业务页。

---

## 9.x 神行库业务前端实现（Mock 数据驱动 → 真实链路切换）

> **背景**：后端服务开发期间，前端采用 Mock 数据驱动开发。接口命名、字段、错误码均与《神行库_接口设计文档》保持一致，后端就绪后将 `VITE_APP_USE_MOCK_BIZ` 改为 `false` 即可自动切换真实链路，业务页面无需改动。

### 9.x.1 业务路由表（已注册）

| 路径 | 文件 | 说明 |
|------|------|------|
| `/dashboard/index` | [views/sxk/dashboard/index.vue](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/src/views/sxk/dashboard/index.vue) | 首页：4 张统计卡 + 常用模板 + 最近生成 |
| `/knowledge/index` | [views/sxk/knowledge/index.vue](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/src/views/sxk/knowledge/index.vue) | 产品知识库：CRUD + 关键词高亮 |
| `/generate/index` | [views/sxk/generate/index.vue](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/src/views/sxk/generate/index.vue) | 内容生成：左配置 + 右 4 Tab（编辑/Agent/渠道/对比） |
| `/history/index` | [views/sxk/history/index.vue](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/src/views/sxk/history/index.vue) | 生成历史：表格 + 详情/重编辑/删除 |
| `/templates/index` | [views/sxk/templates/index.vue](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/src/views/sxk/templates/index.vue) | 场景模板管理：列表 + 详情/创建 |

### 9.x.2 关键基础设施

- **Mock 数据集**：[src/mock/data.js](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/src/mock/data.js)
  - 6 个产品 / 7 个模板 / 5 条生成历史 / 单版本内容 / Agent 思考链 / 校验问题 / Dashboard 统计
- **Mock API 封装**：[src/mock/sxkApi.js](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/src/mock/sxkApi.js)
  - 方法命名严格对齐接口文档资源路径（`getDashboardStats` / `listProducts` / `triggerGeneration` 等）
  - 双轨开关 `USE_MOCK_BIZ = VITE_APP_USE_MOCK_BIZ !== 'false'`，每个方法内 `if (!USE_MOCK_BIZ) return real(...)` 切换
  - 真实链路 `real()` 已提取 `res.data`，使返回形态与 Mock `ok()` 完全一致，调用方无感知
  - 业务校验示例：`4091 重名` / `4006 内容块为空` / `4042 已删除` / `4030 预置模板不可删`
- **登录后菜单注入**：[store/modules/user.js](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/src/store/modules/user.js) `initSxkMenu()`
  - 绕过 `/blade-system/menu/routes`，直接写入 5 个 SXK 业务菜单
- **可复用组件**：
  - [components/basic-block/main.vue](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/src/components/basic-block/main.vue) — 扩展了 `header`/`aside` 插槽与 `hoverShadow`/`padding` props
  - [components/tag-input/index.vue](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/src/components/tag-input/index.vue) — 通用标签输入器（回车/失焦提交、删除、backspace）

### 9.x.3 业务字段规范

- **统一响应壳**：`{ code: 0, msg: 'ok', data, trace_id }`
- **API 路径前缀**：`/api/sxk/...`
- **业务规则代号**：BR-K-XX（产品）/ BR-G-XX（生成）/ BR-H-XX（历史）/ BR-T-XX（模板）/ BR-A-XX（认证）
- **场景代号**：`product_intro` / `competitor` / `channel_adapt` / `email` / `event` / `other` / `custom`
- **Agent 协作流（默认 4 节点）**：retrieval → generation → channel_adapt → validation
- **Agent 协作流（竞品 4 节点）**：retrieval → competitor_analysis → generation → validation

---

## 10. AI 协作约定（写给 AI Agent）

### 10.1 已知陷阱（Known Pitfalls）

以下为本项目实际踩过/已确认的风险点，AI Agent 编写代码前必须先确认是否命中：

1. **自定义全局组件不会自动导入**：`unplugin-vue-components` 仅配置了 `ElementPlusResolver`（`dirs: []`, `deep: false`），对 `src/components/` 下的自定义组件（`basic-container`、`basic-block`、`tag-input` 等）**不会自动注册**。[main.js](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/src/main.js) 中已显式 import 注册 `basicContainer` / `basicBlock`；其他自定义组件使用前必须先显式 `import`，否则报「Unknown custom element」。
2. **生产/测试 `VITE_API_TARGET` 为空**：`prod` / `test` 模式下 `VITE_API_TARGET` 留空，`baseUrl` 生产态又为空，**请求会发往同源**。任何新增/修改的接口默认走 `/api`，必须由部署层（nginx / 网关）将 `/api/*` 反代到后端，否则 404。不要在代码里假设后端域名。
3. **`sessionStorage` 不跨标签页共享**：所有非 token 状态（userInfo / menu / permission / language）存于 `sessionStorage`（前缀 `sxk-`），新标签页打开会触发「有 cookie 但 store 为空 → fedLogOut」分支。若 AI 需要「跨标签同步」逻辑，请改用 `localStorage` 或 `BroadcastChannel`，不要硬塞进 `util/store.js`。
4. **`userStore.delAllTag()` / `clearLock()` 已用动态 import 修复**：当前这两个方法通过动态 `import('@/store/modules/tags')` / `import('@/store/modules/common')` 跨模块委托实现（避免循环依赖）。新增登出/锁屏流程时**必须沿用动态 import 写法**，不要静态 import store 模块。
5. **`crypto-js` 的 AES key/iv 是固定常量**：见 [util/crypto.js](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/src/util/crypto.js#L6-L7) 中的硬编码 key/iv，**仅用于前端密码传输的二次混淆**，不是安全存储。任何「把 token / refreshToken 用 AES 加密再存」的需求都属过度设计，直接复用 `util/auth.js` 的 Cookie 工具即可。
6. **按钮权限判定依赖后端下发的 `permission` map**：UI 上 `userStore.permission['btn_xxx']` 仅当 `getButtons` 接口被调用且返回该 code 时才生效。AI 不要在前端硬编码权限码，权限码以 `website.js` / `api/system/menu.js` 的契约为准。
7. **不要新增 `.env.*` 文件而不补 `.gitignore`**：本仓库 `.env.local` / `.env.*.local` 已被 `.gitignore` 忽略；若 AI 必须新增环境文件，请同步在 `.gitignore` 中忽略，避免真实后端域名泄露到公开仓库。
8. **菜单路径必须含 `/index` 后缀**：`initSxkMenu()` 写入的 5 个菜单项均为 `/dashboard/index` / `/knowledge/index` / `/generate/index` / `/history/index` / `/templates/index`，与 [router/views/index.js](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/src/router/views/index.js) 中注册的 `child.path` 一致。**不要省略 `/index`**，否则侧边栏点击会跳到无匹配路由的路径。
9. **`sxkApi` Mock 返回的是「裸 data 壳」而非 AxiosResponse**：[mock/sxkApi.js](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/src/mock/sxkApi.js) 中 Mock 方法 `return delay().then(() => ok(...))`，`ok()` 返回 `{code, msg, data, trace_id}`（**注意：与 api/user.js 的 ok 不同，此处未包成 AxiosResponse**）。业务页面调用 sxkApi 后直接读 `resp.data.xxx`（即 `resp.data.items` / `resp.data.total`）。真实链路 `real()` 已做 `res.data` 提取对齐。
10. **Generate 页用了 `document.execCommand` 做轻量富文本**：仅用于演示阶段，生产可替换为 Tiptap / Quill。**注意**：`execCmd('formatBlock', 'H2')` 第二个参数必须是字符串字面量；`editorRef` 是 `<div contenteditable>`，赋值请用 `innerHTML` 而不是 `v-model`，否则 Vue 会把 HTML 当文本。
11. **Agent 协作轮询为前端模拟**：[views/sxk/generate/index.vue](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/src/views/sxk/generate/index.vue) `startAgentPolling()` 用 `setTimeout` 把每个 Agent 节点从 `pending → running → success` 推进，仅为视觉演示。**真实实现应改为 SSE / WebSocket**（按接口文档 `GET /generations/{id}/agents` 长连接），不要在生产代码里保留这个轮询。
12. **`getSceneSchemas()` 返回的 `params` 字段是「字段定义」而不是「字段值」**：`mockSceneSchemas` 中 `params[i].default` 是默认值，业务页面要遍历 schema 渲染表单，**不要把整个 `params` 数组直接 `v-model`**。
13. **模板 `is_custom` 默认 `false`**：系统预置模板均为 `is_custom: false`，仅当用户通过 `sxkApi.createTemplate()` 创建时才置 `true`。**模板列表页筛选「我的模板」时务必传 `is_custom: true`**。预置模板不可删除（返回 `4030`）。
14. **Mock 双轨开关独立**：`VITE_APP_USE_MOCK_AUTH`（鉴权域）与 `VITE_APP_USE_MOCK_BIZ`（业务域）是两个独立开关。当前 `.env.dev` 两者均为 `false`（已切真实链路）。开启 Mock Auth 时，[store/modules/user.js](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/src/store/modules/user.js) `loginByUsername()` 会**完全跳过**后端 `/api/sxk/auth/login`，仅做本地校验后伪造 token。**生产环境务必确保两者为 `false`**。
15. **本地 SVG 验证码仅前端演示**：[util/svg-captcha.js](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/src/util/svg-captcha.js) 把生成时的正确答案返回到 login 页并写入 `sessionStorage('sxk-captcha-text')`，**客户端比对 = 0 安全意义**。后端就绪后应删除整个文件 + 恢复真实 `getCaptcha` 实现，并在后端做权威校验。
16. **`vite.config.js` 已关闭全局组件自动注册**：`Components({ dirs: [], deep: false, dts: false })` 仅按需注册 ElementPlus。**所有 `src/components/*` 下的组件必须显式 `import` 后再使用**。
17. **端口冲突 → 52400 报 404**：开发期 `localhost:52400` 出现 404 时，**优先检查端口是否被占用**（Vite 启动日志 `Port 52400 is in use, trying another one...` 会自动落到 52401+）。需 `netstat -ano | findstr 52400` + `taskkill /PID <pid> /F` 后重启 `npm run dev`。
18. **项目独立性约束**：神行库独立部署，使用 `sxk` 前缀（`clientId='sxk'`、`TokenKey='sxk-access-token'`、sessionStorage 前缀 `sxk-`、`website.key='sxk'`）。**严禁再把其他同源业务系统（B2B-HGSH 等）的 clientId / tokenKey / 注释直接复制进来**；新增 `.env.*` 时只保留 `dev / test / prod` 三套。
19. **axios 响应拦截优先读 `code` 字段**：[router/axios.js](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/src/router/axios.js#L72-L112) 当 `res.data.code !== undefined` 时用 `code` 判定（SXK 约定 `0` 成功，业务错误码如 `4091` 正常 return 由页面处理）；无 `code` 字段才回退 HTTP status。新增接口若返回壳含 `code`，业务错误不会触发全局 ElMessage，需在页面自行处理。

### 10.2 编码与工程约束（Operational Rules）

1. **import 必须使用 `@/` 别名**，禁止 `../../` 相对路径（别名见 [vite.config.js](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/vite.config.js#L23-L26)）。
2. **新增 API**：在 `src/api/<业务域>.js` 内导出函数，统一调用 `@/router/axios` 的 `request`；URL 以 `/api/sxk/` 或 `/api/blade-*` 开头；不要在业务组件里直接 `import axios`。
3. **新增业务视图**：放在 `src/views/<模块>/`，并在 [src/router/views/index.js](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/src/router/views/index.js) 注册路由，使用 `Layout` 父级，`child.path` 用 `index`；`meta` 必填语义（`keepAlive` / `isTab` / `isAuth` / `title`）。
4. **Element Plus 组件**：模板直接写 `<el-*>`，**不要**手动 import 组件；图标 `@element-plus/icons-vue` 需显式 import。
5. **状态管理**：跨页共享状态写 Pinia store（`src/store/modules/`），不要滥用全局属性；持久化用 `@/util/store`（sessionStorage，自动加 `sxk-` 前缀），token 类用 `@/util/auth`（Cookie，key `sxk-access-token`）。
6. **样式**：组件内 `<style lang="scss" scoped>`；变量直接使用 `variables.scss` 中的值（已自动注入），不要再 `@import`。
7. **鉴权**：免 token 请求需在 request 配置里加 `meta: { isToken: false }`；新增需登录的页面**不要**加 `meta.isAuth = false`。
8. **密码 / 敏感数据**：复用 [util/crypto.js](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/src/util/crypto.js) 与 [util/auth.js](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/src/util/auth.js)，不要自造加密逻辑；不要把 `clientSecret` 等常量复制到业务文件，统一引用 `@/config/website`。
9. **代码风格**：2 空格、单引号、无分号、文件尾空行、中文注释；改动完成后执行 `npm run lint` 自检。
10. **不确定处先问**：不要臆造后端接口、菜单字段或环境变量；后端契约以 [api/](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/src/api) 现有调用与 [website.js](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/src/config/website.js) `menu.props` 字段映射为准。

---

## 11. 待确认项（基于假设，需人工核实）

1. **`.env.prod` / `.env.test` 的 `VITE_API_TARGET` 为空**：生产/测试构建后请求路径如何路由到后端（同源？网关？）需部署方确认。当前两文件 `VITE_API_TARGET` 留空，由部署/CI 注入或经 nginx 网关反代 `/api/*`。
2. **`.env.dev` 中 `VITE_API_TARGET=http://localhost:8000`**：为本地后端服务地址，启动后端服务前请勿提交实际域名。
3. **ESLint 规则已确认**：仓库使用 [.eslintrc.cjs](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/.eslintrc.cjs)（eslint:recommended + vue3-recommended），`vue/multi-word-component-names: 'off'`，生产环境禁 `console`/`debugger`。
4. **Node 版本未约束**：无 `engines` / `.nvmrc`，Vite 6 要求 Node 18+，请确认团队统一版本。
5. **后端版本与契约**：后端服务版本、是否启用租户模式、`clientSecret` 是否为前端可见值，需后端确认。当前 `clientSecret='sxk_secret'` 为本地占位，生产前必须由部署/CI 注入或移至网关鉴权。
6. **测试体系缺失**：未检测到任何测试框架（jest/vitest/cypress）与 `*.test.*` 文件，`package.json` 也无 `test` 脚本。若需补测试，建议引入 Vitest。
7. **Mock 残留**：`src/mock/*` 与 `VITE_APP_USE_MOCK_AUTH` / `VITE_APP_USE_MOCK_BIZ` 用于后端未启阶段。当前 `.env.dev` 均已置 `false`（切真实链路），但 `src/mock/` 目录仍保留作为双轨兜底。后端稳定后可考虑移除。
8. **CI/CD 与容器化**：仓库无相关配置，部署链路需运维确认。
9. **refresh_token 管理方式**：[store/modules/user.js](file:///d:/Postgraduate/e-resource/CDC/B2B-SXK-ManageGF/src/store/modules/user.js#L202-L225) 注释提及「refresh_token 由后端通过 Set-Cookie (HttpOnly) 管理」，但前端 `util/auth.js` 仍用 js-cookie 存储 `sxk-refresh-token`。后端实际 refresh_token 策略需确认。
