import request from '@/router/axios'
import website from '@/config/website'
// Phase 4：后端未启期间用本地 SVG 验证码代替 /api/blade-auth/oauth/captcha
import { createSvgCaptcha } from '@/util/svg-captcha'

/**
 * Phase 4：全局 Mock 短路开关
 * 由 .env.dev 中 VITE_APP_USE_MOCK_AUTH=true 开启；
 * 关闭后所有 API 完全等同于改前行为（直接走真实 request()）。
 *
 * 注意：本开关仅影响以下 6 个鉴权/系统级接口；业务接口（src/api/system/* 等）
 * 仍按真实链路调用，业务本身由 src/mock/sxkApi.js 独立短路。
 */
const MOCK_AUTH = import.meta.env.VITE_APP_USE_MOCK_AUTH === 'true'

// 统一响应壳，与 axios 拦截器 status 200 兼容
const ok = (data) =>
  Promise.resolve({
    status: 200,
    data: { code: 0, msg: 'ok', data, trace_id: `mock-${Date.now()}` }
  })

/**
 * Phase 4 Mock：本地生成 SVG 验证码
 * 保持与原 getCaptcha() 同名同形态，业务侧只需替换 import 源即可
 */
export const getCaptcha = () => {
  const { key, svg, text } = createSvgCaptcha()
  // 把生成的 code 暂存到 sessionStorage，供登录时比对（仅前端演示）
  sessionStorage.setItem('sxk-captcha-text', text)
  return Promise.resolve({
    data: { key, svg, captchaEnabled: website.captchaMode }
  })
}

/**
 * 神行库登录
 * POST /api/sxk/auth/login
 *
 * 请求体：{ tenantId, username, password, key, code, grant_type, scope, type }
 * 响应体：{ code: 0, data: { access_token, expires_in, token_type, user: { user_id, username, role, ... } } }
 *
 * @param {string} username  用户名（或邮箱）
 * @param {string} password  明文密码（传输层建议 HTTPS）
 * @param {string} key       验证码 key（captchaMode 时必填）
 * @param {string} code      用户输入的验证码（captchaMode 时必填）
 */
export const loginByUsername = (username, password, key, code) => {
  if (MOCK_AUTH) {
    // 真实鉴权链路已在 store/modules/user.js loginByUsername 入口短路，
    // 此处仅保留函数签名兼容，避免调用方走到 request() 时 ECONNREFUSED。
    return ok({ access_token: 'mock', refresh_token: 'mock' })
  }
  return request({
    url: '/api/sxk/auth/login',
    method: 'post',
    meta: { isToken: false },
    data: {
      tenantId: website.tenantId,
      username,
      password,
      key,
      code,
      grant_type: website.captchaMode ? 'captcha' : 'password',
      scope: 'all',
      type: 'account'
    }
  })
}

/**
 * 神行库注册
 * POST /api/sxk/auth/register
 *
 * 请求体：{ username, email, password, key, code }
 * 响应体：{ code: 0, data: { user_id, username, ... }, msg }
 *
 * @param {string} username  用户名
 * @param {string} email     邮箱
 * @param {string} password  明文密码（传输层建议 HTTPS）
 * @param {string} key       验证码 key
 * @param {string} code      用户输入的验证码
 */
export const registerByInfo = (username, email, password, key, code) => {
  if (MOCK_AUTH) {
    return ok({ username })
  }
  return request({
    url: '/api/sxk/auth/register',
    method: 'post',
    meta: { isToken: false },
    data: { username, email, password, key, code }
  })
}

/**
 * 用户名查重
 * GET /api/sxk/auth/check-username
 *
 * @param {string} username  待检查的用户名
 * @returns { available: boolean, username: string }
 */
export const checkUsername = (username) => {
  if (MOCK_AUTH) {
    // mock：保留 3 个已占用用户名
    const taken = ['admin', 'test', 'demo']
    return ok({ available: !taken.includes((username || '').toLowerCase()), username })
  }
  return request({
    url: '/api/sxk/auth/check-username',
    method: 'get',
    meta: { isToken: false },
    params: { username }
  })
}

export const loginBySocial = (tenantId, source, code, state) => {
  if (MOCK_AUTH) return ok({ access_token: 'mock', refresh_token: 'mock' })
  return request({
    url: '/api/blade-auth/oauth/token',
    method: 'post',
    headers: {
      'Tenant-Id': tenantId
    },
    data: {
      tenantId,
      source,
      code,
      state,
      grant_type: source,
      scope: 'all'
    }
  })
}

export const refreshToken = (refresh_token, tenantId, deptId, roleId, switchMode) => {
  if (MOCK_AUTH) {
    // 演示阶段：刷新 token 直接复用原 token，不更新过期时间
    return ok({
      access_token: refresh_token,
      refresh_token
    })
  }
  return request({
    url: '/api/sxk/auth/refresh',
    method: 'post',
    meta: { isToken: false },
    data: {}
  })
}

export const getButtons = () => {
  if (MOCK_AUTH) return ok({})
  return request({
    url: '/api/blade-system/menu/buttons',
    method: 'get'
  })
}

export const logout = () => {
  if (MOCK_AUTH) return ok(null)
  return request({
    url: '/api/sxk/auth/logout',
    method: 'post',
    meta: { isToken: false },
    data: {}
  })
}

export const getUserInfo = () => {
  if (MOCK_AUTH) {
    return ok({
      user_id: 'u_mock',
      username: 'mock-user',
      role: 'user',
      roles: ['user']
    })
  }
  return request({
    url: '/api/blade-auth/oauth/user-info',
    method: 'get'
  })
}
