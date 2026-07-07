import request from '@/router/axios'
import website from '@/config/website'

export const loginByUsername = (tenantId, deptId, roleId, username, password, type, key, code, switchMode, captchaMode) =>
  request({
    url: '/api/blade-auth/oauth/token',
    method: 'post',
    headers: {
      'Tenant-Id': tenantId,
      'Dept-Id': switchMode ? deptId : '',
      'Role-Id': switchMode ? roleId : '',
      'Captcha-Key': key,
      'Captcha-Code': code
    },
    data: {
      tenantId,
      username,
      password,
      grant_type: captchaMode ? 'captcha' : 'password',
      scope: 'all',
      type
    }
  })

export const loginBySocial = (tenantId, source, code, state) =>
  request({
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

export const refreshToken = (refresh_token, tenantId, deptId, roleId, switchMode) =>
  request({
    url: '/api/blade-auth/oauth/token',
    method: 'post',
    headers: {
      'Tenant-Id': tenantId,
      'Dept-Id': switchMode ? deptId : '',
      'Role-Id': switchMode ? roleId : ''
    },
    data: {
      tenantId,
      refresh_token,
      grant_type: 'refresh_token',
      scope: 'all'
    }
  })

export const getButtons = () =>
  request({
    url: '/api/blade-system/menu/buttons',
    method: 'get'
  })

export const getCaptcha = () =>
  request({
    url: '/api/blade-auth/oauth/captcha',
    method: 'get',
    meta: { isToken: false }
  })

export const logout = () =>
  request({
    url: '/api/blade-auth/oauth/logout',
    method: 'get',
    meta: { isToken: false }
  })

export const getUserInfo = () =>
  request({
    url: '/api/blade-auth/oauth/user-info',
    method: 'get'
  })
