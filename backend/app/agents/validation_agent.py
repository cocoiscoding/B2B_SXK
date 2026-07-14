"""内容校验 Agent：检查生成内容的参数一致性与完整性。

这是多 Agent 链路的第 5 个（最后一个）Agent。

校验项：
1. 产品名称一致性：内容中是否出现正确的产品名
2. 关键参数校验：定价是否与知识库一致
3. 敏感词检查：过滤"第一""最"等绝对化用词（违反广告法）
4. 卖点覆盖：内容是否包含至少 1 个核心卖点

对应需求：F3-5 内容校验 Agent
"""
import re
from app.agents.base import BaseAgent, AgentContext

# 敏感词/绝对化用语：违反《广告法》第九条等。
# 注意：不能用裸 "最"/"第一" 做子串匹配，否则 "最后/最终/最近/第一天/第一步" 等合法用法会误报，
# 导致几乎所有文案校验失败、触发重试放大 LLM 调用。这里用正则匹配真正的绝对化用法。
SENSITIVE_PATTERNS = [
    # "最" + 褒义最高级形容词（最后/最终/最近 等不含这些字，不会命中）
    r"最(?:好|佳|强|优|大|高|低|快|新|先进|优惠|划算|安全|稳定|专业|权威|完美|低廉|便宜|受欢迎)",
    # 排名/地位绝对化：行业第一、全国第一、销量第一 ……
    r"(?:行业|全国|全网|全球|销量|市场|国内|国际|品类)第[一二三四五六七八九十]",
    # 第一品牌 / 第一名 / 第一名牌
    r"第[一二三四五六七八九十](?:品牌|名牌|名)",
    r"国家级",
    r"唯一",
    r"绝对",
    r"100%",
    r"包治",
    # 其他常见绝对化用语
    r"(?:顶级|极品|万能|之王|之最|巅峰|首选)",
]
# 给生成 Agent 的可读提示（与 SENSITIVE_PATTERNS 表达同一组约束，同步维护）
SENSITIVE_WORDS_HINT = "最好/最佳/最强/最优、行业第一/第一品牌、国家级、唯一、绝对、100%、包治、顶级/极品/万能"

# 方向类参数名（如竞品对比的 focus「对比重点」）：这类参数的值是"整体方向/重点"，
# 应作为各版本共同展开的背景，而非每版必须原样包含的词--否则会与各版差异化维度(dim)
# 冲突、把版本差异抹平（focus 值常与某 dim 重叠，如"功能全面性"）。标识类参数
# （如 competitor 竞品名）仍要求原样包含。生成端(_format_hard_requirements)与
# 校验端(_check_constraints)共用此集合。
DIRECTIONAL_PARAMS = {"focus"}


