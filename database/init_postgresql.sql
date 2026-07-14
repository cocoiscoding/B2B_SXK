-- ============================================================
-- 神行库 · Product Marketing AI  数据库初始化脚本
-- 数据库：PostgreSQL 12+
-- 说明：本脚本包含 建库 → 建表 → 注释 → 插入模拟数据 全流程
-- 用法：psql -U postgres -f init_postgresql.sql
-- ============================================================

-- ============================================================
-- 一、建库
-- ============================================================
-- 注意：CREATE DATABASE 不能在事务块中执行，需先连接到默认库 postgres
-- 若已存在同名库，请先手动 DROP DATABASE shenxingdb; 再执行

SELECT '开始创建数据库 shenxingdb' AS info;

-- 终断已有连接（防止库被占用无法重建）
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE datname = 'shenxingdb' AND pid <> pg_backend_pid();

DROP DATABASE IF EXISTS shenxingdb;
CREATE DATABASE shenxingdb
    WITH ENCODING 'UTF8'
    LC_COLLATE 'en_US.utf8'
    LC_CTYPE 'en_US.utf8'
    TEMPLATE template0;

-- 连接到新库
\connect shenxingdb

-- ============================================================
-- 二、建表（含完备字段注释）
-- ============================================================

-- ---------- 2.1 产品知识库表 ----------
CREATE TABLE products (
    id               VARCHAR(20)  PRIMARY KEY,
    name             VARCHAR(200) NOT NULL,
    category         JSONB        NOT NULL DEFAULT '[]'::jsonb,
    description      TEXT,
    features         JSONB        NOT NULL DEFAULT '[]'::jsonb,
    target_customers JSONB        NOT NULL DEFAULT '[]'::jsonb,
    pricing          VARCHAR(500),
    selling_points   JSONB        NOT NULL DEFAULT '[]'::jsonb,
    images           JSONB        NOT NULL DEFAULT '[]'::jsonb,
    documents        JSONB        NOT NULL DEFAULT '[]'::jsonb,
    embedding        JSONB,
    created_by       VARCHAR(20),
    created_at       TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at       TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

COMMENT ON TABLE products IS '产品知识库表：存储产品的核心信息（功能、参数、卖点、竞品等），是 Agent 生成营销内容的数据来源';

COMMENT ON COLUMN products.id               IS '产品唯一标识，如 P001';
COMMENT ON COLUMN products.name             IS '产品名称（必填）';
COMMENT ON COLUMN products.category         IS '产品分类列表，JSON 字符串数组，如 ["数据分析","企业级"]';
COMMENT ON COLUMN products.description      IS '产品详细描述，用于生成文案的背景信息';
COMMENT ON COLUMN products.features         IS '核心功能列表，JSON 数组，元素结构 {name, description}';
COMMENT ON COLUMN products.target_customers IS '目标客户行业列表，JSON 字符串数组，如 ["制造业","金融业"]';
COMMENT ON COLUMN products.pricing          IS '定价信息，自由文本描述';
COMMENT ON COLUMN products.selling_points   IS '核心卖点关键词列表，JSON 字符串数组，如 ["部署快","成本低"]';
COMMENT ON COLUMN products.images           IS '产品图片列表，JSON 数组，元素结构 {url, name, size}';
COMMENT ON COLUMN products.documents        IS '产品文档列表，JSON 数组，元素结构 {url, name, size, type}';
COMMENT ON COLUMN products.embedding        IS '产品文本向量嵌入（JSON 浮点数组），用于语义检索，由 embedding API 生成';
COMMENT ON COLUMN products.created_at       IS '记录创建时间';
COMMENT ON COLUMN products.updated_at       IS '记录最后更新时间';

CREATE INDEX idx_products_name     ON products (name);
CREATE INDEX idx_products_category ON products (category);
CREATE INDEX idx_products_features ON products USING GIN (features);


-- ---------- 2.2 营销场景表 ----------
CREATE TABLE scenarios (
    id          VARCHAR(20)  PRIMARY KEY,
    name        VARCHAR(200) NOT NULL,
    description TEXT,
    parameters  JSONB        NOT NULL DEFAULT '[]'::jsonb,
    created_by  VARCHAR(20),
    created_at  TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

COMMENT ON TABLE scenarios IS '营销场景表：定义不同营销场景及其参数配置';

COMMENT ON COLUMN scenarios.id          IS '场景唯一标识，如 S001';
COMMENT ON COLUMN scenarios.name        IS '场景名称，如 官网首页 Banner 文案';
COMMENT ON COLUMN scenarios.description IS '场景用途说明';
COMMENT ON COLUMN scenarios.parameters  IS '场景参数定义，JSON 数组，元素结构 {name, description}';
COMMENT ON COLUMN scenarios.created_by  IS '自定义场景创建人；NULL 表示内置/存量场景';


-- ---------- 2.3 模板表（关联在场景下）----------
CREATE TABLE templates (
    id          VARCHAR(20)  PRIMARY KEY,
    scenario_id VARCHAR(20)  NOT NULL REFERENCES scenarios(id) ON DELETE CASCADE,
    name        VARCHAR(200) NOT NULL,
    tag         VARCHAR(100),
    description TEXT,
    prompt      TEXT,
    constraints JSONB        NOT NULL DEFAULT '{}'::jsonb,
    structure   TEXT,
    examples    JSONB        NOT NULL DEFAULT '[]'::jsonb,
    differentiation_dims JSONB NOT NULL DEFAULT '[]'::jsonb,
    applicable_channels JSONB NOT NULL DEFAULT '[]'::jsonb,
    tags                 JSONB NOT NULL DEFAULT '[]'::jsonb,
    status               VARCHAR(20)  NOT NULL DEFAULT 'approved',  -- pending/approved/rejected；默认 approved 保证内置+存量模板可用
    created_by           VARCHAR(20),                               -- 创建人（用户 id）
    reviewed_by          VARCHAR(20),                               -- 审核管理员
    reviewed_at          TIMESTAMP WITH TIME ZONE,                  -- 审核时间
    review_note          TEXT,                                      -- 驳回原因/审核备注
    use_count            INT          NOT NULL DEFAULT 0,           -- 生成使用次数
    is_featured          BOOLEAN      NOT NULL DEFAULT FALSE,       -- 管理员推荐
    created_at  TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

COMMENT ON TABLE templates IS '模板表：每个场景下可关联多个模板，定义不同的提示词及产出格式；用户创建的模板需管理员审核（status）通过才能在生成中使用';

COMMENT ON COLUMN templates.id          IS '模板唯一标识，如 T001';
COMMENT ON COLUMN templates.scenario_id IS '关联的场景 ID';
COMMENT ON COLUMN templates.name        IS '模板名称';
COMMENT ON COLUMN templates.tag         IS '标签（单个，简单描述）';
COMMENT ON COLUMN templates.description IS '模板描述';
COMMENT ON COLUMN templates.prompt      IS '提示词/模板产出格式';
COMMENT ON COLUMN templates.constraints IS '结构化硬约束 JSON，供校验 Agent 机械执行：title_max_chars/body_chars[min,max]/must_include_params/min_selling_points';
COMMENT ON COLUMN templates.structure   IS '产出骨架文本，引导 body 结构（如钩子->痛点->方案->CTA），供生成 Agent 注入 prompt';
COMMENT ON COLUMN templates.examples   IS '参考范例 JSON 数组（few-shot），元素结构 {title,body,tags}，供生成 Agent 注入 prompt';
COMMENT ON COLUMN templates.differentiation_dims IS '多版本差异化维度 JSON 字符串数组（如["价格","限时","赠品"]），驱动各版本差异方向，留空用默认风格锚点';
COMMENT ON COLUMN templates.applicable_channels IS '适用渠道名 JSON 数组（如["官网","微信公众号"]），留空表示不限；ChannelAgent 在渠道不匹配时告警';
COMMENT ON COLUMN templates.tags                 IS '多维标签 JSON 字符串数组（如["标准","短文案"]），供前端筛选，比单 tag 更灵活';
COMMENT ON COLUMN templates.created_at  IS '记录创建时间';

CREATE INDEX idx_templates_scenario_id ON templates (scenario_id);


-- ---------- 2.3 生成历史表 ----------
CREATE TABLE history (
    id            VARCHAR(20)  PRIMARY KEY,
    product_id    VARCHAR(20),
    product_name  VARCHAR(200),
    scenario_id   VARCHAR(20),
    scenario_name VARCHAR(200),
    channel       VARCHAR(100),
    style         VARCHAR(100),
    params        JSONB        NOT NULL DEFAULT '{}'::jsonb,
    versions      JSONB        NOT NULL DEFAULT '[]'::jsonb,
    agent_trace   JSONB        NOT NULL DEFAULT '[]'::jsonb,
    validated     BOOLEAN      NOT NULL DEFAULT FALSE,
    issues        JSONB        NOT NULL DEFAULT '[]'::jsonb,
    feedback      VARCHAR(20),
    feedback_voters JSONB      NOT NULL DEFAULT '{}'::jsonb,  -- 每个成员的反馈 {member_id: like/dislike}，per-user 不覆盖
    created_by    VARCHAR(20),
    created_at    TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

COMMENT ON TABLE history IS '内容生成历史表：记录每次多 Agent 协作生成的完整结果与执行链路，支持回看与复用';

COMMENT ON COLUMN history.id            IS '历史记录唯一标识，如 H030b2326';
COMMENT ON COLUMN history.product_id    IS '关联的产品 ID';
COMMENT ON COLUMN history.product_name  IS '生成时的产品名称快照（冗余字段，便于列表展示）';
COMMENT ON COLUMN history.scenario_id   IS '关联的场景 ID';
COMMENT ON COLUMN history.scenario_name IS '生成时的场景名称快照';
COMMENT ON COLUMN history.channel       IS '目标发布渠道，如 官网/微信公众号/LinkedIn';
COMMENT ON COLUMN history.style         IS '文案风格，如 专业严谨/激情澎湃/亲和走心';
COMMENT ON COLUMN history.params        IS '用户输入的参数键值对，JSON 对象';
COMMENT ON COLUMN history.versions      IS '生成的多版本内容，JSON 数组，元素结构 {index, title, body, tags}';
COMMENT ON COLUMN history.agent_trace   IS 'Agent 执行链路追踪，JSON 数组，元素结构 {agent, status, message, duration_ms, output}';
COMMENT ON COLUMN history.validated     IS '内容校验是否通过';
COMMENT ON COLUMN history.issues        IS '校验发现的问题列表，JSON 字符串数组';
COMMENT ON COLUMN history.feedback      IS '用户反馈标记：like（赞）/ dislike（踩）/ NULL（未标记）【旧字段，单值会被覆盖，仅向后兼容】';
COMMENT ON COLUMN history.feedback_voters IS '每个成员对该记录的反馈，JSON 对象 {member_id: like/dislike}，per-user 不互相覆盖';
COMMENT ON COLUMN history.created_by    IS '生成人（团队成员 id），删除成员时置 NULL';
COMMENT ON COLUMN history.created_at    IS '生成时间';

CREATE INDEX idx_history_product_id  ON history (product_id);
CREATE INDEX idx_history_scenario_id ON history (scenario_id);
CREATE INDEX idx_history_created_at  ON history (created_at DESC);


-- ---------- 2.4 团队成员表（演进为用户表，含登录鉴权）----------
CREATE TABLE members (
    id            VARCHAR(20)  PRIMARY KEY,
    name          VARCHAR(50)  NOT NULL,
    color         VARCHAR(20)  DEFAULT '#409eff',
    username      VARCHAR(50)  UNIQUE,
    password_hash VARCHAR(255),
    email         VARCHAR(100),
    is_admin      BOOLEAN      NOT NULL DEFAULT FALSE,
    created_at    TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

COMMENT ON TABLE members IS '用户表：团队成员 + 登录鉴权。轻量共享工作区，所有登录用户可读全部数据，仅创建者/管理员可改';
COMMENT ON COLUMN members.id            IS '用户唯一标识，如 M001 / U<随机>';
COMMENT ON COLUMN members.name          IS '用户昵称';
COMMENT ON COLUMN members.color         IS '头像彩点颜色';
COMMENT ON COLUMN members.username      IS '登录用户名（唯一）';
COMMENT ON COLUMN members.password_hash IS 'bcrypt 密码哈希（永不明文，永不返回）';
COMMENT ON COLUMN members.email         IS '邮箱';
COMMENT ON COLUMN members.is_admin      IS '是否管理员（可改任何人的数据）';


-- ---------- 2.5 Token 黑名单表（用于退出登录）----------
CREATE TABLE token_blacklist (
    jti          VARCHAR(100) PRIMARY KEY,
    token_type   VARCHAR(20)  NOT NULL,
    user_id      VARCHAR(20)  NOT NULL,
    expires_at   TIMESTAMP WITH TIME ZONE NOT NULL,
    revoked_at   TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

COMMENT ON TABLE token_blacklist IS 'Token 黑名单表：存储已退出的 JWT，防止 Token 被盗用';
COMMENT ON COLUMN token_blacklist.jti        IS 'JWT ID（唯一标识每个 Token）';
COMMENT ON COLUMN token_blacklist.token_type IS 'Token 类型：access / refresh';
COMMENT ON COLUMN token_blacklist.user_id    IS '用户 ID';
COMMENT ON COLUMN token_blacklist.expires_at IS 'Token 过期时间（用于定期清理）';
COMMENT ON COLUMN token_blacklist.revoked_at IS '撤销时间';

CREATE INDEX idx_token_blacklist_user_id ON token_blacklist (user_id);
CREATE INDEX idx_token_blacklist_expires_at ON token_blacklist (expires_at);


-- ---------- 竞品分析入库 ----------
-- 按 (产品, 竞品) 缓存竞品分析结果，避免每次生成重跑 Tavily 搜索 + LLM 分析
CREATE TABLE competitor_analyses (
    id              VARCHAR(20)  PRIMARY KEY,
    product_id      VARCHAR(20)  NOT NULL,
    competitor_name VARCHAR(200) NOT NULL,
    analysis        JSONB        NOT NULL,
    source          VARCHAR(50),
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE (product_id, competitor_name)
);

COMMENT ON TABLE  competitor_analyses                  IS '竞品分析缓存：按 产品+竞品 维度复用分析结果';
COMMENT ON COLUMN competitor_analyses.product_id      IS '所属产品 ID';
COMMENT ON COLUMN competitor_analyses.competitor_name IS '竞品名称';
COMMENT ON COLUMN competitor_analyses.analysis        IS '完整分析结果（comparison_table/SWOT/优劣/话术 等）';
COMMENT ON COLUMN competitor_analyses.source          IS '分析来源：tavily / llm / mock';

CREATE INDEX idx_competitor_analyses_product_id ON competitor_analyses (product_id);


-- ============================================================
-- 三、插入模拟数据
-- ============================================================

-- ---------- 3.1 产品数据（3 个示例产品）----------
INSERT INTO products (id, name, category, description, features, target_customers, pricing, selling_points, images, documents) VALUES
(
    'P001',
    '智能数据平台 X',
    '["数据分析","企业级"]'::jsonb,
    '面向中大型企业的一站式智能数据分析平台，覆盖数据接入、清洗、建模、可视化到 AI 预测的全链路能力。',
    '[
        {"name":"多源数据接入","description":"支持 20+ 数据源（MySQL、PostgreSQL、Kafka、Excel、API 等），分钟级完成对接。"},
        {"name":"AI 智能分析","description":"内置机器学习模型，自动识别数据异常、预测业务趋势，支持自然语言提问。"},
        {"name":"可视化看板","description":"拖拽式看板搭建，50+ 图表类型，支持实时刷新与大屏投放。"},
        {"name":"行列级权限管控","description":"细粒度权限体系，满足金融级数据安全合规要求。"}
    ]'::jsonb,
    '["制造业","金融业","零售业","互联网"]'::jsonb,
    '按年订阅，基础版 ¥50,000/年，企业版 ¥200,000/年',
    '["部署快","成本低","易上手","AI 原生"]'::jsonb,
    '[]'::jsonb,
    '[]'::jsonb
),
(
    'P002',
    '云雀协同办公',
    '["协同办公","SaaS"]'::jsonb,
    '面向中小团队的实时协同办公套件，整合文档、表格、即时通讯、视频会议与项目管理于一体。',
    '[
        {"name":"实时多人协同","description":"文档/表格支持百人同时在线编辑，毫秒级同步无冲突。"},
        {"name":"AI 写作助手","description":"会议纪要自动生成、周报一键起草、智能续写与润色。"},
        {"name":"一体化项目管理","description":"看板/甘特/列表三视图切换，任务自动流转与提醒。"},
        {"name":"跨端无缝同步","description":"Web / 桌面 / 移动端全覆盖，离线编辑自动合并。"}
    ]'::jsonb,
    '["初创公司","中小型企业","远程团队","教育机构"]'::jsonb,
    '免费版 0 元，团队版 ¥99/人/年，企业版联系销售',
    '["轻量","免费起步","AI 加持","上手零成本"]'::jsonb,
    '[]'::jsonb,
    '[]'::jsonb
),
(
    'P003',
    '墨盾安全网关',
    '["网络安全","云原生"]'::jsonb,
    '新一代云原生安全网关，融合 WAF、API 防护、Bot 管理与 DDoS 清洗能力，为 Web 应用提供全栈防护。',
    '[
        {"name":"AI 威胁检测","description":"基于深度学习的 0-day 攻击识别，检出率 99.6%，误报率低于 0.1%。"},
        {"name":"全栈 API 防护","description":"自动发现 API 资产，覆盖 OWASP API Top 10 全部风险。"},
        {"name":"弹性 DDoS 清洗","description":"T 级清洗带宽，秒级响应，业务零中断。"},
        {"name":"可视化安全态势","description":"实时攻击大屏 + 攻防复盘报告，安全运营一目了然。"}
    ]'::jsonb,
    '["金融","政企","电商","游戏"]'::jsonb,
    '按防护流量计费，基础版 ¥3,000/月起',
    '["AI 检测","低延迟","全栈防护","弹性扩展"]'::jsonb,
    '[]'::jsonb,
    '[]'::jsonb
);


-- ---------- 3.2 场景数据（6 个预置场景）----------
INSERT INTO scenarios (id, name, description, parameters) VALUES
(
    'S001',
    '官网首页 Banner 文案',
    '为官网首页生成吸引眼球的 Banner 文案，突出核心卖点。',
    '[
        {"name":"highlight","description":"重点卖点"},
        {"name":"cta","description":"行动号召语"}
    ]'::jsonb
),
(
    'S002',
    '产品介绍文案',
    '完整的产品功能介绍文章，适合官网详情页或白皮书。',
    '[
        {"name":"audience","description":"目标受众（如技术决策者、业务负责人、终端用户、投资人）"},
        {"name":"word_count","description":"字数要求（如300字、600字、1000字）"}
    ]'::jsonb
),
(
    'S003',
    '竞品对比分析报告',
    '自动拉取我方产品信息与竞品对比，生成结构化分析报告。',
    '[
        {"name":"competitor","description":"竞品名称"},
        {"name":"focus","description":"对比重点（如功能全面性、性价比、技术架构、服务支持）"}
    ]'::jsonb
),
(
    'S004',
    '客户案例包装',
    '将客户使用场景包装成可对外发布的成功案例。',
    '[
        {"name":"industry","description":"客户行业"},
        {"name":"result","description":"核心成效"}
    ]'::jsonb
),
(
    'S005',
    '演示 PPT 大纲',
    '生成产品演示 PPT 的结构化大纲，含每页要点。',
    '[
        {"name":"purpose","description":"演示目的（如售前宣讲、投资人路演、内部培训、大会演讲）"},
        {"name":"slides","description":"页数要求（如8页、15页、25页）"}
    ]'::jsonb
),
(
    'S006',
    '社交媒体帖子',
    '生成适合社交媒体传播的短文案，含话题标签。',
    '[
        {"name":"topic","description":"主题/事件"},
        {"name":"tone","description":"语气风格（如活泼有趣、专业干货、情感共鸣、悬念反转）"}
    ]'::jsonb
);


