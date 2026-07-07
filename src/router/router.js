/**
 * 全站路由配置
 *
 * meta 参数说明
 * keepAlive 是否缓冲页面
 * isTab 是否加入到tag导航
 * isAuth 是否需要授权（false 为不需要）
 */
import { createRouter, createWebHashHistory } from 'vue-router'
import PageRouter from './page/'
import ViewsRouter from './views/'

// 创建路由
const router = createRouter({
  history: createWebHashHistory(),
  routes: [...PageRouter, ...ViewsRouter],
  scrollBehavior: () => ({ left: 0, top: 0 })
})

/**
 * 动态添加路由（用于后端菜单数据转换）
 * @param {Array} routes 路由列表
 */
export function addDynamicRoutes(routes = []) {
  routes.forEach((route) => {
    if (!router.hasRoute(route.name)) {
      router.addRoute(route)
    }
  })
}

/**
 * 重置路由（用于身份验证失败，重新登录时）
 */
export function resetRouter() {
  const newRouter = createRouter({
    history: createWebHashHistory(),
    routes: [...PageRouter, ...ViewsRouter],
    scrollBehavior: () => ({ left: 0, top: 0 })
  })
  newRouter.getRoutes().forEach((route) => {
    router.removeRoute(route.name)
  })
  newRouter.getRoutes().forEach((route) => {
    if (!router.hasRoute(route.name)) {
      router.addRoute(route)
    }
  })
}

export default router
