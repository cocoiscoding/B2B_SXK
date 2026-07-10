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
// 首页"最近生成"与"历史列表"列表必须共用同一排序逻辑，
// 才能保证首页展示的最近 3 条与历史表格首屏的前 3 条完全一致。
// mockGenerations 原始数组顺序并非严格按时间降序，因此需显式排序。
const sortByCreatedDesc = (list) =>
  [...list].sort((a, b) => new Date(b.created_at) - new Date(a.created_at))

// ----------------- 工具：预置模板检测 -----------------
// 后端预置模板 ID 为 T001~T008 格式，用户自定义模板 ID 为 T + 6位hex
// 据此在前端区分预置 vs 自定义，用于标签展示和"预置不可删除"规则
const isPresetTemplate = (id) => /^T\d{3}$/.test(id)

// ----------------- 工具：适配后端模板格式 → 前端格式 -----------------
// 后端模板字段：id, scenario_id, name, tag, description, prompt, constraints, structure, ...
// 前端模板字段：template_id, scene_code, output_format, is_custom, sections, ...
const adaptTemplate = (t) => {
  if (!t) return t
  // 已经是前端格式（mock 数据或已适配过），做轻量兼容
  if (t.template_id) {
    return { ...t, is_custom: !isPresetTemplate(t.template_id) }
  }
  // 后端原始格式适配
  const constraints = t.constraints || {}
  return {
    template_id: t.id,
    name: t.name,
    scene_code: t.scenario_id,
    tag: t.tag || '',
    description: t.description || '',
    prompt: t.prompt || '',
    style: constraints.style || '',
    output_format: constraints.output_format || 'long_text',
    sections: t.structure || '',
    examples: t.examples || [],
    differentiation_dims: t.differentiation_dims || [],
    applicable_channels: t.applicable_channels || [],
    tags: t.tags || [],
    is_custom: !isPresetTemplate(t.id),
    use_count_30d: t.use_count_30d || 0,
    created_at: t.created_at || '',
    updated_at: t.updated_at || t.created_at || ''
  }
}

// ----------------- 工具：适配后端场景格式 → 前端格式 -----------------
// 后端场景字段：id, name, description, parameters([{name, description}])
// 前端场景字段：scene_code, name, description, params([{key, type, label, default, ...}])
const adaptScene = (s) => {
  if (!s) return s
  // 已经是前端格式（mock 数据），直接返回
  if (s.scene_code) return s
  // 后端原始格式适配
  const params = (s.parameters || []).map((p, i) => ({
    key: p.name || `param_${i}`,
    type: 'text',
    label: p.name || '',
    required: true,
    default: p.description || ''
  }))
  return {
    scene_code: s.id,
    name: s.name,
    description: s.description || '',
    color: s.color || 'blue',
    icon: s.icon || 'document',
    params,
    created_at: s.created_at || ''
  }
}

/**
 * 后端 Product → 前端格式适配
 * 后端: {id, name, category: [], features: [{name, description}], images: [], documents: []}
 * 前端: {product_id, name, category: "str", features: [{name, description, sort_order}], attachments: {images, docs}}
 */
const adaptProduct = (p) => {
  if (!p) return p
  if (p.product_id) return p
  const cat = p.category
  return {
    product_id: p.id,
    name: p.name,
    category: Array.isArray(cat) ? cat.join(', ') : (cat || ''),
    description: p.description || '',
    pricing: p.pricing || '',
    features: p.features || [],
    target_customers: p.target_customers || [],
    competitors: [],
    selling_points: p.selling_points || [],
    attachments: {
      images: p.images || [],
      docs: p.documents || []
    },
    created_by: p.created_by || '',
    created_at: p.created_at || '',
    updated_at: p.updated_at || '',
    is_deleted: false
  }
}

/**
 * 前端 payload → 后端 ProductCreate 格式
 * category: "数据分析,CRM" → ["数据分析", "CRM"]
 * attachments: {images, docs} → images + documents
 */
const adaptProductToBackend = (payload) => {
  const attachments = payload.attachments || { images: [], docs: [] }
  const cat = payload.category
  return {
    name: payload.name,
    category: Array.isArray(cat)
      ? cat
      : (cat ? String(cat).split(/[,，]/).map((s) => s.trim()).filter(Boolean) : []),
    description: payload.description || '',
    pricing: payload.pricing || '',
    features: payload.features || [],
    target_customers: payload.target_customers || [],
    selling_points: payload.selling_points || [],
    images: attachments.images || [],
    documents: attachments.docs || []
  }
}

