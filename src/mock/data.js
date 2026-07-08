/**
 * 神行库（SXK）前端 Mock 数据集
 *
 * 说明：
 * 1. 后端未联调前，前端通过 import 此处的常量模拟接口数据。
 * 2. 数据结构与《神行库_接口设计文档 v1.1》保持一致（snake_case 字段、code/msg/data/trace_id 响应壳）。
 * 3. 所有时间字段统一 ISO8601（带时区），便于将来切换真实接口时无需改字段。
 */

// ---------- 0. 通用工具：拼装接口标准响应壳 ----------
const ok = (data) => ({
  code: 0,
  msg: 'ok',
  data,
  trace_id: `mock-${Math.random().toString(36).slice(2, 10)}`
})

// ---------- 1. 当前登录用户（用于 dashboard 欢迎区与顶部栏） ----------
export const mockCurrentUser = {
  user_id: 'u_8f1d2c4a6e9b4f7d8a3c5e7b9d2f1a4c',
  username: 'alice.li',
  role: 'user',
  status: 'active',
  created_at: '2026-04-12T10:08:31+08:00',
  last_login_at: '2026-07-07T08:55:11+08:00',
  avatar: ''
}

// ---------- 2. 产品知识库（对应 4.3 接口域） ----------
// 来源：神行库_数据库设计文档 6.5/6.6/6.7/6.8 测试数据；features 与标签分离
export const mockProducts = [
  {
    product_id: 'p_dataplatform_x',
    name: '智能数据平台 X',
    category: '数据分析',
    description:
      '支持多源数据接入、AI 智能分析、实时可视化大屏与自助式 BI，面向业务团队开箱即用。',
    pricing: '基础版 ¥50,000/年',
    features: [
      { name: '多源数据接入', description: '支持 20+ 数据源一键接入，分钟级完成配置。', sort_order: 1 },
      { name: 'AI 智能分析', description: '内置机器学习模型，自动识别异常与趋势。', sort_order: 2 },
      { name: '实时大屏', description: '毫秒级刷新的可视化大屏，支持拖拽布局。', sort_order: 3 }
    ],
    target_customers: ['制造业', '金融业', '消费品'],
    competitors: ['产品Y'],
    selling_points: ['部署快', '成本低', '易上手'],
    created_by: 'u_8f1d2c4a6e9b4f7d8a3c5e7b9d2f1a4c',
    created_at: '2026-04-12T10:30:11+08:00',
    updated_at: '2026-07-05T16:08:42+08:00',
    is_deleted: false
  },
  {
    product_id: 'p_crm_pro',
    name: '智慧 CRM 系统',
    category: 'CRM',
    description:
      '客户全生命周期管理、销售预测、营销自动化与移动外勤一体化。',
    pricing: '标准版 ¥80,000/年',
    features: [
      { name: '客户全生命周期', description: '从线索到回款的全流程闭环管理。', sort_order: 1 },
      { name: '销售预测', description: '基于历史数据的智能销售预测，准确率领先行业。', sort_order: 2 }
    ],
    target_customers: ['消费品'],
    competitors: ['销售易'],
    selling_points: ['销售预测准确率高', '部署快'],
    created_by: 'u_2a7b9c4d1e8f6a5b3c2d7e9f1a4b6c8d',
    created_at: '2026-05-04T09:18:30+08:00',
    updated_at: '2026-07-06T11:42:18+08:00',
    is_deleted: false
  },
  {
    product_id: 'p_martech_ai',
    name: '营销自动化平台',
    category: '营销自动化',
    description:
      '全渠道触达、A/B 测试、用户旅程编排与营销 ROI 分析。',
    pricing: '企业版 ¥120,000/年',
    features: [
      { name: '用户旅程编排', description: '可视化拖拽搭建多触点用户旅程。', sort_order: 1 },
      { name: 'A/B 测试', description: '多版本实验与显著性分析，决策有据可依。', sort_order: 2 }
    ],
    target_customers: ['消费品'],
    competitors: ['营销宝'],
    selling_points: ['A/B 测试', '行业模板多'],
    created_by: 'u_4c6e8a2b5d7f9c1e3a4b6d8f0c2e4a7b',
    created_at: '2026-06-19T13:55:42+08:00',
    updated_at: '2026-07-07T08:21:09+08:00',
    is_deleted: false
  },
  {
    product_id: 'p_collab_suite',
    name: '企业协作套件',
    category: '其他',
    description:
      '团队即时沟通、文档协作、项目管理与日历一体化。',
    pricing: '旗舰版 ¥36,000/年',
    features: [
      { name: '即时沟通', description: '支持群聊、@提醒、消息已读与文件传输。', sort_order: 1 }
    ],
    target_customers: ['制造业'],
    competitors: ['产品Y'],
    selling_points: ['部署快', '成本低'],
    created_by: 'u_8a2c4e6b8d0f2a5c7e9b1d4f6a8c0e3b',
    created_at: '2026-02-15T10:11:24+08:00',
    updated_at: '2026-07-04T19:33:51+08:00',
    is_deleted: false
  },
  {
    product_id: 'p_insight_ocr',
    name: '智能识别引擎',
    category: '数据分析',
    description:
      '票据、合同、证照的高精度 OCR 与结构化抽取，秒级响应。',
    pricing: '按调用量计费',
    features: [
      { name: '票据识别', description: '支持 12 类常见票据模板，准确率 99.2%。', sort_order: 1 },
      { name: '合同抽取', description: '自动抽取合同关键字段，秒级返回结构化结果。', sort_order: 2 }
    ],
    target_customers: ['金融业'],
    competitors: ['产品Y'],
    selling_points: ['行业模板多'],
    created_by: 'u_2a7b9c4d1e8f6a5b3c2d7e9f1a4b6c8d',
    created_at: '2026-06-02T14:46:08+08:00',
    updated_at: '2026-07-01T09:12:37+08:00',
    is_deleted: false
  },
  {
    product_id: 'p_legacy_cms',
    name: '老门户内容站',
    category: '其他',
    description: '内部已下线的产品，仅历史数据保留。',
    pricing: '停售',
    features: [{ name: '内容发布', description: '简单的图文发布能力。', sort_order: 1 }],
    target_customers: [],
    competitors: [],
    selling_points: [],
    created_by: 'u_8f1d2c4a6e9b4f7d8a3c5e7b9d2f1a4c',
    created_at: '2025-11-08T09:00:00+08:00',
    updated_at: '2026-03-15T17:24:06+08:00',
    is_deleted: true // 软删除示例
  }
]

