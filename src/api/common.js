import request from '@/router/axios'

/**
 * 通用 API 示例（按业务域扩展）
 */
export const commonApi = {
  // 示例：获取字典数据
  getDict: (code) =>
    request({
      url: '/api/blade-system/dict/dictionary',
      method: 'get',
      params: { code }
    })
}
