"""Agent 基类：统一执行接口与链路追踪。

本模块定义了所有 Agent 的基类和共享上下文。

设计模式：
- 模板方法模式：BaseAgent.execute() 定义执行框架，子类只需实现 _execute()
- 上下文对象：AgentContext 在多个 Agent 间传递中间结果

什么是 Agent？
→ Agent 是一个能独立完成某项任务的智能体。
  本系统有 5 个 Agent 串行协作：
  检索 → 竞品分析 → 生成 → 渠道适配 → 校验
"""
import time
from dataclasses import dataclass, field
from typing import Any


# @dataclass 装饰器：自动生成 __init__、__repr__ 等方法
# 相当于一个只有数据没有逻辑的类，适合做数据容器
@dataclass
class AgentContext:
    """Agent 链路共享上下文。

    这个对象在所有 Agent 间流转，每个 Agent 读取上游产物、写入自己的产物。
    就像流水线上的工件，每经过一道工序就多一些东西。
    """
    # ===== 输入参数（由 orchestrator 设置）=====
    product: dict[str, Any] = field(default_factory=dict)       # 产品信息
    scenario: dict[str, Any] = field(default_factory=dict)      # 场景模板
    channel: str = "官网"                                       # 目标渠道
    style: str = "专业严谨"                                     # 文案风格
    params: dict[str, Any] = field(default_factory=dict)        # 用户填写的参数
    version_count: int = 3                                      # 生成版本数

    # ===== 中间产物（各 Agent 写入，供下游读取）=====
    retrieved_info: dict[str, Any] = field(default_factory=dict)    # 检索 Agent 的产物
    draft_versions: list[dict[str, Any]] = field(default_factory=list)  # 生成 Agent 的初稿
    versions: list[dict[str, Any]] = field(default_factory=list)    # 渠道适配后的最终版
    competitor_info: dict[str, Any] = field(default_factory=dict)   # 竞品分析产物
    # 返工反馈：校验失败时由 orchestrator 写入上次的问题，供 GenerationAgent 下次生成时规避
    feedback_issues: list[str] = field(default_factory=list)

class BaseAgent:
    """所有 Agent 的抽象基类。

    子类只需实现 _execute() 方法，execute() 会自动处理：
    - 计时
    - 异常捕获
    - 返回标准化的执行步骤字典
    """

    # 类属性：所有实例共享，子类覆盖
    name: str = "BaseAgent"
    description: str = ""

    def __init__(self, llm=None):
        # LLM Provider 实例，用于调用大模型
        self._llm = llm

    def _execute(self, ctx: AgentContext) -> tuple[str, str, Any]:
        """子类实现：执行具体逻辑，返回 (status, message, output)。

        - status: "success" / "warning" / "error"
        - message: 执行信息（展示给用户）
        - output: 输出数据（存入执行链路）
        """
        raise NotImplementedError   # 基类不实现，强制子类重写

    def execute(self, ctx: AgentContext) -> dict[str, Any]:
        """执行 Agent 并返回标准化的步骤字典。

        这个方法不需要子类重写，它包装了 _execute()，添加了：
        - 计时功能
        - 异常捕获（出错也返回标准结构，不会中断整个流程）
        """
        start = time.time()
        try:
            # 调用子类实现的 _execute
            status, message, output = self._execute(ctx)
            duration = int((time.time() - start) * 1000)    # 耗时（毫秒）
            return {
                "agent": self.name,
                "status": status,
                "message": message,
                "duration_ms": duration,
                "output": output,
            }
        except Exception as e:
            # 出错时也返回标准结构，而不是抛异常中断整个流程
            duration = int((time.time() - start) * 1000)
            return {
                "agent": self.name,
                "status": "error",
                "message": f"{type(e).__name__}: {e}",
                "duration_ms": duration,
                "output": None,
            }