// ---------- 3. 模板（对应 4.5 接口域） ----------
export const mockTemplates = [
  {
    template_id: 't_intro_professional',
    name: '产品介绍·专业正式',
    scene_code: 'product_intro',
    output_format: 'long_text',
    description: '适用于官网、白皮书与客户提案的专业产品介绍。',
    prompt:
      '请基于产品[name]与卖点[selling_points]撰写一段专业正式的产品介绍，目标受众为[audience]，重点突出[highlights]。',
    is_custom: false,
    use_count_30d: 86,
    tags: [{ tag_id: 12, name: '高客单价' }],
    sections: [
      { section_id: 1, title: '产品概述', guidance: '1 段，简明扼要定义产品定位与目标客户。', sort_order: 1 },
      { section_id: 2, title: '核心功能', guidance: '列出 3-5 个核心能力，每条配 1 句场景化描述。', sort_order: 2 },
      { section_id: 3, title: '差异化优势', guidance: '突出与同类产品的差异点与可量化收益。', sort_order: 3 }
    ],
    updated_at: '2026-06-20T14:11:02+08:00'
  },
  {
    template_id: 't_intro_casual',
    name: '产品介绍·亲切口语',
    scene_code: 'product_intro',
    output_format: 'long_text',
    description: '公众号与社群风格的轻松产品介绍。',
    prompt: '以亲切口语风格介绍产品[name]，结合生活化场景，控制在[length]字以内。',
    is_custom: false,
    use_count_30d: 64,
    tags: [],
    sections: [
      { section_id: 4, title: '场景引入', guidance: '用一个贴近生活的小故事切入。', sort_order: 1 }
    ],
    updated_at: '2026-06-21T10:08:13+08:00'
  },
  {
    template_id: 't_intro_brief',
    name: '产品介绍·简洁有力',
    scene_code: 'product_intro',
    output_format: 'short_text',
    description: 'Banner 与广告位的一句话价值主张。',
    prompt: '用一句 30 字以内的口号概括产品[name]的核心价值，聚焦[highlights]。',
    is_custom: false,
    use_count_30d: 51,
    tags: [],
    sections: [{ section_id: 5, title: '一句话价值', guidance: '不超过 30 字。', sort_order: 1 }],
    updated_at: '2026-06-22T08:51:44+08:00'
  },
  {
    template_id: 't_competitor_objective',
    name: '竞品对比·客观中立',
    scene_code: 'competitor',
    output_format: 'table',
    description: '客观中立的竞品对比报告，含功能表与差异化分析。',
    prompt:
      '基于产品[name]对比竞品[competitor]，从[dimensions]维度展开，输出对比表与差异化结论。',
    is_custom: false,
    use_count_30d: 39,
    tags: [{ tag_id: 12, name: '高客单价' }],
    sections: [
      { section_id: 6, title: '功能对比表', guidance: '输出 markdown 表格，列为我方与竞品。', sort_order: 1 },
      { section_id: 7, title: '差异化分析', guidance: '每行对比给出 1 句"我方优势 / 持平 / 劣势"标注。', sort_order: 2 },
      { section_id: 8, title: '话术建议', guidance: '给出 3 句可直接面向客户的话术。', sort_order: 3 }
    ],
    updated_at: '2026-06-25T11:42:08+08:00'
  },
  {
    template_id: 't_channel_adapt',
    name: '多渠道适配',
    scene_code: 'channel_adapt',
    output_format: 'long_text',
    description: '将一段源内容适配为微信公众号 / LinkedIn / 内部 PPT 三种风格。',
    prompt: '将源内容[source]按目标渠道[channel]调整语言风格、排版与长度，输出三个版本。',
    is_custom: false,
    use_count_30d: 27,
    tags: [],
    sections: [
      { section_id: 9, title: '微信公众号版', guidance: '控制在 800 字以内，含小标题与 emoji。', sort_order: 1 },
      { section_id: 10, title: 'LinkedIn 版', guidance: '英文友好的国际化口吻，3-5 段。', sort_order: 2 },
      { section_id: 11, title: '内部 PPT 版', guidance: '输出 1 页标题 + 1 页核心要点。', sort_order: 3 }
    ],
    updated_at: '2026-06-26T15:30:21+08:00'
  },
  {
    template_id: 't_email_newsletter',
    name: '邮件营销·月度动态',
    scene_code: 'email',
    output_format: 'long_text',
    description: '月度产品动态邮件模板。',
    prompt: '撰写一封面向[audience]的月度产品邮件，包含 1 个核心动态与 2 个使用案例。',
    is_custom: false,
    use_count_30d: 33,
    tags: [{ tag_id: 11, name: '金融行业' }],
    sections: [
      { section_id: 12, title: '核心动态', guidance: '1 段产品近况更新。', sort_order: 1 }
    ],
    updated_at: '2026-06-18T13:24:50+08:00'
  },
  {
    template_id: 't_intro_finance',
    name: '金融业产品介绍',
    scene_code: 'product_intro',
    output_format: 'long_text',
    description: '面向金融行业决策者的合规型产品介绍。',
    prompt: '围绕金融合规与数据安全撰写产品[name]介绍，强调[highlights]与风控能力。',
    is_custom: true,
    use_count_30d: 12,
    tags: [
      { tag_id: 11, name: '金融行业' },
      { tag_id: 12, name: '高客单价' }
    ],
    sections: [
      { section_id: 13, title: '合规要点', guidance: '列出 3 条', sort_order: 1 },
      { section_id: 14, title: '产品价值', guidance: '突出 [highlights]', sort_order: 2 }
    ],
    updated_at: '2026-07-01T18:42:09+08:00'
  }
]

