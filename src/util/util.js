/**
 * 通用工具函数
 */

/**
 * 动态加载样式
 */
export const loadStyle = (url) => {
  const link = document.createElement('link')
  link.type = 'text/css'
  link.rel = 'stylesheet'
  link.href = url
  const head = document.getElementsByTagName('head')[0]
  head.appendChild(link)
}

/**
 * 序列化对象为 URL 参数
 */
export const serialize = (data) => {
  const list = []
  Object.keys(data).forEach((ele) => {
    list.push(`${ele}=${data[ele]}`)
  })
  return list.join('&')
}

/**
 * 深拷贝
 */
export const deepClone = (obj) => {
  if (obj === null || typeof obj !== 'object') return obj
  if (obj instanceof Date) return new Date(obj)
  if (obj instanceof Array) {
    const arr = []
    for (let i = 0; i < obj.length; i++) {
      arr[i] = deepClone(obj[i])
    }
    return arr
  }
  if (obj instanceof Object) {
    const copy = {}
    for (const key in obj) {
      if (Object.prototype.hasOwnProperty.call(obj, key)) {
        copy[key] = deepClone(obj[key])
      }
    }
    return copy
  }
}

/**
 * 获取URL参数
 */
export const getUrlParams = (url) => {
  const params = {}
  const search = url.split('?')[1]
  if (search) {
    const strs = search.split('&')
    for (let i = 0; i < strs.length; i++) {
      params[strs[i].split('=')[0]] = decodeURIComponent(strs[i].split('=')[1])
    }
  }
  return params
}

/**
 * 生成随机字符串
 */
export const randomString = (len = 32) => {
  const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
  let str = ''
  for (let i = 0; i < len; i++) {
    str += chars.charAt(Math.floor(Math.random() * chars.length))
  }
  return str
}
