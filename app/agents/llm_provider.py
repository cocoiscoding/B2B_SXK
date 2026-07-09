"""LLM Provider：双模式切换 + Embedding 向量生成。

本模块封装了大语言模型（LLM）的调用，提供两种模式：
1. MockLLMProvider：本地模拟，无需 API Key，开箱即用
2. OpenAICompatibleProvider：调用真实 LLM API（通义千问/DeepSeek/GLM 等）

通过 config.LLM_ENABLED 自动选择（配置了 API_KEY 就用真实 LLM，否则用 Mock）。

为什么需要双模式？
- 开发/测试环境：不想花钱调 API，用 Mock 模式快速验证
- 生产环境：配置 API_KEY 获得真正的 AI 生成能力

两个核心方法：
- chat()：对话生成（用于内容生成 Agent）
- embed()：文本向量化（用于语义检索 Agent）
"""
import hashlib
import base64
import io
import time
import httpx   # HTTP 客户端库，类似 requests 但支持异步
from config import (
    LLM_API_KEY, LLM_BASE_URL, LLM_MODEL, LLM_TIMEOUT, LLM_ENABLED,
    EMBEDDING_API_KEY, EMBEDDING_BASE_URL, EMBEDDING_MODEL, EMBEDDING_ENABLED,
    EMBEDDING_DIM,
)


class LLMProvider:
    """LLM 统一接口（抽象基类）。

    所有 Provider 都要实现这两个方法：
    - chat()：对话生成
    - embed()：文本向量化
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

    def embed(self, text: str) -> list[float]:
        """文本向量化。

        把一段文本转成浮点数向量，用于计算文本相似度。
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

    @property
    def name(self) -> str:
        """Provider 名称（用于日志和展示）。"""
        raise NotImplementedError


class MockLLMProvider(LLMProvider):
    """本地 Mock：不调用真实 API，用模板/哈希模拟。

    优点：无需联网、无需 API Key、响应快
    缺点：生成质量有限，向量只是伪向量

    适用场景：开发调试、功能演示
    """

    @property
    def name(self) -> str:
        return "mock-engine"

    def chat(self, system_prompt: str, user_prompt: str, temperature: float = 0.8) -> str:
        """Mock 对话：返回占位响应。

        真正的生成逻辑由各 Agent 内部的模板函数完成。
        """
        return f"[mock-llm] 已收到生成请求，将由模板引擎处理。"

    def embed(self, text: str) -> list[float]:
        """Mock 向量：基于关键词哈希的伪向量。

        原理：
        1. 把文本切成 2-gram（两个字的组合）或单词
        2. 每个词用 MD5 哈希映射到一个向量维度
        3. 该维度 +1
        4. L2 归一化（让向量长度为 1）

        这样相同/相似的关键词会产生相近的向量，模拟语义相似度。
        """
        vec = [0.0] * EMBEDDING_DIM    # 初始化为零向量
        if not text:
            return vec
        # 分词：中文按 2-gram，英文按空格
        tokens = []
        for i in range(len(text) - 1):
            ch = text[i:i + 2]
            if not ch[0].isspace() and not ch[1].isspace():
                tokens.append(ch)
        for word in text.lower().split():
            tokens.append(word)
        # 每个词哈希到一个维度
        for token in tokens:
            # md5 哈希 → 取模映射到 [0, EMBEDDING_DIM) 范围
            idx = int(hashlib.md5(token.encode()).hexdigest(), 16) % EMBEDDING_DIM
            vec[idx] += 1.0
        # L2 归一化：让向量长度为 1，便于计算余弦相似度
        norm = sum(v * v for v in vec) ** 0.5
        if norm > 0:
            vec = [v / norm for v in vec]
        return vec

    def generate_image(self, prompt: str, theme: str = "", scene_style: dict = None) -> str:
        """Mock 文生图：生成主题化 SVG 占位图（即时、无需联网）。"""
        return _build_svg_image(prompt, theme, scene_style)


class OpenAICompatibleProvider(LLMProvider):
    """OpenAI 兼容 Chat Completions + Embeddings 客户端。

    兼容所有 OpenAI 格式的 API：通义千问、DeepSeek、智谱 GLM、Moonshot 等。

    使用 httpx.Client 发送 HTTP 请求：
    - POST /chat/completions：对话生成
    - POST /embeddings：文本向量化
    """

    def __init__(self) -> None:
        # 对话客户端（DeepSeek 等）与向量客户端（通义千问等）独立：
        # 它们可能是不同供应商，base_url / key / model 各不相同
        self._client = httpx.Client(timeout=LLM_TIMEOUT)
        self._embed_client = httpx.Client(timeout=LLM_TIMEOUT)
        # 向量降级用：embedding 不可用时回退到 Mock 关键词哈希向量
        self._mock = MockLLMProvider()

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

    def embed(self, text: str) -> list[float]:
        """调用 Embeddings API 生成向量。

        向量供应商可与对话供应商不同（对话用 DeepSeek、向量用通义千问）。
        - 未配置 EMBEDDING_API_KEY / EMBEDDING_MODEL → 直接 Mock 向量降级
        - 调用失败（供应商无此接口 / 网络 / 限流）→ 回退 Mock 向量
        保证应用永远能启动、语义检索永远可用（质量可能降级，但绝不崩）。
        """
        # 未配置真实 embedding → Mock 降级（DeepSeek 用户若没配千问就走这里）
        if not EMBEDDING_ENABLED:
            return self._mock.embed(text)
        url = f"{EMBEDDING_BASE_URL.rstrip('/')}/embeddings"
        headers = {
            "Authorization": f"Bearer {EMBEDDING_API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": EMBEDDING_MODEL,    # 如通义千问 text-embedding-v3
            "input": text,
        }
        try:
            resp = self._embed_client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            return resp.json()["data"][0]["embedding"]
        except Exception:
            # 失败回退 Mock（Mock 用 EMBEDDING_DIM，与真实向量维度保持一致，避免维度错配）
            return self._mock.embed(text)

    def generate_image(self, prompt: str, theme: str = "", scene_style: dict = None) -> str:
        """真实文生图：调用图像生成 API，失败则回退到 SVG 占位图。

        兼容 OpenAI 格式 /images/generations（通义万相 wanx、DALL-E 等）。
        响应可能返回 url 或 b64_json，任一可用即返回；否则回退 SVG。
        任何异常（API 不支持 / 网络 / 格式不符）都回退，绝不阻断生成流程。
        """
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

        payload = {"model": "wanx2.1-t2i-turbo", "prompt": prompt, "n": 1, "size": size}
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


def get_provider() -> LLMProvider:
    """根据配置选择 Provider（单例模式）。

    配置了 LLM_API_KEY → 返回真实 LLM Provider
    未配置             → 返回 Mock Provider
    """
    if LLM_ENABLED:
        return OpenAICompatibleProvider()
    return MockLLMProvider()