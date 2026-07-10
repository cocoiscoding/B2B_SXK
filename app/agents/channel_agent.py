"""渠道适配 Agent：将生成内容按目标渠道调整风格与排版。

这是多 Agent 链路的第 4 个 Agent。

设计原则：
- 通用性：渠道配置存储在数据库 channels 表中，新增渠道只需 INSERT 无需改代码
- LLM 模式：通过提示词按渠道语气自适应改写
- Mock 模式：根据渠道属性（emoji/format）做组合式规则变换，与渠道名称解耦

渠道属性说明：
  - tone:   语气描述（如"亲切口语""专业正式"），LLM 模式使用，Mock 模式参考
  - emoji:  是否增加 emoji 点缀（标题 ✨、列表项 👉）
  - format: 排版格式（markdown / 短段落 / CTA导向 / bullet / short）
"""

import json
from app.agents.base import BaseAgent, AgentContext
from app.database import query_one

# 数据库无法访问时的兜底配置（极少发生，仅用于容错）
_FALLBACK_CHANNEL = {
    "name": "官网",
    "tone": "专业正式",
    "emoji": False,
    "format": "markdown",
}


def get_channel_config(channel_name: str) -> dict | None:
    """从数据库查询渠道配置，返回 None 表示渠道不存在。"""
    row = query_one(
        "SELECT name, tone, emoji, format, description FROM channels WHERE name = %s",
        (channel_name,),
    )
    return dict(row) if row else None


