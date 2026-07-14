import { defineStore } from 'pinia'
import { setToken, setRefreshToken, removeToken, removeRefreshToken } from '@/util/auth'
import { setStore, getStore } from '@/util/store'
import { validatenull } from '@/util/validate'
import { deepClone } from '@/util/util'
import website from '@/config/website'
import {
  loginByUsername,
  loginBySocial,
  getUserInfo,
  logout,
  refreshToken,
  getButtons
} from '@/api/user'
import { getTopMenu, getRoutes } from '@/api/system/menu'
import { ElMessage } from 'element-plus'

function addPath(ele, first) {
  const menu = website.menu
  const propsConfig = menu.props
  const propsDefault = {
    label: propsConfig.label || 'name',
    path: propsConfig.path || 'path',
    icon: propsConfig.icon || 'icon',
    children: propsConfig.children || 'children'
  }
  const icon = ele[propsDefault.icon]
  ele[propsDefault.icon] = validatenull(icon) ? menu.iconDefault : icon
  const isChild = ele[propsDefault.children] && ele[propsDefault.children].length !== 0
  if (!isChild) ele[propsDefault.children] = []
  if (!isChild && first && !/^https?:\/\//.test(ele[propsDefault.path])) {
    ele[propsDefault.path] = ele[propsDefault.path] + '/index'
  } else {
    ele[propsDefault.children].forEach((child) => {
      addPath(child)
    })
  }
}

