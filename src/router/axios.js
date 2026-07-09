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
import { Base64 } from 'js-base64'
import { baseUrl } from '@/config/env'
import NProgress from 'nprogress'
import 'nprogress/nprogress.css'
import router from '@/router/router'

// 默认超时时间
axios.defaults.timeout = 60000
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
    // Basic Auth
    config.headers['Authorization'] = `Basic ${Base64.encode(
      `${website.clientId}:${website.clientSecret}`
    )}`
    // 让每个请求携带token
    const meta = config.meta || {}
    const isToken = meta.isToken === false
    const token = getToken()
    if (token && !isToken) {
      config.headers[website.tokenHeader] = token
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
    // SXK 约定 code === 0 表示成功；BladeX 约定 HTTP 状态码（200/401/...）
    // 当响应体含 code 字段时优先使用，否则回退到 HTTP status
    const code = res.data.code
    const status = code !== undefined ? code : res.status
    const statusWhiteList = website.statusWhiteList || []
    const message = res.data.msg || res.data.error_description || '未知错误'

    // 白名单里的状态码自行 catch 处理
    if (statusWhiteList.includes(status)) return Promise.reject(res)

    // 401: token 无效，刷新token
    if (status === 401) {
      if (!isTokenRefreshing) {
        isTokenRefreshing = true
        // 动态导入避免循环依赖
        import('@/store/modules/user').then(({ useUserStore }) => {
          const userStore = useUserStore()
          userStore
            .refreshToken()
            .then(() => {
              ElMessage.success('Token已刷新，如有需要请重新操作')
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
    } else if (code !== undefined) {
      // SXK 业务错误码（code !== 0）：正常返回，由页面 else 分支处理
      return res
    } else if (res.status >= 400) {
      // 纯 HTTP 错误（无 code 字段，如 500/502）
      ElMessage({ message: message, type: 'error' })
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