class ChannelAgent(BaseAgent):
    """渠道适配 Agent。"""

    name = "渠道适配 Agent"
    description = "根据目标渠道调整文案措辞与排版格式。"

    def _execute(self, ctx: AgentContext) -> tuple[str, str, list]:
        """执行渠道适配。

        从数据库读取渠道配置，按配置属性做适配：
        - LLM 模式：调用大模型按渠道语气改写
        - Mock 模式：根据渠道 emoji/format 属性组合规则变换
        """
        if not ctx.draft_versions:
            return "warning", "无初稿可适配", ctx.draft_versions

        channel = ctx.channel
        cfg = get_channel_config(channel)
        if cfg is None:
            return (
                "error",
                f"未知渠道「{channel}」，请在渠道管理中添加该渠道配置",
                ctx.draft_versions,
            )

        # 模板适用渠道检查：模板标注了 applicable_channels 时，实际渠道不在其中则告警（不阻断适配）
        applicable = ctx.scenario.get("template_applicable_channels") or []
        status = "success"
        warn_note = ""
        if applicable and channel not in applicable:
            status = "warning"
            warn_note = f"；⚠ 渠道「{channel}」不在模板适用渠道 {applicable} 内，产出可能不理想"

        use_llm = bool(self._llm) and self._llm.name != "mock-engine"
        if use_llm:
            adapted = [
                self._adapt_with_llm(v, channel, cfg) for v in ctx.draft_versions
            ]
            method = "LLM 改写"
        else:
            adapted = [
                self._adapt_rule(v, cfg, channel) for v in ctx.draft_versions
            ]
            method = "规则适配"

        ctx.versions = adapted
        return (
            status,
            f"已将文案适配至「{channel}」渠道"
            f"（{method}，风格：{cfg['tone']}）{warn_note}",
            adapted,
        )

    # ----- 多渠道适配（新流程：单版本 -> N 渠道，每渠道 1 版）-----

    def adapt_to_channels(
        self, version: dict, channels: list[str], scenario: dict
    ) -> tuple[list[dict], list[str]]:
        """把单个版本适配到多个渠道，每个渠道产出 1 个版本。

        与 _execute（一批版本 -> 单渠道）互补，本方法服务于交互式流程的阶段3：
        用户已选定 1 个版本，多选 N 个渠道 -> 产出 N 个渠道版本。

        返回 (适配后的版本列表, 跳过的未知渠道列表)。
        每个版本带 channel 字段标识归属；index 重新编号 1..N。
        模板标注了 applicable_channels 时，实际渠道不在其中则在该版本 tags 里告警（不阻断）。
        """
        results: list[dict] = []
        skipped: list[str] = []
        applicable = scenario.get("template_applicable_channels") or []

        for i, ch in enumerate(channels, 1):
            cfg = get_channel_config(ch)
            if cfg is None:
                skipped.append(ch)
                continue
            use_llm = bool(self._llm) and self._llm.name != "mock-engine"
            if use_llm:
                adapted = self._adapt_with_llm(version, ch, cfg)
            else:
                adapted = self._adapt_rule(version, cfg, ch)
            # 标识渠道归属 + 重新编号
            adapted["channel"] = ch
            adapted["index"] = i
            # 渠道不在模板适用范围 -> 在 tags 里告警（前端可见，不阻断适配）
            if applicable and ch not in applicable:
                tags = list(adapted.get("tags") or [])
                warn = f"⚠{ch}非模板适用渠道"
                if warn not in tags:
                    tags.append(warn)
                adapted["tags"] = tags
            results.append(adapted)
        return results, skipped

    # ----- LLM 改写 -----

    def _adapt_with_llm(self, version: dict, channel: str, cfg: dict) -> dict:
        """用 LLM 按渠道语气改写单个版本。

        严格要求保持产品名/定价/参数/卖点等事实不变。
        LLM 返回 JSON {title, body}；解析失败或异常则回退规则适配。
        """
        tone = cfg["tone"]
        sys_prompt = (
            "你是渠道文案适配专家。把营销文案改写为适合目标渠道发布的风格，"
            "严格保持产品名、定价、参数、卖点等事实不变，只调整语气与排版。输出 JSON。"
        )
        user_prompt = (
            f"目标渠道：{channel}（风格要求：{tone}）\n"
            f"原标题：{version.get('title', '')}\n"
            f"原正文：\n{version.get('body', '')}\n\n"
            f"请按「{channel}」渠道的阅读习惯改写语气与排版（{tone}），"
            "保留核心事实与 markdown 结构。只输出 JSON："
            '{"title":"...","body":"..."}'
        )
        try:
            raw = self._llm.chat(sys_prompt, user_prompt, temperature=0.5)
            parsed = self._parse_json(raw)
            if parsed:
                return {
                    "index": version.get("index", 1),
                    "title": parsed.get("title") or version.get("title", ""),
                    "body": parsed.get("body") or version.get("body", ""),
                    "tags": list(set(version.get("tags", []) + [channel])),
                }
        except Exception:
            pass
        # LLM 失败 → 回退规则适配
        return self._adapt_rule(version, cfg, channel)

    @staticmethod
    def _parse_json(raw: str) -> dict | None:
        """解析 LLM 返回的 {title, body} JSON，兼容 ```json 包裹。"""
        try:
            text = raw.strip()
            if text.startswith("```"):
                text = text.split("```", 2)[1]
                if text.startswith("json"):
                    text = text[4:]
            obj = json.loads(text)
            if isinstance(obj, dict) and ("title" in obj or "body" in obj):
                return obj
        except Exception:
            pass
        return None

    # ----- 通用规则适配（与渠道名称解耦，仅由属性驱动）-----

    def _adapt_rule(self, version: dict, cfg: dict, channel: str) -> dict:
        """通用规则适配：根据渠道属性（emoji/format）做组合变换，与渠道名无关。

        变换流水线（按顺序执行）：
        1. emoji=True → 标题加 ✨，列表项加 👉
        2. format 决定排版结构：
           - "markdown" → 保持原样
           - "短段落"   → 每段后加空行分隔（移动端友好）
           - "CTA导向"  → 正文后添加行动号召
           - "bullet"   → 标题转 ■，内容转 ·（PPT 要点风格）
           - "short"    → 截断为短文（取前 8 行）
        """
        body = version.get("body", "")

        # Step 1: emoji 点缀
        if cfg.get("emoji"):
            body = self._apply_emoji(body)

        # Step 2: format 排版
        fmt = cfg.get("format", "markdown")
        if fmt == "短段落":
            body = self._to_short_paragraphs(body)
        elif fmt == "CTA导向":
            body = self._add_cta(body, version.get("title", ""))
        elif fmt == "bullet":
            body = self._to_bullet(body)
        elif fmt == "short":
            body = self._truncate_short(body)

        return {
            "index": version.get("index", 1),
            "title": version.get("title", ""),
            "body": body,
            "tags": list(set(version.get("tags", []) + [channel])),
        }

    # ----- 原子变换函数（可组合）-----

    @staticmethod
    def _apply_emoji(body: str) -> str:
        """为标题和列表项添加 emoji 点缀（幂等：已有点缀的不重复加）。"""
        lines = body.split("\n")
        result = []
        for line in lines:
            stripped = line.strip()
            if not stripped:
                result.append("")
                continue
            if stripped.startswith("#"):
                # 标题加 ✨（跳过已有点缀的）
                if not stripped.lstrip("#").strip().startswith("✨"):
                    indent = line[: len(line) - len(line.lstrip())]
                    level = "#" * (len(stripped) - len(stripped.lstrip("#")))
                    content = stripped[len(level) + 1 :].strip() if " " in stripped else stripped[len(level) :].strip()
                    result.append(f"{indent}{level} ✨ {content}")
                else:
                    result.append(line)
            elif stripped.startswith("- ") or stripped.startswith("• "):
                # 列表项加 👉（跳过已有点缀的）
                prefix = stripped[:1]
                content = stripped[2:].strip()
                if not content.startswith("👉"):
                    result.append(f"{prefix} 👉 {content}")
                else:
                    result.append(line)
            else:
                result.append(line)
        return "\n".join(result)

    @staticmethod
    def _to_short_paragraphs(body: str) -> str:
        """转换为短段落风格：段落间加空行，适合移动端阅读。"""
        lines = body.split("\n")
        result = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            result.append(line)
            result.append("")
        return "\n".join(result).strip()

    @staticmethod
    def _add_cta(body: str, title: str) -> str:
        """CTA 导向：提取要点 + 结尾添加行动号召。"""
        lines = [
            l.strip()
            for l in body.split("\n")
            if l.strip() and not l.startswith("#") and not l.startswith("|") and not l.startswith(">")
        ][:5]
        return (
            f"主题：{title}\n\n"
            + "\n".join(lines)
            + "\n\n———\n立即申请试用 → 回复本邮件或访问官网\n"
        )

    @staticmethod
    def _to_bullet(body: str) -> str:
        """转换为要点风格：标题转 ■，内容转 ·。"""
        lines = body.split("\n")
        result = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if line.startswith("#"):
                result.append(f"\n■ {line.lstrip('# ').strip()}")
            elif not line.startswith("|") and not line.startswith("---"):
                result.append(f"  · {line.lstrip('-• ')}")
        return "\n".join(result)

    @staticmethod
    def _truncate_short(body: str, max_lines: int = 8) -> str:
        """截断为短文风格，适合微博等短内容平台。"""
        lines = [l for l in body.split("\n") if l.strip()]
        return "\n".join(lines[:max_lines])
