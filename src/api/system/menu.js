import request from '@/router/axios'

export const getTopMenu = () =>
  request({
    url: '/api/blade-system/menu/top-menu',
    method: 'get'
  })

export const getRoutes = (topMenuId) =>
  request({
    url: '/api/blade-system/menu/routes',
    method: 'get',
    params: { topMenuId }
  })
