/**
 * 业务视图路由
 *
 * 神行库（SXK）业务路由：
 *   /dashboard  首页
 *   /knowledge  产品知识库
 *   /generate   内容生成（4 Tab：编辑/Agent协作/渠道预览/多版本对比）
 *   /history    生成历史
 *   /templates  场景模板管理
 *
 * 保留：
 *   /workbenches 旧入口，等同 /dashboard
 *   /info        个人信息（来自参考项目，沿用）
 */
import Layout from '@/page/index/index.vue'

export default [
  // ============ 神行库 5 大业务页面 ============
  {
    path: '/dashboard',
    component: Layout,
    redirect: '/dashboard/index',
    children: [
      {
        path: 'index',
        name: '首页',
        meta: { keepAlive: true, isTab: true, title: '首页' },
        component: () => import('@/views/sxk/dashboard/index.vue')
      }
    ]
  },
  {
    path: '/knowledge',
    component: Layout,
    redirect: '/knowledge/index',
    children: [
      {
        path: 'index',
        name: '产品知识库',
        meta: { keepAlive: false, isTab: true, title: '产品知识库' },
        component: () => import('@/views/sxk/knowledge/index.vue')
      }
    ]
  },
  {
    path: '/generate',
    component: Layout,
    redirect: '/generate/index',
    children: [
      {
        path: 'index',
        name: '内容生成',
        meta: { keepAlive: true, isTab: true, title: '内容生成' },
        component: () => import('@/views/sxk/generate/index.vue')
      }
    ]
  },
  {
    path: '/history',
    component: Layout,
    redirect: '/history/index',
    children: [
      {
        path: 'index',
        name: '生成历史',
        meta: { keepAlive: false, isTab: true, title: '生成历史' },
        component: () => import('@/views/sxk/history/index.vue')
      }
    ]
  },
  {
    path: '/templates',
    component: Layout,
    redirect: '/templates/index',
    children: [
      {
        path: 'index',
        name: '场景模板管理',
        meta: { keepAlive: false, isTab: true, title: '场景模板管理' },
        component: () => import('@/views/sxk/templates/index.vue')
      }
    ]
  },
  {
    path: '/members',
    component: Layout,
    redirect: '/members/index',
    children: [
      {
        path: 'index',
        name: '成员管理',
        meta: { keepAlive: false, isTab: true, title: '成员管理', requiresAdmin: true },
        component: () => import('@/views/sxk/members/index.vue')
      }
    ]
  },

  // ============ 旧业务页（保留） ============
  {
    path: '/workbenches',
    component: Layout,
    redirect: '/workbenches/index',
    children: [
      {
        path: 'index',
        name: '工作台',
        meta: {
          keepAlive: true,
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
