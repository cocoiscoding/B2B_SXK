"""LLM Provider：双模式切换（对话 + 文生图）。

本模块封装了大语言模型（LLM）的调用，提供两种模式：
1. MockLLMProvider：本地模拟，无需 API Key，开箱即用
2. OpenAICompatibleProvider：调用真实 LLM API（通义千问/DeepSeek/GLM 等）

通过 config.LLM_ENABLED 自动选择（配置了 API_KEY 就用真实 LLM，否则用 Mock）。

为什么需要双模式？
- 开发/测试环境：不想花钱调 API，用 Mock 模式快速验证
- 生产环境：配置 API_KEY 获得真正的 AI 生成能力

核心方法：
- chat()：对话生成（用于内容生成 Agent）
- generate_image() / generate_qwen_image()：文生图（用于配图 Agent）
"""
import hashlib
import base64
import io
import time
import httpx   # HTTP 客户端库，类似 requests 但支持异步
from config import (
    LLM_API_KEY, LLM_BASE_URL, LLM_MODEL, LLM_TIMEOUT, LLM_ENABLED,
)


class LLMProvider:
    """LLM 统一接口（抽象基类）。

    所有 Provider 都要实现：
    - chat()：对话生成
    - generate_image() / generate_qwen_image()：文生图
    """

    def chat(self, system_prompt: str, user_prompt: str, temperature: float = 0.8) -> str:
        """对话生成。

        参数：
            system_prompt: 系统提示词（设定 AI 的角色和规则）
            user_prompt: 用户输入（具体任务）
            temperature: 温度参数（0-1，越高越随机，越低越确定）

        返回：AI 生成的文本
        """
        raise NotImplementedError


    def generate_image(self, prompt: str, theme: str = "", scene_style: dict = None) -> str:
        """文生图（加分项）：根据提示词生成配图，返回图片 URL 或 data URL。

        参数：
            prompt: 画面描述（通常用文案标题 + 卖点）
            theme: 主题（如渠道名），用于决定配色
            scene_style: 场景风格配置，包含 aspect/style/elements/color_hint
        """
        raise NotImplementedError

    def generate_qwen_image(
        self, prompt: str, size: str = "1024x1024", n: int = 1, **kwargs
    ) -> list[dict]:
        """通义千问/万相 文生图专用接口。

        这是为对接千问生图大模型预留的专用方法，与 generate_image 不同的是：
        - 返回结构化数据而非单 URL
        - 支持尺寸/数量/seed 等 Qwen 特有参数
        - 不做 SVG 降级（失败就该让上层知道）
        - 后续接真实千问 API 时直接改此方法即可

        参数：
            prompt: 图片描述
            size: 图片尺寸，如 "1024x1024"、"1024x576"、"720x1280"
            n: 生成数量（1-4）
            **kwargs: Qwen 扩展参数，如 style、seed 等

        返回：
            [{"url": str | None, "b64_json": str | None, "prompt": str}, ...]
            每张图一个元素，url 和 b64_json 至少有一个不为 None
        """
        raise NotImplementedError

    @property
    def name(self) -> str:
        """Provider 名称（用于日志和展示）。"""
        raise NotImplementedError

    @property
    def is_mock(self) -> bool:
        """是否 mock/占位 provider（非真实 LLM）。

        Agent 据此选择"调 LLM"还是"走模板/规则兜底"，替代原先字符串比较
        provider.name。真实 provider 走默认 False，MockLLMProvider 覆盖为 True。
        """
        return False


