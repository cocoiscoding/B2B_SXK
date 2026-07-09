/**
 * 神行库业务接口调用层
 *
 * 设计要点：
 * 1. 每个方法返回 Promise，resolve 值统一为 { code, msg, data, trace_id } 形态，
 *    兼容现有 axios 拦截器的 status === 200 判定（见 src/router/axios.js）。
 * 3. 双轨开关：USE_MOCK_BIZ=true（默认）走本地 Mock 数据；
 *    后端就绪后在 .env.dev 改为 false，所有方法自动切换到真实 request() 链路，
 *    业务页面 import 路径与调用方式完全不变。
 */

import request from '@/router/axios'
import {
  ok,
  mockCurrentUser,
  mockProducts,
  mockTemplates,
  mockSceneSchemas,
  mockGenerations,
  mockVersionContents,
  mockAgentRunsDefault,
  mockAgentRunsCompetitor,
  mockValidationIssues,
  mockDashboardStats,
  mockProductStats,
  mockSceneNameMap
} from './data'

// 业务域 Mock 开关：由 .env.dev 中 VITE_APP_USE_MOCK_BIZ 控制
const USE_MOCK_BIZ = import.meta.env.VITE_APP_USE_MOCK_BIZ !== 'false'

// 真实链路统一封装：request() 返回 axios response { status, data: {code,msg,data} }，
// 此处提取 res.data，使其与 Mock 的 ok() 返回形态完全一致，调用方无感知切换。
const real = (config) => request(config).then((res) => res.data)

// ----------------- 工具：模拟延迟 -----------------
const delay = (ms = 300) => new Promise((resolve) => setTimeout(resolve, ms))

// ----------------- 工具：分页 -----------------
const paginate = (list, page = 1, size = 20) => {
  const start = (page - 1) * size
  return {
    items: list.slice(start, start + size),
    total: list.length,
    page,
    size
  }
}

// ----------------- 工具：按生成时间降序排序 -----------------
// 首页"最近生成"与"生成历史"列表必须共用同一排序逻辑，
// 才能保证首页展示的最近 3 条与历史表格首屏的前 3 条完全一致。
// mockGenerations 原始数组顺序并非严格按时间降序，因此需显式排序。
const sortByCreatedDesc = (list) =>
  [...list].sort((a, b) => new Date(b.created_at) - new Date(a.created_at))

