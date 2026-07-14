import request from '@/router/axios'

// Phase 4：后端未启期间短路菜单相关请求，避免 ECONNREFUSED
const MOCK_AUTH = import.meta.env.VITE_APP_USE_MOCK_AUTH === 'true'
const ok = (data) =>
  Promise.resolve({
    status: 200,
    data: { code: 0, msg: 'ok', data, trace_id: `mock-${Date.now()}` }
  })

export const getTopMenu = () => {
  // 真实菜单由 store/modules/user.js initSxkMenu() 在登录后注入，
  // 此处即使被调用也直接返回空数组，避免 axios 拦截器 401 风暴
  if (MOCK_AUTH) return ok([])
  return request({
    url: '/api/blade-system/menu/top-menu',
    method: 'get'
  })
}

export const getRoutes = (topMenuId) => {
  if (MOCK_AUTH) return ok([])
  return request({
    url: '/api/blade-system/menu/routes',
    method: 'get',
    params: { topMenuId }
  })
}
