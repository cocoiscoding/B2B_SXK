"""初始示例数据：3 个产品 + 6 个场景模板。

首次启动时若表为空则自动灌入，确保用户开箱即用。
如果用户已通过 SQL 脚本初始化了数据，则为缺少 embedding 的产品补上向量。

设计目的：
- 让用户启动后立即有数据可看、可测试
- 避免空数据库导致的功能无法演示
"""
from psycopg2.extras import Json
from app.database import query_one, transaction
from app.vector_search import embed_product
from config import DEFAULT_USER_PASSWORD, EMBEDDING_DIM
from app.auth import hash_password


# SEED_PRODUCTS 是预置的 3 个示例产品
# 每个产品是一个字典，包含名称、类别、标语、描述、功能列表、技术参数等
SEED_PRODUCTS: list[dict] = [
    {
        "id": "P001",
        "created_by": "M001",
        "name": "智能数据平台 X",
        "category": ["数据分析", "企业级"],
        "description": "面向中大型企业的一站式智能数据分析平台，覆盖数据接入、清洗、建模、可视化到 AI 预测的全链路能力。",
        "features": [
            {"name": "多源数据接入", "description": "支持 20+ 数据源（MySQL、PostgreSQL、Kafka、Excel、API 等），分钟级完成对接。"},
            {"name": "AI 智能分析", "description": "内置机器学习模型，自动识别数据异常、预测业务趋势，支持自然语言提问。"},
            {"name": "可视化看板", "description": "拖拽式看板搭建，50+ 图表类型，支持实时刷新与大屏投放。"},
            {"name": "行列级权限管控", "description": "细粒度权限体系，满足金融级数据安全合规要求。"},
        ],
        "target_customers": ["制造业", "金融业", "零售业", "互联网"],
        "pricing": "按年订阅，基础版 ¥50,000/年，企业版 ¥200,000/年",
        "selling_points": ["部署快", "成本低", "易上手", "AI 原生"],
        "images": [],
        "documents": [],
    },
    {
        "id": "P002",
        "created_by": "M002",
        "name": "云雀协同办公",
        "category": ["协同办公", "SaaS"],
        "description": "面向中小团队的实时协同办公套件，整合文档、表格、即时通讯、视频会议与项目管理于一体。",
        "features": [
            {"name": "实时多人协同", "description": "文档/表格支持百人同时在线编辑，毫秒级同步无冲突。"},
            {"name": "AI 写作助手", "description": "会议纪要自动生成、周报一键起草、智能续写与润色。"},
            {"name": "一体化项目管理", "description": "看板/甘特/列表三视图切换，任务自动流转与提醒。"},
            {"name": "跨端无缝同步", "description": "Web / 桌面 / 移动端全覆盖，离线编辑自动合并。"},
        ],
        "target_customers": ["初创公司", "中小型企业", "远程团队", "教育机构"],
        "pricing": "免费版 0 元，团队版 ¥99/人/年，企业版联系销售",
        "selling_points": ["轻量", "免费起步", "AI 加持", "上手零成本"],
        "images": [],
        "documents": [],
    },
    {
        "id": "P003",
        "created_by": "M003",
        "name": "墨盾安全网关",
        "category": ["网络安全", "云原生"],
        "description": "新一代云原生安全网关，融合 WAF、API 防护、Bot 管理与 DDoS 清洗能力，为 Web 应用提供全栈防护。",
        "features": [
            {"name": "AI 威胁检测", "description": "基于深度学习的 0-day 攻击识别，检出率 99.6%，误报率低于 0.1%。"},
            {"name": "全栈 API 防护", "description": "自动发现 API 资产，覆盖 OWASP API Top 10 全部风险。"},
            {"name": "弹性 DDoS 清洗", "description": "T 级清洗带宽，秒级响应，业务零中断。"},
            {"name": "可视化安全态势", "description": "实时攻击大屏 + 攻防复盘报告，安全运营一目了然。"},
        ],
        "target_customers": ["金融", "政企", "电商", "游戏"],
        "pricing": "按防护流量计费，基础版 ¥3,000/月起",
        "selling_points": ["AI 检测", "低延迟", "全栈防护", "弹性扩展"],
        "images": [],
        "documents": [],
    },
]