-- ---------- 3.3 模板数据（每个场景下关联若干模板）----------
INSERT INTO templates (id, scenario_id, name, tag, description, prompt, constraints) VALUES
(
    'T001', 'S001', 'Banner 标准版', '标准',
    '适用于官网首页标准 Banner 文案生成',
    '生成官网 Banner 文案，主标题不超过 12 字，副标题不超过 30 字，突出「{highlight}」，行动号召为「{cta}」。',
    '{"title_max_chars":12,"must_include_params":["highlight","cta"]}'::jsonb
),
(
    'T002', 'S001', 'Banner 促销版', '促销',
    '适用于促销活动期间的 Banner 文案',
    '生成促销 Banner 文案，主标题突出限时优惠，副标题强调「{highlight}」，行动号召为「{cta}」。要求紧迫感强，用语直接。',
    '{"title_max_chars":12,"must_include_params":["highlight","cta"]}'::jsonb
),
(
    'T003', 'S002', '产品介绍标准版', '标准',
    '标准产品介绍文章模板',
    '撰写产品介绍文章，面向「{audience}」，篇幅约「{word_count}」，覆盖核心功能、技术优势与典型应用场景。',
    '{"must_include_params":["audience"]}'::jsonb
),
(
    'T004', 'S002', '产品介绍白皮书', '深度',
    '深度产品白皮书模板',
    '撰写产品白皮书，面向「{audience}」，篇幅约「{word_count}」，包含行业背景、产品定位、技术架构、实施路径与效益分析。',
    '{"must_include_params":["audience"]}'::jsonb
),
(
    'T005', 'S003', '竞品对比标准', '标准',
    '标准竞品对比报告模板',
    '生成竞品对比报告，对比对象为「{competitor}」，聚焦「{focus}」，包含功能对比表、差异化卖点、销售话术建议。',
    '{"must_include_params":["competitor","focus"]}'::jsonb
),
(
    'T006', 'S003', '竞品对比深度', '深度',
    '深度竞品分析报告模板',
    '生成深度竞品分析报告，对比对象为「{competitor}」，核心维度「{focus}」，包含 SWOT 分析、功能矩阵对比、市场定位差异和应对策略建议。',
    '{"must_include_params":["competitor","focus"]}'::jsonb
),
(
    'T007', 'S004', '案例包装标准', '标准',
    '标准客户案例模板',
    '撰写客户成功案例，客户属于「{industry}」行业，核心成效为「{result}」，采用 STAR 结构（背景-任务-方案-成果）。',
    '{"must_include_params":["industry","result"]}'::jsonb
),
(
    'T008', 'S004', '案例包装简短', '简短',
    '简短客户案例模板（适合社交媒体）',
    '撰写简短客户案例，客户属于「{industry}」行业，核心成效为「{result}」，300 字以内，突出核心数据与客户评价。',
    '{"body_chars":[0,300],"must_include_params":["industry","result"]}'::jsonb
),
(
    'T009', 'S005', 'PPT 大纲标准', '标准',
    '标准演示大纲模板',
    '生成 PPT 大纲，目的为「{purpose}」，约「{slides}」，每页标注标题与 3-5 个要点。',
    '{"must_include_params":["purpose"]}'::jsonb
),
(
    'T010', 'S005', 'PPT 大纲详细', '详细',
    '详细演示大纲模板（含演讲备注）',
    '生成 PPT 大纲，目的为「{purpose}」，约「{slides}」，每页包含标题、3-5 个要点、演讲备注和预期讨论时间。',
    '{"must_include_params":["purpose"]}'::jsonb
),
(
    'T011', 'S006', '社媒通用版', '通用',
    '适用于多平台的通用社交媒体帖子模板',
    '撰写社交媒体帖子，主题为「{topic}」，语气「{tone}」，200 字以内，附 3-5 个话题标签。',
    '{"body_chars":[0,200]}'::jsonb
),
(
    'T012', 'S006', '社媒故事版', '故事化',
    '用讲故事的方式吸引受众的帖子模板',
    '撰写故事化社交媒体帖子，围绕「{topic}」讲一个小故事，语气「{tone}」，300 字以内，结尾带行动号召和话题标签。',
    '{"body_chars":[0,300]}'::jsonb
);


-- ---------- 3.4 团队成员数据（4 个示例用户）----------
-- password_hash 留空，由应用首次启动时 seed_data.py 回填（默认密码 123456）
INSERT INTO members (id, name, color, username, email, is_admin) VALUES
('M001', '张营销', '#409eff', 'zhang', 'zhang@sx.com', TRUE),
('M002', '李产品', '#67c23a', 'li',    'li@sx.com',    FALSE),
('M003', '王运营', '#e6a23c', 'wang',  'wang@sx.com',  FALSE),
('M004', '赵设计', '#f56c6c', 'zhao',  'zhao@sx.com',  FALSE);


-- ============================================================
-- 四、验证查询
-- ============================================================
SELECT '=== 数据初始化完成 ===' AS info;
SELECT '产品数量' AS item, COUNT(*) AS count FROM products
UNION ALL
SELECT '场景数量' AS item, COUNT(*) AS count FROM scenarios
UNION ALL
SELECT '模板数量' AS item, COUNT(*) AS count FROM templates
UNION ALL
SELECT '历史记录' AS item, COUNT(*) AS count FROM history;