// ---------- 4. 模板场景元数据（对应 4.5.7 / 4.6.11） ----------
// 用于"内容生成"页动态渲染参数表单
export const mockSceneSchemas = [
  {
    scene_code: 'product_intro',
    name: '产品介绍文案',
    params: [
      {
        key: 'channel',
        type: 'enum',
        label: '目标渠道',
        options: ['微信公众号', 'LinkedIn', '官网', '内部 PPT'],
        required: true,
        default: '微信公众号'
      },
      {
        key: 'style',
        type: 'enum',
        label: '文案风格',
        options: ['专业正式', '轻松活泼', '极简风格'],
        required: true,
        default: '专业正式'
      },
      {
        key: 'length',
        type: 'enum',
        label: '内容长度',
        options: ['短(200字)', '中(500字)', '长(1000字)'],
        required: true,
        default: '中(500字)'
      },
      { key: 'audience', type: 'text', label: '目标受众', required: true, default: '企业决策者' },
      {
        key: 'highlights',
        type: 'text',
        label: '重点突出',
        required: true,
        default: '核心卖点与差异化优势'
      }
    ]
  },
  {
    scene_code: 'competitor',
    name: '竞品对比报告',
    params: [
      { key: 'competitor', type: 'text', label: '对比竞品', required: true, default: '传统 BI 厂商' },
      { key: 'dimensions', type: 'text', label: '对比维度', required: true, default: '功能、性能、价格' },
      {
        key: 'style',
        type: 'enum',
        label: '报告风格',
        options: ['客观中立', '突出优势', '攻击性'],
        required: true,
        default: '客观中立'
      }
    ]
  },
  {
    scene_code: 'channel_adapt',
    name: '多渠道内容适配',
    params: [
      {
        key: 'channel',
        type: 'enum',
        label: '目标渠道',
        options: ['微信公众号', 'LinkedIn', '官网', '内部 PPT'],
        required: true,
        default: '微信公众号'
      },
      {
        key: 'tone',
        type: 'enum',
        label: '渠道调性',
        options: ['保持原样', '更活泼', '更正式'],
        required: true,
        default: '保持原样'
      },
      { key: 'source', type: 'textarea', label: '源内容', required: true, default: '' }
    ]
  }
]