export const useUserStore = defineStore('user', {
  state: () => ({
    tenantId: getStore({ name: 'tenantId' }) || '',
    userInfo: getStore({ name: 'userInfo' }) || {},
    permission: getStore({ name: 'permission' }) || {},
    roles: [],
    menuId: {},
    menu: getStore({ name: 'menu' }) || [],
    menuAll: getStore({ name: 'menuAll' }) || [],
    token: getStore({ name: 'token' }) || '',
    refreshToken: getStore({ name: 'refreshToken' }) || '',
    source: getStore({ name: 'source' }) || ''
  }),
  getters: {
    // 权限检查：state.permission[code] 为 true
    hasPermission: (state) => (code) => {
      return !!state.permission[code]
    }
  },
  actions: {
    // 根据用户名登录
    loginByUsername(userInfo) {
      return new Promise((resolve, reject) => {
        // Phase 4：后端未启 → 走本地 Mock 登录
        // 校验规则：用户名非空 + 密码非空 + 验证码（若开启）与本地缓存一致
        if (import.meta.env.VITE_APP_USE_MOCK_AUTH === 'true') {
          const username = (userInfo.username || '').trim()
          const password = (userInfo.password || '').trim()
          if (!username || !password) {
            ElMessage({ message: '请输入用户名与密码', type: 'error' })
            return reject(new Error('用户名/密码为空'))
          }
          if (userInfo.captchaMode) {
            const expected = sessionStorage.getItem('sxk-captcha-text') || ''
            if (!userInfo.code || userInfo.code.trim().toLowerCase() !== expected.toLowerCase()) {
              ElMessage({ message: '验证码错误', type: 'error' })
              return reject(new Error('验证码错误'))
            }
          }
          // 构造 BladeX OAuth2 兼容的响应壳
          // Mock 阶段补充完整用户资料字段，供"个人信息"页展示
          const nowStr = new Date().toISOString()
          // 关键：mock 阶段所有登录用户都视为管理员（方便测试 members/competitors 等高级功能）
          const isAdmin = true
          const fakeTokenResp = {
            data: {
              access_token: `mock-access-${Date.now()}`,
              refresh_token: `mock-refresh-${Date.now()}`,
              tenant_id: userInfo.tenantId || website.tenantId,
              user_id: 'u_mock',
              user_name: username,
              is_admin: isAdmin,
              token_type: 'bearer',
              expires_in: 3600,
              // —— 个人信息展示字段 ——
              nick_name: username === 'admin' ? '系统管理员' : '产品运营',
              real_name: username === 'admin' ? 'Admin' : '李知微',
              avatar: '',
              email: `${username}@sxk.example.com`,
              phone: '138****8888',
              dept_id: 'd_001',
              dept_name: '产品营销中心',
              role_id: username === 'admin' ? 'r_admin' : 'r_operator',
              role_name: username === 'admin' ? '系统管理员' : '内容运营',
              created_at: '2025-03-12 09:30:00',
              last_login_at: nowStr
            }
          }
          const data = fakeTokenResp.data
          this.setToken(data.access_token)
          this.setRefreshToken(data.refresh_token)
          this.setTenantId(data.tenant_id)
          this.setUserInfo(data)
          // Mock 阶段同步填充 roles，供"个人信息"页与权限判断使用
          this.roles = [
            { role_id: data.role_id, role_name: data.role_name, role_alias: data.role_name }
          ]
          this.initSxkMenu() // 神行库：登录后初始化 5 个一级导航菜单（mock 阶段跳过 /blade-system/menu/routes）
          this.delAllTag()
          this.clearLock()
          return resolve()
        }

        // 真实链路：POST /api/auth/login
        loginByUsername(
          userInfo.username,
          userInfo.password,
          userInfo.key,
          userInfo.code
        )
          .then((res) => {
            // Mock 壳格式：{ code: 0, data: { access_token, ... } }
            // 后端裸格式：{ access_token, refresh_token, user: { id, name, ... } }
            const payload = res.data || {}
            const isMock = payload.code !== undefined
            if (isMock && payload.code !== 0) {
              ElMessage({ message: payload.msg || '登录失败', type: 'error' })
              return resolve()
            }
            const tokenData = isMock ? payload.data : payload
            const user = tokenData.user || {}

            this.setToken(tokenData.access_token)
            // refresh_token 可选（部分后端不返回）
            if (tokenData.refresh_token) {
              this.setRefreshToken(tokenData.refresh_token)
            }
            // tenant_id 可选
            if (tokenData.tenant_id) {
              this.setTenantId(tokenData.tenant_id)
            }
            // 扁平化用户信息：将 user 对象展开 + 保留 token 元数据
            this.setUserInfo({
              ...user,
              access_token: tokenData.access_token,
              expires_in: tokenData.expires_in,
              token_type: tokenData.token_type
            })
            // roles 适配：后端用 is_admin 标识，Mock 用 role 字段
            if (isMock && user.role) {
              this.roles = [
                { role_id: user.role, role_name: user.role_name || user.role, role_alias: user.role }
              ]
            } else if (user.is_admin !== undefined) {
              this.roles = user.is_admin
                ? [{ role_id: 'admin', role_name: '管理员', role_alias: 'admin' }]
                : [{ role_id: 'user', role_name: '用户', role_alias: 'user' }]
            } else {
              this.roles = []
            }

            this.initSxkMenu()
            this.delAllTag()
            this.clearLock()
            resolve()
          })
          .catch((error) => {
            reject(error)
          })
      })
    },
    // 第三方登录
    loginBySocial(userInfo) {
      return new Promise((resolve) => {
        let source = userInfo.source == 'saml' ? 'saml' : 'social'
        loginBySocial(userInfo.tenantId, source, userInfo.code, userInfo.state).then((res) => {
          const data = res.data
          if (data.error_description) {
            ElMessage({ message: data.error_description, type: 'error' })
          } else {
            this.setToken(data.access_token)
            this.setRefreshToken(data.refresh_token)
            this.setUserInfo(data)
            this.delAllTag()
            this.clearLock()
          }
          resolve()
        })
      })
    },
    // 获取用户信息
    getUserInfo() {
      return new Promise((resolve, reject) => {
        getUserInfo()
          .then((res) => {
            // Mock 壳格式：{ code: 0, data: { user_id, username, role, roles, is_admin } }
            // 后端裸格式：{ id, name, color, username, email, is_admin, created_at }
            const payload = res.data || {}
            const isMock = payload.code !== undefined
            const data = isMock ? payload.data : payload
            if (isMock) {
              this.roles = data.roles || []
            } else {
              this.roles = data.is_admin
                ? [{ role_id: 'admin', role_name: '管理员', role_alias: 'admin' }]
                : [{ role_id: 'user', role_name: '用户', role_alias: 'user' }]
            }
            // 关键：把 userInfo 写入 store 并重新初始化菜单
            // 之前 getUserInfo 只 resolve 不写 store，导致 sidebar 不会更新
            this.setUserInfo(data)
            resolve(data)
          })
          .catch((err) => {
            reject(err)
          })
      })
    },
    // 刷新 token
    refreshToken(userInfo) {
      return new Promise((resolve, reject) => {
        refreshToken(
          this.refreshToken,
          this.tenantId,
          !validatenull(userInfo) ? userInfo.deptId : this.userInfo.dept_id,
          !validatenull(userInfo) ? userInfo.roleId : this.userInfo.role_id,
          userInfo?.switchMode
        )
          .then((res) => {
            // Mock 壳格式：{ code: 0, data: { access_token, refresh_token } }
            // 后端裸格式：{ access_token }
            const payload = res.data || {}
            const isMock = payload.code !== undefined
            if (isMock && payload.code !== 0) {
              return reject(new Error(payload.msg || '刷新 token 失败'))
            }
            const tokenData = isMock ? payload.data : payload
            this.setToken(tokenData.access_token)
            resolve()
          })
          .catch((error) => {
            reject(error)
          })
      })
    },
    // 登出
    logOut() {
      return new Promise((resolve, reject) => {
        logout()
          .then(() => {
            this.clearAuth()
            resolve()
          })
          .catch((error) => {
            reject(error)
          })
      })
    },
    // 注销 session
    fedLogOut() {
      return new Promise((resolve) => {
        this.clearAuth()
        resolve()
      })
    },
    // 清除认证信息
    clearAuth() {
      this.token = ''
      this.tenantId = ''
      this.userInfo = {}
      this.menu = []
      this.menuAll = []
      this.roles = []
      removeToken()
      removeRefreshToken()
      setStore({ name: 'tenantId', content: '' })
      setStore({ name: 'userInfo', content: {} })
      setStore({ name: 'menu', content: [] })
      setStore({ name: 'menuAll', content: [] })
    },
    // 获取顶部菜单
    getTopMenu() {
      return new Promise((resolve) => {
        getTopMenu().then((res) => {
          resolve(res.data.data || [])
        })
      })
    },
    // 获取系统菜单
    getMenu(topMenuId) {
      return new Promise((resolve) => {
        getRoutes(topMenuId).then((res) => {
          const data = res.data.data
          let menu = deepClone(data)
          menu.forEach((ele) => {
            addPath(ele, true)
          })
          this.menuAll = menu
          this.menu = menu
          this.getButtons()
          resolve(menu)
        })
      })
    },
    // 获取按钮权限
    getButtons() {
      return new Promise((resolve) => {
        getButtons().then((res) => {
          const data = res.data.data
          this.setPermission(data)
          resolve()
        })
      })
    },
    // ---- mutations ----
    setToken(token) {
      setToken(token)
      this.token = token
      setStore({ name: 'token', content: this.token })
    },
    setRefreshToken(refreshToken) {
      setRefreshToken(refreshToken)
      this.refreshToken = refreshToken
      setStore({ name: 'refreshToken', content: this.refreshToken })
    },
    setTenantId(tenantId) {
      this.tenantId = tenantId
      setStore({ name: 'tenantId', content: this.tenantId })
    },
    setUserInfo(userInfo) {
      if (validatenull(userInfo.avatar)) {
        userInfo.avatar = ''
      }
      this.userInfo = userInfo
      setStore({ name: 'userInfo', content: this.userInfo })
      // 关键：每次 userInfo 更新（如 mock 切换 admin、API 返回 is_admin）后重新初始化菜单
      // 否则侧边栏不会自动出现"成员管理"等管理员菜单项
      this.initSxkMenu()
    },
    setPermission(permission) {
      let result = []
      function getCode(list) {
        list.forEach((ele) => {
          if (typeof ele === 'object') {
            const children = ele.children
            const code = ele.code
            if (children) {
              getCode(children)
            } else {
              result.push(code)
            }
          }
        })
      }
      getCode(permission)
      this.permission = {}
      result.forEach((ele) => {
        this.permission[ele] = true
      })
      setStore({ name: 'permission', content: this.permission })
    },
    delAllTag() {
      // 跨 store 委托：tags（动态 import 避免循环依赖）
      return import('@/store/modules/tags').then(({ useTagsStore }) => {
        useTagsStore().delAllTag()
      })
    },
    clearLock() {
      // 跨 store 委托：common（动态 import 避免循环依赖）
      return import('@/store/modules/common').then(({ useCommonStore }) => {
        useCommonStore().clearLock()
      })
    },
    /**
     * 神行库前端菜单初始化
     *
     * 说明：后端菜单接口 /blade-system/menu/routes 未联调前，
     *      前端直接写入 5 个一级导航（与《神行库_产品需求文档》4.2 一级导航一致）。
     *      后续真实菜单接口接入时，可在 loginByUsername 中改为 await this.getMenu()，
     *      此方法保留可作为"登录无菜单接口时的兜底"。
     *
     * 字段说明（参考 src/config/website.js 的 menu.props）：
     *   name   -> label
     *   path   -> path
     *   source -> icon
     *   children
     */
    initSxkMenu() {
      const isAdmin = !!this.userInfo?.is_admin
      const sxkMenu = [
        {
          path: '/dashboard/index',
          name: '首页',
          source: 'HomeFilled', // Element Plus icon 组件名
          children: []
        },
        {
          path: '/knowledge/index',
          name: '产品知识库',
          source: 'Goods',
          children: []
        },
        {
          path: '/generate/index',
          name: '内容生成',
          source: 'MagicStick',
          children: []
        },
        {
          path: '/history/index',
          name: '生成历史',
          source: 'Clock',
          children: []
        },
        {
          path: '/templates/index',
          name: '场景模板管理',
          source: 'Files',
          children: []
        },
        {
          path: '/competitors/index',
          name: '竞品分析',
          source: 'Aim',
          children: []
        }
      ]
      // 成员管理仅管理员可见
      if (isAdmin) {
        sxkMenu.push({
          path: '/members/index',
          name: '成员管理',
          source: 'UserFilled',
          children: []
        })
      }
      this.menuAll = sxkMenu
      this.menu = sxkMenu
      setStore({ name: 'menu', content: sxkMenu })
    }
  }
})
