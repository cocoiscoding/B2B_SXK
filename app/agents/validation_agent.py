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

# 敏感词列表：绝对化用语违反《广告法》
SENSITIVE_WORDS = ["第一", "最", "国家级", "唯一", "绝对", "100%", "包治"]


class ValidationAgent(BaseAgent):
    """内容校验 Agent。"""

    name = "内容校验 Agent"
    description = "校验生成内容与产品知识库的一致性，检测敏感词与信息完整性。"

    def _execute(self, ctx: AgentContext) -> tuple[str, str, dict]:
        """执行内容校验。

        返回 (status, message, {"issues": [...], "validated": bool})
        """
        # 优先取适配后的版本，没有则取初稿
        versions = ctx.versions or ctx.draft_versions
        info = ctx.retrieved_info
        product_name = info.get("product_name", "")
        pricing = info.get("pricing", "")
        sp = info.get("selling_points", [])

        issues: list[str] = []
        # 把所有版本的标题和正文拼成一个字符串，便于统一检查
        all_text = " ".join(v.get("body", "") + v.get("title", "") for v in versions)

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

        # 校验 3：敏感词
        found_sensitive = [w for w in SENSITIVE_WORDS if w in all_text]
        if found_sensitive:
            issues.append(f"⚠ 检测到敏感/绝对化用词：{', '.join(found_sensitive)}，建议修改")

        # 校验 4：卖点覆盖
        if sp:
            covered = [s for s in sp if s in all_text]
            if not covered:
                issues.append("⚠ 内容未覆盖任何知识库中的核心卖点")

        # 校验 5：模板结构化约束（字数 / 必含参数 / 最少卖点等，由模板 constraints 驱动）
        constraints = ctx.scenario.get("template_constraints") or {}
        issues.extend(
            self._check_constraints(versions, constraints, ctx.params, info, all_text)
        )

        # 根据问题数量决定状态
        status = "success" if not issues else "warning"
        msg = "校验通过，内容与知识库一致" if not issues else f"发现 {len(issues)} 项需关注的问题"
        return status, msg, {"issues": issues, "validated": len(issues) == 0}

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
        if must_params and params:
            for name in must_params:
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