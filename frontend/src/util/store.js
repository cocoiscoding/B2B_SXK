import { validatenull } from './validate'
import website from '@/config/website'

const keyName = website.key + '-'

/**
 * 存储sessionStorage
 */
export const setStore = (params = {}) => {
  let { name, content, type } = params
  name = keyName + name
  let obj = {
    dataType: typeof content,
    content: content,
    type: type,
    datetime: new Date().getTime()
  }
  if (type) window.sessionStorage.setItem(name, JSON.stringify(obj))
  else window.sessionStorage.setItem(name, JSON.stringify(obj))
}

/**
 * 获取sessionStorage
 */
export const getStore = (params = {}) => {
  let { name, debug } = params
  name = keyName + name
  let obj = {},
    content
  obj = window.sessionStorage.getItem(name)
  if (validatenull(obj)) return
  try {
    obj = JSON.parse(obj)
  } catch {
    return obj
  }
  if (debug) {
    return obj
  }
  if (obj.dataType == 'string') {
    content = obj.content
  } else if (obj.dataType == 'number') {
    content = Number(obj.content)
  } else if (obj.dataType == 'boolean') {
    content = obj.content === 'true'
  } else if (obj.dataType == 'object') {
    content = obj.content
  }
  return content
}

/**
 * 删除sessionStorage
 */
export const removeStore = (params = {}) => {
  let { name } = params
  name = keyName + name
  window.sessionStorage.removeItem(name)
}

/**
 * 获取全部sessionStorage
 */
export const getAllStore = () => {
  let list = []
  for (let i = 0; i < window.sessionStorage.length; i++) {
    let name = window.sessionStorage.key(i)
    list.push({
      name: name,
      content: getStore({ name: name })
    })
  }
  return list
}

/**
 * 清空全部sessionStorage
 */
export const clearStore = () => {
  window.sessionStorage.clear()
}
