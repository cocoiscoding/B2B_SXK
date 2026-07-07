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
import md5 from 'js-md5'
import aesUtil from '@/util/crypto'
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
        loginByUsername(
          userInfo.tenantId,
          userInfo.deptId,
          userInfo.roleId,
          userInfo.username,
          aesUtil.encrypt(md5(userInfo.password)),
          userInfo.type,
          userInfo.key,
          userInfo.code,
          userInfo.switchMode,
          userInfo.captchaMode
        )
          .then((res) => {
            const data = res.data
            if (data.error_description) {
              ElMessage({ message: data.error_description, type: 'error' })
            } else {
              this.setToken(data.access_token)
              this.setRefreshToken(data.refresh_token)
              this.setTenantId(data.tenant_id)
              this.setUserInfo(data)
              this.delAllTag()
              this.clearLock()
            }
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
            const data = res.data.data
            this.roles = data.roles
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
            const data = res.data
            this.setToken(data.access_token)
            this.setRefreshToken(data.refresh_token)
            this.setUserInfo(data)
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
      this.menu = []
      this.menuAll = []
      this.roles = []
      removeToken()
      removeRefreshToken()
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
      // 委托给 tags store（在 permission.js 中调用）
    },
    clearLock() {
      // 清除锁屏状态（委托给 common store）
    }
  }
})
