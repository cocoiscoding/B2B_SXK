"""
文生图配图 Agent：为营销文案智能生成多张配图。

核心改进：
1. 【新增】文案-图片映射表，确保每张图对应具体文案段落
2. 【新增】语义匹配校验，检查图片描述是否与原文一致
3. 【新增】配图覆盖度分析，避免遗漏重要信息
4. 优化后的 LLM prompt 要求明确标注对应关系
"""
import json
import re
from typing import Optional, List, Dict, Tuple
from urllib.parse import quote
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

# 版本差异化视觉策略：按版本索引循环，让多版文案配图风格有区分度
# - name: 策略名（写入 version.visual_strategy 供展示）
# - color_tint: 色调（注入 prompt 与占位图配色）
# - style_intensity: 风格强度（注入 LLM prompt）
# - type_ratio: 图类型占比，_allocate_image_types 据此把配图数分配到各图类型
VERSION_VISUAL_STRATEGIES = [
    {
        "name": "科技冷调",
        "color_tint": "冷色科技蓝",
        "style_intensity": "强",
        "type_ratio": {"产品图": 0.4, "场景图": 0.3, "数据图": 0.2, "概念图": 0.1},
    },
    {
        "name": "活力暖调",
        "color_tint": "暖色活力橙",
        "style_intensity": "中",
        "type_ratio": {"场景图": 0.4, "产品图": 0.3, "概念图": 0.2, "数据图": 0.1},
    },
    {
        "name": "自然清新",
        "color_tint": "清新自然绿",
        "style_intensity": "中",
        "type_ratio": {"场景图": 0.4, "概念图": 0.3, "产品图": 0.2, "数据图": 0.1},
    },
    {
        "name": "商务稳重",
        "color_tint": "大气深紫",
        "style_intensity": "强",
        "type_ratio": {"数据图": 0.4, "产品图": 0.3, "概念图": 0.2, "场景图": 0.1},
    },
]

MAX_IMAGES_PER_CONTENT = 10
MAX_IMAGES_PER_VERSION = 5
# 配图生成失败时的最后兜底图：自包含内联 SVG data URL，不依赖 Pillow/网络，
# 保证 <img> 永远能渲染出一张占位图，而不是 broken image。
# （曾用 https://placeholder.example.com/... 假域名，图片永远加载不出来）
PLACEHOLDER_IMAGE_URL = (
    "data:image/svg+xml;utf8,"
    + quote(
        '<svg xmlns="http://www.w3.org/2000/svg" width="640" height="360">'
        '<rect width="100%" height="100%" fill="#f1f5f9"/>'
        '<rect x="16" y="16" width="608" height="328" rx="8" fill="none" '
        'stroke="#cbd5e1" stroke-width="2" stroke-dasharray="8 6"/>'
        '<text x="50%" y="46%" font-family="Microsoft YaHei,sans-serif" '
        'font-size="24" fill="#64748b" text-anchor="middle" '
        'dominant-baseline="middle">配图生成失败</text>'
        '<text x="50%" y="60%" font-family="sans-serif" font-size="13" '
        'fill="#94a3b8" text-anchor="middle" dominant-baseline="middle">'
        "神行库 · 占位配图</text>"
        "</svg>",
        safe="",
    )
)


