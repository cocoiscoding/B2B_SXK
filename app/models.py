"""Pydantic 数据模型：请求/响应结构定义。

本文件定义了所有 API 接口的请求体和响应体结构。

Pydantic 核心概念：
- BaseModel：所有模型的基类，继承它即可获得数据验证功能
- 类型注解：如 name: str 表示 name 字段必须是字符串
- Field(default_factory=list)：设置默认值为空列表
- 验证：请求体不符合模型定义时，FastAPI 自动返回 422 错误

为什么用 Pydantic？
1. 自动生成 API 文档（/docs）
2. 自动验证请求数据（类型不符会报错）
3. 自动序列化/反序列化 JSON
"""
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Any


# ===== 产品知识库 =====

class Feature(BaseModel):
    """产品功能项。"""
    name: str               # 功能名称
    description: str = ""   # 功能描述，默认空字符串


class TechParam(BaseModel):
    """技术参数项。"""
    name: str               # 参数名（如"部署方式"）
    value: str = ""         # 参数值（如"私有化 / SaaS 双模式"）


class ImageItem(BaseModel):
    """产品图片项。"""
    url: str                # 图片地址
    name: str = ""          # 文件名
    size: int = 0           # 文件大小（字节）


class DocumentItem(BaseModel):
    """产品文档项。"""
    url: str                # 文档地址
    name: str = ""          # 文件名
    size: int = 0           # 文件大小（字节）
    type: str = ""          # 文件类型（pdf/docx/xlsx/pptx/txt/zip）


class ProductBase(BaseModel):
    """产品基础信息（创建和响应共用）。

    这个类不直接使用，而是被 ProductCreate 和 Product 继承。
    继承可以避免重复定义相同字段。
    """
    name: str                                           # 产品名称（必填）
    category: list[str] = Field(default_factory=list)   # 产品分类列表（JSON数组）
    description: str = ""                               # 产品详细描述
    # list[Feature] 表示 Feature 对象列表
    # Field(default_factory=list) 表示默认值是空列表
    # 注意：不能用 features: list = []，因为可变默认值在 Python 中是陷阱
    features: list[Feature] = Field(default_factory=list)          # 核心功能列表
    target_customers: list[str] = Field(default_factory=list)      # 目标客户行业列表
    pricing: str = ""                                    # 定价信息
    selling_points: list[str] = Field(default_factory=list)        # 核心卖点列表
    competitors: list[str] = Field(default_factory=list)           # 竞品名称列表（供竞品分析 Agent 自动识别）
    images: list[ImageItem] = Field(default_factory=list)          # 产品图片列表
    documents: list[DocumentItem] = Field(default_factory=list)    # 产品文档列表
    # 注意：created_by 不在请求模型里——它由后端从登录令牌取，不信任前端传入
    # 见下方 Product 响应模型


class ProductCreate(ProductBase):
    """创建产品的请求体。

    继承 ProductBase 的所有字段，额外添加可选的 id。
    id 由前端传入或后端自动生成。
    """
    # str | None 表示可以是字符串或 None（Python 3.10+ 联合类型语法）
    id: str | None = None


class Product(ProductBase):
    """产品响应模型（包含数据库自动生成的字段）。

    继承 ProductBase，额外添加 id、created_by、created_at、updated_at。
    """
    id: str
    created_by: str | None = None    # 创建人（用户 id，由后端从登录令牌写入）
    created_at: datetime    # 创建时间（datetime 类型）
    updated_at: datetime    # 更新时间

    model_config = {"from_attributes": True}


# ===== 场景 =====

class ScenarioParam(BaseModel):
    """场景参数定义（简化为名称和描述，前端表现为可增删列表）。"""
    name: str                               # 参数名称（如"audience"）
    description: str = ""                   # 参数描述（如"目标受众"）


class ScenarioBase(BaseModel):
    """场景基础信息。"""
    name: str                                               # 场景名称（必填）
    description: str = ""                                   # 场景描述
    parameters: list[ScenarioParam] = Field(default_factory=list)  # 参数列表


class ScenarioCreate(ScenarioBase):
    """创建场景的请求体。"""
    id: str | None = None


class Scenario(ScenarioBase):
    """场景响应模型。"""
    id: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ===== 模板（关联在场景下）=====

