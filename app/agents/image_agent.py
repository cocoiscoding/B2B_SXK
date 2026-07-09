"""文生图配图 Agent：为营销文案智能生成多张配图。

这是多 Agent 链路的最后一个 Agent，排在校验之后。

优化后的逻辑：
1. 根据场景类型选择配图风格（Banner/产品介绍/案例/PPT/社交）
2. LLM 分析文案内容，决定配图数量和每张图的主题
3. 最多生成 10 张配图，最少 1 张
4. 每张图都有独立的提示词和风格

设计要点：
- 放在最后：配图是锦上添花，不应阻断内容生成主流程
- BaseAgent.execute 已包裹 try/except：图像生成失败也只记一个 error 步骤
"""
import json
from app.agents.base import BaseAgent, AgentContext
from app.agents.llm_provider import get_provider


# 场景配图风格配置
SCENE_IMAGE_STYLES = {
    "Banner": {
        "aspect": "横幅",
        "style": "简洁大气，突出核心卖点",
        "elements": "产品图标、标语、行动按钮",
        "color_hint": "品牌色为主，对比强烈",
        "max_images": 3,
    },
    "产品介绍": {
        "aspect": "产品展示",
        "style": "专业科技感，展现产品价值",
        "elements": "产品界面、功能图标、数据可视化",
        "color_hint": "蓝紫色调，科技渐变",
        "max_images": 5,
    },
    "竞品分析": {
        "aspect": "对比图表",
        "style": "清晰对比，突出优势",
        "elements": "对比表格、勾选标记、数据图表",
        "color_hint": "绿色优势、灰色对比",
        "max_images": 3,
    },
    "客户案例": {
        "aspect": "场景故事",
        "style": "真实感、可信度",
        "elements": "行业场景、人物剪影、成果数据",
        "color_hint": "温暖色调，信任感",
        "max_images": 4,
    },
    "PPT": {
        "aspect": "演示封面",
        "style": "商务专业，层次分明",
        "elements": "标题区域、装饰图形、页码",
        "color_hint": "深蓝/深灰，商务稳重",
        "max_images": 8,
    },
    "社交媒体": {
        "aspect": "社交卡片",
        "style": "活泼吸引，适合分享",
        "elements": "表情符号、话题标签、互动元素",
        "color_hint": "明亮多彩，年轻化",
        "max_images": 4,
    },
}

# 绝对上限
MAX_IMAGES_PER_CONTENT = 10