class ValidationAgent(BaseAgent):
    """内容校验 Agent。"""

    name = "内容校验 Agent"
    description = "校验生成内容与产品知识库的一致性，检测敏感词与信息完整性。"

    def _execute(self, ctx: AgentContext) -> tuple[str, str, dict]:
        """执行内容校验（批量：所有版本拼接统一检查，供老 run() 流程兼容）。

        返回 (status, message, {"issues": [...], "validated": bool})
        """
        # 优先取适配后的版本，没有则取初稿
        versions = ctx.versions or ctx.draft_versions
        all_text = " ".join(v.get("body", "") + v.get("title", "") for v in versions)
        issues = self._collect_issues(all_text, versions, ctx.retrieved_info, ctx.params, ctx.scenario)
        status = "success" if not issues else "warning"
        msg = "校验通过，内容与知识库一致" if not issues else f"发现 {len(issues)} 项需关注的问题"
        return status, msg, {"issues": issues, "validated": len(issues) == 0}

    def validate_single(self, version: dict, ctx: AgentContext) -> dict:
        """校验单个版本，返回 {"issues": [...], "validated": bool}。

        供 orchestrator 逐版本生成时调用：每个版本独立校验，卖点覆盖/字数等约束
        均按单版本维度判定（每版都要满足），比批量"任一版本满足即过"更严。
        """
        all_text = version.get("body", "") + version.get("title", "")
        issues = self._collect_issues(all_text, [version], ctx.retrieved_info, ctx.params, ctx.scenario)
        return {"issues": issues, "validated": len(issues) == 0}

    def _collect_issues(self, all_text: str, versions: list, info: dict, params: dict, scenario: dict) -> list[str]:
        """汇总 5 类校验问题（产品名/定价/敏感词/卖点覆盖/模板 constraints）。

        all_text 与 versions 由调用方决定：批量校验传全版本拼接文本，
        单版本校验传单版本文本 + [version]。
        """
        issues: list[str] = []
        product_name = info.get("product_name", "")
        pricing = info.get("pricing", "")
        sp = info.get("selling_points", [])

        # 校验 1：产品名称是否出现
        if product_name and product_name not in all_text:
            issues.append(f"⚠ 内容中未出现正确的产品名称「{product_name}」")

        # 校验 2：定价一致性
        if pricing:
            # 正则提取价格（如 ¥50,000）
            price_nums = re.findall(r"¥[\d,]+", all_text)
            kb_price = re.findall(r"¥[\d,]+", pricing)
            if kb_price and price_nums:
                # 内容中的价格必须都在知识库中
                if not all(p in kb_price for p in price_nums):
                    issues.append(f"⚠ 内容中的价格与知识库不一致（知识库：{kb_price}）")

        # 校验 3：敏感词（正则匹配绝对化用法，避免 "最后/第一天" 等合法用法误报）
        found_sensitive: list[str] = []
        for pattern in SENSITIVE_PATTERNS:
            m = re.search(pattern, all_text)
            if m and m.group() not in found_sensitive:
                found_sensitive.append(m.group())
        if found_sensitive:
            issues.append(f"⚠ 检测到敏感/绝对化用词：{', '.join(found_sensitive)}，建议修改")

        # 校验 4：卖点覆盖
        if sp:
            covered = [s for s in sp if s in all_text]
            if not covered:
                issues.append("⚠ 内容未覆盖任何知识库中的核心卖点")

        # 校验 5：模板结构化约束（字数 / 必含参数 / 最少卖点等，由模板 constraints 驱动）
        constraints = scenario.get("template_constraints") or {}
        issues.extend(self._check_constraints(versions, constraints, params, info, all_text))

        return issues

    # ===== 模板结构化约束校验 =====

    def _check_constraints(self, versions, constraints, params, info, all_text):
        """按模板 constraints 做机械校验，返回问题列表。

        支持的约束：
        - title_max_chars(int)：每个版本标题字符数上限
        - body_chars([min, max])：正文纯文字字数区间（min=0 表示只限上限）
        - must_include_params(list[str])：用户填写的这些参数值必须出现在内容中
        - min_selling_points(int)：至少覆盖几个核心卖点
        """
        issues: list[str] = []
        if not constraints:
            return issues

        title_max = constraints.get("title_max_chars")
        body_range = constraints.get("body_chars")
        must_params = constraints.get("must_include_params", [])
        min_sp = constraints.get("min_selling_points")

        # 逐版本检查标题与正文字数
        for v in versions:
            idx = v.get("index", "?")
            title = v.get("title", "")
            body = v.get("body", "")

            if isinstance(title_max, int) and title_max > 0 and len(title) > title_max:
                issues.append(f"⚠ 版本{idx} 标题 {len(title)} 字，超过模板上限 {title_max} 字")

            if isinstance(body_range, list) and len(body_range) == 2:
                lo, hi = body_range
                n = self._plain_char_count(body)
                if isinstance(lo, int) and lo > 0 and n < lo:
                    issues.append(f"⚠ 版本{idx} 正文 {n} 字，少于模板要求 {lo} 字")
                if isinstance(hi, int) and hi > 0 and n > hi:
                    issues.append(f"⚠ 版本{idx} 正文 {n} 字，超过模板上限 {hi} 字")

        # 必含参数：用户填写的参数值必须出现在内容中
        # 只检查非空且较短的值（≤50 字），长描述性参数允许 LLM 改写
        # 方向类参数（如 focus 对比重点）跳过--它与各版 dim 冲突，强制每版包含会把
        # 版本差异抹平（见 DIRECTIONAL_PARAMS）；标识类参数（如 competitor）仍校验
        if must_params and params:
            for name in must_params:
                if name in DIRECTIONAL_PARAMS:
                    continue
                val = params.get(name)
                if val and len(str(val)) <= 50 and str(val) not in all_text:
                    issues.append(f"⚠ 内容未包含用户指定的「{name}」：{val}")

        # 最少卖点覆盖
        if isinstance(min_sp, int) and min_sp > 0:
            sp = info.get("selling_points", [])
            if sp:
                covered = [s for s in sp if s in all_text]
                if len(covered) < min_sp:
                    issues.append(f"⚠ 内容仅覆盖 {len(covered)} 个核心卖点，模板要求至少 {min_sp} 个")

        return issues

    @staticmethod
    def _plain_char_count(text: str) -> int:
        """统计正文字数：去掉 markdown 符号与空白，按字符计。"""
        cleaned = re.sub(r"[#*\->|`\s]", "", text or "")
        return len(cleaned)