class MockLLMProvider(LLMProvider):
    """本地 Mock：不调用真实 API，用模板/哈希模拟。

    优点：无需联网、无需 API Key、响应快
    缺点：生成质量有限，向量只是伪向量

    适用场景：开发调试、功能演示
    """

    @property
    def name(self) -> str:
        return "mock-engine"

    @property
    def is_mock(self) -> bool:
        return True

    def chat(self, system_prompt: str, user_prompt: str, temperature: float = 0.8) -> str:
        """Mock 对话：返回占位响应。

        真正的生成逻辑由各 Agent 内部的模板函数完成。
        """
        return f"[mock-llm] 已收到生成请求，将由模板引擎处理。"


    def generate_image(self, prompt: str, theme: str = "", scene_style: dict = None) -> str:
        """Mock 文生图：生成主题化 SVG 占位图（即时、无需联网）。"""
        return _build_svg_image(prompt, theme, scene_style)

    def generate_qwen_image(
        self, prompt: str, size: str = "1024x1024", n: int = 1, **kwargs
    ) -> list[dict]:
        """Mock 千问文生图：生成 n 张 Pillow 占位图。"""
        results = []
        for i in range(n):
            b64 = _build_svg_image(prompt, theme=kwargs.get("style", ""))
            results.append({"url": None, "b64_json": b64, "prompt": prompt})
        return results