// ---------- 5. 生成历史（对应 4.6 / 4.7 接口域） ----------
export const mockGenerations = [
  {
    generation_id: 'g_2026070709_a1b2c3',
    product: { product_id: 'p_dataplatform_x', name: '智能数据平台 X', is_deleted: false },
    template: { template_id: 't_intro_professional', name: '产品介绍·专业正式' },
    status: 'success',
    selected_version: 'A',
    duration_ms: 11420,
    params: { channel: '微信公众号', style: '专业正式', length: '中(500字)' },
    created_at: '2026-07-07T09:01:48+08:00',
    updated_at: '2026-07-07T09:02:00+08:00',
    archived_at: null
  },
  {
    generation_id: 'g_2026070709_d4e5f6',
    product: { product_id: 'p_martech_ai', name: '营销自动化平台', is_deleted: false },
    template: { template_id: 't_intro_casual', name: '产品介绍·亲切口语' },
    status: 'success',
    selected_version: 'B',
    duration_ms: 9870,
    params: { channel: 'LinkedIn', style: '亲切口语' },
    created_at: '2026-07-07T09:08:11+08:00',
    updated_at: '2026-07-07T09:08:21+08:00',
    archived_at: null
  },
  {
    generation_id: 'g_2026070617_7a8b9c',
    product: { product_id: 'p_dataplatform_x', name: '智能数据平台 X', is_deleted: false },
    template: { template_id: 't_competitor_objective', name: '竞品对比·客观中立' },
    status: 'success',
    selected_version: 'A',
    duration_ms: 22080,
    params: { competitor: '产品Y', dimensions: '功能、性能、价格', style: '客观中立' },
    created_at: '2026-07-06T17:22:30+08:00',
    updated_at: '2026-07-06T17:22:52+08:00',
    archived_at: null
  },
  {
    generation_id: 'g_2026070611_0d1e2f',
    product: { product_id: 'p_crm_pro', name: '智慧 CRM 系统', is_deleted: false },
    template: { template_id: 't_intro_brief', name: '产品介绍·简洁有力' },
    status: 'running',
    selected_version: null,
    duration_ms: null,
    params: { channel: '官网', style: '简洁有力', length: '短(200字)' },
    created_at: '2026-07-06T11:18:09+08:00',
    updated_at: '2026-07-06T11:18:17+08:00',
    archived_at: null
  },
  {
    generation_id: 'g_2026070509_3g4h5i',
    product: {
      product_id: 'p_collab_suite',
      name: '老门户内容站',
      is_deleted: true // 软删除产品仍出现在历史（BR-H-08）
    },
    template: { template_id: 't_channel_adapt', name: '多渠道适配' },
    status: 'success',
    selected_version: 'A',
    duration_ms: 14210,
    params: { channel: '微信公众号 / LinkedIn / 内部 PPT', tone: '更正式' },
    created_at: '2026-07-05T09:42:18+08:00',
    updated_at: '2026-07-05T09:42:32+08:00',
    archived_at: null
  }
]

