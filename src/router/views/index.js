/**
 * 业务视图路由
 */
import Layout from '@/page/index/index.vue'

export default [
  {
    path: '/workbenches',
    component: Layout,
    redirect: '/workbenches/index',
    children: [
      {
        path: 'index',
        name: '工作台',
        meta: {
          keepAlive: false,
          isTab: true
        },
        component: () => import('@/views/workbenches/index.vue')
      }
    ]
  },
  {
    path: '/info',
    component: Layout,
    redirect: '/info/index',
    children: [
      {
        path: 'index',
        name: '个人信息',
        meta: { keepAlive: true, isTab: true },
        component: () => import('@/views/system/userinfo.vue')
      }
    ]
  }
]