class ImageAgent(BaseAgent):
    """文生图配图 Agent - 增强版（带文案映射校验）。"""

    name = "文生图配图 Agent"
    description = "根据每版文案内容智能配图，确保图片与文案段落精准对应。"

    def _execute(self, ctx: AgentContext) -> tuple[str, str, list]:
        """为每个版本独立配图，并建立文案-图片映射。"""
        versions = ctx.versions or ctx.draft_versions
        if not versions:
            return "warning", "无版本可配图", []

        provider = get_provider()
        scene_style = self._get_scene_style(ctx.scenario.get("name", ""))
        info = ctx.retrieved_info or {}

        total_images = 0
        successful_versions = 0

        for idx, v in enumerate(versions):
            try:
                visual_strategy = self._get_version_strategy(idx)

                # 1. 先分析文案结构
                content_analysis = self._analyze_content_structure(v, info)

                # 2. 策划配图方案（带文案映射）
                image_plan = self._plan_images_for_version(
                    v=v,
                    content_analysis=content_analysis,
                    scene_style=scene_style,
                    visual_strategy=visual_strategy,
                )
                if not image_plan:
                    continue

                # 3. 【新增】校验配图与文案的对应关系
                validated_plan = self._validate_image_content_mapping(
                    image_plan=image_plan,
                    content_analysis=content_analysis,
                )

                # 4. 生成图片
                images = self._generate_version_images_with_fallback(
                    provider=provider,
                    image_plan=validated_plan,
                    scene_style=scene_style,
                )

                # 5. 【新增】挂载映射表和覆盖度分析
                v["images"] = images
                v["visual_strategy"] = visual_strategy["name"]
                v["content_image_mapping"] = self._build_content_mapping(
                    content_analysis, validated_plan
                )
                v["coverage_analysis"] = self._analyze_coverage(
                    content_analysis, validated_plan
                )

                if images:
                    v["image"] = images[0]["url"]

                total_images += len(images)
                successful_versions += 1

            except Exception as e:
                v["images"] = []
                v["image_plan_error"] = str(e)

        if total_images == 0:
            return "warning", "配图生成失败（所有版本均无图片）", versions

        return (
            "success",
            f"已为 {successful_versions}/{len(versions)} 个版本生成 {total_images} 张配图（含文案映射）",
            versions,
        )

    # ===== 文案结构分析 =====

    def _analyze_content_structure(self, v: dict, info: dict) -> dict:
        """分析文案结构，拆解为可配图的信息单元。"""
        title = v.get("title", "")
        body = v.get("body", "")
        tags = v.get("tags", [])
        sp = info.get("selling_points", [])

        # 提取段落
        paragraphs = self._extract_paragraphs(body)

        # 用 LLM 或规则识别文案结构
        if self._use_llm:
            structure = self._analyze_structure_with_llm(title, body, paragraphs, sp)
        else:
            structure = self._analyze_structure_with_rules(title, paragraphs, sp, tags)

        structure["title"] = title
        structure["tags"] = tags
        return structure

    def _analyze_structure_with_llm(
        self, title: str, body: str, paragraphs: list, sp: list
    ) -> dict:
        """用 LLM 识别文案的钩子/痛点/卖点/CTA 等结构。"""
        sys_prompt = (
            "你是文案结构分析师。分析以下营销文案，识别关键信息单元。\n"
            "输出 JSON 格式：\n"
            '{\n'
            '  "hook": "开头的吸引点（可为空）",\n'
            '  "pain_points": ["痛点1", "痛点2"],\n'
            '  "solutions": ["方案1", "方案2"],\n'
            '  "selling_points": [{"point": "卖点", "paragraph_index": 0}],\n'
            '  "cta": "行动号召（可为空）",\n'
            '  "paragraphs": [{"index": 0, "text": "...", "type": "hook/pain/solution/sp/cta"}],\n'
            '  "key_visual_elements": ["需要配图的关键元素"]\n'
            '}'
        )
        user_prompt = (
            f"【标题】{title}\n"
            f"【卖点列表】{'、'.join(sp)}\n"
            f"【正文】\n{body[:3000]}\n\n"
            f"请分析文案结构，并为每个段落标注类型。"
        )

        try:
            raw = self._llm.chat(sys_prompt, user_prompt, temperature=0.3)
            return self._parse_json_safely(raw)
        except Exception:
            return self._analyze_structure_with_rules(title, paragraphs, sp, [])

    def _analyze_structure_with_rules(
        self, title: str, paragraphs: list, sp: list, tags: list
    ) -> dict:
        """规则模式：简单识别文案结构。"""
        structure = {
            "hook": "",
            "pain_points": [],
            "solutions": [],
            "selling_points": [{"point": s, "paragraph_index": -1} for s in sp],
            "cta": "",
            "paragraphs": [],
            "key_visual_elements": [],
        }

        # 分析每个段落
        cta_keywords = ["立即", "马上", "点击", "扫码", "咨询", "购买", "下载", "免费试用"]
        pain_keywords = ["痛点", "问题", "困扰", "烦恼", "困难", "麻烦", "复杂", "低效"]
        solution_keywords = ["解决", "方案", "功能", "特性", "优势", "帮助", "实现"]

        for i, para in enumerate(paragraphs):
            para_type = "body"  # 默认类型
            para_lower = para.lower()

            # 判断段落类型
            if i == 0:
                para_type = "hook" if len(para) < 100 else "body"
                if para_type == "hook":
                    structure["hook"] = para

            if any(kw in para_lower for kw in cta_keywords):
                para_type = "cta"
                structure["cta"] = para
            elif any(kw in para_lower for kw in pain_keywords):
                para_type = "pain"
                structure["pain_points"].append(para)
            elif any(kw in para_lower for kw in solution_keywords):
                para_type = "solution"
                structure["solutions"].append(para)

            structure["paragraphs"].append({
                "index": i,
                "text": para[:100],
                "type": para_type,
            })

        # 关键词作为视觉元素
        structure["key_visual_elements"] = self._extract_keywords(
            title, "\n".join(paragraphs), sp
        )[:5]

        return structure

    # ===== 配图策划（增强版） =====

    def _plan_images_for_version(
        self,
        v: dict,
        content_analysis: dict,
        scene_style: dict,
        visual_strategy: dict,
    ) -> Optional[list[dict]]:
        """策划配图方案，强制要求每张图标注对应文案。"""
        title = v.get("title", "")
        body = v.get("body", "")
        tags = content_analysis.get("tags", [])
        sp = content_analysis.get("selling_points", [])
        target_count = self._calculate_image_count(
            body, [s["point"] for s in sp], scene_style.get("max_images", 5)
        )

        # 优先 LLM
        if self._use_llm:
            plan = self._plan_with_enhanced_llm(
                title, body, content_analysis, scene_style, visual_strategy, target_count
            )
            if plan:
                return plan[:target_count]

        # 规则兜底
        return self._plan_with_content_mapping(
            title, body, content_analysis, scene_style, visual_strategy, target_count
        )

    def _plan_with_enhanced_llm(
        self,
        title: str,
        body: str,
        content_analysis: dict,
        scene_style: dict,
        visual_strategy: dict,
        target_count: int,
    ) -> Optional[list[dict]]:
        """增强版 LLM prompt：要求明确标注对应关系。"""
        paragraphs_info = json.dumps(
            content_analysis.get("paragraphs", [])[:10], ensure_ascii=False
        )
        selling_points = json.dumps(
            content_analysis.get("selling_points", []), ensure_ascii=False
        )

        sys_prompt = (
            "你是营销视觉策划师。为文案策划配图，**每张图必须精确对应文案中的具体段落或卖点**。\n\n"
            "输出 JSON 数组，每个元素包含：\n"
            '  - caption: 图片说明（会显示在图片下方）\n'
            '  - prompt: 50-80字详细画面描述（含构图/色调/氛围/元素）\n'
            '  - theme: 主题标签（主视觉/痛点/卖点/解决方案/行动号召）\n'
            '  - type: 图类型（产品图/数据图/场景图/概念图）\n'
            f'  - source_paragraph_index: 对应的原文段落索引（数字，必须对应下面的段落编号）\n'
            '  - source_text: 引用的原文片段（10-30字）\n'
            '  - relevance: 配图与原文的相关性说明（10-20字）\n\n'
            f"要求：\n"
            f"1. 图类型比例：{json.dumps(visual_strategy.get('type_ratio', {}), ensure_ascii=False)}\n"
            f"2. 色调：{visual_strategy.get('color_tint')}，风格强度：{visual_strategy.get('style_intensity')}\n"
            f"3. 必须覆盖：钩子、痛点、核心卖点、CTA（如有）\n"
            f"4. source_paragraph_index 必须对应下面给出的段落索引\n"
        )

        user_prompt = (
            f"【标题】{title}\n"
            f"【段落列表】（索引从0开始）\n{paragraphs_info}\n"
            f"【卖点列表】\n{selling_points}\n"
            f"【场景风格】{scene_style.get('style')} · {scene_style.get('aspect')}\n"
            f"【色调建议】{scene_style.get('color_hint')}\n"
            f"【正文全文】\n{body[:3000]}\n\n"
            f"请策划 {target_count} 张配图，确保 source_paragraph_index 字段准确对应段落索引。"
        )

        try:
            raw = self._llm.chat(sys_prompt, user_prompt, temperature=0.5)
            plan = self._parse_image_plan(raw)
            if plan:
                # 验证 source_paragraph_index 的有效性
                max_index = len(content_analysis.get("paragraphs", [])) - 1
                for item in plan:
                    idx = item.get("source_paragraph_index", -1)
                    if idx < 0 or idx > max_index:
                        item["source_paragraph_index"] = -1  # 标记为无效
                return plan
        except Exception:
            pass
        return None

    def _plan_with_content_mapping(
        self,
        title: str,
        body: str,
        content_analysis: dict,
        scene_style: dict,
        visual_strategy: dict,
        target_count: int,
    ) -> list[dict]:
        """规则模式：确保配图与文案段落一一对应。"""
        color_tint = visual_strategy.get("color_tint", "默认")
        type_ratio = visual_strategy.get("type_ratio", {})
        paragraphs = content_analysis.get("paragraphs", [])
        selling_points = content_analysis.get("selling_points", [])

        plan = []

        # 1. 主视觉图（对应标题/钩子）
        hook_para = next((p for p in paragraphs if p["type"] == "hook"), None)
        plan.append({
            "caption": f"「{title[:15]}」主视觉",
            "prompt": self._build_prompt(scene_style, color_tint, f"主标题「{title[:30]}」"),
            "theme": "主视觉",
            "type": "概念图",
            "source_paragraph_index": hook_para["index"] if hook_para else 0,
            "source_text": title[:30],
            "relevance": "标题视觉化呈现",
        })

        remaining = target_count - 1
        if remaining <= 0:
            return plan

        # 2. 按类型比例分配
        type_allocation = self._allocate_image_types(type_ratio, remaining)

        # 3. 构建信息单元队列（按重要性排序：卖点 > 痛点 > 方案 > CTA）
        info_units = []

        # 卖点（优先级最高）
        for sp_item in selling_points:
            info_units.append({
                "text": sp_item["point"],
                "type": "selling_point",
                "para_index": sp_item.get("paragraph_index", -1),
                "img_type_hint": "产品图",
            })

        # 痛点
        for pain in content_analysis.get("pain_points", []):
            if pain not in [u["text"] for u in info_units]:
                info_units.append({
                    "text": pain[:50],
                    "type": "pain_point",
                    "para_index": -1,
                    "img_type_hint": "场景图",
                })

        # 解决方案
        for sol in content_analysis.get("solutions", []):
            if sol not in [u["text"] for u in info_units]:
                info_units.append({
                    "text": sol[:50],
                    "type": "solution",
                    "para_index": -1,
                    "img_type_hint": "数据图",
                })

        # CTA
        cta = content_analysis.get("cta", "")
        if cta:
            info_units.append({
                "text": cta[:50],
                "type": "cta",
                "para_index": -1,
                "img_type_hint": "概念图",
            })

        # 4. 按类型分配填充
        for img_type, count in type_allocation.items():
            for _ in range(count):
                # 找匹配的信息单元
                unit = None
                for u in info_units:
                    if u["img_type_hint"] == img_type or img_type == "概念图":
                        unit = u
                        break
                if not unit and info_units:
                    unit = info_units.pop(0)

                if unit:
                    info_units.remove(unit)
                    plan.append({
                        "caption": unit["text"][:25],
                        "prompt": self._build_prompt(scene_style, color_tint, unit["text"]),
                        "theme": unit["type"],
                        "type": img_type,
                        "source_paragraph_index": unit["para_index"],
                        "source_text": unit["text"][:30],
                        "relevance": f"对应{unit['type']}信息",
                    })
                else:
                    # 兜底：从段落中取
                    if paragraphs:
                        para = paragraphs.pop(0)
                        plan.append({
                            "caption": para["text"][:25],
                            "prompt": self._build_prompt(scene_style, color_tint, para["text"]),
                            "theme": "内容插图",
                            "type": img_type,
                            "source_paragraph_index": para["index"],
                            "source_text": para["text"][:30],
                            "relevance": "对应文案段落",
                        })

        return plan[:target_count]

    # ===== 新增：校验与映射 =====

    def _validate_image_content_mapping(
        self,
        image_plan: list[dict],
        content_analysis: dict,
    ) -> list[dict]:
        """校验配图与文案的对应关系，修正不合理的映射。"""
        validated = []
        paragraphs = content_analysis.get("paragraphs", [])

        for item in image_plan:
            para_index = item.get("source_paragraph_index", -1)

            # 检查段落索引是否有效
            if para_index >= 0 and para_index < len(paragraphs):
                para = paragraphs[para_index]
                # 【新增】检查图片描述中是否包含原文关键词
                source_text = item.get("source_text", "")
                prompt = item.get("prompt", "")

                # 提取 source_text 中的关键词（至少2个字的中文词）
                source_keywords = re.findall(r'[\u4e00-\u9fff]{2,}', source_text)
                prompt_keywords = re.findall(r'[\u4e00-\u9fff]{2,}', prompt)

                # 计算关键词重叠度
                overlap = len(set(source_keywords) & set(prompt_keywords))
                if overlap == 0 and source_keywords:
                    # 相关性低，补充原文关键词到 prompt
                    item["prompt"] += f"。关键信息：{'、'.join(source_keywords[:3])}"
                    item["relevance"] = "已自动补充原文关键词"

            validated.append(item)

        return validated

    def _build_content_mapping(
        self, content_analysis: dict, image_plan: list[dict]
    ) -> dict:
        """构建文案-图片映射表。"""
        mapping = {
            "paragraphs_covered": [],  # 已被覆盖的段落索引
            "paragraphs_missed": [],   # 未被覆盖的段落索引
            "image_mapping": [],       # 每张图对应什么
        }

        paragraphs = content_analysis.get("paragraphs", [])
        covered_indices = set()

        for img in image_plan:
            para_idx = img.get("source_paragraph_index", -1)
            mapping_entry = {
                "image_caption": img.get("caption", ""),
                "source_paragraph_index": para_idx,
                "source_text": img.get("source_text", ""),
                "relevance": img.get("relevance", ""),
            }

            if para_idx >= 0:
                covered_indices.add(para_idx)

            mapping["image_mapping"].append(mapping_entry)

        mapping["paragraphs_covered"] = sorted(list(covered_indices))
        mapping["paragraphs_missed"] = [
            p["index"] for p in paragraphs if p["index"] not in covered_indices
        ]

        return mapping

    def _analyze_coverage(
        self, content_analysis: dict, image_plan: list[dict]
    ) -> dict:
        """分析配图覆盖度。"""
        total_paragraphs = len(content_analysis.get("paragraphs", []))
        total_images = len(image_plan)

        # 检查关键信息是否被覆盖（theme 在中英文命名间不统一，归一化后再判）
        theme_aliases = {
            "主视觉": "hook", "hook": "hook",
            "痛点": "pain", "pain": "pain", "pain_point": "pain",
            "卖点": "selling_point", "selling_point": "selling_point",
            "行动号召": "cta", "cta": "cta",
        }
        key_types = {"hook": False, "pain": False, "cta": False, "selling_point": False}
        for img in image_plan:
            norm = theme_aliases.get(img.get("theme", ""))
            if norm in key_types:
                key_types[norm] = True
            # selling_point 可能映射到 theme="卖点" 或 type="产品图"
            if img.get("type") == "产品图":
                key_types["selling_point"] = True

        covered_keys = sum(1 for v in key_types.values() if v)
        total_keys = len(key_types)

        return {
            "total_paragraphs": total_paragraphs,
            "total_images": total_images,
            "coverage_ratio": round(total_images / max(total_paragraphs, 1), 2),
            "key_info_coverage": f"{covered_keys}/{total_keys}",
            "missing_key_info": [k for k, v in key_types.items() if not v],
            "is_adequate": covered_keys >= 2,  # 至少覆盖2类关键信息
        }

    # ===== 辅助方法 =====

    def _build_prompt(
        self, scene_style: dict, color_tint: str, content: str
    ) -> str:
        """构建图片生成 prompt。"""
        return (
            f"{scene_style.get('aspect', '')}配图，{scene_style.get('style', '')}。"
            f"表现「{content[:40]}」。"
            f"色调：{color_tint}，{scene_style.get('color_hint', '')}。"
            f"元素：{scene_style.get('elements', '')}。"
        )

    # ===== 场景与版本视觉策略 =====

    def _get_scene_style(self, scenario_name: str) -> dict:
        """根据场景名称匹配配图风格，未命中则回退到产品介绍。"""
        for key, style in SCENE_IMAGE_STYLES.items():
            if key in scenario_name:
                return style
        return SCENE_IMAGE_STYLES["产品介绍"]

    def _get_version_strategy(self, version_index: int) -> dict:
        """按版本索引返回差异化视觉策略（色调/图类型比例/风格强度）。"""
        return VERSION_VISUAL_STRATEGIES[version_index % len(VERSION_VISUAL_STRATEGIES)]

    # ===== 文案拆解辅助 =====

    @staticmethod
    def _extract_paragraphs(body: str) -> list[str]:
        """按换行拆分正文为段落，去掉空行和 markdown 标题行。"""
        if not body:
            return []
        return [
            p.strip()
            for p in body.split("\n")
            if p.strip() and not p.strip().startswith("#")
        ]

    @staticmethod
    def _extract_keywords(title: str, body: str, sp: list) -> list[str]:
        """从文案中提取关键词用于配图（标题+正文取长词，拼接卖点）。"""
        text = f"{title} {body}"
        words = re.findall(r'[一-鿿\w]+', text)
        meaningful = [w for w in words if len(w) > 1]
        meaningful.sort(key=len, reverse=True)
        return (meaningful + sp)[:10]

    # ===== 配图数量与类型分配 =====

    @staticmethod
    def _calculate_image_count(body: str, sp_list: list, max_images: int) -> int:
        """根据正文长度和卖点数量决定配图数量（1~单版本上限）。"""
        max_allowed = min(max_images, MAX_IMAGES_PER_VERSION)
        body_len = len(body or "")
        sp_count = len(sp_list or [])
        if body_len < 200:
            count = 1
        elif body_len < 500:
            count = 2
        elif body_len < 1000:
            count = min(3, max_allowed)
        else:
            count = min(2 + sp_count, max_allowed)
        return max(1, min(count, max_allowed))

    @staticmethod
    def _allocate_image_types(type_ratio: dict, remaining: int) -> dict:
        """按 type_ratio 比例把 remaining 张图分配到各图类型，总和恰为 remaining。"""
        if remaining <= 0:
            return {}
        items = [(t, float(r)) for t, r in (type_ratio or {}).items() if r]
        total = sum(r for _, r in items)
        if total <= 0:
            # 无比例信息：全部归为概念图
            return {"概念图": remaining}
        allocation: dict[str, int] = {}
        assigned = 0
        for t, r in items:
            n = max(0, round(remaining * r / total))
            allocation[t] = n
            assigned += n
        # 修正取整误差：差额补到比例最大的类型，保证总和 == remaining
        diff = remaining - assigned
        if diff != 0 and allocation:
            top = max(allocation, key=allocation.get)
            allocation[top] = max(0, allocation[top] + diff)
        return {t: n for t, n in allocation.items() if n > 0}

    # ===== 图片生成（含兜底） =====

    def _generate_version_images_with_fallback(
        self, provider, image_plan: list[dict], scene_style: dict
    ) -> list[dict]:
        """逐张生成图片；单张失败时用占位图兜底，保证该版本不丢图。"""
        images = []
        for i, img_desc in enumerate(image_plan):
            try:
                img_url = provider.generate_image(
                    img_desc.get("prompt", ""),
                    theme=img_desc.get("theme", ""),
                    scene_style=scene_style,
                )
                if not img_url:
                    raise ValueError("生成图片返回空 URL")
                images.append({
                    "url": img_url,
                    "caption": img_desc.get("caption", f"配图 {i + 1}"),
                    "theme": img_desc.get("theme", ""),
                    "type": img_desc.get("type", ""),
                })
            except Exception:
                fb = self._generate_fallback_image(img_desc, i)
                if fb:
                    images.append(fb)
        return images

    @staticmethod
    def _generate_fallback_image(img_desc: dict, index: int) -> dict:
        """provider 不可用时的最后保障：返回占位图条目。"""
        return {
            "url": PLACEHOLDER_IMAGE_URL,
            "caption": img_desc.get("caption", f"配图 {index + 1}"),
            "theme": img_desc.get("theme", ""),
            "type": img_desc.get("type", ""),
        }

    @staticmethod
    def _parse_image_plan(raw: str) -> Optional[list[dict]]:
        """解析 LLM 返回的配图方案 JSON（增强版字段更多）。"""
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
                            "source_paragraph_index": item.get("source_paragraph_index", -1),
                            "source_text": item.get("source_text", ""),
                            "relevance": item.get("relevance", ""),
                        })
                return result if result else None
        except (json.JSONDecodeError, IndexError, KeyError):
            pass
        return None

    @staticmethod
    def _parse_json_safely(raw: str, default: dict = None) -> dict:
        """安全解析 JSON。"""
        try:
            text = raw.strip()
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
            return json.loads(text)
        except Exception:
            return default or {}
