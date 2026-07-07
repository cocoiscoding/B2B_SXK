// 阿里矢量图标库配置
let iconfontVersion = ['567566_pwc3oottzol']
let iconfontUrl = `//at.alicdn.com/t/font_$key.css`

let baseUrl = ''
let codeUrl = `${baseUrl}/code`
const env = import.meta.env

if (env.DEV) {
  baseUrl = `/api` // 开发环境地址
} else if (env.PROD) {
  baseUrl = `` // 生产环境地址
}

export { baseUrl, iconfontUrl, iconfontVersion, codeUrl, env }
