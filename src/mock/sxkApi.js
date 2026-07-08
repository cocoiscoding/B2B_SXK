/**
 * 神行库业务接口调用层（Mock 模式）
 *
 * 设计要点：
 * 1. 命名与《神行库_接口设计文档 v1.1》保持一致（资源复数 / 动作子资源）。
 * 2. 每个方法返回 Promise<AxiosResponse> 形态的 { code, msg, data, trace_id }，
 *    兼容现有 axios 拦截器的 status === 200 判定（见 src/router/axios.js）。
 * 3. 当后端就绪后，只需把实现替换成 `request({...})`，
 *    业务页面 import 路径保持不变，最大化复用。
 */

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
   * 4.3.1 产品列表 GET /products
   */
  listProducts: ({ page = 1, size = 20, keyword = '', category = '' } = {}) => {
    return delay().then(() => {
      const kw = String(keyword || '').trim().toLowerCase()
      const filtered = mockProducts.filter((p) => {
        if (category && p.category !== category) return false
        if (!kw) return true
        const haystack = [p.name, p.category, p.description, ...(p.selling_points || [])]
          .join(' ')
          .toLowerCase()
        return haystack.includes(kw)
      })
      return ok(paginate(filtered, page, size))
    })
  },

  /**
   * 4.3.2 产品详情 GET /products/{id}
   */
  getProduct: (productId) => {
    return delay().then(() => {
      const found = mockProducts.find((p) => p.product_id === productId)
      if (!found) {
        return { code: 4041, msg: '产品不存在', data: null }
      }
      return ok(found)
    })
  },

  /**
   * 4.3.3 新增产品 POST /products
   */
  createProduct: (payload) => {
    return delay().then(() => {
      // BR-K-03 业务校验：必填字段
      if (!payload.name || !payload.category) {
        return { code: 4001, msg: '产品名称与分类为必填项', data: null }
      }
      // BR-K-03：至少 1 项功能特性
      if (!payload.features || payload.features.length === 0) {
        return { code: 4006, msg: '请至少添加一个内容块', data: null }
      }
      // 重名校验
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
   * 4.3.4 修改产品 PUT /products/{id}
   */
  updateProduct: (productId, payload) => {
    return delay().then(() => {
      const idx = mockProducts.findIndex((p) => p.product_id === productId)
      if (idx === -1) return { code: 4041, msg: '产品不存在', data: null }
      mockProducts[idx] = {
        ...mockProducts[idx],
        ...payload,
        updated_at: new Date().toISOString()
      }
      return ok(null)
    })
  },

  /**
   * 4.3.5 删除产品 DELETE /products/{id}（软删）
   */
  removeProduct: (productId) => {
    return delay().then(() => {
      const p = mockProducts.find((x) => x.product_id === productId)
      if (!p) return { code: 4041, msg: '产品不存在', data: null }
      p.is_deleted = true
      p.updated_at = new Date().toISOString()
      return ok(null)
    })
  },

  /**
   * 4.3.9 产品统计 GET /products/stats
   */
  getProductStats: () => {
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
   */
  getTemplate: (templateId) => {
    return delay().then(() => {
      const t = mockTemplates.find((x) => x.template_id === templateId)
      if (!t) return { code: 4041, msg: '模板不存在', data: null }
      return ok(t)
    })
  },

  /**
   * 4.5.3 创建自定义模板 POST /templates
   */
  createTemplate: (payload) => {
    return delay().then(() => {
      // BR-T-05：至少 1 个章节
      if (!payload.sections || payload.sections.length === 0) {
        return { code: 4006, msg: '请至少添加一个内容块', data: null }
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
        description: payload.description || '',
        prompt: payload.prompt || '',
        is_custom: true,
        use_count_30d: 0,
        tags: payload.tags || [],
        sections: payload.sections || [],
        updated_at: now
      }
      mockTemplates.push(tpl)
      return ok({ template_id: tpl.template_id })
    })
  },

  /**
   * 4.5.6 模板使用次数 +1（mock：仅自增 use_count_30d）
   */
  useTemplate: (templateId) => {
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
          { code: 'outline', name: '大纲' }
        ]
      })
    )
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

  /**
   * 4.6.11 场景参数 schema 元数据 GET /generations/schemas
   */
  getSceneSchemas: () => {
    return delay(100).then(() => ok({ scenes: mockSceneSchemas }))
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