// ============================================================
// 业务 API（全部基于 Mock 数据实现）
// ============================================================
export const sxkApi = {
  /**
   * 4.8.1 首页统计 GET /stats/dashboard
   */
  getDashboardStats: () => {
    return delay().then(() => ok(mockDashboardStats))
  },

  /**
   * 4.2.1 当前用户信息 GET /users/me
   */
  getCurrentUser: () => {
    return delay(150).then(() => ok(mockCurrentUser))
  },

  /**
   * 4.7.2 最近 3 条 GET /history/recent?limit=3
   * 按生成时间降序后取前 limit 条，与 listHistory 共用 sortByCreatedDesc
   */
  getRecentGenerations: (limit = 3) => {
    return delay().then(() => ok({ items: sortByCreatedDesc(mockGenerations).slice(0, limit) }))
  },

  // ----------------- 产品域（4.3） -----------------

  /**
   * 4.3.1 产品列表 GET /api/sxk/products
   * @param {number} page            页码（从 1 起）
   * @param {number} size            每页条数
   * @param {string} keyword         搜索关键词（可选）
   * @param {string} category        分类筛选（可选）
   * @param {string} sort            排序字段，默认 -updated_at（可选）
   * @param {boolean} include_deleted 是否包含已删除产品（可选）
   */
  listProducts: ({
    page = 1,
    size = 20,
    keyword = '',
    category = '',
    sort = '-updated_at',
    include_deleted = false
  } = {}) => {
    if (!USE_MOCK_BIZ) {
      return real({
        url: '/api/sxk/products',
        method: 'get',
        params: { page, size, keyword, category, sort, include_deleted }
      })
    }
    return delay().then(() => {
      const kw = String(keyword || '').trim().toLowerCase()
      let filtered = mockProducts.filter((p) => {
        if (!include_deleted && p.is_deleted) return false
        if (category && p.category !== category) return false
        if (!kw) return true
        const haystack = [p.name, p.category, p.description, ...(p.selling_points || [])]
          .join(' ')
          .toLowerCase()
        return haystack.includes(kw)
      })
      // 排序
      const desc = sort.startsWith('-')
      const field = desc ? sort.slice(1) : sort
      filtered = filtered.slice().sort((a, b) => {
        const va = a[field] || ''
        const vb = b[field] || ''
        if (va < vb) return desc ? 1 : -1
        if (va > vb) return desc ? -1 : 1
        return 0
      })
      return ok(paginate(filtered, page, size))
    })
  },

  /**
   * 4.3.2 产品详情 GET /api/sxk/products/{productId}
   */
  getProduct: (productId) => {
    if (!USE_MOCK_BIZ) {
      return real({
        url: `/api/sxk/products/${productId}`,
        method: 'get'
      })
    }
    return delay().then(() => {
      const found = mockProducts.find((p) => p.product_id === productId)
      if (!found) {
        return { code: 4041, msg: '产品不存在', data: null }
      }
      return ok(found)
    })
  },

  /**
   * 4.3.3 新增产品 POST /api/sxk/products
   */
  createProduct: (payload) => {
    if (!USE_MOCK_BIZ) {
      return real({
        url: '/api/sxk/products',
        method: 'post',
        data: payload
      })
    }
    return delay().then(() => {
      // BR-K-03 业务校验：必填字段
      if (!payload.name || !payload.category) {
        return { code: 4001, msg: '产品名称与分类为必填项', data: null }
      }
      // BR-K-04：至少 1 项功能特性
      if (!payload.features || payload.features.length === 0) {
        return { code: 4006, msg: '请至少添加一个功能特性', data: null }
      }
      // BR-K-03：同名校验（排除已删除）
      if (mockProducts.some((p) => p.name === payload.name && !p.is_deleted)) {
        return { code: 4091, msg: '产品名称已存在', data: null }
      }
      const now = new Date().toISOString()
      const product = {
        product_id: `p_${Date.now()}`,
        name: payload.name,
        category: payload.category,
        description: payload.description || '',
        pricing: payload.pricing || '',
        features: payload.features || [],
        target_customers: payload.target_customers || [],
        competitors: payload.competitors || [],
        selling_points: payload.selling_points || [],
        attachments: payload.attachments || { images: [], docs: [] },
        created_by: mockCurrentUser.user_id,
        created_at: now,
        updated_at: now,
        is_deleted: false
      }
      mockProducts.unshift(product)
      return ok({ product_id: product.product_id })
    })
  },

  /**
   * 4.3.4 修改产品 PUT /api/sxk/products/{productId}
   */
  updateProduct: (productId, payload) => {
    if (!USE_MOCK_BIZ) {
      return real({
        url: `/api/sxk/products/${productId}`,
        method: 'put',
        data: payload
      })
    }
    return delay().then(() => {
      const idx = mockProducts.findIndex((p) => p.product_id === productId)
      if (idx === -1) return { code: 4041, msg: '产品不存在', data: null }
      // BR-K-05：必填字段校验
      if (!payload.name || !payload.category) {
        return { code: 4001, msg: '产品名称与分类为必填项', data: null }
      }
      // BR-K-05：同名校验（排除自身）
      if (
        mockProducts.some(
          (p) => p.product_id !== productId && p.name === payload.name && !p.is_deleted
        )
      ) {
        return { code: 4091, msg: '产品名称已存在', data: null }
      }
      mockProducts[idx] = {
        ...mockProducts[idx],
        ...payload,
        attachments: payload.attachments || mockProducts[idx].attachments,
        updated_at: new Date().toISOString()
      }
      return ok(null)
    })
  },

  /**
   * 4.3.5 删除产品 DELETE /api/sxk/products/{productId}（软删）
   */
  removeProduct: (productId) => {
    if (!USE_MOCK_BIZ) {
      return real({
        url: `/api/sxk/products/${productId}`,
        method: 'delete'
      })
    }
    return delay().then(() => {
      const p = mockProducts.find((x) => x.product_id === productId)
      if (!p) return { code: 4041, msg: '产品不存在', data: null }
      p.is_deleted = true
      p.updated_at = new Date().toISOString()
      return ok(null)
    })
  },

  /**
   * 4.3.6 产品统计 GET /api/sxk/products/stats
   */
  getProductStats: () => {
    if (!USE_MOCK_BIZ) {
      return real({
        url: '/api/sxk/products/stats',
        method: 'get'
      })
    }
    return delay(150).then(() => ok(mockProductStats))
  },

  // ----------------- 模板域（4.5） -----------------

  /**
   * 4.5.1 模板列表 GET /templates
   */
  listTemplates: ({
    page = 1,
    size = 20,
    scene_code = '',
    keyword = '',
    is_custom = null
  } = {}) => {
    if (!USE_MOCK_BIZ) {
      return real({
        url: '/api/sxk/templates',
        method: 'get',
        params: { page, size, scene_code, keyword, is_custom }
      })
    }
    return delay().then(() => {
      const kw = String(keyword || '').trim().toLowerCase()
      const filtered = mockTemplates.filter((t) => {
        if (scene_code && t.scene_code !== scene_code) return false
        if (is_custom !== null && t.is_custom !== is_custom) return false
        if (!kw) return true
        return (t.name + ' ' + (t.description || '')).toLowerCase().includes(kw)
      })
      return ok(paginate(filtered, page, size))
    })
  },

  /**
   * 4.5.2 模板详情 GET /templates/{id}
   * 返回模板本身 + 同场景下所有模板列表（templates 数组）
   */
  getTemplate: (templateId) => {
    if (!USE_MOCK_BIZ) {
      return real({
        url: `/api/sxk/templates/${templateId}`,
        method: 'get'
      })
    }
    return delay().then(() => {
      const t = mockTemplates.find((x) => x.template_id === templateId)
      if (!t) return { code: 4041, msg: '模板不存在', data: null }
      // 附带同场景下的所有模板（用于详情弹窗"已有模板"区块）
      const siblings = mockTemplates
        .filter((x) => x.scene_code === t.scene_code)
        .map((x) => ({
          template_id: x.template_id,
          name: x.name,
          output_format: x.output_format,
          description: x.description,
          use_count_30d: x.use_count_30d,
          updated_at: x.updated_at
        }))
      return ok({ ...t, templates: siblings })
    })
  },

  /**
   * 4.5.3 创建子模板 POST /templates
   */
  createTemplate: (payload) => {
    if (!USE_MOCK_BIZ) {
      return real({
        url: '/api/sxk/templates',
        method: 'post',
        data: payload
      })
    }
    return delay().then(() => {
      // BR-T-05：sections 可选，如提供则至少 1 个
      if (payload.sections && payload.sections.length === 0) {
        return { code: 4006, msg: '内容结构至少需要 1 个章节', data: null }
      }
      // BR-T-04：场景下重名校验
      if (
        mockTemplates.some(
          (t) => t.scene_code === payload.scene_code && t.name === payload.name
        )
      ) {
        return { code: 4092, msg: '当前场景下已存在同名模板', data: null }
      }
      const now = new Date().toISOString()
      const tpl = {
        template_id: `t_${Date.now()}`,
        name: payload.name,
        scene_code: payload.scene_code,
        output_format: payload.output_format || 'long_text',
        style: payload.style || '',
        description: payload.description || '',
        prompt: payload.prompt || '',
        is_custom: true,
        use_count_30d: 0,
        sections: payload.sections || [],
        updated_at: now
      }
      mockTemplates.push(tpl)
      return ok({ template_id: tpl.template_id })
    })
  },

  /**
   * 4.5.4 更新子模板 PUT /templates/{id}
   */
  updateTemplate: (templateId, payload) => {
    if (!USE_MOCK_BIZ) {
      return real({
        url: `/api/sxk/templates/${templateId}`,
        method: 'put',
        data: payload
      })
    }
    return delay().then(() => {
      const idx = mockTemplates.findIndex((x) => x.template_id === templateId)
      if (idx === -1) return { code: 4041, msg: '模板不存在', data: null }
      // BR-T-04：场景下重名校验（排除自身）
      if (
        mockTemplates.some(
          (t) =>
            t.template_id !== templateId &&
            t.scene_code === mockTemplates[idx].scene_code &&
            t.name === payload.name
        )
      ) {
        return { code: 4092, msg: '当前场景下已存在同名模板', data: null }
      }
      mockTemplates[idx] = {
        ...mockTemplates[idx],
        ...payload,
        updated_at: new Date().toISOString()
      }
      return ok(null)
    })
  },

  /**
   * 4.5.5 删除子模板 DELETE /templates/{id}
   */
  deleteTemplate: (templateId) => {
    if (!USE_MOCK_BIZ) {
      return real({
        url: `/api/sxk/templates/${templateId}`,
        method: 'delete'
      })
    }
    return delay().then(() => {
      const idx = mockTemplates.findIndex((x) => x.template_id === templateId)
      if (idx === -1) return { code: 4041, msg: '模板不存在', data: null }
      // BR-T-06：预置模板不可删除
      if (!mockTemplates[idx].is_custom) {
        return { code: 4030, msg: '预置模板不可删除', data: null }
      }
      mockTemplates.splice(idx, 1)
      return ok(null)
    })
  },

  /**
   * 4.5.6 模板使用次数 +1 POST /templates/{id}/use
   */
  useTemplate: (templateId) => {
    if (!USE_MOCK_BIZ) {
      return real({
        url: `/api/sxk/templates/${templateId}/use`,
        method: 'post'
      })
    }
    return delay(80).then(() => {
      const t = mockTemplates.find((x) => x.template_id === templateId)
      if (t) t.use_count_30d += 1
      return ok(null)
    })
  },

  /**
   * 4.5.7 模板场景与标签元数据 GET /templates/meta
   */
  getTemplateMeta: () => {
    if (!USE_MOCK_BIZ) {
      return real({
        url: '/api/sxk/templates/meta',
        method: 'get'
      })
    }
    return delay(80).then(() =>
      ok({
        scene_codes: [
          { code: 'product_intro', name: '产品介绍文案' },
          { code: 'competitor', name: '竞品对比报告' },
          { code: 'channel_adapt', name: '多渠道适配' },
          { code: 'email', name: '邮件营销' },
          { code: 'event', name: '活动宣传' },
          { code: 'other', name: '其他' }
        ],
        output_formats: [
          { code: 'long_text', name: '长文案' },
          { code: 'short_text', name: '短文案' },
          { code: 'table', name: '表格' },
          { code: 'outline', name: '大纲' },
          { code: 'email', name: '邮件' }
        ]
      })
    )
  },

  // ----------------- 场景域（4.5.8~10） -----------------

  /**
   * 4.5.8 场景列表 GET /scenes
   */
  getSceneSchemas: () => {
    if (!USE_MOCK_BIZ) {
      return real({
        url: '/api/sxk/scenes',
        method: 'get'
      })
    }
    return delay(100).then(() => ok({ scenes: mockSceneSchemas }))
  },

  /**
   * 4.5.9 新增场景 POST /scenes
   */
  createScene: (payload) => {
    if (!USE_MOCK_BIZ) {
      return real({
        url: '/api/sxk/scenes',
        method: 'post',
        data: payload
      })
    }
    return delay().then(() => {
      // BR-T-01：场景名称不可重复
      if (mockSceneSchemas.some((s) => s.name === payload.name)) {
        return { code: 4092, msg: '场景名称已存在', data: null }
      }
      // 将 { 参数名: 参数值 } 对象转为 params 数组
      const params = Object.entries(payload.params || {}).map(([label, desc]) => {
        if (typeof desc === 'string' && desc.includes(' / ')) {
          return { key: label, type: 'enum', label, options: desc.split(' / ').map((s) => s.trim()), required: true, default: desc.split(' / ')[0].trim() }
        }
        return { key: label, type: 'text', label, required: true, default: desc }
      })
      const scene_code = `custom_${Date.now()}`
      const scene = {
        scene_code,
        name: payload.name,
        description: payload.description || '',
        color: payload.color || 'blue',
        icon: payload.icon || 'document',
        params
      }
      mockSceneSchemas.push(scene)
      return ok({ scene_code })
    })
  },

  /**
   * 4.5.10 更新场景 PUT /scenes/{scene_code}
   */
  updateScene: (sceneCode, payload) => {
    if (!USE_MOCK_BIZ) {
      return real({
        url: `/api/sxk/scenes/${sceneCode}`,
        method: 'put',
        data: payload
      })
    }
    return delay().then(() => {
      const idx = mockSceneSchemas.findIndex((s) => s.scene_code === sceneCode)
      if (idx === -1) return { code: 4041, msg: '场景不存在', data: null }
      // BR-T-01：场景名称不可与其他场景重复
      if (
        mockSceneSchemas.some(
          (s) => s.scene_code !== sceneCode && s.name === payload.name
        )
      ) {
        return { code: 4092, msg: '场景名称已存在', data: null }
      }
      // 将 { 参数名: 参数值 } 对象转回 params 数组
      const params = Object.entries(payload.params || {}).map(([label, desc]) => {
        // 尝试匹配原有参数以保留 key/type 等字段
        const orig = mockSceneSchemas[idx].params.find(
          (p) => p.label === label || p.key === label
        )
        if (orig) {
          if (typeof desc === 'string' && desc.includes(' / ')) {
            return { ...orig, label, options: desc.split(' / ').map((s) => s.trim()) }
          }
          return { ...orig, label, default: desc }
        }
        return { key: label, type: 'text', label, required: false, default: desc }
      })
      mockSceneSchemas[idx] = {
        ...mockSceneSchemas[idx],
        name: payload.name,
        description: payload.description,
        color: payload.color,
        icon: payload.icon,
        params
      }
      return ok(null)
    })
  },

  // ----------------- 生成域（4.6） -----------------

  /**
   * 4.6.1 触发生成 POST /generations
   * mock：根据 scene_code 异步"模拟"Agent 执行，最终落库到 mockGenerations。
   */
  triggerGeneration: (payload) => {
    return delay(200).then(() => {
      // BR-G-01：产品 + 场景必填
      if (!payload.product_id || !payload.scene_code) {
        return { code: 4007, msg: '请填写必填参数', data: null }
      }
      const product = mockProducts.find((p) => p.product_id === payload.product_id)
      if (!product) return { code: 4041, msg: '产品不存在', data: null }
      if (product.is_deleted) return { code: 4042, msg: '该产品已删除', data: null }

      const generation_id = `g_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`
      const templatesByScene = mockTemplates.filter((t) => t.scene_code === payload.scene_code)
      const template = templatesByScene[0] || mockTemplates[0]
      const now = new Date().toISOString()

      const record = {
        generation_id,
        product: {
          product_id: product.product_id,
          name: product.name,
          is_deleted: product.is_deleted
        },
        template: { template_id: template.template_id, name: template.name },
        status: 'success', // mock 直接成功
        selected_version: payload.scene_code === 'competitor' ? 'A' : 'A',
        duration_ms: 11000 + Math.floor(Math.random() * 4000),
        params: payload.params || {},
        created_at: now,
        updated_at: now,
        archived_at: null
      }
      mockGenerations.unshift(record)
      // 同时准备一份版本内容（使用"建议 A"首版本示例）
      mockVersionContents[generation_id] = [
        {
          version_key: 'A',
          name: '版本 A: 推荐版本',
          is_recommended: true,
          content_html: `<h2>${product.name}</h2><p>基于场景 [${
            mockSceneNameMap[payload.scene_code] || payload.scene_code
          }] 与所选参数自动生成的内容样例（mock）。</p>`,
          word_count: 360
        },
        {
          version_key: 'B',
          name: '版本 B: 备选风格',
          is_recommended: false,
          content_html: `<h2>${product.name}</h2><p>备选风格内容样例（mock）。</p>`,
          word_count: 320
        }
      ]
      return ok({ generation_id, status: 'success', estimated_ms: record.duration_ms })
    })
  },

  /**
   * 4.6.2 生成详情 GET /generations/{id}
   */
  getGeneration: (generationId) => {
    return delay().then(() => {
      const g = mockGenerations.find((x) => x.generation_id === generationId)
      if (!g) return { code: 4041, msg: '生成记录不存在', data: null }
      const versions = mockVersionContents[generationId] || []
      return ok({ ...g, versions })
    })
  },

  /**
   * 4.6.3 单版本内容 GET /generations/{id}/versions/{key}
   */
  getVersionContent: (generationId, versionKey) => {
    return delay(150).then(() => {
      const list = mockVersionContents[generationId] || []
      const v = list.find((x) => x.version_key === versionKey)
      if (!v) return { code: 4041, msg: '版本不存在', data: null }
      // FIX-4：附带 validation_summary
      const issues = mockValidationIssues[`${generationId}:${versionKey}`] || []
      return ok({
        ...v,
        content_markdown: v.content_html.replace(/<[^>]+>/g, ''),
        validation_summary: {
          total: issues.length,
          error: issues.filter((x) => x.severity === 'error').length,
          warn: issues.filter((x) => x.severity === 'warn').length,
          info: issues.filter((x) => x.severity === 'info').length,
          passed: issues.every((x) => x.severity !== 'error')
        }
      })
    })
  },

  /**
   * 4.6.6 选用版本 POST /generations/{id}/select
   */
  selectVersion: (generationId, versionKey) => {
    return delay(150).then(() => {
      const g = mockGenerations.find((x) => x.generation_id === generationId)
      if (!g) return { code: 4041, msg: '生成记录不存在', data: null }
      g.selected_version = versionKey
      g.updated_at = new Date().toISOString()
      return ok({ generation_id: generationId, selected_version: versionKey })
    })
  },

  /**
   * 4.6.8 Agent 协作进度 GET /generations/{id}/agents
   * 复用 mock 阶段数据，返回 4 个 Agent 节点
   */
  getAgentRuns: (generationId, sceneCode = 'product_intro') => {
    return delay(100).then(() => {
      // Deep clone 避免污染原常量
      const base =
        sceneCode === 'competitor' ? mockAgentRunsCompetitor : mockAgentRunsDefault
      return ok({ runs: JSON.parse(JSON.stringify(base)) })
    })
  },

  /**
   * 4.6.9 校验问题列表 GET /generations/{id}/versions/{key}/issues
   */
  getValidationIssues: (generationId, versionKey) => {
    return delay(120).then(() => {
      const list = mockValidationIssues[`${generationId}:${versionKey}`] || []
      return ok({ issues: list })
    })
  },

  // ----------------- 历史域（4.7） -----------------

  /**
   * 4.7.1 历史列表 GET /history
   * 先按生成时间降序，再做条件筛选与分页，
   * 保证与首页"最近生成"的数据顺序一致。
   */
  listHistory: ({
    page = 1,
    size = 20,
    keyword = '',
    scene_code = '',
    template_id = '',
    status = ''
  } = {}) => {
    return delay().then(() => {
      const kw = String(keyword || '').trim().toLowerCase()
      // 先排序，再筛选（顺序与 getRecentGenerations 完全一致）
      const sorted = sortByCreatedDesc(mockGenerations)
      const filtered = sorted.filter((g) => {
        if (template_id && g.template.template_id !== template_id) return false
        if (status && g.status !== status) return false
        if (kw && !g.product.name.toLowerCase().includes(kw)) return false
        return true
      })
      return ok(paginate(filtered, page, size))
    })
  },

  /**
   * 4.7.3 删除历史 DELETE /history/{id}
   */
  removeHistory: (generationId) => {
    return delay(150).then(() => {
      const idx = mockGenerations.findIndex((x) => x.generation_id === generationId)
      if (idx === -1) return { code: 4041, msg: '记录不存在', data: null }
      mockGenerations.splice(idx, 1)
      return ok(null)
    })
  },

  // ----------------- 通用占位 -----------------
  noop: () => Promise.resolve(ok(null))
}

export default sxkApi