class TemplateBase(BaseModel):
    """模板基础信息。"""
    name: str                                               # 模板名称（必填）
    tag: str = ""                                           # 标签（单个，简单描述）
    description: str = ""                                   # 模板描述（必填）
    prompt: str = ""                                        # 提示词/模板产出格式
    # 结构化硬约束：把 prompt 里散落的约束（字数/必含参数等）变成 ValidationAgent 可机械执行项
    # 支持：title_max_chars(int)、body_chars([min,max])、must_include_params(list[str])、min_selling_points(int)
    constraints: dict[str, Any] = Field(default_factory=dict)
    # 产出骨架：body 的结构指引（如"钩子→痛点→方案→功能→CTA"），稳定 LLM 产出结构
    structure: str = ""
    # 参考范例（few-shot）：1-2 个优质产出样本，引导 LLM 学习结构与语气，勿照抄内容
    examples: list[dict[str, Any]] = Field(default_factory=list)
    # 多版本差异化维度：指定各版本沿什么维度差异（如"价格/限时/赠品"），留空则用默认风格锚点
    differentiation_dims: list[str] = Field(default_factory=list)
    # 适用渠道：模板标注适合的渠道名列表（如["官网","微信公众号"]），留空表示不限；
    # ChannelAgent 会在渠道不匹配时告警，前端可据此联动筛选
    applicable_channels: list[str] = Field(default_factory=list)
    # 多维标签：比单 tag 更灵活的分类维度（如["标准","短文案","官网"]），供前端筛选
    tags: list[str] = Field(default_factory=list)


class TemplateCreate(TemplateBase):
    """创建模板的请求体。"""
    id: str | None = None


class Template(TemplateBase):
    """模板响应模型。"""
    id: str
    scenario_id: str
    # 审核制：pending(待审) / approved(已通过) / rejected(已驳回)。默认 approved 保证内置+存量模板可用
    status: str = "approved"
    created_by: str | None = None
    reviewed_by: str | None = None
    reviewed_at: datetime | None = None
    review_note: str = ""
    # 复用：使用次数 + 管理员推荐
    use_count: int = 0
    is_featured: bool = False
    created_at: datetime

    model_config = {"from_attributes": True}


class TemplateReviewRequest(BaseModel):
    """模板审核请求体（仅管理员）：通过 approved / 驳回 rejected。"""
    decision: str                              # 'approved' / 'rejected'
    note: str = ""                             # 驳回原因（驳回时填写）


class TemplateFeatureRequest(BaseModel):
    """模板推荐切换请求体（仅管理员）。"""
    featured: bool


# ===== 内容生成 =====

class GenerateRequest(BaseModel):
    """内容生成请求体。

    对应 POST /api/generate 接口的请求体。
    """
    product_id: str                             # 产品 ID
    scenario_id: str                            # 场景 ID
    template_id: str = ""                       # 模板 ID（场景关联的模板）
    channel: str = "官网"                       # 目标渠道
    style: str = "专业严谨"                     # 文案风格
    params: dict[str, Any] = Field(default_factory=dict)  # 用户填写的参数
    # ge=1 表示大于等于 1，le=3 表示小于等于 3（上限 3，避免选项疲劳与 LLM 成本）
    version_count: int = Field(default=3, ge=1, le=3)     # 生成版本数（1-3）
    # created_by 由后端从登录令牌取，不在请求体中


class VersionContent(BaseModel):
    """单个版本的生成内容。"""
    index: int                  # 版本序号
    title: str                  # 标题
    body: str                   # 正文
    tags: list[str] = Field(default_factory=list)  # 标签列表
    # 渠道归属：多渠道适配后标识该版本属于哪个渠道；初稿阶段为空字符串
    channel: str = ""
    # 版本特色：该版本的差异化方向（如"专业严谨"/"活泼有趣"），供前端展示对比
    feature: str = ""
    image: str | None = None    # 文生图配图（首图，向后兼容；SVG data URL 或图片 URL，加分项）
    # 全部配图列表（1-5 张）：每张 {url, caption, theme, type}，前端按小节穿插展示
    images: list[dict[str, Any]] = Field(default_factory=list)
    # A/B 测试票数（加分项）：每个版本独立计票，用于对比哪个版本更受欢迎
    votes: dict[str, int] = Field(default_factory=lambda: {"like": 0, "dislike": 0})
    # 已投票成员及其方向 {member_id: 'like'|'dislike'}，用于防重复投票 / 改票 / 取消
    voters: dict[str, str] = Field(default_factory=dict)
    # SEO 分析结果（深度集成：生成流程自动计算，随版本持久化）
    # 结构同 SeoAnalyzeResponse：{score, suggestions, keywords, stats}
    # None 表示尚未分析（老数据兼容）；dict 表示已分析
    seo: dict[str, Any] | None = None