class OpenAICompatibleProvider(LLMProvider):
    """OpenAI 兼容 Chat Completions 客户端。

    兼容所有 OpenAI 格式的 API：通义千问、DeepSeek、智谱 GLM、Moonshot 等。

    使用 httpx.Client 发送 HTTP 请求：
    - POST /chat/completions：对话生成
    """

    def __init__(self) -> None:
        # 对话客户端（DeepSeek 等）与向量客户端（通义千问等）独立：
        # 它们可能是不同供应商，base_url / key / model 各不相同
        self._client = httpx.Client(timeout=LLM_TIMEOUT)

    @property
    def name(self) -> str:
        return f"llm:{LLM_MODEL}"

    def chat(self, system_prompt: str, user_prompt: str, temperature: float = 0.8) -> str:
        """调用 Chat Completions API 生成文本。

        对 429（限流）和超时做最多 2 次重试（1.5s / 3s 退避），仍失败才抛异常。
        异常会被 BaseAgent.execute 捕获，转成 error 步骤，不中断整条 Agent 链。
        """
        url = f"{LLM_BASE_URL.rstrip('/')}/chat/completions"
        headers = {
            "Authorization": f"Bearer {LLM_API_KEY}",    # Bearer Token 认证
            "Content-Type": "application/json",
        }
        payload = {
            "model": LLM_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},   # 系统角色
                {"role": "user", "content": user_prompt},       # 用户角色
            ],
            "temperature": temperature,
        }
        last_exc: Exception | None = None
        for attempt in range(3):    # 初试 + 最多 2 次重试
            try:
                resp = self._client.post(url, json=payload, headers=headers)
                resp.raise_for_status()    # 非 2xx 抛 HTTPStatusError
                return resp.json()["choices"][0]["message"]["content"]
            except (httpx.HTTPStatusError, httpx.TimeoutException) as e:
                last_exc = e
                # 仅对 429 限流 / 超时 重试；其它（如 401 鉴权失败）立即抛
                retryable = isinstance(e, httpx.TimeoutException) or (
                    isinstance(e, httpx.HTTPStatusError) and e.response.status_code == 429
                )
                if not retryable or attempt == 2:
                    raise
                time.sleep(1.5 * (attempt + 1))   # 退避：1.5s、3s
        raise last_exc    # 理论上不可达


    def generate_image(self, prompt: str, theme: str = "", scene_style: dict = None) -> str:
        """真实文生图：调用图像生成 API，失败则回退到 SVG 占位图。

        兼容 OpenAI 格式 /images/generations（通义万相 wanx、DALL-E 等）。
        响应可能返回 url 或 b64_json，任一可用即返回；否则回退 SVG。
        任何异常（API 不支持 / 网络 / 格式不符）都回退，绝不阻断生成流程。

        优化：将 scene_style 中的风格描述、元素、色调建议注入 prompt，
        让生成的图片更符合场景定位。
        """
        # 增强 prompt：融入场景风格描述
        if scene_style:
            style_desc = scene_style.get("style", "")
            elements = scene_style.get("elements", "")
            color_hint = scene_style.get("color_hint", "")
            style_extra = f"。风格：{style_desc}，元素：{elements}，色调：{color_hint}"
        else:
            style_extra = ""

        enhanced_prompt = prompt + style_extra if style_extra else prompt

        url = f"{LLM_BASE_URL.rstrip('/')}/images/generations"
        headers = {
            "Authorization": f"Bearer {LLM_API_KEY}",
            "Content-Type": "application/json",
        }
        # 根据场景风格调整尺寸
        aspect = scene_style.get("aspect", "") if scene_style else ""
        if "横幅" in aspect:
            size = "1024x576"  # 16:9 横幅
        elif "封面" in aspect:
            size = "1024x1024"  # 正方形封面
        else:
            size = "1024x1024"  # 默认正方形

        payload = {"model": "wanx2.1-t2i-turbo", "prompt": enhanced_prompt, "n": 1, "size": size}
        try:
            resp = self._client.post(url, json=payload, headers=headers, timeout=LLM_TIMEOUT)
            resp.raise_for_status()
            data = resp.json()
            items = data.get("data") or []
            if items:
                item = items[0]
                if item.get("b64_json"):
                    return f"data:image/png;base64,{item['b64_json']}"
                if item.get("url"):
                    return item["url"]
        except Exception:
            pass  # 静默回退：图像 API 不可用时用 SVG 占位
        return _build_svg_image(prompt, theme, scene_style)

    def generate_qwen_image(
        self, prompt: str, size: str = "1024x1024", n: int = 1, **kwargs
    ) -> list[dict]:
        """通义千问/万相 文生图专用接口。

        调用 OpenAI-compatible /images/generations 端点。
        与 generate_image 的不同：
        - 不做 SVG 降级，失败直接抛异常（让上层决策如何处理）
        - 支持 n>1 批量生图
        - 支持 seed/style 等 Qwen 扩展参数
        - 返回结构化列表而非单 URL

        后续接千问原生 API 时，改写此方法即可，调用方不受影响。
        """
        url = f"{LLM_BASE_URL.rstrip('/')}/images/generations"
        headers = {
            "Authorization": f"Bearer {LLM_API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": kwargs.get("model", "wanx2.1-t2i-turbo"),
            "prompt": prompt,
            "n": min(n, 4),  # 千问单次最多 4 张
            "size": size,
        }
        # 可选参数透传
        for key in ("seed", "style"):
            if key in kwargs:
                payload[key] = kwargs[key]

        resp = self._client.post(url, json=payload, headers=headers, timeout=LLM_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        items = data.get("data") or []
        if not items:
            raise RuntimeError(f"千问生图返回空结果: {data}")

        results = []
        for item in items:
            result = {"url": None, "b64_json": None, "prompt": prompt}
            if item.get("b64_json"):
                result["b64_json"] = f"data:image/png;base64,{item['b64_json']}"
            if item.get("url"):
                result["url"] = item["url"]
            results.append(result)
        return results


# ===== 文生图 SVG 占位图生成器（Mock / 回退共用）=====

# 配色调色板：渐变起止色，按主题哈希选择，保证同一内容配色稳定
_IMAGE_PALETTES = [
    ("#1a2a6c", "#fdbb2d"),
    ("#0f4c5c", "#5f0f40"),
    ("#2b5876", "#4e4376"),
    ("#1488cc", "#2b32b2"),
    ("#ff8008", "#ffc837"),
    ("#11998e", "#38ef7d"),
]


def _build_svg_image(prompt: str, theme: str = "", scene_style: dict = None) -> str:
    """生成场景化 PNG 配图，返回 base64 data URL。

    用 Pillow 绘制渐变背景 + 装饰圆 + 标题文字，输出 PNG。
    PNG 可被前端 <img> 和 docx add_picture 直接消费，无需 SVG 转换。
    （函数名保留历史命名，曾生成 SVG。）
    """
    from PIL import Image, ImageDraw, ImageFont

    # 按主题哈希选配色
    key = (theme or prompt or "default").encode("utf-8")
    idx = int(hashlib.md5(key).hexdigest(), 16) % len(_IMAGE_PALETTES)
    c1, c2 = _IMAGE_PALETTES[idx]
    c1_rgb = _hex_to_rgb(c1)
    c2_rgb = _hex_to_rgb(c2)

    # 解析场景风格 -> 尺寸 + 标题位置
    aspect = scene_style.get("aspect", "产品展示") if scene_style else "产品展示"
    style_desc = scene_style.get("style", "") if scene_style else ""
    if "横幅" in aspect:
        w, h, ty, sy = 800, 450, 200, 260
    elif "封面" in aspect or "社交" in aspect:
        w, h, ty, sy = 600, 600, 280, 340
    else:
        w, h, ty, sy = 800, 600, 280, 340

    # 渐变背景（逐行插值）
    img = Image.new("RGB", (w, h))
    draw = ImageDraw.Draw(img)
    for y in range(h):
        t = y / max(h - 1, 1)
        r = int(c1_rgb[0] + (c2_rgb[0] - c1_rgb[0]) * t)
        g = int(c1_rgb[1] + (c2_rgb[1] - c1_rgb[1]) * t)
        b = int(c1_rgb[2] + (c2_rgb[2] - c1_rgb[2]) * t)
        draw.line([(0, y), (w, y)], fill=(r, g, b))

    # 装饰圆（半透明，在 RGBA overlay 上画再合成到背景）
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    od.ellipse([20, 20, 160, 160], fill=(255, 255, 255, 28))
    od.ellipse([w - 180, h - 180, w - 20, h - 20], fill=(255, 255, 255, 22))
    if "社交" in aspect:
        od.ellipse([80, 80, 180, 180], fill=(255, 107, 107, 50))
        od.ellipse([w - 200, 100, w - 120, 180], fill=(78, 205, 196, 50))
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(img)

    # 标题 + 副标题
    title = (prompt or "营销配图").strip()[:20]
    subtitle = style_desc[:30] if style_desc else "神行库 · AI 营销配图"

    # 中文字体（Windows 微软雅黑），失败用默认
    try:
        font_t = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 36)
        font_s = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 16)
    except Exception:
        font_t = ImageFont.load_default()
        font_s = ImageFont.load_default()

    _draw_centered(draw, title, w // 2, ty, font_t, (255, 255, 255))
    _draw_centered(draw, subtitle, w // 2, sy, font_s, (255, 255, 255))

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    return f"data:image/png;base64,{b64}"


def _hex_to_rgb(h: str) -> tuple:
    """十六进制颜色转 RGB 元组，如 '#1a2a6c' -> (26, 42, 108)。"""
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _draw_centered(draw, text: str, cx: int, y: int, font, fill) -> None:
    """在 (cx, y) 水平居中绘制文字。"""
    try:
        bbox = draw.textbbox((0, 0), text, font=font)
        tw = bbox[2] - bbox[0]
    except Exception:
        tw = len(text) * 20
    draw.text((max(0, cx - tw // 2), y), text, font=font, fill=fill)


# Provider 单例：整个应用共享一个实例，避免每次 chat 新建 httpx.Client
_provider_instance: LLMProvider | None = None


def get_provider() -> LLMProvider:
    """根据配置选择 Provider（单例模式）。

    配置了 LLM_API_KEY → 返回真实 LLM Provider
    未配置             → 返回 Mock Provider
    """
    global _provider_instance
    if _provider_instance is None:
        if LLM_ENABLED:
            _provider_instance = OpenAICompatibleProvider()
        else:
            _provider_instance = MockLLMProvider()
    return _provider_instance