/**
 * 后端 VersionContent → 前端 version 格式
 * 后端: {index, title, body, tags, image, votes, voters}
 * 前端: {version_key, name, is_recommended, content_html, content_markdown, word_count}
 */
const adaptVersion = (v) => {
  if (!v) return v
  if (v.version_key) return v // 已是前端格式
  const idx = v.index || 1
  const letter = String.fromCharCode(64 + idx) // 1→A, 2→B
  return {
    version_key: letter,
    name: v.title || `版本 ${letter}`,
    is_recommended: idx === 1,
    content_html: v.body || '',
    content_markdown: v.body || '',
    word_count: (v.body || '').length,
    tags: v.tags || [],
    image: v.image || null,
    votes: v.votes || { like: 0, dislike: 0 },
    voters: v.voters || {}
  }
}

/**
 * 后端 HistoryItem → 前端 generation 格式
 * 后端: {id, product_id, product_name, scenario_id, scenario_name, channel, style, params, versions, agent_trace, validated, issues, created_at, feedback, created_by}
 * 前端: {generation_id, product:{product_id, name}, scene_code, scene_name, channel, style, params, versions, ...}
 */
const adaptHistory = (h) => {
  if (!h) return h
  if (h.generation_id) return h // 已是前端格式
  return {
    generation_id: h.id,
    product: {
      product_id: h.product_id,
      name: h.product_name,
      is_deleted: false
    },
    template: { template_id: '', name: '' },
    status: 'success',
    selected_version: null,
    duration_ms: 0,
    scene_code: h.scenario_id,
    scene_name: h.scenario_name,
    channel: h.channel || '',
    style: h.style || '',
    params: h.params || {},
    versions: (h.versions || []).map(adaptVersion),
    agent_trace: h.agent_trace || [],
    validated: h.validated || false,
    issues: h.issues || [],
    feedback: h.feedback || null,
    created_by: h.created_by || '',
    created_at: h.created_at || '',
    updated_at: h.created_at || '',
    archived_at: null
  }
}