class AgentStep(BaseModel):
    """Agent 执行步骤追踪。

    记录每个 Agent 的执行状态、耗时、输出，用于前端展示执行链路。
    """
    agent: str                                  # Agent 名称
    status: str = "success"                     # 状态：success / warning / error
    message: str = ""                           # 执行信息
    duration_ms: int = 0                        # 执行耗时（毫秒）
    output: Any = None                          # 输出内容（任意类型）


class GenerateResponse(BaseModel):
    """内容生成响应体。"""
    history_id: str                             # 历史记录 ID
    product_name: str                           # 产品名称
    scenario_name: str                          # 场景名称
    channel: str                                # 渠道
    style: str                                  # 风格
    versions: list[VersionContent]              # 多版本内容列表
    agent_trace: list[AgentStep]                # Agent 执行链路
    validated: bool                             # 是否校验通过
    issues: list[str] = Field(default_factory=list)  # 校验问题列表


# ===== 历史记录 =====

class HistoryItem(BaseModel):
    """历史记录项。"""
    id: str
    product_id: str
    product_name: str
    scenario_id: str
    scenario_name: str
    channel: str
    style: str
    params: dict[str, Any] = Field(default_factory=dict)
    versions: list[VersionContent] = Field(default_factory=list)
    agent_trace: list[AgentStep] = Field(default_factory=list)
    validated: bool = False
    issues: list[str] = Field(default_factory=list)
    created_at: datetime
    # 用户反馈：'like'（赞）/ 'dislike'（踩）/ None（未标记）
    # 对应加分项「引入用户反馈机制，根据点赞/踩标记优化生成质量」
    # 注意：feedback 单值会被多人覆盖，仅作向后兼容；明细见 feedback_voters
    feedback: str | None = None
    # 每个成员对该记录的反馈 {member_id: "like"/"dislike"}，per-user 不互相覆盖
    # 路由层返回时用 feedback_voters.get(当前用户id) 回填 feedback 字段，前端零改动
    feedback_voters: dict = Field(default_factory=dict)
    # 赞/踩总数：路由层从 feedback_voters 统计回填，供前端按钮显示数量
    like_count: int = 0
    dislike_count: int = 0
    created_by: str | None = None    # 生成人（团队成员 id，加分项：团队协作）


class HistoryUpdate(BaseModel):
    """历史记录更新请求体（手动编辑后保存）。"""
    versions: list[VersionContent] | None = None    # 只允许更新 versions 字段


class FeedbackRequest(BaseModel):
    """用户反馈请求体（赞 / 踩 / 取消）。

    feedback 取值：
    - "like"     点赞
    - "dislike"  踩
    - ""         取消标记（清空）
    """
    feedback: str = Field(..., description="like / dislike / 空字符串表示取消")


# ===== 上传产品手册解析（加分项）=====

class ImportDocxResponse(BaseModel):
    """上传 Word 手册解析结果。

    解析后不直接入库，而是返回一个产品草稿，由用户在前端核对、补充后再保存。
    这样设计是因为手册内容千差万别，自动解析只能做到"尽量准确"，
    人工确认一遍再入库更可靠。
    """
    product: "ProductCreate"    # 解析出的产品草稿（结构同新建产品请求体）
    char_count: int             # 文档纯文本字符数（衡量解析输入量）
    extractor: str              # 使用的提取器：llm / heuristic
    note: str = ""              # 解析说明（如哪些字段未识别到）


# 延迟解析：ProductCreate 在本文件上方已定义，但 Pydantic 需要显式重建模型引用
# rebuild() 让 ImportDocxResponse 正确识别字符串引用 "ProductCreate"
ImportDocxResponse.model_rebuild()


# ===== 团队成员（加分项：团队协作）=====

class Member(BaseModel):
    """用户/团队成员（响应模型，不含密码哈希）。"""
    id: str
    name: str
    color: str = "#409eff"
    username: str | None = None
    email: str | None = None
    is_admin: bool = False
    created_at: datetime

    model_config = {"from_attributes": True}


class MemberUpdate(BaseModel):
    """管理员修改成员资料请求体（改他人）。所有字段可选。"""
    name: str | None = None
    email: str | None = None
    color: str | None = None
    is_admin: bool | None = None
    new_password: str | None = None    # 重置密码（管理员无需旧密码）


class MemberCreate(BaseModel):
    """管理员创建成员请求体。"""
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6, max_length=100)
    name: str = Field(..., min_length=1, max_length=50)
    email: str = ""
    is_admin: bool = False