class ImageAgent(BaseAgent):
    """文生图配图 Agent。"""

    name = "文生图配图 Agent"
    description = "根据文案内容智能决定配图数量（1-10张），为每张图生成独立主题。"

    def _execute(self, ctx: AgentContext) -> tuple[str, str, list]:
        """为生成的版本智能配图。"""
        versions = ctx.versions or ctx.draft_versions
        if not versions:
            return "warning", "无版本可配图", []

        provider = get_provider()
        info = ctx.retrieved_info
        scenario_name = ctx.scenario.get("name", "")
        channel = ctx.channel

        # 获取场景对应的配图风格
        scene_style = self._get_scene_style(scenario_name)

        v = versions[0]
        title = v.get("title", "")
        body = v.get("body", "")
        sp = info.get("selling_points", [])

        # 决定配图数量和每张图的主题
        if self._llm and self._llm.name != "mock-engine":
            # LLM 模式：让大模型分析文案，决定配图方案
            image_plan = self._plan_images_with_llm(
                title, body, sp, scenario_name, channel, scene_style
            )
        else:
            # Mock 模式：用规则决定配图方案
            image_plan = self._plan_images_rule(
                title, body, sp, scenario_name, scene_style
            )

        # 生成配图
        images = []
        for i, img_desc in enumerate(image_plan, 1):
            try:
                img_url = provider.generate_image(
                    img_desc.get("prompt", ""),
                    theme=channel,
                    scene_style=scene_style
                )
                images.append({
                    "url": img_url,
                    "caption": img_desc.get("caption", f"配图 {i}"),
                    "theme": img_desc.get("theme", ""),
                })
            except Exception:
                # 单张图失败不影响其他图
                continue

        # 将图片列表存入版本（兼容旧的单图字段）
        v["images"] = images
        if images:
            v["image"] = images[0]["url"]  # 兼容旧逻辑

        count = len(images)
        return "success", f"已生成 {count} 张配图（{scene_style['aspect']}风格）", versions

    def _get_scene_style(self, scenario_name: str) -> dict:
        """根据场景名称匹配配图风格。"""
        for key, style in SCENE_IMAGE_STYLES.items():
            if key in scenario_name:
                return style
        return SCENE_IMAGE_STYLES["产品介绍"]

    def _plan_images_with_llm(
        self, title: str, body: str, sp: list,
        scenario_name: str, channel: str, scene_style: dict
    ) -> list[dict]:
        """使用 LLM 分析文案，决定配图数量和每张图的主题。"""
        max_images = min(scene_style.get("max_images", 5), MAX_IMAGES_PER_CONTENT)

        sys_prompt = (
            "你是专业的视觉策划师，擅长为营销内容规划配图方案。"
            "根据文案内容，决定需要几张配图，以及每张图的主题和描述。"
            "输出 JSON 数组，每个元素包含：caption（图片说明）、prompt（图像描述）、theme（主题标签）。"
        )
        user_prompt = (
            f"场景类型：{scenario_name}\n"
            f"发布渠道：{channel}\n"
            f"配图风格要求：{scene_style['style']}\n"
            f"色调建议：{scene_style['color_hint']}\n\n"
            f"文案标题：{title}\n"
            f"核心卖点：{'、'.join(sp[:3]) if sp else '无'}\n"
            f"正文内容：\n{body}\n\n"
            f"请决定配图数量（1-{max_images}张），并为每张图生成描述。"
            f"输出 JSON 数组格式：[{{\"caption\":\"图片说明\",\"prompt\":\"50字图像描述\",\"theme\":\"主题\"}}]"
        )

        try:
            raw = self._llm.chat(sys_prompt, user_prompt, temperature=0.7)
            plan = self._parse_image_plan(raw)
            if plan:
                return plan[:max_images]
        except Exception:
            pass

        # LLM 失败，回退到规则
        return self._plan_images_rule(title, body, sp, scenario_name, scene_style)

    def _plan_images_rule(
        self, title: str, body: str, sp: list,
        scenario_name: str, scene_style: dict
    ) -> list[dict]:
        """用规则决定配图方案。"""
        aspect = scene_style.get("aspect", "产品展示")
        style = scene_style.get("style", "")
        elements = scene_style.get("elements", "")
        color_hint = scene_style.get("color_hint", "")

        # 根据内容长度和卖点数量决定配图数
        body_len = len(body)
        sp_count = len(sp)

        if body_len < 200:
            count = 1
        elif body_len < 500:
            count = 2
        elif body_len < 1000:
            count = 3
        else:
            count = min(4 + sp_count // 2, MAX_IMAGES_PER_CONTENT)

        # 限制在场景允许范围内
        count = min(count, scene_style.get("max_images", 5))

        plan = []
        # 第一张：封面/主图
        plan.append({
            "caption": f"{title[:20]} 主图",
            "prompt": f"{aspect}配图，{style}，主题：{title[:20]}，元素：{elements}，色调：{color_hint}",
            "theme": "封面",
        })

        # 后续图：根据卖点或内容段落
        if count > 1 and sp:
            for i, s in enumerate(sp[:count-1], 2):
                plan.append({
                    "caption": f"卖点：{s[:15]}",
                    "prompt": f"{aspect}配图，突出「{s}」，{style}，元素：{elements}，色调：{color_hint}",
                    "theme": f"卖点{i-1}",
                })

        # 如果还不够，补充内容段落图
        while len(plan) < count:
            idx = len(plan)
            plan.append({
                "caption": f"内容插图 {idx}",
                "prompt": f"{aspect}配图，{style}，展示产品特性，元素：{elements}，色调：{color_hint}",
                "theme": f"插图{idx}",
            })

        return plan[:count]

    @staticmethod
    def _parse_image_plan(raw: str) -> list[dict] | None:
        """解析 LLM 返回的配图方案 JSON。"""
        try:
            text = raw.strip()
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
            plan = json.loads(text)
            if isinstance(plan, list) and plan:
                # 验证每个元素的结构
                result = []
                for item in plan:
                    if isinstance(item, dict) and "prompt" in item:
                        result.append({
                            "caption": item.get("caption", "配图"),
                            "prompt": item.get("prompt", ""),
                            "theme": item.get("theme", ""),
                        })
                return result if result else None
        except (json.JSONDecodeError, IndexError, KeyError):
            pass
        return None