// ---------- 6. 单版本内容（用于历史详情 / 内容编辑 tab） ----------
// 字段命名对应 generation_versions.content
export const mockVersionContents = {
  g_2026070709_a1b2c3: [
    {
      version_key: 'A',
      name: '版本 A: 专业正式（推荐）',
      is_recommended: true,
      content_html:
        '<h2>智能数据平台 X</h2><p>面向企业决策者的下一代数据中台，提供多源数据接入、AI 智能分析与实时可视化大屏能力。</p><p>区别于同类产品，我们提供秒级刷新的实时大屏与可拖拽的仪表盘，让业务团队无需编码即可上手。</p>',
      word_count: 538
    },
    {
      version_key: 'B',
      name: '版本 B: 亲切口语',
      is_recommended: false,
      content_html:
        '<h2>想看懂业务？试试数据平台 X</h2><p>不用懂代码也能上手，数据接入只需几分钟，关键指标自动跑出来。</p>',
      word_count: 486
    },
    {
      version_key: 'C',
      name: '版本 C: 简洁有力',
      is_recommended: false,
      content_html: '智能数据平台 X：让业务团队 5 分钟看懂数据。',
      word_count: 22
    }
  ],
  g_2026070709_d4e5f6: [
    {
      version_key: 'A',
      name: '版本 A: 亲切口语（推荐）',
      is_recommended: true,
      content_html:
        '<h2>营销自动化，也能很轻盈</h2><p>想让用户旅程不再繁琐？试试可视化拖拽搭建，一键上线多触点营销活动。</p>',
      word_count: 502
    },
    {
      version_key: 'B',
      name: '版本 B: 专业正式',
      is_recommended: false,
      content_html:
        '<h2>营销自动化平台：全渠道 ROI 透明化</h2><p>面向 CMO 与增长团队的统一编排能力，实时监控每条旅程的转化表现。</p>',
      word_count: 588
    }
  ],
  g_2026070617_7a8b9c: [
    {
      version_key: 'A',
      name: '概览版（推荐）',
      is_recommended: true,
      content_html:
        '<h3>智能数据平台 X vs 产品Y 对比</h3><table border="1" cellpadding="6"><thead><tr><th>维度</th><th>智能数据平台 X</th><th>产品Y</th></tr></thead><tbody><tr><td>数据源接入</td><td>20+ 一键接入</td><td>10+ 需开发</td></tr><tr><td>智能分析</td><td>内置 AI 模型</td><td>依赖人工建模</td></tr><tr><td>实时性</td><td>毫秒级</td><td>分钟级</td></tr></tbody></table>',
      word_count: 312
    },
    {
      version_key: 'B',
      name: '详细版',
      is_recommended: false,
      content_html:
        '<h3>详细对比</h3><p>从功能、性能、价格三方面展开，结合客户实际场景给出我方优势说明。</p>',
      word_count: 612
    }
  ]
}

