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
  mockSceneNameMap,
  mockMembers
} from './data'

// 业务域 Mock 开关：由 .env.dev 中 VITE_APP_USE_MOCK_BIZ 控制
const USE_MOCK_BIZ = import.meta.env.VITE_APP_USE_MOCK_BIZ !== 'false'

// 真实链路统一封装：request() 返回 axios response { status, data: {code,msg,data} }，
// 此处提取 res.data，使其与 Mock 的 ok() 返回形态完全一致，调用方无感知切换。
const real = (config) => request(config).then((res) => res.data)

/**
 * 真实链路辅助：批量上传产品文件
 * @param {string} productId
 * @param {Object} withFiles - { images: [...], docs: [...] }，每项可能含 file 对象
 * @returns {Promise<{images: [], documents: []}>}
 *
 * 关键：每项只上传"有 file 对象的项"（即用户本次新选的），
 *      已有 url 的项（从后端 loadProduct 取回）直接保留。
 */
const uploadAllFiles = (productId, withFiles) => {
  const images = withFiles.images || []
  const docs = withFiles.docs || []

  const uploadImageTasks = images
    .filter((im) => im.file)  // 只上传有 file 的
    .map((im) =>
      real({
        url: `/api/products/${productId}/upload-image`,
        method: 'post',
        data: (() => {
          const fd = new FormData()
          fd.append('file', im.file)
          return fd
        })(),
        meta: { isSerialize: false }
      }).then((raw) => ({ url: raw.url, name: raw.name, size: raw.size }))
    )

  const uploadDocTasks = docs
    .filter((d) => d.file)
    .map((d) =>
      real({
        url: `/api/products/${productId}/upload-document`,
        method: 'post',
        data: (() => {
          const fd = new FormData()
          fd.append('file', d.file)
          return fd
        })(),
        meta: { isSerialize: false }
      }).then((raw) => ({ url: raw.url, name: raw.name, size: raw.size }))
    )

  return Promise.all(uploadImageTasks).then((uploadedImages) =>
    Promise.all(uploadDocTasks).then((uploadedDocs) => ({
      images: uploadedImages,
      documents: uploadedDocs
    }))
  )
}

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
    category: Array.isArray(cat) ? cat : (cat ? [cat] : []),
    description: p.description || '',
    pricing: p.pricing || '',
    features: p.features || [],
    target_customers: p.target_customers || [],
    competitors: p.competitors || [],
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
  // 真实链路过滤：剔除 dataUrl（前端 buffer 标记），保留 url 项（已上传资源）
  // 后端 ImageItem/DocumentItem 必填 url 字段，dataUrl 会被后端拒绝
  const cleanImages = (attachments.images || []).filter(
    (im) => im && (im.url || im.name) && !im.dataUrl
  )
  const cleanDocs = (attachments.docs || []).filter(
    (d) => d && (d.url || d.name) && !d.dataUrl
  )
  return {
    name: payload.name,
    category: Array.isArray(cat)
      ? cat
      : (cat ? String(cat).split(/[,，]/).map((s) => s.trim()).filter(Boolean) : []),
    description: payload.description || '',
    pricing: payload.pricing || '',
    features: payload.features || [],
    target_customers: payload.target_customers || [],
    competitors: payload.competitors || [],
    selling_points: payload.selling_points || [],
    images: cleanImages,
    documents: cleanDocs
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
    // 保留后端原始字段（供历史详情弹窗的 v.title / v.body / v.images / v.channel 使用）
    index: idx,
    title: v.title || `版本 ${letter}`,
    body: v.body || '',
    channel: v.channel || '',
    images: v.images || [],
    tags: v.tags || [],
    image: v.image || null,
    votes: v.votes || { like: 0, dislike: 0 },
    voters: v.voters || {},
    seo: v.seo || null,
    // 兼容旧版式模板/老接口的字段
    version_key: letter,
    name: v.title || `版本 ${letter}`,
    is_recommended: idx === 1,
    content_html: v.body || '',
    content_markdown: v.body || '',
    word_count: (v.body || '').length
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
        // ========== 关键：计算"平均耗时" ==========
        // 数据源：每条 history.agent_trace（JSON 数组，元素含 duration_ms）
        // 策略：累加每条 history 的所有 Agent 的 duration_ms，得到该条总耗时；
        //       过滤无效值（null/0/缺失）后取平均
        const durations = []
        histList.forEach((h) => {
          const trace = h.agent_trace
          if (!Array.isArray(trace) || trace.length === 0) return
          const total = trace.reduce((sum, step) => {
            const d = step && step.duration_ms
            return sum + (typeof d === 'number' && d > 0 ? d : 0)
          }, 0)
          if (total > 0) durations.push(total)
        })
        const avg_duration_ms = durations.length > 0
          ? Math.round(durations.reduce((a, b) => a + b, 0) / durations.length)
          : 0
        // ==========================================
        return ok({
          product_count: prodList.length,
          monthly_generation_count: histList.length,
          avg_score: 0,
          avg_duration_ms,  // 关键：真实计算（之前 hardcode 0）
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
        // 关键：把 is_admin 字段也透传出去，store 用它判断是否显示"成员管理"菜单
        is_admin: !!raw.is_admin,
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
   *
   * @param {Object} payload - 产品数据
   * @param {Object} [withFiles] - 真实后端链路中，附加待上传的 file 对象
   *   { images: [{id, name, size, type, dataUrl, file}], docs: [{id, name, size, type, ext, file}] }
   *   只有 file 字段存在的项会被真实上传
   */
  createProduct: (payload, withFiles) => {
    if (!USE_MOCK_BIZ) {
      // 真实链路：先 POST 产品（不传 dataUrl），拿到 productId 后循环 upload
      return real({
        url: '/api/products',
        method: 'post',
        data: adaptProductToBackend(payload)
      }).then((raw) => {
        const productId = raw.id
        // 真实链路：上传文件（如果有 file 对象）
        if (withFiles && productId) {
          return uploadAllFiles(productId, withFiles).then((uploaded) => {
            // 把上传结果写回 product.images/documents（用 PUT 增量更新）
            // 关键：后端 PUT 走的是 ProductCreate 校验，必须发完整字段，不能只发 images/documents
            const basePayload = adaptProductToBackend(payload)
            return real({
              url: `/api/products/${productId}`,
              method: 'put',
              data: {
                ...basePayload,
                images: uploaded.images,
                documents: uploaded.documents
              }
            }).then(() => ok({ product_id: productId }))
          })
        }
        return ok({ product_id: productId })
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
   * 4.3.4 修改产品 PUT /api/products/{productId}
   *
   * @param {string} productId
   * @param {Object} payload
   * @param {Object} [withFiles] - 同 createProduct
   */
  updateProduct: (productId, payload, withFiles) => {
    if (!USE_MOCK_BIZ) {
      // 真实链路：先 PUT 产品（不传 dataUrl），再上传新文件
      const backendPayload = adaptProductToBackend(payload)
      return real({
        url: `/api/products/${productId}`,
        method: 'put',
        data: backendPayload
      }).then(() => {
        if (withFiles && productId) {
          return uploadAllFiles(productId, withFiles).then((uploaded) => {
            // 合并到原 images/documents 再 PUT 一次
            // 关键：后端 PUT 走的是 ProductCreate 校验，必须发完整字段，不能只发 images/documents
            return real({
              url: `/api/products/${productId}`,
              method: 'put',
              data: {
                ...backendPayload,
                images: [...(backendPayload.images || []), ...uploaded.images],
                documents: [...(backendPayload.documents || []), ...uploaded.documents]
              }
            }).then(() => ok(null))
          })
        }
        return ok(null)
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


  /**
   * 产品资源上传（真实后端链路）
   *
   * - 上传图片：POST /api/products/{id}/upload-image（multipart/form-data）
   *   返回 { url, name, size }
   * - 上传文档：POST /api/products/{id}/upload-document（multipart/form-data）
   *   返回 { url, name, size }
   *
   * Mock 阶段不实现（保持原有 dataUrl 缓冲机制）
   */
  uploadProductImage: (productId, file) => {
    if (USE_MOCK_BIZ) {
      return delay().then(() =>
        ok({ url: `mock://upload-image/${file.name}`, name: file.name, size: file.size })
      )
    }
    const fd = new FormData()
    fd.append('file', file)
    return real({
      url: `/api/products/${productId}/upload-image`,
      method: 'post',
      data: fd,
      meta: { isSerialize: false }  // 关键：禁止 serialize（multipart 用 FormData）
    }).then((raw) => ok({ url: raw.url, name: raw.name, size: raw.size }))
  },

  uploadProductDocument: (productId, file) => {
    if (USE_MOCK_BIZ) {
      return delay().then(() =>
        ok({ url: `mock://upload-document/${file.name}`, name: file.name, size: file.size })
      )
    }
    const fd = new FormData()
    fd.append('file', file)
    return real({
      url: `/api/products/${productId}/upload-document`,
      method: 'post',
      data: fd,
      meta: { isSerialize: false }
    }).then((raw) => ok({ url: raw.url, name: raw.name, size: raw.size }))
  },

  /**
   * Word/PDF 建库（真实后端链路）
   * POST /api/products/import-docx（multipart/form-data）
   * 返回 { product: ProductCreate, char_count, extractor, note }
   *
   * Mock 阶段：返回友好提示，让前端 UI 决定如何引导用户
   * （不弹错误码，让前端能用 ElMessage.warning 区别对待）
   */
  importDocx: (file) => {
    if (USE_MOCK_BIZ) {
      return delay(200).then(() => ({
        code: 0,
        msg: 'mock 链路不支持',
        data: {
          product: null,
          char_count: 0,
          extractor: 'mock',
          note: 'Word/PDF 建库功能需要在真实后端环境（USE_MOCK_BIZ=false）下使用，mock 阶段请用"添加产品"按钮手动录入。',
          mock_unavailable: true  // 关键：让前端判断是 mock 不支持
        }
      }))
    }
    const fd = new FormData()
    fd.append('file', file)
    return real({
      url: '/api/products/import-docx',
      method: 'post',
      data: fd,
      meta: { isSerialize: false }
    }).then((raw) => ok(raw))
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
        // 补齐详情弹窗与卡片列表所需的字段
        scene_code: payload.scene_code,
        scene_name: mockSceneNameMap[payload.scene_code] || payload.scene_code,
        channel: payload.channel || '',
        style: payload.style || '专业严谨',
        feedback: '',
        validated: true,
        created_by: mockCurrentUser?.username || 'admin',
        // 原有字段
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
      const rawVersions = mockVersionContents[generationId] || []
      // 适配为详情弹窗期望的字段：index/title/body/images/attachments
      const versions = rawVersions.map((v, i) => {
        const index = i + 1
        const version_key = v.version_key || String.fromCharCode(64 + index)
        const body = v.body || v.content_html || ''
        const title = v.title || v.name || `版本 ${version_key}: ${(g.product?.name || '').slice(0, 20)}`
        return {
          ...v,
          index,
          version_key,
          title,
          body,
          content_html: body,
          attachments: v.attachments || { images: v.images || [], docs: v.docs || [] }
        }
      })
      // 补齐卡片/弹窗共用的元信息字段（兼容老 record）
      const enriched = {
        ...g,
        scene_code: g.scene_code || g.scenario_id || g.template?.scene_code || '',
        scene_name:
          g.scene_name ||
          mockSceneNameMap[g.scene_code || g.scenario_id || g.template?.scene_code] ||
          g.scene_code ||
          '—',
        channel: g.channel || '',
        style: g.style || '专业严谨',
        feedback: g.feedback || '',
        validated: g.validated !== false,
        created_by: g.created_by || g.creator || 'admin',
        versions
      }
      return ok(enriched)
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
        if (kw && !(g.product.name || '').toLowerCase().includes(kw)) return false
        return true
      })
      // 补齐卡片列表所需字段
      const enriched = filtered.map((g) => ({
        ...g,
        scene_code: g.scene_code || g.scenario_id || g.template?.scene_code || '',
        scene_name:
          g.scene_name ||
          mockSceneNameMap[g.scene_code || g.scenario_id || g.template?.scene_code] ||
          g.scene_code ||
          '—',
        channel: g.channel || '',
        style: g.style || '专业严谨',
        feedback: g.feedback || '',
        validated: g.validated !== false,
        created_by: g.created_by || g.creator || 'admin'
      }))
      return ok(paginate(enriched, page, size))
    })
  },

  /**
   * 4.7.3 更新历史 PUT /history/{id}（详情弹窗保存修改用）
   * 后端预留接口：PUT /api/history/{id}
   * 入参 { versions: [...] }
   */
  updateHistory: (generationId, payload) => {
    if (!USE_MOCK_BIZ) {
      return real({
        url: `/api/history/${generationId}`,
        method: 'put',
        data: payload
      }).then((d) => ok(adaptHistory(d)))
    }
    return delay(150).then(() => {
      const gen = mockGenerations.find((x) => x.generation_id === generationId)
      if (!gen) return { code: 4041, msg: '记录不存在', data: null }
      // 仅更新传入的 versions 字段
      if (Array.isArray(payload.versions)) {
        gen.versions = payload.versions.map((v) => ({
          ...v,
          version_key: v.version_key || v.index
        }))
      }
      return ok(adaptHistory(gen))
    })
  },

  /**
   * 4.7.4 删除历史 DELETE /history/{id}
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
  noop: () => Promise.resolve(ok(null)),

  // ===================================================================
  // 内容生成页专用 mock 工具（与后端参考版 B2B-SXK-FastApi/frontend 对齐）
  // 后端 API 暂未提供时，前端用 mock 数据呈现完整 UI/UX 流程
  // ===================================================================

  /**
   * 获取可选发布渠道列表
   * 后端预留接口：GET /api/channels
   */
  listChannels: () => {
    if (!USE_MOCK_BIZ) {
      return real({ url: '/api/channels', method: 'get' }).then((d) => ok(d))
    }
    return delay(80).then(() =>
      ok([
        { name: 'wechat', display_name: '微信公众号', tone: '亲和走心', format: '长图文' },
        { name: 'linkedin', display_name: 'LinkedIn', tone: '专业严谨', format: '短帖' },
        { name: 'ppt', display_name: '内部 PPT', tone: '结构化', format: '幻灯片' },
        { name: 'email', display_name: 'EDM 邮件', tone: '正式简洁', format: 'HTML 邮件' },
        { name: 'weibo', display_name: '微博', tone: '年轻活泼', format: '短帖' },
        { name: 'douyin', display_name: '抖音短视频脚本', tone: '口语化', format: '60s 口播' }
      ])
    )
  },

  /**
   * SEO 评分分析
   * 后端预留接口：POST /api/seo/analyze
   * 入参 { title, body } 出参 { score, keywords, suggestions, stats }
   */
  analyzeSeo: ({ title, body }) => {
    if (!USE_MOCK_BIZ) {
      return real({
        url: '/api/seo/analyze',
        method: 'post',
        data: { title, body }
      }).then((d) => ok(d))
    }
    return delay(300).then(() => {
      const text = (title || '') + '\n' + (body || '')
      const cjk = (text.match(/[一-龥]/g) || []).length
      const en = (text.replace(/[一-龥]/g, ' ').match(/[A-Za-z]+/g) || []).length
      const titleLen = (title || '').length
      const bodyLen = cjk + en
      const headings = ((body || '').match(/^#{1,3}\s+/gm) || []).length
      const avgSentenceLength = bodyLen
        ? Math.round(bodyLen / Math.max(1, (body.match(/[。！？.!?]/g) || []).length || 1))
        : 0
      // 简易评分：标题 15~30 字 +25；正文 200~1500 字 +30；含 H2/H3 +20；句长 10~35 +25
      let score = 0
      if (titleLen >= 15 && titleLen <= 30) score += 25
      if (bodyLen >= 200 && bodyLen <= 1500) score += 30
      if (headings >= 2) score += 20
      if (avgSentenceLength >= 10 && avgSentenceLength <= 35) score += 25
      const keywords = (body || '').match(/[A-Za-z]{3,}/g)?.slice(0, 5) || []
      const suggestions = []
      if (titleLen < 15) suggestions.push({ type: 'title', level: 'warning', message: '标题偏短，建议 15~30 字' })
      else if (titleLen > 30) suggestions.push({ type: 'title', level: 'warning', message: '标题偏长，建议控制在 30 字内' })
      else suggestions.push({ type: 'title', level: 'good', message: '标题长度合适' })
      if (bodyLen < 200) suggestions.push({ type: 'body', level: 'danger', message: '正文偏短，建议 200~1500 字' })
      else if (bodyLen > 1500) suggestions.push({ type: 'body', level: 'warning', message: '正文偏长，可考虑拆分段落' })
      else suggestions.push({ type: 'body', level: 'good', message: '正文字数合适' })
      if (headings < 2) suggestions.push({ type: 'structure', level: 'warning', message: '建议使用 H2/H3 划分小节' })
      else suggestions.push({ type: 'structure', level: 'good', message: '文章结构清晰' })
      if (avgSentenceLength > 35) suggestions.push({ type: 'readability', level: 'warning', message: '句子偏长，建议拆分' })
      else if (avgSentenceLength > 0) suggestions.push({ type: 'readability', level: 'good', message: '句长易于阅读' })
      return ok({
        score,
        keywords,
        suggestions,
        stats: {
          title_length: titleLen,
          body_length: bodyLen,
          headings,
          avg_sentence_length: avgSentenceLength,
          meta_description: (body || '').replace(/\s+/g, ' ').slice(0, 120)
        }
      })
    })
  },

  /**
   * 多阶段草稿流程（与后端参考版 step 0/1/2 对齐）
   * 后端预留接口：POST /api/drafts、PUT /api/drafts/{id}/select、
   *   POST /api/drafts/{id}/adapt、POST /api/drafts/{id}/finalize
   *
   * 草稿状态机：draft -> editing -> adapted -> done
   *   draft     Step 0：初稿多版本选择
   *   editing   Step 1：编辑选定内容 + 多选渠道
   *   adapted   Step 2：多渠道版本展示
   *   done      Step 2：文生图完成，可导出/查看历史
   */
  _drafts: [], // 模块级 mock 草稿库

  _genDraftVersions(product, scene) {
    // 简易版「3 个初稿」：标题 + 段落 + 标签
    const t = (i) => `${product.name} · ${scene.name} · 版本 ${String.fromCharCode(65 + i)}`
    return [
      {
        index: 1,
        title: t(0),
        body: `# ${product.name}\n\n## 核心卖点\n${product.selling_points?.join('、') || '高效、易用、稳定'}\n\n## 适用场景\n- 企业级部署\n- 团队协作\n- 行业定制\n\n> ${product.description || '为企业提供端到端解决方案'}\n\n## 行动号召\n立即体验，开启数字化升级之旅。`,
        tags: ['产品介绍', '专业'],
        images: []
      },
      {
        index: 2,
        title: t(1),
        body: `## 为什么选择 ${product.name}\n\n**一、行业领先**：深耕行业 10+ 年，沉淀 1000+ 头部客户最佳实践。\n\n**二、开箱即用**：覆盖产品/方案/咨询/实施全流程，5 天快速上线。\n\n**三、安全可靠**：通过等保三级、ISO27001、SOC2 认证。\n\n| 维度 | ${product.name} | 传统方案 |\n|---|---|---|\n| 部署周期 | 5 天 | 30 天 |\n| 维护成本 | 低 | 高 |\n| 扩展性 | ★★★★★ | ★★ |\n\n立即联系我们，获取专属方案。`,
        tags: ['方案对比', '正式'],
        images: []
      },
      {
        index: 3,
        title: t(2),
        body: `> 让营销更简单，让内容更有温度。\n\n## 我们能为你做什么\n\n1. **智能生成**：输入产品信息，3 秒产出专业文案\n2. **多渠道适配**：一次输入，5 大渠道自动适配\n3. **数据驱动**：A/B 测试，实时反馈效果\n\n---\n\n### 客户怎么说\n\n"使用 ${product.name} 后，我们的营销效率提升了 3 倍。" —— 某世界 500 强客户\n\n**限时福利**：注册即享 30 天免费试用，点击下方按钮立即开启！`,
        tags: ['客户故事', '亲和'],
        images: []
      }
    ]
  },

  /** 步骤 0：创建草稿（检索-生成-校验） */
  createDraft: ({ product_id, scene_code, template_id, style, params, version_count = 3 }) => {
    if (!USE_MOCK_BIZ) {
      return real({
        url: '/api/drafts',
        method: 'post',
        data: { product_id, scenario_id: scene_code, template_id, style, params, version_count }
      }).then((d) => ok(d))
    }
    return delay(800).then(() => {
      const product = mockProducts.find((p) => p.product_id === product_id) || mockProducts[0]
      const scene = mockSceneSchemas.scenes?.find((s) => s.scene_code === scene_code) || { name: scene_code }
      const draft = {
        id: 'd_' + Date.now(),
        product_id,
        product_name: product.name,
        scene_code,
        scene_name: scene.name,
        stage: 'draft',
        style: style || '专业严谨',
        draft_versions: sxkApi._genDraftVersions(product, scene),
        selected_version: null,
        versions: [],
        channels: [],
        agent_trace: mockAgentRunsDefault.map((r, i) => ({
          agent: r.agent_name,
          status: 'success',
          message: r.output_summary,
          duration_ms: 800 + i * 220
        })),
        validation: {
          validated: true,
          issues: []
        },
        history_id: null
      }
      sxkApi._drafts.unshift(draft)
      return ok(draft)
    })
  },

  /** 步骤 0：重新生成初稿 */
  regenerateDraft: (draftId) => {
    if (!USE_MOCK_BIZ) {
      return real({ url: `/api/drafts/${draftId}/regenerate`, method: 'post', data: {} }).then((d) => ok(d))
    }
    return delay(600).then(() => {
      const draft = sxkApi._drafts.find((d) => d.id === draftId)
      if (!draft) return { code: 4041, msg: '草稿不存在', data: null }
      const product = mockProducts.find((p) => p.product_id === draft.product_id) || mockProducts[0]
      const scene = { name: draft.scene_name }
      draft.draft_versions = sxkApi._genDraftVersions(product, scene)
      draft.selected_version = null
      draft.stage = 'draft'
      return ok({ ...draft })
    })
  },

  /**
   * Phase E：SSE 流式创建草稿
   *
   * - 真实链路：POST /api/drafts/stream（text/event-stream）
   *   事件协议：
   *     event: step  data: {agent, status, message?, duration_ms?, output?}
   *     event: done  data: {完整 Draft}
   *     event: error data: {message}
   *
   * - Mock 链路：抛出错误（mock 阶段走原 createDraft，保持同步体验）
   *
   * @param {Object} payload
   * @param {Object} callbacks - { onStep, onDone, onError }
   * @returns {{ abort: Function }} 返回 abort 函数
   */
  createDraftStream: (payload, callbacks = {}) => {
    if (USE_MOCK_BIZ) {
      // mock 阶段不支持流式，调用方应走 createDraft
      const err = new Error('Mock 阶段不支持 SSE 流式生成')
      err.code = 'MOCK_UNSUPPORTED'
      throw err
    }
    // 动态 import 避免循环依赖
    // eslint-disable-next-line no-undef
    return import('@/util/sse-client').then(({ default: SSEClient }) => {
      const sse = new SSEClient({
        url: '/api/drafts/stream',
        method: 'POST',
        data: {
          product_id: payload.product_id,
          scenario_id: payload.scene_code,
          template_id: payload.template_id,
          style: payload.style,
          params: payload.params,
          version_count: payload.version_count || 3
        },
        onStep: callbacks.onStep,
        onDone: callbacks.onDone,
        onError: callbacks.onError
      })
      sse.start()
      return { abort: () => sse.abort() }
    })
  },

  /**
   * Phase E：SSE 流式重新生成
   * POST /api/drafts/{id}/regenerate/stream
   */
  regenerateDraftStream: (draftId, callbacks = {}) => {
    if (USE_MOCK_BIZ) {
      const err = new Error('Mock 阶段不支持 SSE 流式重新生成')
      err.code = 'MOCK_UNSUPPORTED'
      throw err
    }
    return import('@/util/sse-client').then(({ default: SSEClient }) => {
      const sse = new SSEClient({
        url: `/api/drafts/${draftId}/regenerate/stream`,
        method: 'POST',
        data: {},
        onStep: callbacks.onStep,
        onDone: callbacks.onDone,
        onError: callbacks.onError
      })
      sse.start()
      return { abort: () => sse.abort() }
    })
  },

  /**
   * Phase E 能力探测：真实后端是否支持 SSE
   * 探测方式：尝试连接 stream 端点，看是否返回 text/event-stream
   *
   * 注意：此函数会发送实际请求，仅在用户点击"生成"前调用
   * 真实实现可在后端加 GET /api/drafts/stream-capabilities 探测端点
   *
   * 当前简化处理：直接信任 USE_MOCK_BIZ 开关
   */
  isSSEEnabled: () => {
    return !USE_MOCK_BIZ
  },

  /** 步骤 0->1：选定一个版本（写回 selected_version） */
  selectDraftVersion: (draftId, version) => {
    if (!USE_MOCK_BIZ) {
      return real({
        url: `/api/drafts/${draftId}/select`,
        method: 'put',
        data: { version }
      }).then((d) => ok(d))
    }
    return delay(150).then(() => {
      const draft = sxkApi._drafts.find((d) => d.id === draftId)
      if (!draft) return { code: 4041, msg: '草稿不存在', data: null }
      draft.selected_version = { ...version }
      draft.stage = 'editing'
      return ok({ ...draft })
    })
  },

  /** 步骤 1->2：多渠道适配（为每个渠道生成一个版本） */
  adaptDraft: (draftId, channels) => {
    if (!USE_MOCK_BIZ) {
      return real({
        url: `/api/drafts/${draftId}/adapt`,
        method: 'post',
        data: { channels }
      }).then((d) => ok(d))
    }
    return delay(800).then(() => {
      const draft = sxkApi._drafts.find((d) => d.id === draftId)
      if (!draft) return { code: 4041, msg: '草稿不存在', data: null }
      const base = draft.selected_version || draft.draft_versions[0]
      const versions = channels.map((ch, i) => {
        // 不同渠道风格化标题
        const styleMap = {
          wechat: { suffix: '｜公众号版', lead: '✨ ' },
          linkedin: { suffix: '｜LinkedIn 精简版', lead: '🚀 ' },
          ppt: { suffix: '｜PPT 演示版', lead: '▎' },
          email: { suffix: '｜邮件版', lead: 'Dear Reader,' },
          weibo: { suffix: '｜微博短帖', lead: '【速看】' },
          douyin: { suffix: '｜口播脚本', lead: '[开场 0-3s]' }
        }
        const s = styleMap[ch] || { suffix: `｜${ch}`, lead: '' }
        return {
          index: i + 1,
          channel: ch,
          title: s.lead + (base.title || '营销内容') + s.suffix,
          body: base.body,
          tags: [...(base.tags || []), ch],
          images: []
        }
      })
      draft.versions = versions
      draft.channels = channels
      draft.stage = 'adapted'
      return ok({ ...draft })
    })
  },

  /** 步骤 2：文生图 + 落 history */
  finalizeDraft: (draftId) => {
    if (!USE_MOCK_BIZ) {
      return real({ url: `/api/drafts/${draftId}/finalize`, method: 'post', data: {} }).then((d) => ok(d))
    }
    return delay(1200).then(() => {
      const draft = sxkApi._drafts.find((d) => d.id === draftId)
      if (!draft) return { code: 4041, msg: '草稿不存在', data: null }
      // 为每个渠道版本生成 1 张占位配图（用 SVG data URL 避免外部依赖）
      draft.versions.forEach((v, i) => {
        v.images = [
          {
            url: `data:image/svg+xml;utf8,${encodeURIComponent(
              `<svg xmlns="http://www.w3.org/2000/svg" width="640" height="360"><rect width="100%" height="100%" fill="#f1f5f9"/><text x="50%" y="50%" font-family="sans-serif" font-size="22" fill="#475569" text-anchor="middle" dominant-baseline="middle">${v.channel} · 配图 ${i + 1}</text></svg>`
            )}`,
            caption: `${v.channel} 主题配图`
          }
        ]
      })
      draft.stage = 'done'
      // 同步到历史列表（用 sxkApi 的 mockGenerations）
      const historyId = 'g_' + Date.now()
      draft.history_id = historyId
      mockGenerations.unshift({
        generation_id: historyId,
        product_id: draft.product_id,
        product: { product_id: draft.product_id, name: draft.product_name },
        scene_code: draft.scene_code,
        scene_name: draft.scene_name,
        style: draft.style,
        selected_version: 'A',
        versions: draft.versions.map((v) => ({
          version_key: 'A',
          name: v.title,
          content_html: v.body,
          word_count: (v.body || '').length,
          is_recommended: v.index === 1,
          attachments: { images: v.images, docs: [] }
        })),
        validated: true,
        created_at: new Date().toISOString()
      })
      return ok({ ...draft })
    })
  },

  /** 获取草稿（刷新续作用） */
  getDraft: (draftId) => {
    if (!USE_MOCK_BIZ) {
      return real({ url: `/api/drafts/${draftId}`, method: 'get' }).then((d) => ok(d))
    }
    return delay(100).then(() => {
      const draft = sxkApi._drafts.find((d) => d.id === draftId)
      if (!draft) return { code: 4041, msg: '草稿不存在', data: null }
      return ok({ ...draft })
    })
  },

  /** A/B 投票：按版本投票，同方向再点 = 取消 */
  castVote: (generationId, versionIndex, vote) => {
    if (!USE_MOCK_BIZ) {
      return real({
        url: `/api/history/${generationId}/vote`,
        method: 'put',
        data: { version_index: versionIndex, vote }
      }).then((d) => ok(d))
    }
    return delay(120).then(() => {
      const gen = mockGenerations.find((g) => g.generation_id === generationId)
      if (!gen) return { code: 4041, msg: '记录不存在', data: null }
      const v = gen.versions[versionIndex - 1]
      if (!v) return ok(gen)
      v.votes = v.votes || { like: 0, dislike: 0 }
      v.voters = v.voters || {}
      const voterId = mockCurrentUser?.username || 'guest'
      const prev = v.voters[voterId]
      // 切换/取消
      if (prev === vote) {
        v.voters[voterId] = ''
        v.votes[vote] = Math.max(0, v.votes[vote] - 1)
      } else {
        if (prev) v.votes[prev] = Math.max(0, v.votes[prev] - 1)
        v.voters[voterId] = vote
        v.votes[vote] = (v.votes[vote] || 0) + 1
      }
      return ok({ ...gen })
    })
  },

  /** 整体反馈（👍/👎 在历史记录级别） */
  setHistoryFeedback: (generationId, feedback) => {
    if (!USE_MOCK_BIZ) {
      return real({
        url: `/api/history/${generationId}/feedback`,
        method: 'put',
        data: { feedback }
      }).then((d) => ok(d))
    }
    return delay(80).then(() => {
      const gen = mockGenerations.find((g) => g.generation_id === generationId)
      if (!gen) return { code: 4041, msg: '记录不存在', data: null }
      gen.feedback = gen.feedback === feedback ? '' : feedback
      return ok({ ...gen })
    })
  },

  /** 简单 Markdown 渲染（前端工具方法，方便调用） */
  renderMarkdown: (md) => md || '',

  /**
   * 导出历史内容（支持 docx / markdown / txt 三种格式）
   * GET /api/history/{id}/export?format=docx|markdown|txt
   * - 真实链路：responseType: blob，由后端生成文件，前端从 blob + Content-Disposition 触发下载
   * - Mock 阶段：按 format 生成本地 blob 触发下载
   */
  exportHistory: (generationId, format = 'docx') => {
    if (!USE_MOCK_BIZ) {
      // 关键：不能用 real()（它只返回 res.data），需要拿到完整 response 以读取 Content-Disposition 文件名
      return request({
        url: `/api/history/${generationId}/export?format=${format}`,
        method: 'get',
        responseType: 'blob'
      }).then((res) => {
        const blob = res.data
        const cd = res.headers['content-disposition'] || ''
        // 从 Content-Disposition 提取文件名（优先 filename*=UTF-8''，回退 filename=）
        let filename = `export_${generationId}.${format === 'markdown' ? 'md' : format}`
        const starMatch = cd.match(/filename\*=UTF-8''(.+?)(?:;|$)/i)
        if (starMatch) {
          try { filename = decodeURIComponent(starMatch[1]) } catch { /* ignore */ }
        } else {
          const plainMatch = cd.match(/filename="?([^";]+)"?/i)
          if (plainMatch) filename = plainMatch[1]
        }
        // 触发浏览器下载（与 mock 路径一致的 <a> 点击方式）
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = filename
        a.style.display = 'none'
        document.body.appendChild(a)
        a.click()
        setTimeout(() => {
          document.body.removeChild(a)
          URL.revokeObjectURL(url)
        }, 100)
        return ok({ filename, format })
      })
    }
    return delay(200).then(() => {
      const gen = mockGenerations.find((g) => g.generation_id === generationId)
      const baseName = gen?.product?.name || 'content'
      const mdText = gen
        ? gen.versions
            .map((v) => `# ${v.name}\n\n${v.content_html || v.content_markdown || v.body || ''}`)
            .join('\n\n---\n\n')
        : ''
      // mock 阶段统一按 format 生成本地文件
      let blob, ext, mime
      if (format === 'txt') {
        // txt 去掉 markdown 标记
        const txtText = (mdText || '').replace(/[#*`_>\-]/g, '').trim() || '空内容'
        blob = new Blob([txtText], { type: 'text/plain;charset=utf-8' })
        ext = 'txt'
        mime = 'text/plain'
      } else if (format === 'markdown') {
        blob = new Blob([mdText || '# 空内容\n'], { type: 'text/markdown;charset=utf-8' })
        ext = 'md'
        mime = 'text/markdown'
      } else {
        // docx 真实后端响应；mock 用 markdown 替代
        blob = new Blob([mdText || '# 空内容\n'], { type: 'text/markdown;charset=utf-8' })
        ext = 'docx'
        mime = 'application/octet-stream'
      }
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${baseName}_${generationId}.${ext}`
      a.style.display = 'none'
      document.body.appendChild(a)
      a.click()
      setTimeout(() => {
        document.body.removeChild(a)
        URL.revokeObjectURL(url)
      }, 100)
      return ok({ filename: a.download, size: blob.size, format, mime })
    })
  },

  // 别名：保留向后兼容（Phase F 前历史页面调 exportDocx）
  exportDocx: (generationId) => sxkApi.exportHistory(generationId, 'docx'),
  exportMarkdown: (generationId) => sxkApi.exportHistory(generationId, 'markdown'),
  exportTxt: (generationId) => sxkApi.exportHistory(generationId, 'txt'),

  // ============== Phase C: 成员管理 ==============

  /**
   * 4.x.1 列出成员 GET /api/members
   * 真实后端响应：[{id, username, name, email, color, is_admin, created_at}, ...]
   */
  listMembers: () => {
    if (!USE_MOCK_BIZ) {
      return real({ url: '/api/members', method: 'get' })
        .then((raw) => ok(raw))
    }
    return delay(200).then(() => ok(mockMembers || []))
  },

  /**
   * 4.x.2 创建成员 POST /api/members
   * 请求：{username, password, name, email, color, is_admin}
   */
  createMember: (payload) => {
    if (!USE_MOCK_BIZ) {
      return real({ url: '/api/members', method: 'post', data: payload })
        .then((raw) => ok(raw))
    }
    return delay().then(() => {
      const list = mockMembers || []
      if (list.some((m) => m.username === payload.username)) {
        return { code: 4091, msg: '用户名已存在', data: null }
      }
      const newM = {
        id: `m_${Date.now()}`,
        username: payload.username,
        name: payload.name || payload.username,
        email: payload.email || '',
        color: payload.color || '#3b82f6',
        is_admin: !!payload.is_admin,
        created_at: new Date().toISOString()
      }
      list.push(newM)
      return ok(newM)
    })
  },

  /**
   * 4.x.3 更新成员 PUT /api/members/{id}
   * 请求：{name?, email?, color?, is_admin?, new_password?}
   */
  updateMember: (id, payload) => {
    if (!USE_MOCK_BIZ) {
      return real({ url: `/api/members/${id}`, method: 'put', data: payload })
        .then((raw) => ok(raw))
    }
    return delay().then(() => {
      const list = mockMembers || []
      const idx = list.findIndex((m) => m.id === id)
      if (idx < 0) return { code: 4041, msg: '成员不存在', data: null }
      list[idx] = { ...list[idx], ...payload, id }
      return ok(list[idx])
    })
  },

  /**
   * 4.x.4 删除成员 DELETE /api/members/{id}
   */
  removeMember: (id) => {
    if (!USE_MOCK_BIZ) {
      return real({ url: `/api/members/${id}`, method: 'delete' })
        .then(() => ok(null))
    }
    return delay().then(() => {
      const list = mockMembers || []
      const idx = list.findIndex((m) => m.id === id)
      if (idx < 0) return { code: 4041, msg: '成员不存在', data: null }
      list.splice(idx, 1)
      return ok(null)
    })
  },

  // ============== Phase D: 竞品分析 ==============

  /**
   * 4.x.5 列出竞品 GET /api/products/{pid}/competitors
   * 真实后端响应：[{name, score, summary, source, last_updated}]
   */
  listCompetitors: (productId) => {
    if (!USE_MOCK_BIZ) {
      // 真实链路：竞品名存在 products.competitors 数组中，直接取产品详情构造
      // （后端 /api/products/{pid}/competitors 查的是 competitor_analyses 表，
      //  该表需内容生成阶段才会填充，与页面"展示已填竞品"的意图不符）
      return real({ url: `/api/products/${productId}`, method: 'get' })
        .then((raw) => {
          const p = adaptProduct(raw)
          const comps = (p && p.competitors) || []
          const list = comps.map((name, i) => ({
            name,
            score: 0,
            summary: `${name} 是与本产品具有相似定位的竞品。`,
            source: 'manual',
            last_updated: p.updated_at || new Date().toISOString()
          }))
          return ok(list)
        })
    }
    return delay(200).then(() => {
      // mock：从产品的 competitors 字段构造
      const p = (mockProducts || []).find((x) => x.product_id === productId)
      if (!p) return ok([])
      const list = (p.competitors || []).map((name, i) => ({
        name,
        score: 4.2 - i * 0.1,
        summary: `${name} 是与本产品具有相似定位的竞品。`,
        source: 'heuristic',
        last_updated: new Date().toISOString()
      }))
      return ok(list)
    })
  },

  /**
   * 4.x.6 删除竞品 DELETE /api/products/{pid}/competitors/{name}
   */
  removeCompetitor: (productId, name) => {
    if (!USE_MOCK_BIZ) {
      // 真实链路：竞品名存在 products.competitors 数组中，
      // 删除 = 取出当前数组，过滤掉目标后整体 PUT 回写
      return real({ url: `/api/products/${productId}`, method: 'get' })
        .then((raw) => {
          const p = adaptProduct(raw)
          const newComps = (p.competitors || []).filter((n) => n !== name)
          const backendPayload = adaptProductToBackend({ ...p, competitors: newComps })
          return real({ url: `/api/products/${productId}`, method: 'put', data: backendPayload })
        })
        .then(() => ok(null))
    }
    return delay().then(() => {
      const p = (mockProducts || []).find((x) => x.product_id === productId)
      if (p && Array.isArray(p.competitors)) {
        p.competitors = p.competitors.filter((n) => n !== name)
      }
      return ok(null)
    })
  }
}

export default sxkApi