# SEED_SCENARIOS 是预置的 6 个内置场景模板
# 每个场景定义了参数表单、生成模板、适用渠道
# 渠道配置：驱动 ChannelAgent 的通用规则适配
# 每个渠道定义 tone（语气）、emoji（是否加 emoji）、format（排版格式）
# 新增渠道只需 INSERT 一条记录，无需修改代码
DEFAULT_CHANNELS: list[dict] = [
    {"name": "官网",          "display_name": "官网",          "tone": "专业正式",   "emoji": False, "format": "markdown",    "description": "品牌官网首页/详情页，风格专业正式"},
    {"name": "微信公众号",    "display_name": "微信公众号",    "tone": "亲切口语",   "emoji": True,  "format": "短段落",    "description": "公众号推文，短段落+emoji点缀"},
    {"name": "LinkedIn",     "display_name": "LinkedIn",      "tone": "专业且国际", "emoji": False, "format": "markdown",    "description": "领英专业社交平台"},
    {"name": "邮件营销",      "display_name": "邮件营销",      "tone": "直接说服",   "emoji": False, "format": "CTA导向",   "description": "EDM 邮件营销，突出行动号召"},
    {"name": "内部培训PPT",   "display_name": "内部培训PPT",   "tone": "要点精简",   "emoji": False, "format": "bullet",     "description": "PPT 演示文稿，要点化 bullet 风格"},
    {"name": "小红书",        "display_name": "小红书",        "tone": "种草分享",   "emoji": True,  "format": "短段落",    "description": "小红书笔记，种草风格+emoji"},
    {"name": "知乎",          "display_name": "知乎",          "tone": "深度专业",   "emoji": False, "format": "markdown",    "description": "知乎专栏/回答，深度内容"},
    {"name": "微博",          "display_name": "微博",          "tone": "简洁明快",   "emoji": True,  "format": "short",      "description": "微博短文案，140字内"},
    {"name": "抖音/短视频脚本","display_name": "抖音/短视频脚本","tone": "口语化强",   "emoji": False, "format": "short",      "description": "短视频口播脚本，口语化"},
    {"name": "B站",           "display_name": "B站",           "tone": "轻松有趣",   "emoji": True,  "format": "短段落",    "description": "B站专栏/动态，年轻化风格"},
]


SEED_SCENARIOS: list[dict] = [
    {
        "id": "S001",
        "name": "官网首页 Banner 文案",
        "description": "为官网首页生成吸引眼球的 Banner 文案，突出核心卖点。",
        "parameters": [
            {"name": "highlight", "description": "重点卖点"},
            {"name": "cta", "description": "行动号召语"},
        ],
    },
    {
        "id": "S002",
        "name": "产品介绍文案",
        "description": "完整的产品功能介绍文章，适合官网详情页或白皮书。",
        "parameters": [
            {"name": "audience", "description": "目标受众（如技术决策者、业务负责人、终端用户、投资人）"},
            {"name": "word_count", "description": "字数要求（如300字、600字、1000字）"},
        ],
    },
    {
        "id": "S003",
        "name": "竞品对比分析报告",
        "description": "自动拉取我方产品信息与竞品对比，生成结构化分析报告。",
        "parameters": [
            {"name": "competitor", "description": "竞品名称"},
            {"name": "focus", "description": "对比重点（如功能全面性、性价比、技术架构、服务支持）"},
        ],
    },
    {
        "id": "S004",
        "name": "客户案例包装",
        "description": "将客户使用场景包装成可对外发布的成功案例。",
        "parameters": [
            {"name": "industry", "description": "客户行业"},
            {"name": "result", "description": "核心成效"},
        ],
    },
    {
        "id": "S005",
        "name": "演示 PPT 大纲",
        "description": "生成产品演示 PPT 的结构化大纲，含每页要点。",
        "parameters": [
            {"name": "purpose", "description": "演示目的（如售前宣讲、投资人路演、内部培训、大会演讲）"},
            {"name": "slides", "description": "页数要求（如8页、15页、25页）"},
        ],
    },
    {
        "id": "S006",
        "name": "社交媒体帖子",
        "description": "生成适合社交媒体传播的短文案，含话题标签。",
        "parameters": [
            {"name": "topic", "description": "主题/事件"},
            {"name": "tone", "description": "语气风格（如活泼有趣、专业干货、情感共鸣、悬念反转）"},
        ],
    },
]