// ============================================================
// 业务 API（全部基于 Mock 数据实现）
// ============================================================
export const sxkApi = {
  /**
   * 4.8.1 首页统计 GET /stats/dashboard
   */
  getDashboardStats: () => {
    if (!USE_MOCK_BIZ) {
      // 后端无独立 dashboard 端点，并行拉取产品和历史记录后聚合
      return Promise.all([
        real({ url: '/api/products', method: 'get' }),
        real({ url: '/api/history', method: 'get' })
      ]).then(([products, history]) => {
        const prodList = products || []
        const histList = history || []
        // 统计各场景使用次数
        const sceneCount = {}
        histList.forEach((h) => {
          const sid = h.scenario_id
          sceneCount[sid] = (sceneCount[sid] || 0) + 1
        })
        const popular_scenes = Object.entries(sceneCount)
          .sort((a, b) => b[1] - a[1])
          .slice(0, 3)
          .map(([scene_code, use_count_30d]) => ({ scene_code, use_count_30d }))
        return ok({
          product_count: prodList.length,
          monthly_generation_count: histList.length,
          avg_score: 0,
          avg_duration_ms: 0,
          running_tasks: 0,
          popular_scenes
        })
      })
    }
    return delay().then(() => ok(mockDashboardStats))
  },

  /**
   * 4.2.1 当前用户信息 GET /api/auth/me
   */
  getCurrentUser: () => {
    if (!USE_MOCK_BIZ) {
      // 后端路径：GET /api/auth/me（需携带 Bearer token）
      return real({
        url: '/api/auth/me',
        method: 'get'
      }).then((raw) => ok({
        user_id: raw.id,
        username: raw.username || raw.name,
        role: raw.is_admin ? 'admin' : 'user',
        status: 'active',
        created_at: raw.created_at || '',
        last_login_at: '',
        avatar: raw.color || ''
      }))
    }
    return delay(150).then(() => ok(mockCurrentUser))
  },

  /**
   * 4.7.2 最近 3 条 GET /history/recent?limit=3
   * 按生成时间降序后取前 limit 条，与 listHistory 共用 sortByCreatedDesc
   */
  getRecentGenerations: (limit = 3) => {
    if (!USE_MOCK_BIZ) {
      return real({
        url: '/api/history',
        method: 'get'
      }).then((rawList) => {
        const items = (rawList || []).slice(0, limit).map(adaptHistory)
        return ok({ items })
      })
    }
    return delay().then(() => ok({ items: sortByCreatedDesc(mockGenerations).slice(0, limit) }))
  },

  // ----------------- 产品域（4.3） -----------------

  /**
   * 4.3.1 产品列表 GET /api/products
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
      // 后端路径：GET /api/products?keyword=xxx
      return real({
        url: '/api/products',
        method: 'get',
        params: { keyword }
      }).then((rawList) => {
        const items = (rawList || []).map(adaptProduct)
        // 前端本地排序（后端按 created_at DESC 返回）
        const desc = sort.startsWith('-')
        const field = desc ? sort.slice(1) : sort
        const sorted = items.slice().sort((a, b) => {
          const va = a[field] || ''
          const vb = b[field] || ''
          if (va < vb) return desc ? 1 : -1
          if (va > vb) return desc ? -1 : 1
          return 0
        })
        return ok(paginate(sorted, page, size))
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
   * 4.3.2 产品详情 GET /api/products/{productId}
   */
  getProduct: (productId) => {
    if (!USE_MOCK_BIZ) {
      // 后端路径：GET /api/products/{product_id}
      return real({
        url: `/api/products/${productId}`,
        method: 'get'
      }).then((raw) => ok(adaptProduct(raw)))
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
   * 4.3.3 新增产品 POST /api/products
   */
  createProduct: (payload) => {
    if (!USE_MOCK_BIZ) {
      // 后端路径：POST /api/products
      return real({
        url: '/api/products',
        method: 'post',
        data: adaptProductToBackend(payload)
      }).then((raw) => ok({ product_id: raw.id }))
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
   * 4.3.4 修改产品 PUT /api/products/{productId}
   */
  updateProduct: (productId, payload) => {
    if (!USE_MOCK_BIZ) {
      // 后端路径：PUT /api/products/{product_id}
      return real({
        url: `/api/products/${productId}`,
        method: 'put',
        data: adaptProductToBackend(payload)
      }).then(() => ok(null))
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
   * 4.3.5 删除产品 DELETE /api/products/{productId}（软删）
   */
  removeProduct: (productId) => {
    if (!USE_MOCK_BIZ) {
      // 后端路径：DELETE /api/products/{product_id}（后端硬删）
      return real({
        url: `/api/products/${productId}`,
        method: 'delete'
      }).then(() => ok(null))
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
   * 4.3.6 产品统计（后端无独立端点，从产品列表计算）
   */
  getProductStats: () => {
    if (!USE_MOCK_BIZ) {
      // 后端无 /api/products/stats 端点，从 GET /api/products 自行统计
      return real({
        url: '/api/products',
        method: 'get'
      }).then((rawList) => {
        const items = rawList || []
        return ok({
          total: items.length,
          active: items.length,
          categories: [...new Set(items.flatMap((p) =>
            Array.isArray(p.category) ? p.category : [p.category]
          ))].filter(Boolean).length
        })
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
      // 后端提供 GET /api/templates/all 一次性返回所有模板
      return real({
        url: '/api/templates/all',
        method: 'get'
      }).then((rawList) => {
        // 适配字段格式
        let items = (rawList || []).map(adaptTemplate)
        // 前端筛选：scene_code
        if (scene_code) {
          items = items.filter((t) => t.scene_code === scene_code)
        }
        // 前端筛选：is_custom（基于 ID 模式检测）
        if (is_custom !== null && is_custom !== undefined) {
          items = items.filter((t) => t.is_custom === is_custom)
        }
        // 前端筛选：keyword
        const kw = String(keyword || '').trim().toLowerCase()
        if (kw) {
          items = items.filter((t) =>
            (t.name + ' ' + (t.description || '')).toLowerCase().includes(kw)
          )
        }
        return ok(paginate(items, page, size))
      })
    }
    return delay().then(() => {
      const kw = String(keyword || '').trim().toLowerCase()
      const filtered = mockTemplates.filter((t) => {
        if (scene_code && t.scene_code !== scene_code) return false
        // is_custom 过滤：基于 ID 模式检测
        const tIsCustom = !isPresetTemplate(t.template_id)
        if (is_custom !== null && is_custom !== undefined && tIsCustom !== is_custom) return false
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
  getTemplate: (templateId, sceneCode) => {
    if (!USE_MOCK_BIZ) {
      // 后端路径：GET /api/scenarios/{scenario_id}/templates/{template_id}
      // 同时获取同场景下的所有模板列表（用于详情弹窗"已有模板"区块）
      return real({
        url: `/api/scenarios/${sceneCode}/templates/${templateId}`,
        method: 'get'
      }).then(async (raw) => {
        const t = adaptTemplate(raw)
        // 获取同场景下的所有模板（siblings）
        const siblingsRaw = await real({
          url: `/api/scenarios/${sceneCode}/templates`,
          method: 'get'
        })
        const siblings = (siblingsRaw || []).map(adaptTemplate).map((x) => ({
          template_id: x.template_id,
          name: x.name,
          output_format: x.output_format,
          description: x.description,
          use_count_30d: x.use_count_30d,
          updated_at: x.updated_at
        }))
        return ok({ ...t, templates: siblings })
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
      // 后端路径：POST /api/scenarios/{scenario_id}/templates
      // output_format 存入 constraints.output_format（后端无独立字段）
      const constraints = {
        ...(payload.constraints || {}),
        output_format: payload.output_format || 'long_text'
      }
      return real({
        url: `/api/scenarios/${payload.scene_code}/templates`,
        method: 'post',
        data: {
          name: payload.name,
          tag: payload.tag || '',
          description: payload.description || '',
          prompt: payload.prompt || '',
          constraints,
          structure: payload.sections || '',
          examples: payload.examples || [],
          differentiation_dims: payload.differentiation_dims || [],
          applicable_channels: payload.applicable_channels || [],
          tags: payload.tags || []
        }
      }).then((raw) => ok({ template_id: raw.id }))
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
      // 后端路径：PUT /api/scenarios/{scenario_id}/templates/{template_id}
      // output_format 存入 constraints.output_format
      const constraints = {
        ...(payload.constraints || {}),
        output_format: payload.output_format || 'long_text'
      }
      return real({
        url: `/api/scenarios/${payload.scene_code}/templates/${templateId}`,
        method: 'put',
        data: {
          name: payload.name,
          tag: payload.tag || '',
          description: payload.description || '',
          prompt: payload.prompt || '',
          constraints,
          structure: payload.sections || '',
          examples: payload.examples || [],
          differentiation_dims: payload.differentiation_dims || [],
          applicable_channels: payload.applicable_channels || [],
          tags: payload.tags || []
        }
      }).then(() => ok(null))
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
  deleteTemplate: (templateId, sceneCode) => {
    if (!USE_MOCK_BIZ) {
      // 后端路径：DELETE /api/scenarios/{scenario_id}/templates/{template_id}
      return real({
        url: `/api/scenarios/${sceneCode}/templates/${templateId}`,
        method: 'delete'
      }).then(() => ok(null))
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
      // 后端暂无独立使用次数接口，mock only
      return ok(null)
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
      // 后端无独立 meta 端点，从 /api/scenarios 获取场景列表构建
      return real({
        url: '/api/scenarios',
        method: 'get'
      }).then((rawList) => {
        const scenes = (rawList || []).map(adaptScene)
        return ok({
          scene_codes: scenes.map((s) => ({ code: s.scene_code, name: s.name })),
          output_formats: [
            { code: 'long_text', name: '长文案' },
            { code: 'short_text', name: '短文案' },
            { code: 'table', name: '表格' },
            { code: 'outline', name: '大纲' },
            { code: 'email', name: '邮件' }
          ]
        })
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
      // 后端路径：GET /api/scenarios
      return real({
        url: '/api/scenarios',
        method: 'get'
      }).then((rawList) => {
        const scenes = (rawList || []).map(adaptScene)
        return ok({ scenes })
      })
    }
    return delay(100).then(() => ok({ scenes: mockSceneSchemas }))
  },

  /**
   * 4.5.9 新增场景 POST /scenarios
   */
  createScene: (payload) => {
    if (!USE_MOCK_BIZ) {
      // 后端路径：POST /api/scenarios
      // 后端参数格式：parameters: [{name, description}]
      const parameters = Object.entries(payload.params || {}).map(([label, desc]) => ({
        name: label,
        description: typeof desc === 'string' ? desc : String(desc)
      }))
      return real({
        url: '/api/scenarios',
        method: 'post',
        data: {
          name: payload.name,
          description: payload.description || '',
          parameters
        }
      }).then((raw) => ok({ scene_code: raw.id }))
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
   * 4.5.10 更新场景 PUT /scenarios/{scene_code}
   */
  updateScene: (sceneCode, payload) => {
    if (!USE_MOCK_BIZ) {
      // 后端路径：PUT /api/scenarios/{scenario_id}
      const parameters = Object.entries(payload.params || {}).map(([label, desc]) => ({
        name: label,
        description: typeof desc === 'string' ? desc : String(desc)
      }))
      return real({
        url: `/api/scenarios/${sceneCode}`,
        method: 'put',
        data: {
          name: payload.name,
          description: payload.description || '',
          parameters
        }
      }).then(() => ok(null))
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

  /**
   * 4.5.11 删除场景 DELETE /scenarios/{scene_code}
   * 关联的模板会级联删除
   */
  deleteScene: (sceneCode) => {
    if (!USE_MOCK_BIZ) {
      // 后端路径：DELETE /api/scenarios/{scenario_id}
      return real({
        url: `/api/scenarios/${sceneCode}`,
        method: 'delete'
      }).then(() => ok(null))
    }
    return delay().then(() => {
      const idx = mockSceneSchemas.findIndex((s) => s.scene_code === sceneCode)
      if (idx === -1) return { code: 4041, msg: '场景不存在', data: null }
      // 预置场景不可删除（scene_code 不以 custom_ 开头视为预置）
      if (!sceneCode.startsWith('custom_')) {
        return { code: 4030, msg: '预置场景不可删除', data: null }
      }
      mockSceneSchemas.splice(idx, 1)
      // 同步删除该场景下的所有模板
      for (let i = mockTemplates.length - 1; i >= 0; i--) {
        if (mockTemplates[i].scene_code === sceneCode) {
          mockTemplates.splice(i, 1)
        }
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
    if (!USE_MOCK_BIZ) {
      // 后端路径：POST /api/generate
      // 前端 scene_code → 后端 scenario_id
      return real({
        url: '/api/generate',
        method: 'post',
        data: {
          product_id: payload.product_id,
          scenario_id: payload.scene_code,
          template_id: payload.template_id || '',
          channel: payload.channel || '官网',
          style: payload.style || '专业严谨',
          params: payload.params || {},
          version_count: payload.version_count || 3
        }
      }).then((raw) => ok({
        generation_id: raw.history_id,
        status: 'success',
        estimated_ms: 0
      }))
    }
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
    if (!USE_MOCK_BIZ) {
      // 后端路径：GET /api/history/{id}
      return real({
        url: `/api/history/${generationId}`,
        method: 'get'
      }).then((raw) => ok(adaptHistory(raw)))
    }
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
    if (!USE_MOCK_BIZ) {
      // 后端无独立版本端点，从 GET /api/history/{id} 提取对应版本
      return real({
        url: `/api/history/${generationId}`,
        method: 'get'
      }).then((raw) => {
        const versions = (raw.versions || []).map(adaptVersion)
        const v = versions.find((x) => x.version_key === versionKey)
        if (!v) return { code: 4041, msg: '版本不存在', data: null }
        const issues = raw.issues || []
        return ok({
          ...v,
          validation_summary: {
            total: issues.length,
            error: 0,
            warn: issues.length,
            info: 0,
            passed: raw.validated !== false
          }
        })
      })
    }
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
    if (!USE_MOCK_BIZ) {
      // 后端无直接"选用版本"端点，用 PUT /api/history/{id}/feedback 标记偏好
      const fb = versionKey === 'A' ? 'like' : ''
      return real({
        url: `/api/history/${generationId}/feedback`,
        method: 'put',
        data: { feedback: fb }
      }).then(() => ok({ generation_id: generationId, selected_version: versionKey }))
    }
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
    if (!USE_MOCK_BIZ) {
      // 从 GET /api/history/{id} 的 agent_trace 字段提取
      return real({
        url: `/api/history/${generationId}`,
        method: 'get'
      }).then((raw) => {
        const trace = raw.agent_trace || []
        return ok({ runs: trace })
      })
    }
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
    if (!USE_MOCK_BIZ) {
      // 从 GET /api/history/{id} 的 issues 字段提取
      return real({
        url: `/api/history/${generationId}`,
        method: 'get'
      }).then((raw) => {
        const issueStrings = raw.issues || []
        const issues = issueStrings.map((msg, i) => ({
          id: `issue_${i}`,
          severity: 'warn',
          message: msg,
          section: ''
        }))
        return ok({ issues })
      })
    }
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
    if (!USE_MOCK_BIZ) {
      // 后端路径：GET /api/history（返回扁平列表，前端做筛选+分页）
      return real({
        url: '/api/history',
        method: 'get'
      }).then((rawList) => {
        let items = (rawList || []).map(adaptHistory)
        const kw = String(keyword || '').trim().toLowerCase()
        if (kw) {
          items = items.filter((g) =>
            (g.product.name || '').toLowerCase().includes(kw)
          )
        }
        if (scene_code) {
          items = items.filter((g) => g.scene_code === scene_code)
        }
        if (status) {
          items = items.filter((g) => g.status === status)
        }
        return ok(paginate(items, page, size))
      })
    }
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
    if (!USE_MOCK_BIZ) {
      // 后端路径：DELETE /api/history/{id}
      return real({
        url: `/api/history/${generationId}`,
        method: 'delete'
      }).then(() => ok(null))
    }
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
