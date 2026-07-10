"""文生图配图 Agent：为营销文案智能生成多张配图。

这是多 Agent 链路的最后一个 Agent，排在校验之后。

优化后逻辑：
1. 为每个版本独立配图（不再只看 versions[0]）
2. LLM 深度分析文案（识别钩子/痛点/卖点/CTA），每张图对应具体段落
3. 版本间差异化视觉策略（不同色调、图类型比例）
4. Mock 模式也从文案提取关键词生成个性化提示
"""
import json
import re
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

MAX_IMAGES_PER_CONTENT = 10
MAX_IMAGES_PER_VERSION = 5     # 单版本上限，避免一个版本生成过多


class ImageAgent(BaseAgent):
    """文生图配图 Agent。"""

    name = "文生图配图 Agent"
    description = "根据每版文案内容智能配图（1-5张/版本），生成差异化视觉方案。"

    def _execute(self, ctx: AgentContext) -> tuple[str, str, list]:
        """为每个版本独立配图。"""
        versions = ctx.versions or ctx.draft_versions
        if not versions:
            return "warning", "无版本可配图", []

        provider = get_provider()
        scene_style = self._get_scene_style(ctx.scenario.get("name", ""))
        info = ctx.retrieved_info
        total_images = 0
        version_count = 0

        for v in versions:
            # 每个版本基于自己的文案独立策划配图
            image_plan = self._plan_images_for_version(v, info, scene_style)
            if not image_plan:
                continue

            # 生成该版本的图片
            images = self._generate_version_images(provider, image_plan, scene_style)
            v["images"] = images
            if images:
                v["image"] = images[0]["url"]
            total_images += len(images)
            version_count += 1

        if total_images == 0:
            return "warning", "配图生成失败（所有版本均无图片）", versions
        return "success", f"已为 {version_count} 个版本共生成 {total_images} 张配图", versions

    def _get_scene_style(self, scenario_name: str) -> dict:
        """根据场景名称匹配配图风格。"""
        for key, style in SCENE_IMAGE_STYLES.items():
            if key in scenario_name:
                return style
        return SCENE_IMAGE_STYLES["产品介绍"]

    # ===== 单版本配图策划 =====

    def _plan_images_for_version(self, v: dict, info: dict, scene_style: dict) -> list[dict]:
        """针对单个版本策划配图方案。"""
        title = v.get("title", "")
        body = v.get("body", "")
        tags = v.get("tags", [])
        sp = info.get("selling_points", [])

        if self._llm and self._llm.name != "mock-engine":
            return self._plan_with_llm(title, body, tags, sp, scene_style)
        return self._plan_with_rules(title, body, tags, sp, scene_style, v.get("index", 1))

    def _plan_with_llm(self, title, body, tags, sp, scene_style) -> list[dict]:
        """LLM 模式：深度分析文案后策划配图。"""
        max_images = min(scene_style.get("max_images", 5), MAX_IMAGES_PER_VERSION)

        sys_prompt = (
            "你是资深的营销视觉策划师。你的任务是根据营销文案，策划一套配图方案。\n"
            "要求：\n"
            "1. 深入理解文案：识别出钩子（开头吸引）、痛点、方案、卖点、CTA（行动号召）各在哪儿\n"
            "2. 每张图必须对应文案中的具体段落或信息点\n"
            "3. 图类型多样化：产品展示图 / 数据可视化图 / 场景插画 / 抽象概念图\n"
            "4. 给出具体的画面描述：构图、色调、氛围、核心元素\n"
            "5. 所有图保持一致的品牌视觉感\n"
            f"输出 JSON 数组，每个元素包含 caption（图片说明）、prompt（50-80字详细画面描述）、"
            "theme（主题标签）、type（图类型）四个字段。"
        )
        user_prompt = (
            f"【文案标题】{title}\n"
            f"【文案标签】{'、'.join(tags) if tags else '无'}\n"
            f"【核心卖点】{'、'.join(sp[:5]) if sp else '无'}\n"
            f"【场景风格】{scene_style['style']} · {scene_style['aspect']}\n"
            f"【色调建议】{scene_style['color_hint']}\n"
            f"【正文内容】\n{body}\n\n"
            f"请策划 1-{max_images} 张配图，输出 JSON 数组格式：\n"
            '[{"caption":"图片说明","prompt":"50-80字详细画面描述含构图/色调/氛围/元素",'
            '"theme":"主题标签","type":"产品图/数据图/场景图/概念图"}]'
        )

        try:
            raw = self._llm.chat(sys_prompt, user_prompt, temperature=0.7)
            plan = self._parse_image_plan(raw)
            if plan:
                return plan[:max_images]
        except Exception:
            pass

        # LLM 失败回退规则
        return self._plan_with_rules(title, body, tags, sp, scene_style, 0)

    def _plan_with_rules(self, title, body, tags, sp, scene_style, version_index: int = 0) -> list[dict]:
        """Mock/规则模式：基于文案关键词策划配图。"""
        # 从文案提取关键词
        keywords = self._extract_keywords(title, body, sp)
        body_len = len(body)
        sp_count = len(sp)
        max_allowed = min(scene_style.get("max_images", 5), MAX_IMAGES_PER_VERSION)

        # 根据内容长度 + 卖点数量决定配图数
        if body_len < 200:
            count = 1
        elif body_len < 500:
            count = 2
        elif body_len < 1000:
            count = min(3, max_allowed)
        else:
            count = min(2 + sp_count, max_allowed)

        # 版本间色调差异化
        palette_hints = ["冷色科技蓝", "暖色活力橙", "清新自然绿", "大气深紫"]
        color_tint = palette_hints[version_index % len(palette_hints)]

        # 判断正文是否有明确段落结构
        paragraphs = [p.strip() for p in body.split("\n") if p.strip() and not p.strip().startswith("#")]

        plan = []
        # 第 1 张：标题主图
        plan.append({
            "caption": f"「{title[:15]}」主视觉",
            "prompt": (
                f"{scene_style['aspect']}配图，{scene_style['style']}。"
                f"主标题：{title[:20]}。"
                f"色调：{color_tint}，{scene_style['color_hint']}。"
                f"元素：{scene_style['elements']}。"
                f"风格关键词：{'、'.join(keywords[:3])}。"
            ),
            "theme": "主视觉",
            "type": "概念图",
        })

        # 后续图：优先用卖点
        if count > 1 and sp:
            for s in sp[:count - 1]:
                plan.append({
                    "caption": f"卖点：{s[:20]}",
                    "prompt": (
                        f"{scene_style['aspect']}配图，突出「{s}」。"
                        f"风格：{scene_style['style']}。"
                        f"色调：{color_tint}，{scene_style['color_hint']}。"
                        f"元素：{scene_style['elements']}。"
                    ),
                    "theme": "卖点",
                    "type": "产品图" if version_index % 2 == 0 else "场景图",
                })

        # 还不够 → 用正文段落补充
        if len(plan) < count and len(paragraphs) > 1:
            for p in paragraphs[1:count - len(plan) + 1]:
                p_clean = p.replace("**", "").replace("##", "").strip()
                if p_clean and len(p_clean) > 5:
                    plan.append({
                        "caption": p_clean[:25],
                        "prompt": (
                            f"{scene_style['aspect']}配图，表现「{p_clean[:30]}」。"
                            f"风格：{scene_style['style']}，色调：{color_tint}。"
                        ),
                        "theme": "内容插图",
                        "type": "数据图" if any(c in p_clean for c in "0123456789%") else "场景图",
                    })

        # 补齐到 count
        while len(plan) < count:
            idx = len(plan)
            plan.append({
                "caption": f"配图 {idx + 1}",
                "prompt": (
                    f"{scene_style['aspect']}配图，{scene_style['style']}。"
                    f"色调：{color_tint}，元素：{scene_style['elements']}。"
                ),
                "theme": f"插图{idx + 1}",
                "type": "概念图",
            })

        return plan[:count]

    def _generate_version_images(self, provider, image_plan: list[dict], scene_style: dict) -> list[dict]:
        """为单个版本的配图方案生成实际图片。"""
        images = []
        for i, img_desc in enumerate(image_plan):
            try:
                img_url = provider.generate_image(
                    img_desc.get("prompt", ""),
                    theme=img_desc.get("theme", ""),
                    scene_style=scene_style,
                )
                images.append({
                    "url": img_url,
                    "caption": img_desc.get("caption", f"配图 {i + 1}"),
                    "theme": img_desc.get("theme", ""),
                    "type": img_desc.get("type", ""),
                })
            except Exception:
                continue
        return images

    @staticmethod
    def _extract_keywords(title: str, body: str, sp: list) -> list[str]:
        """从文案中提取关键词用于配图。"""
        text = f"{title} {body}"
        words = re.findall(r'[一-鿿\w]+', text)
        meaningful = [w for w in words if len(w) > 1]
        meaningful.sort(key=len, reverse=True)
        return (meaningful + sp)[:10]

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
                result = []
                for item in plan:
                    if isinstance(item, dict) and "prompt" in item:
                        result.append({
                            "caption": item.get("caption", "配图"),
                            "prompt": item.get("prompt", ""),
                            "theme": item.get("theme", ""),
                            "type": item.get("type", ""),
                        })
                return result if result else None
        except (json.JSONDecodeError, IndexError, KeyError):
            pass
        return None