# SEED_TEMPLATES 是预置的模板数据，每个场景下关联若干模板
SEED_TEMPLATES: list[dict] = [
    {"id": "T001", "scenario_id": "S001", "name": "Banner 标准版", "tag": "标准",
     "description": "适用于官网首页标准 Banner 文案生成",
     "prompt": "生成官网 Banner 文案，主标题不超过 12 字，副标题不超过 30 字，突出「{highlight}」，行动号召为「{cta}」。",
     "constraints": {"title_max_chars": 12, "must_include_params": ["highlight", "cta"]},
     "structure": "主标题（≤12字，点出核心卖点）-> 副标题（≤30字，补充价值）-> 行动号召（用 cta 参数）",
     "examples": [{"title": "数据驱动决策", "body": "## 让每个动作都有数据支撑\n\n多源接入 + AI 分析，分钟级洞察趋势。\n\n👉 立即申请试用", "tags": ["Banner"]}],
     "differentiation_dims": ["核心卖点切入", "使用场景切入", "数据效果切入"],
     "applicable_channels": ["官网", "微信公众号", "小红书", "微博"],
     "tags": ["标准", "短文案", "官网"]},
    {"id": "T002", "scenario_id": "S001", "name": "Banner 促销版", "tag": "促销",
     "description": "适用于促销活动期间的 Banner 文案",
     "prompt": "生成促销 Banner 文案，主标题突出限时优惠，副标题强调「{highlight}」，行动号召为「{cta}」。要求紧迫感强，用语直接。",
     "constraints": {"title_max_chars": 12, "must_include_params": ["highlight", "cta"]},
     "structure": "主标题（突出限时优惠，制造紧迫感）-> 副标题（强调 highlight 参数）-> 行动号召（用 cta 参数，用语直接）",
     "examples": [{"title": "限时特惠即日止", "body": "## 年度低价，错过等一年\n\n现在开通享专属折扣，部署快、见效快。\n\n👉 立即抢购", "tags": ["Banner", "促销"]}],
     "differentiation_dims": ["价格优惠角度", "限时紧迫角度", "赠品加成角度"],
     "applicable_channels": ["官网", "微信公众号", "小红书", "微博"],
     "tags": ["促销", "短文案", "官网"]},
    {"id": "T003", "scenario_id": "S002", "name": "产品介绍标准版", "tag": "标准",
     "description": "标准产品介绍文章模板",
     "prompt": "撰写产品介绍文章，面向「{audience}」，篇幅约「{word_count}」，覆盖核心功能、技术优势与典型应用场景。",
     "constraints": {"must_include_params": ["audience"]},
     "structure": "开篇钩子（受众痛点）-> 产品定位 -> 核心功能（3-4项）-> 典型场景 -> 结语",
     "examples": [{"title": "重新定义团队协作", "body": "## 协作的痛点\n\n文档来回传、版本乱、跟进靠嘴催。\n\n## 我们的方案\n\n一站式协同：实时编辑、AI 起草、任务自动流转。\n\n## 适用场景\n\n远程团队、跨部门项目、客户协作。\n\n> 让协作回归简单。", "tags": ["产品介绍"]}],
     "differentiation_dims": ["技术决策者视角", "业务负责人视角", "终端用户视角"],
     "applicable_channels": ["官网", "知乎", "微信公众号"],
     "tags": ["标准", "长文", "产品介绍"]},
    {"id": "T004", "scenario_id": "S002", "name": "产品介绍白皮书", "tag": "深度",
     "description": "深度产品白皮书模板",
     "prompt": "撰写产品白皮书，面向「{audience}」，篇幅约「{word_count}」，包含行业背景、产品定位、技术架构、实施路径与效益分析。",
     "constraints": {"must_include_params": ["audience"]},
     "structure": "行业背景 -> 产品定位 -> 技术架构 -> 实施路径 -> 效益分析",
     "examples": [{"title": "XX 平台技术白皮书", "body": "## 行业背景\n\n企业数据分散，分析滞后。\n\n## 产品定位\n\n一站式智能分析平台。\n\n## 技术架构\n\n接入层 -> 计算层 -> AI 层 -> 展示层。\n\n## 实施路径\n\n接入 -> 建模 -> 试点 -> 推广。\n\n## 效益分析\n\n决策效率提升 3 倍。", "tags": ["白皮书"]}],
     "differentiation_dims": ["技术架构侧重", "商业价值侧重", "实施路径侧重"],
     "applicable_channels": ["官网", "知乎"],
     "tags": ["深度", "长文", "白皮书"]},
    {"id": "T005", "scenario_id": "S003", "name": "竞品对比标准", "tag": "标准",
     "description": "标准竞品对比报告模板",
     "prompt": "生成竞品对比报告，对比对象为「{competitor}」，聚焦「{focus}」，包含功能对比表、差异化卖点、销售话术建议。",
     "constraints": {"must_include_params": ["competitor", "focus"]},
     "structure": "对比概览 -> 功能对比表（Markdown表格）-> 差异化卖点 -> 销售话术建议",
     "examples": [{"title": "XX VS 竞品A 对比", "body": "## 对比概览\n\n从功能、性价比、服务三维度对比。\n\n## 功能对比\n\n| 维度 | XX | 竞品A |\n|---|---|---|\n| AI分析 | ✓ | ✗ |\n| 部署 | 快 | 慢 |\n\n## 差异化卖点\n\nAI 原生、部署快。\n\n## 销售话术\n\n强调 AI 能力与快速落地。", "tags": ["竞品对比"]}],
     "differentiation_dims": ["功能全面性", "性价比", "服务支持"],
     "applicable_channels": ["官网", "知乎", "邮件营销", "内部培训PPT"],
     "tags": ["标准", "对比", "销售赋能"]},
    {"id": "T006", "scenario_id": "S003", "name": "竞品对比深度", "tag": "深度",
     "description": "深度竞品分析报告模板",
     "prompt": "生成深度竞品分析报告，对比对象为「{competitor}」，核心维度「{focus}」，包含 SWOT 分析、功能矩阵对比、市场定位差异和应对策略建议。",
     "constraints": {"must_include_params": ["competitor", "focus"]},
     "structure": "SWOT 分析 -> 功能矩阵对比 -> 市场定位差异 -> 应对策略建议",
     "examples": [{"title": "XX 竞品深度分析", "body": "## SWOT\n\n优势：AI 检测；劣势：品牌新；机会：合规升级；威胁：价格战。\n\n## 功能矩阵\n\n核心能力逐项打分对比。\n\n## 市场定位差异\n\nXX 主攻中大型，竞品偏 SMB。\n\n## 应对策略\n\n主打安全合规与 AI 检出率。", "tags": ["竞品分析"]}],
     "differentiation_dims": ["SWOT 分析视角", "功能矩阵视角", "市场定位视角"],
     "applicable_channels": ["官网", "知乎", "内部培训PPT"],
     "tags": ["深度", "对比", "销售赋能"]},
    {"id": "T007", "scenario_id": "S004", "name": "案例包装标准", "tag": "标准",
     "description": "标准客户案例模板",
     "prompt": "撰写客户成功案例，客户属于「{industry}」行业，核心成效为「{result}」，采用 STAR 结构（背景-任务-方案-成果）。",
     "constraints": {"must_include_params": ["industry", "result"]},
     "structure": "背景(Situation) -> 任务(Task) -> 方案(Action，含产品) -> 成果(Result，含数据)",
     "examples": [{"title": "某制造企业的转型之路", "body": "## 背景\n\n某制造企业数据分散，决策靠经验。\n\n## 任务\n\n一季度内建立统一分析体系。\n\n## 方案\n\n引入 XX 平台，完成多源接入与看板搭建。\n\n## 成果\n\n报表周期从 7 天缩至 1 天。\n\n> 「终于能看着数据做决策了。」-- CIO", "tags": ["客户案例"]}],
     "differentiation_dims": ["IT 负责人视角", "业务负责人视角", "高管决策视角"],
     "applicable_channels": ["官网", "微信公众号", "知乎", "邮件营销"],
     "tags": ["标准", "案例", "STAR"]},
    {"id": "T008", "scenario_id": "S004", "name": "案例包装简短", "tag": "简短",
     "description": "简短客户案例模板（适合社交媒体）",
     "prompt": "撰写简短客户案例，客户属于「{industry}」行业，核心成效为「{result}」，300 字以内，突出核心数据与客户评价。",
     "constraints": {"body_chars": [0, 300], "must_include_params": ["industry", "result"]},
     "structure": "核心成效（一句话点题）-> 关键数据 -> 客户评价",
     "examples": [{"title": "7 天到 1 天的蜕变", "body": "某制造企业引入 XX 平台后，报表周期从 7 天缩至 1 天，决策效率提升 3 倍。\n\n> 「看着数据做决策，踏实。」-- 客户 CIO", "tags": ["案例", "简短"]}],
     "differentiation_dims": ["数据驱动", "客户评价", "效率提升"],
     "applicable_channels": ["微信公众号", "小红书", "微博", "B站"],
     "tags": ["简短", "案例", "社媒"]},
    {"id": "T009", "scenario_id": "S005", "name": "PPT 大纲标准", "tag": "标准",
     "description": "标准演示大纲模板",
     "prompt": "生成 PPT 大纲，目的为「{purpose}」，约「{slides}」，每页标注标题与 3-5 个要点。",
     "constraints": {"must_include_params": ["purpose"]},
     "structure": "按页组织：封面 -> 背景 -> 核心功能 -> 优势 -> 总结，每页标题 + 3-5 要点",
     "examples": [{"title": "XX 平台演示大纲", "body": "## 第1页：封面\n- XX 平台\n\n## 第2页：背景\n- 数据分散痛点\n\n## 第3页：核心功能\n- 多源接入\n- AI 分析\n\n## 第4页：总结\n- 立即试用", "tags": ["PPT大纲"]}],
     "differentiation_dims": ["问题-方案结构", "功能演示结构", "价值证明结构"],
     "applicable_channels": ["内部培训PPT"],
     "tags": ["标准", "大纲", "PPT"]},
    {"id": "T010", "scenario_id": "S005", "name": "PPT 大纲详细", "tag": "详细",
     "description": "详细演示大纲模板（含演讲备注）",
     "prompt": "生成 PPT 大纲，目的为「{purpose}」，约「{slides}」，每页包含标题、3-5 个要点、演讲备注和预期讨论时间。",
     "constraints": {"must_include_params": ["purpose"]},
     "structure": "按页组织，每页含：标题 + 3-5 要点 + 演讲备注 + 预期讨论时间",
     "examples": [{"title": "XX 平台演示大纲（详）", "body": "## 第1页：封面\n- 要点：产品名 + slogan\n- 备注：开场介绍\n- 时间：3 分钟\n\n## 第2页：核心功能\n- 要点：接入 / 分析 / 看板\n- 备注：现场演示\n- 时间：8 分钟", "tags": ["PPT大纲", "详细"]}],
     "differentiation_dims": ["技术深度", "商业价值", "客户案例"],
     "applicable_channels": ["内部培训PPT"],
     "tags": ["详细", "大纲", "PPT"]},
    {"id": "T011", "scenario_id": "S006", "name": "社媒通用版", "tag": "通用",
     "description": "适用于多平台的通用社交媒体帖子模板",
     "prompt": "撰写社交媒体帖子，主题为「{topic}」，语气「{tone}」，200 字以内，附 3-5 个话题标签。",
     "constraints": {"body_chars": [0, 200]},
     "structure": "吸睛开头 -> 核心信息（200字内）-> 3-5 个话题标签",
     "examples": [{"title": "一个让协作变简单的小工具", "body": "文档来回传？版本乱？\n\nXX 协同套件，实时编辑 + AI 起草，让团队告别低效。\n\n#效率 #协同办公 #AI写作", "tags": ["社媒"]}],
     "differentiation_dims": ["活泼有趣", "专业干货", "情感共鸣"],
     "applicable_channels": ["微信公众号", "小红书", "微博", "B站", "知乎"],
     "tags": ["通用", "短文案", "社媒"]},
    {"id": "T012", "scenario_id": "S006", "name": "社媒故事版", "tag": "故事化",
     "description": "用讲故事的方式吸引受众的帖子模板",
     "prompt": "撰写故事化社交媒体帖子，围绕「{topic}」讲一个小故事，语气「{tone}」，300 字以内，结尾带行动号召和话题标签。",
     "constraints": {"body_chars": [0, 300]},
     "structure": "故事引入 -> 冲突/转折 -> 产品登场解围 -> 结局 + 行动号召 + 话题标签",
     "examples": [{"title": "那次差点延期的项目", "body": "上个月，团队差点因版本混乱错过交付。\n\n直到用了 XX 协同套件--文档实时同步，AI 自动整理纪要。\n\n项目如期上线。试试看？\n\n#协同 #效率 #AI", "tags": ["社媒", "故事"]}],
     "differentiation_dims": ["悬念反转", "温暖治愈", "励志逆袭"],
     "applicable_channels": ["小红书", "B站", "微博", "微信公众号"],
     "tags": ["故事化", "短文案", "社媒"]},
]


