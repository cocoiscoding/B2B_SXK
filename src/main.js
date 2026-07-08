import { createApp } from 'vue'
import App from './App.vue'
import router from './router/router'
import pinia from './store'
import i18n from './lang'
import website from './config/website'
import { baseUrl, iconfontUrl, iconfontVersion } from './config/env'
import { loadStyle } from './util/util'

// Element Plus（通过 unplugin 自动按需引入组件，此处仅注册语言与全局配置）
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'

// 全局样式
import './styles/common.scss'
import './styles/layout.scss'
import './styles/login.scss'

// 路由权限
import './permission'

// 全局基础组件：必须在 app.component 之前显式 import，
// 因 unplugin-vue-components 已关闭 src/components 扫描。
import basicContainer from '@/components/basic-container/main.vue'
import basicBlock from '@/components/basic-block/main.vue'

const app = createApp(App)

// 注册插件
app.use(pinia)
app.use(router)
app.use(i18n)
app.use(ElementPlus, { locale: zhCn })

// 注册全局组件
app.component('basicContainer', basicContainer)
app.component('basicBlock', basicBlock)

// 全局属性
app.config.globalProperties.website = website
app.config.globalProperties.baseUrl = baseUrl

// 动态加载阿里云字体库
iconfontVersion.forEach((ele) => {
  loadStyle(iconfontUrl.replace('$key', ele))
})

app.mount('#app')