# ===== 用户鉴权 =====

class RegisterRequest(BaseModel):
    """注册请求体。"""
    username: str = Field(..., min_length=3, max_length=50, description="登录用户名")
    password: str = Field(..., min_length=6, max_length=100, description="密码（至少 6 位）")
    name: str = Field(..., min_length=1, max_length=50, description="昵称")
    email: str = ""


class LoginRequest(BaseModel):
    """登录请求体。"""
    username: str
    password: str


class User(BaseModel):
    """用户响应模型（永不包含 password_hash）。"""
    id: str
    name: str
    color: str = "#409eff"
    username: str | None = None
    email: str | None = None
    is_admin: bool = False
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    """登录/注册成功响应：双令牌 + 当前用户。"""
    access_token: str      # 访问令牌（短期有效，每次请求携带）
    refresh_token: str     # 刷新令牌（长期有效，仅用于刷新 access_token）
    user: User


class UserUpdate(BaseModel):
    """修改个人资料请求体。

    name/email/color 可直接改；改密码需提供 old_password + new_password。
    只改资料时可不传密码字段。
    """
    name: str | None = None
    email: str | None = None
    color: str | None = None
    old_password: str | None = None    # 改密码时必须提供
    new_password: str | None = None    # 改密码时必须提供（至少 6 位）


# ===== SEO 分析（加分项）=====

class SeoSuggestion(BaseModel):
    """单条 SEO 建议。"""
    type: str        # 类别：title / content / keyword / structure / readability
    level: str       # 级别：good / warning / error
    message: str     # 建议内容


class SeoAnalyzeRequest(BaseModel):
    """SEO 分析请求体。"""
    title: str
    body: str


class SeoAnalyzeResponse(BaseModel):
    """SEO 分析结果。"""
    score: int                          # SEO 评分 0-100
    suggestions: list[SeoSuggestion]    # 优化建议列表
    keywords: list[str] = Field(default_factory=list)  # 从正文提取的关键词
    stats: dict[str, Any] = Field(default_factory=dict)  # 统计信息（字数/标题长度等）


# ===== 草稿（多阶段交互式生成流程的中间状态）=====
# 四阶段：检索-生成-校验 -> 用户选版+改内容 -> 多渠道适配 -> 文生图+落 history
# 跨阶段状态存 drafts 表，draft_id 串联，最终确认才写 history


class CreateDraftRequest(BaseModel):
    """创建草稿请求体（阶段1：检索+生成+校验）。

    与 GenerateRequest 的区别：渠道后置（不在阶段1传），由阶段3多选。
    """
    product_id: str
    scenario_id: str
    template_id: str = ""
    style: str = "专业严谨"
    params: dict[str, Any] = Field(default_factory=dict)
    version_count: int = Field(default=3, ge=1, le=3)


class RegenerateRequest(BaseModel):
    """重新生成请求体（阶段1内）：可选微调参数后重新生成初稿。"""
    params: dict[str, Any] | None = None   # 传则覆盖原参数，不传用草稿原参数


class RewriteRequest(BaseModel):
    """单版本微调请求体：用户输入自然语言改写指令，LLM 按指令重写该版本。"""
    instruction: str   # 如「标题再短一点」「卖点换成成本」


class SelectVersionRequest(BaseModel):
    """阶段2：提交用户选定+改动后的那一版。"""
    version: dict[str, Any]               # {index, title, body, tags, ...}


class AdaptRequest(BaseModel):
    """阶段3：多选渠道，产出每渠道 1 个适配版本。"""
    channels: list[str]                   # 用户多选的渠道名列表


class Draft(BaseModel):
    """草稿完整状态（GET /api/drafts/{id} 及各阶段响应共用）。"""
    id: str
    user_id: str
    product_id: str
    product_name: str = ""
    scenario_id: str
    scenario_name: str = ""
    template_id: str | None = None
    template_name: str | None = None
    style: str = ""
    params: dict[str, Any] = Field(default_factory=dict)
    stage: str = "draft"                  # draft / editing / adapted / imaged / done
    retrieved_info: dict[str, Any] = Field(default_factory=dict)
    draft_versions: list[VersionContent] = Field(default_factory=list)
    validation: dict[str, Any] = Field(default_factory=dict)   # {issues, validated}
    agent_trace: list[AgentStep] = Field(default_factory=list)
    selected_version: VersionContent | None = None
    channels: list[str] = Field(default_factory=list)
    versions: list[VersionContent] = Field(default_factory=list)   # 多渠道适配后的版本
    history_id: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
