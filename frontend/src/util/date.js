/**
 * 日期工具函数
 */

/**
 * 计算两个时间的时间差
 * @param {number} startTime 开始时间戳
 * @param {number} endTime 结束时间戳
 */
export const calcDate = (startTime, endTime) => {
  if (!startTime || !endTime) return null
  const diff = endTime - startTime
  const result = {}
  if (diff < 0) return null
  result.seconds = Math.floor(diff / 1000)
  result.minutes = Math.floor(result.seconds / 60)
  result.hours = Math.floor(result.minutes / 60)
  result.days = Math.floor(result.hours / 24)
  return result
}

/**
 * 格式化日期
 * @param {Date|string|number} date 日期
 * @param {string} fmt 格式
 */
export const formatDate = (date, fmt = 'yyyy-MM-dd hh:mm:ss') => {
  if (!date) return ''
  if (typeof date === 'string' || typeof date === 'number') {
    date = new Date(date)
  }
  const o = {
    'M+': date.getMonth() + 1, // 月份
    'd+': date.getDate(), // 日
    'h+': date.getHours(), // 小时
    'm+': date.getMinutes(), // 分
    's+': date.getSeconds(), // 秒
    'q+': Math.floor((date.getMonth() + 3) / 3), // 季度
    S: date.getMilliseconds() // 毫秒
  }
  if (/(y+)/.test(fmt)) {
    fmt = fmt.replace(RegExp.$1, (date.getFullYear() + '').substr(4 - RegExp.$1.length))
  }
  for (const k in o) {
    if (new RegExp('(' + k + ')').test(fmt)) {
      fmt = fmt.replace(RegExp.$1, RegExp.$1.length === 1 ? o[k] : ('00' + o[k]).substr(('' + o[k]).length))
    }
  }
  return fmt
}