# SEED_MEMBERS 是预置的 4 个团队成员（现已演进为登录用户）
# 每个成员都有 username + 默认密码（DEFAULT_USER_PASSWORD，默认 123456）
# M001 为管理员，可编辑/删除任何人的数据
SEED_MEMBERS: list[dict] = [
    {"id": "M001", "name": "张营销", "color": "#409eff", "username": "zhang", "email": "zhang@sx.com", "is_admin": True},
    {"id": "M002", "name": "李产品", "color": "#67c23a", "username": "li",    "email": "li@sx.com",    "is_admin": False},
    {"id": "M003", "name": "王运营", "color": "#e6a23c", "username": "wang",  "email": "wang@sx.com",  "is_admin": False},
    {"id": "M004", "name": "赵设计", "color": "#f56c6c", "username": "zhao",  "email": "zhao@sx.com",  "is_admin": False},
]


def seed_if_empty() -> None:
    """若产品/场景表为空则灌入种子数据。

    两种情况会执行灌入：
    1. 表为空（用户没有执行 SQL 脚本）→ 插入完整种子数据 + embedding
    2. 表有数据但 embedding 为空（用户执行了 SQL 但没有 embedding）→ 只补 embedding

    这确保无论用户用哪种方式初始化数据库，向量检索都能正常工作。
    """
    # 延迟导入避免循环依赖
    from app.database import query

    # 检查 products 表是否为空
    if query_one("SELECT COUNT(*) AS cnt FROM products")["cnt"] == 0:
        # 情况 1：表为空，插入完整种子数据
        with transaction() as cur:
            for p in SEED_PRODUCTS:
                # 为每个产品生成向量嵌入
                embedding = embed_product(p)
                cur.execute(
                    """INSERT INTO products
                    (id,created_by,name,category,description,features,
                     target_customers,pricing,selling_points,images,documents,embedding)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                    (
                        p["id"], p.get("created_by"), p["name"], Json(p["category"]), p["description"],
                        Json(p["features"]),
                        Json(p["target_customers"]), p["pricing"],
                        Json(p["selling_points"]),
                        Json(p.get("images", [])), Json(p.get("documents", [])),
                        Json(embedding),
                    ),
                )
    else:
        # 情况 2：表有数据。检查"缺向量"或"向量维度与当前 EMBEDDING_DIM 不符"的产品
        # 维度不符发生在切换 embedding 模型时（如 Mock 128 → 通义千问 1024），需重建
        need_embed = query(
            "SELECT * FROM products WHERE embedding IS NULL "
            "OR jsonb_array_length(embedding) <> %s",
            (EMBEDDING_DIM,),
        )
        if need_embed:
            # 重新生成向量（真实 embedding 不可用时 embed_product 会自动降级 Mock）
            with transaction() as cur:
                for row in need_embed:
                    embedding = embed_product(row)
                    cur.execute(
                        "UPDATE products SET embedding=%s, updated_at=NOW() WHERE id=%s",
                        (Json(embedding), row["id"]),
                    )
            print(f"[seed] 已为 {len(need_embed)} 个产品（重新）生成向量嵌入")
        # 老库回填：种子产品在新增 created_by 列前已插入，此处补上创建人
        seed_cb = {p["id"]: p.get("created_by") for p in SEED_PRODUCTS if p.get("created_by")}
        if seed_cb:
            with transaction() as cur:
                for pid, cb in seed_cb.items():
                    cur.execute(
                        "UPDATE products SET created_by=%s WHERE id=%s AND created_by IS NULL",
                        (cb, pid),
                    )

    # 检查 scenarios 表是否为空
    if query_one("SELECT COUNT(*) AS cnt FROM scenarios")["cnt"] == 0:
        with transaction() as cur:
            for s in SEED_SCENARIOS:
                cur.execute(
                    """INSERT INTO scenarios
                    (id,name,description,parameters)
                    VALUES (%s,%s,%s,%s)""",
                    (
                        s["id"], s["name"], s["description"],
                        Json(s["parameters"]),
                    ),
                )

    # 检查 templates 表是否为空
    if query_one("SELECT COUNT(*) AS cnt FROM templates")["cnt"] == 0:
        with transaction() as cur:
            for t in SEED_TEMPLATES:
                cur.execute(
                    """INSERT INTO templates
                    (id,scenario_id,name,tag,description,prompt,constraints,structure,examples,differentiation_dims,applicable_channels,tags)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                    (t["id"], t["scenario_id"], t["name"],
                     t["tag"], t["description"], t["prompt"], Json(t.get("constraints", {})),
                     t.get("structure", ""), Json(t.get("examples", [])), Json(t.get("differentiation_dims", [])),
                     Json(t.get("applicable_channels", [])), Json(t.get("tags", []))),
                )
    else:
        # 老库回填：各结构化列新增前已插入的种子模板，按 id 幂等补值
        # 各字段独立回填，不覆盖用户已修改的值；用户自建模板不在 SEED_TEMPLATES 中，不受影响
        with transaction() as cur:
            for t in SEED_TEMPLATES:
                cur.execute(
                    "UPDATE templates SET constraints=%s "
                    "WHERE id=%s AND (constraints IS NULL OR constraints = '{}'::jsonb)",
                    (Json(t.get("constraints", {})), t["id"]),
                )
                cur.execute(
                    "UPDATE templates SET structure=%s "
                    "WHERE id=%s AND structure IS NULL",
                    (t.get("structure", ""), t["id"]),
                )
                cur.execute(
                    "UPDATE templates SET examples=%s "
                    "WHERE id=%s AND (examples IS NULL OR examples = '[]'::jsonb)",
                    (Json(t.get("examples", [])), t["id"]),
                )
                cur.execute(
                    "UPDATE templates SET differentiation_dims=%s "
                    "WHERE id=%s AND (differentiation_dims IS NULL OR differentiation_dims = '[]'::jsonb)",
                    (Json(t.get("differentiation_dims", [])), t["id"]),
                )
                cur.execute(
                    "UPDATE templates SET applicable_channels=%s "
                    "WHERE id=%s AND (applicable_channels IS NULL OR applicable_channels = '[]'::jsonb)",
                    (Json(t.get("applicable_channels", [])), t["id"]),
                )
                cur.execute(
                    "UPDATE templates SET tags=%s "
                    "WHERE id=%s AND (tags IS NULL OR tags = '[]'::jsonb)",
                    (Json(t.get("tags", [])), t["id"]),
                )

    # 检查 members 表是否为空
    if query_one("SELECT COUNT(*) AS cnt FROM members")["cnt"] == 0:
        # 表为空：插入完整用户（含鉴权字段）
        pw_hash = hash_password(DEFAULT_USER_PASSWORD)
        with transaction() as cur:
            for m in SEED_MEMBERS:
                cur.execute(
                    """INSERT INTO members
                       (id, name, color, username, password_hash, email, is_admin)
                       VALUES (%s,%s,%s,%s,%s,%s,%s)""",
                    (m["id"], m["name"], m["color"], m["username"], pw_hash, m["email"], m["is_admin"]),
                )
    else:
        # 老库回填：上一轮的 members 没有 password_hash 等鉴权列，按 id 补（幂等）
        pw_hash = hash_password(DEFAULT_USER_PASSWORD)
        with transaction() as cur:
            for m in SEED_MEMBERS:
                cur.execute(
                    """UPDATE members SET username=%s, password_hash=%s, email=%s, is_admin=%s
                       WHERE id=%s AND password_hash IS NULL""",
                    (m["username"], pw_hash, m["email"], m["is_admin"], m["id"]),
                )

    # 检查 channels 表是否为空
    if query_one("SELECT COUNT(*) AS cnt FROM channels")["cnt"] == 0:
        with transaction() as cur:
            for ch in DEFAULT_CHANNELS:
                cur.execute(
                    """INSERT INTO channels
                       (name, display_name, tone, emoji, format, description, is_builtin)
                       VALUES (%s,%s,%s,%s,%s,%s,%s)""",
                    (ch["name"], ch["display_name"], ch["tone"],
                     ch["emoji"], ch["format"], ch["description"], True),
                )
        print(f"[seed] 已灌入 {len(DEFAULT_CHANNELS)} 个预置渠道配置")