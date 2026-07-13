/**
 * 全站http配置
 *
 * axios参数说明
 * isSerialize 是否开启form表单提交
 * isToken 是否需要token（通过 config.meta.isToken 配置）
 */
import axios from 'axios'
import { ElMessage } from 'element-plus'
import { serialize } from '@/util/util'
import { getToken } from '@/util/auth'
import { isURL } from '@/util/validate'
import website from '@/config/website'
import { baseUrl } from '@/config/env'
import NProgress from 'nprogress'
import 'nprogress/nprogress.css'
import router from '@/router/router'

// 默认超时时间（5 分钟：内容生成的 adapt/finalize 在多 Tab 并发时需调多次 LLM，耗时长）
axios.defaults.timeout = 300000
// 返回其他状态码
axios.defaults.validateStatus = function (status) {
  return status >= 200 && status <= 500
}
// 跨域请求，允许保存cookie
axios.defaults.withCredentials = true

// NProgress 配置
NProgress.configure({ showSpinner: false })

// http request 拦截
axios.interceptors.request.use(
  (config) => {
    NProgress.start()
    // 地址为已配置状态则不添加前缀
    if (!isURL(config.url) && !config.url.startsWith(baseUrl)) {
      config.url = baseUrl + config.url
    }
    // 鉴权：meta.isToken === false 的请求（登录/注册）不附加 token
    // 其他请求携带 Authorization: Bearer <token>（后端 FastAPI 标准 OAuth2）
    const meta = config.meta || {}
    const skipToken = meta.isToken === false
    const token = getToken()
    if (token && !skipToken) {
      config.headers['Authorization'] = `Bearer ${token}`
    }
    // headers 中配置 text 请求
    if (config.text === true) {
      config.headers['Content-Type'] = 'text/plain'
    }
    // headers 中配置 serialize 为 true 开启序列化
    if (config.method === 'post' && meta.isSerialize === true) {
      config.data = serialize(config.data)
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

let isTokenRefreshing = false

// http response 拦截
axios.interceptors.response.use(
  (res) => {
    NProgress.done()

    // 两种响应格式：
    // 1. Mock（SXK 壳）：{ code: 0, msg, data } — code === 0 表示成功
    // 2. 后端（FastAPI）：直接返回对象体，错误为 { detail: "..." } + HTTP 4xx/5xx
    const meta = (res.config && res.config.meta) || {}
    const skipToken = meta.isToken === false
    const code = res.data.code
    const hasCode = code !== undefined

    // 错误消息：detail（FastAPI）优先，msg（Mock/SXK）兜底
    let message = res.data.detail || res.data.msg || res.data.error_description || '未知错误'
    if (Array.isArray(message)) {
      message = message.map((e) => e.msg || JSON.stringify(e)).join('; ')
    }

    const statusWhiteList = website.statusWhiteList || []

    // --- Mock/SXK 壳格式：有 code 字段 ---
    if (hasCode) {
      if (statusWhiteList.includes(code)) return Promise.reject(res)
      if (code === 0) return res // 成功
      // Mock 业务错误码：正常返回，由调用方处理
      return res
    }

    // --- 后端格式：无 code 字段，按 HTTP 状态码判断 ---
    const httpStatus = res.status
    if (statusWhiteList.includes(httpStatus)) return Promise.reject(res)

    if (httpStatus === 401) {
      // 登录/注册请求的 401 是凭证错误，不走 token 刷新
      if (!skipToken && !isTokenRefreshing) {
        isTokenRefreshing = true
        import('@/store/modules/user').then(({ useUserStore }) => {
          const userStore = useUserStore()
          userStore
            .refreshToken()
            .then(() => {
              ElMessage.success('Token 已刷新，如有需要请重新操作')
            })
            .catch(() => {
              userStore.fedLogOut().then(() => {
                router.push({ path: '/login' })
              })
            })
            .finally(() => {
              isTokenRefreshing = false
            })
        })
      }
      ElMessage({ message, type: 'error' })
      return Promise.reject(new Error(message))
    }

    if (httpStatus >= 400) {
      ElMessage({ message, type: 'error' })
      return Promise.reject(new Error(message))
    }

    return res
  },
  (error) => {
    NProgress.done()
    return Promise.reject(new Error(error))
  }
)

export default axios
