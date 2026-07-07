/**
 * 全站权限配置
 */
import router from './router/router'
import { useUserStore } from './store/modules/user'
import { useCommonStore } from './store/modules/common'
import { useTagsStore } from './store/modules/tags'
import { validatenull } from './util/validate'
import { getToken } from './util/auth'
import NProgress from 'nprogress'
import 'nprogress/nprogress.css'

NProgress.configure({ showSpinner: false })

const whiteList = ['/login', '/register', '/lock', '/404', '/403', '/500']

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
        // 添加标签页
        const tagsStore = useTagsStore()
        const value = to.query.src || to.fullPath
        const label = to.query.name || to.name
        if (meta.isTab !== false && !validatenull(value) && !validatenull(label)) {
          tagsStore.addTag({
            label: label,
            value: value,
            params: to.params,
            query: to.query,
            meta: meta,
            group: []
          })
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
