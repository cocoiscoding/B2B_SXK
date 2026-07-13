/**
 * 全站权限配置
 */
import router from './router/router'
import { useUserStore } from './store/modules/user'
import { useCommonStore } from './store/modules/common'
import { useTagsStore, generateTabId } from './store/modules/tags'
import { validatenull } from './util/validate'
import { getToken } from './util/auth'
import { ElMessage } from 'element-plus'
import NProgress from 'nprogress'
import 'nprogress/nprogress.css'

NProgress.configure({ showSpinner: false })

const whiteList = ['/login', '/register', '/lock', '/404', '/403', '/500']

// 首页路径（不需要 tabId，使用固定 tabId 'tab_welcome'）
const isDashboard = (path) => path === '/dashboard' || path === '/dashboard/index'

router.beforeEach((to, from, next) => {
  const meta = to.meta || {}
  NProgress.start()

  // 设置菜单标识
  const commonStore = useCommonStore()
  const isMenu = meta.menu === undefined ? to.query.menu : meta.menu
  commonStore.setIsMenu(isMenu === undefined)

  if (getToken()) {
    const userStore = useUserStore()
    if (commonStore.isLock && to.path !== '/lock') {
      // 系统激活锁屏，全部跳转到锁屏页
      next({ path: '/lock' })
    } else if (to.path === '/login') {
      // 登录成功访问登录页跳转到主页
      next({ path: '/' })
    } else {
      // 如果 token 存在但用户信息为空，需要重新获取
      if (!userStore.token) {
        userStore.fedLogOut().then(() => {
          next({ path: '/login' })
        })
      } else {
        // 管理员路由守卫：requiresAdmin 标记的路由仅管理员可访问
        if (meta.requiresAdmin && !userStore.userInfo?.is_admin) {
          ElMessage({ message: '该页面仅管理员可访问', type: 'error' })
          next({ path: '/dashboard/index' })
          return
        }

        // ====== 多 Tab：tabId 生成 ======
        // 非首页的业务页面，如果没有 tabId，则生成一个并重定向
        if (meta.isTab !== false && !isDashboard(to.path) && !to.query.tabId) {
          const tabId = generateTabId()
          next({
            path: to.path,
            query: { ...to.query, tabId }
          })
          return
        }

        // ====== 添加标签页 ======
        const tagsStore = useTagsStore()
        const label = to.query.name || to.name
        if (meta.isTab !== false && !validatenull(label)) {
          if (isDashboard(to.path)) {
            // 首页：固定 tabId，不可关闭
            tagsStore.addTag({
              label: label,
              value: '/dashboard',
              tabId: 'tab_welcome',
              params: to.params,
              query: {},
              meta: meta,
              group: [],
              close: false
            })
          } else {
            tagsStore.addTag({
              label: label,
              value: to.fullPath,
              tabId: to.query.tabId,
              params: to.params,
              query: to.query,
              meta: meta,
              group: [],
              close: true
            })
          }
        }
        next()
      }
    }
  } else {
    // 没有token，判断是否需要认证
    if (whiteList.includes(to.path) || meta.isAuth === false) {
      next()
    } else {
      next('/login')
    }
  }
})

router.afterEach(() => {
  NProgress.done()
})
