/**
 * 页面级路由（登录、注册、锁屏、错误页等）
 */
import Layout from '@/page/index/index.vue'

export default [
  {
    path: '/login',
    name: '登录页',
    component: () => import('@/page/login/index.vue'),
    meta: {
      keepAlive: true,
      isTab: false,
      isAuth: false
    }
  },
  {
    path: '/register',
    name: '注册页',
    component: () => import('@/page/register/index.vue'),
    meta: {
      keepAlive: true,
      isTab: false,
      isAuth: false
    }
  },
  {
    path: '/lock',
    name: '锁屏页',
    component: () => import('@/page/lock/index.vue'),
    meta: {
      keepAlive: true,
      isTab: false,
      isAuth: false
    }
  },
  {
    path: '/404',
    component: () => import('@/components/error-page/404.vue'),
    name: '404',
    meta: { keepAlive: true, isTab: false, isAuth: false }
  },
  {
    path: '/403',
    component: () => import('@/components/error-page/403.vue'),
    name: '403',
    meta: { keepAlive: true, isTab: false, isAuth: false }
  },
  {
    path: '/500',
    component: () => import('@/components/error-page/500.vue'),
    name: '500',
    meta: { keepAlive: true, isTab: false, isAuth: false }
  },
  {
    path: '/',
    name: '首页',
    redirect: '/workbenches/index'
  },
  {
    path: '/myiframe',
    component: Layout,
    redirect: '/myiframe',
    children: [
      {
        path: ':routerPath',
        name: 'iframe',
        component: () => import('@/components/iframe/main.vue'),
        props: true
      }
    ]
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/404'
  }
]