// ---------- 7. Agent 协作（默认 4 Agent / 竞品专用 4 Agent） ----------
// 对应 generation_agent_runs 表
export const mockAgentRunsDefault = [
  {
    agent_code: 'retrieval',
    agent_name: '产品信息检索 Agent',
    status: 'pending',
    duration_ms: null,
    sort_order: 1,
    thought_chain: ['正在从"产品知识库"检索产品信息...']
  },
  {
    agent_code: 'generation',
    agent_name: '内容生成 Agent',
    status: 'pending',
    duration_ms: null,
    sort_order: 2,
    thought_chain: ['应用"专业正式"风格构建初稿...']
  },
  {
    agent_code: 'channel_adapt',
    agent_name: '渠道适配 Agent',
    status: 'pending',
    duration_ms: null,
    sort_order: 3,
    thought_chain: ['适配微信公众号格式...']
  },
  {
    agent_code: 'validation',
    agent_name: '内容校验 Agent',
    status: 'pending',
    duration_ms: null,
    sort_order: 4,
    thought_chain: ['参数一致性核验...']
  }
]

export const mockAgentRunsCompetitor = [
  {
    agent_code: 'retrieval',
    agent_name: '产品信息检索 Agent',
    status: 'pending',
    duration_ms: null,
    sort_order: 1,
    thought_chain: ['正在检索我方产品信息...']
  },
  {
    agent_code: 'competitor_analysis',
    agent_name: '竞品分析 Agent',
    status: 'pending',
    duration_ms: null,
    sort_order: 2,
    thought_chain: ['检索竞品公开信息...']
  },
  {
    agent_code: 'generation',
    agent_name: '内容生成 Agent',
    status: 'pending',
    duration_ms: null,
    sort_order: 3,
    thought_chain: ['构建对比报告...']
  },
  {
    agent_code: 'validation',
    agent_name: '内容校验 Agent',
    status: 'pending',
    duration_ms: null,
    sort_order: 4,
    thought_chain: ['客观性核验...']
  }
]

// ---------- 8. 校验问题（对应 validation_issues 表） ----------
export const mockValidationIssues = {
  'g_2026070709_a1b2c3:A': [
    {
      issue_id: 1,
      category: 'param_consistency',
      severity: 'info',
      message: '产品名称与知识库一致：智能数据平台 X。',
      suggestion: '无需修改',
      resolved: true
    },
    {
      issue_id: 2,
      category: 'fact_accuracy',
      severity: 'warn',
      message: '"毫秒级响应"在产品表中未找到对应佐证，请补充依据。',
      suggestion: '改为"秒级响应"或补充技术说明。',
      resolved: false
    },
    {
      issue_id: 3,
      category: 'sensitive_word',
      severity: 'info',
      message: '命中停用词 0 处，敏感词 0 处。',
      suggestion: '无需修改',
      resolved: true
    }
  ]
}

// ---------- 9. 首页 Dashboard 专用统计 ----------
// 对应 4.8.1 GET /stats/dashboard
export const mockDashboardStats = {
  product_count: 6, // 与 mockProducts.length (含软删除) 对齐
  monthly_generation_count: 18,
  avg_score: 4.6,
  avg_duration_ms: 11240, // 与 mockGenerations 内 success 的均值近似
  running_tasks: 1, // mockGenerations 中 1 条 status='running'
  popular_scenes: [
    { scene_code: 'product_intro', use_count_30d: 8 },
    { scene_code: 'competitor', use_count_30d: 4 },
    { scene_code: 'channel_adapt', use_count_30d: 2 }
  ]
}

// ---------- 10. 场景码 → 中文名映射 ----------
export const mockSceneNameMap = mockTemplates.reduce((acc, t) => {
  if (!acc[t.scene_code]) acc[t.scene_code] = t.name
  return acc
}, {
  product_intro: '产品介绍',
  competitor: '竞品分析',
  channel_adapt: '渠道适配',
  email: '邮件营销',
  event: '活动宣传',
  other: '其他'
})

// 页面级统计常用：返回 {total, by_category}
export const mockProductStats = {
  total: mockProducts.length,
  by_category: mockProducts.reduce((acc, p) => {
    if (p.is_deleted) return acc
    acc[p.category] = (acc[p.category] || 0) + 1
    return acc
  }, {})
}

// 导出通用 ok 工具，供后续 sxkApi 直接复用
export { ok }
