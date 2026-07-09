"""SEO 分析模块：对营销文案做规则化 SEO 评估（加分项）。

对应需求加分项：「接入 SEO 分析，为生成的文案提供 SEO 优化建议」。

采用规则引擎而非 LLM：
- 确定性强、可测试、零成本、开箱即用
- 检查维度：标题长度、正文字数、标题层级、关键词命中与密度、
  行动号召(CTA)、量化数据、可读性(平均句长)、meta 描述建议
- 输出 0-100 评分 + 分级建议(good/warning/error) + 关键词 + 统计

后续可在此基础上叠加 LLM 生成更口语化的优化建议，但规则层本身已能给出
具体、可执行的改进点。
"""
import re

# 无意义字：出现在 2-gram 首尾时跳过，避免"的了""我们"等被当成关键词
_STOPCHARS = set("的了在是和与及或我们你他这那有对于为以而地把被让")


def _extract_keywords(text: str, top_n: int = 5) -> list[str]:
    """提取中文 2-gram 关键词，按频次降序取前 top_n。

    思路：把文本切成"中文/字母/数字"片段，对每个片段取相邻 2 字组合，
    统计频次。2-gram 比"分词"简单且无需词典，对短营销文案够用。
    """
    tokens = re.findall(r"[A-Za-z0-9一-龥]+", text)
    freq: dict[str, int] = {}
    for tok in tokens:
        if len(tok) >= 2:
            for i in range(len(tok) - 1):
                g = tok[i:i + 2]
                # 首尾任一是停用字、或纯数字（如价格里的"00"）则跳过
                if g[0] in _STOPCHARS or g[1] in _STOPCHARS or g.isdigit():
                    continue
                freq[g] = freq.get(g, 0) + 1
        else:
            freq[tok] = freq.get(tok, 0) + 1
    ranked = sorted(freq.items(), key=lambda x: -x[1])
    return [k for k, _ in ranked[:top_n]]


def analyze(title: str, body: str) -> dict:
    """分析文案的 SEO 友好度。

    返回：{"score": 0-100, "suggestions": [...], "keywords": [...], "stats": {...}}
    """
    title = title or ""
    body = body or ""
    suggestions: list[tuple[str, str, str]] = []   # (type, level, message)
    stats: dict = {}

    title_len = len(title)
    body_len = len(body)
    stats["title_length"] = title_len
    stats["body_length"] = body_len

    # 1. 标题长度（中文理想 15-30 字）
    if title_len == 0:
        suggestions.append(("title", "error", "标题为空，搜索引擎无法索引"))
    elif title_len < 10:
        suggestions.append(("title", "warning", f"标题仅 {title_len} 字，建议 15-30 字并覆盖核心关键词"))
    elif title_len > 35:
        suggestions.append(("title", "warning", f"标题 {title_len} 字偏长，搜索结果可能截断，建议精简到 30 字内"))
    else:
        suggestions.append(("title", "good", "标题长度合适"))

    # 2. 正文字数
    if body_len == 0:
        suggestions.append(("content", "error", "正文为空"))
    elif body_len < 150:
        suggestions.append(("content", "warning", f"正文仅 {body_len} 字，内容偏薄，建议 300 字以上"))
    else:
        suggestions.append(("content", "good", f"正文字数 {body_len}，内容充实"))

    # 3. 标题层级（Markdown # 小标题）
    h_count = len(re.findall(r"^#{1,6}\s", body, re.M))
    stats["headings"] = h_count
    if h_count == 0 and body_len > 150:
        suggestions.append(("structure", "warning", "正文缺少小标题(##)，建议分层提升可读性与结构化"))
    elif h_count >= 2:
        suggestions.append(("structure", "good", f"正文有 {h_count} 个小标题，结构清晰"))

    # 4. 关键词命中
    keywords = _extract_keywords(title + " " + body)
    stats["keywords"] = keywords
    if keywords:
        top_kw = keywords[0]
        if top_kw in title:
            suggestions.append(("keyword", "good", f"核心关键词「{top_kw}」出现在标题中，利于排名"))
        else:
            suggestions.append(("keyword", "warning", f"核心关键词「{top_kw}」未出现在标题中，建议写入标题"))

    # 5. 关键词密度（防堆砌）
    if keywords and body_len:
        top_kw = keywords[0]
        occ = body.count(top_kw)
        density = occ / body_len * 100
        stats["keyword_density"] = round(density, 2)
        if density > 5:
            suggestions.append(("keyword", "warning", f"关键词「{top_kw}」密度 {density:.1f}% 偏高，注意避免堆砌"))

    # 6. 行动号召 CTA
    has_cta = bool(re.search(r"立即|体验|咨询|申请|试用|下载|注册|购买|联系|报名|了解", body))
    stats["has_cta"] = has_cta
    if has_cta:
        suggestions.append(("content", "good", "正文包含行动号召(CTA)，利于转化"))
    else:
        suggestions.append(("content", "warning", "正文缺少行动号召(CTA)，建议加入引导语"))

    # 7. 量化数据
    has_data = bool(re.search(r"\d+%|\d+万|\d+亿|\d+元|\d+\s*人|\d+\s*倍", body))
    stats["has_data"] = has_data
    if has_data:
        suggestions.append(("content", "good", "正文包含量化数据，增强可信度"))
    else:
        suggestions.append(("content", "warning", "正文缺少量化数据，建议补充数字佐证"))

    # 8. 可读性：平均句长
    sentences = [s for s in re.split(r"[。！？\n]", body) if s.strip()]
    avg_len = (sum(len(s) for s in sentences) / len(sentences)) if sentences else 0
    stats["avg_sentence_length"] = round(avg_len, 1)
    if avg_len > 80:
        suggestions.append(("readability", "warning", f"平均句长 {avg_len:.0f} 字偏长，建议拆分长句"))
    elif sentences:
        suggestions.append(("readability", "good", "句长适中，易于阅读"))

    # 9. meta 描述建议（正文前 80 字去空白）
    stats["meta_description"] = re.sub(r"\s+", " ", body).strip()[:80]

    # 评分：基准 60 分，good +5 / warning -4 / error -15，夹到 [0,100]
    score = 60
    for _, level, _ in suggestions:
        if level == "good":
            score += 5
        elif level == "warning":
            score -= 4
        elif level == "error":
            score -= 15
    score = max(0, min(100, score))

    return {
        "score": score,
        "suggestions": [{"type": t, "level": l, "message": m} for t, l, m in suggestions],
        "keywords": keywords,
        "stats": stats,
    }
