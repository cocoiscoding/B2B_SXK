"""向量检索模块：余弦相似度、产品文本向量化、语义搜索。

本模块实现了基于向量嵌入的语义检索功能，让用户可以用自然语言查询产品。

核心概念：
- Embedding（嵌入）：把文本转成一组浮点数向量（如 [0.1, 0.3, ...]）
- 余弦相似度：衡量两个向量的方向相似程度，值越接近 1 越相似
- 语义搜索：相比 LIKE 关键词匹配，语义搜索能理解"意思相近"的文本

工作原理：
1. 把每个产品的文本信息转成向量，存入数据库 embedding 字段
2. 用户查询时，把查询文本也转成向量
3. 计算查询向量与每个产品向量的余弦相似度
4. 按相似度排序，返回最匹配的产品

向量维度与 config.EMBEDDING_DIM 一致。
Mock 模式下使用关键词哈希伪向量（相同/相似关键词会产生相近向量）。
真实 LLM 模式下使用 Embedding API 生成高质量语义向量。
"""
import math
from app.database import query
from app.agents.llm_provider import get_provider, LLMProvider


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """计算两个向量的余弦相似度。

    公式：cos(θ) = (a·b) / (|a| × |b|)
    - a·b 是点积（对应位置相乘再求和）
    - |a| 是向量长度（各项平方和再开方）

    返回值范围 [-1, 1]：
    - 1 表示方向完全相同（最相似）
    - 0 表示正交（不相关）
    - -1 表示方向完全相反

    本项目中向量都是非负的（来自文本嵌入），所以范围是 [0, 1]。
    """
    # 长度不一致或任一为空，相似度为 0
    if not a or not b or len(a) != len(b):
        return 0.0
    # 点积：对应位置相乘再求和
    dot = sum(x * y for x, y in zip(a, b))
    # 向量长度：各项平方和开方
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    # 避免除零
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def build_product_text(product: dict) -> str:
    """将产品结构化信息拼接为一段可用于向量化的文本。

    把产品的名称、类别、标语、描述、功能、卖点、目标客户等信息
    拼成一段连贯的文本，然后交给 embedding 模型生成向量。

    为什么要拼接成文本？
    → Embedding 模型只接受文本输入，不接受结构化字典。
       拼接时按重要性排序，把最关键的信息放前面。
    """
    parts = [
        product.get("name", ""),
        product.get("category", ""),
        product.get("tagline", ""),
        product.get("description", ""),
    ]
    # 拼接功能信息
    features = product.get("features", [])
    if isinstance(features, list):
        for f in features:
            if isinstance(f, dict):
                parts.append(f.get("name", ""))
                parts.append(f.get("description", ""))
    # 拼接卖点
    selling_points = product.get("selling_points", [])
    if isinstance(selling_points, list):
        parts.extend(str(s) for s in selling_points)
    # 拼接目标客户
    target = product.get("target_customers", [])
    if isinstance(target, list):
        parts.extend(str(t) for t in target)
    # 用空格连接所有非空部分
    return " ".join(p for p in parts if p)


def embed_product(product: dict, provider: LLMProvider | None = None) -> list[float]:
    """为单个产品生成向量嵌入。

    参数：
        product: 产品字典
        provider: LLM Provider 实例（不传则自动获取）

    返回：浮点数列表，如 [0.1, 0.3, ...]
    """
    if provider is None:
        provider = get_provider()
    text = build_product_text(product)
    return provider.embed(text)


def embed_text(text: str, provider: LLMProvider | None = None) -> list[float]:
    """为任意文本生成向量嵌入。

    用于把用户的查询文本转成向量。
    """
    if provider is None:
        provider = get_provider()
    return provider.embed(text)


def search_products_by_vector(
    query_vector: list[float],
    top_k: int = 5,
    threshold: float = 0.0,
) -> list[dict]:
    """向量检索：计算所有产品的余弦相似度，返回 top_k 结果。

    参数：
        query_vector: 查询向量
        top_k: 返回前 K 个最相似的结果
        threshold: 相似度阈值，低于此值的结果被过滤（0 表示不过滤）

    返回：[{"id": "P001", "name": "...", "_score": 0.85}, ...]
    """
    # 取出所有产品（embedding 字段已在数据库中）
    rows = query("SELECT * FROM products ORDER BY created_at DESC")
    if not rows:
        return []

    scored = []
    for row in rows:
        emb = row.get("embedding")
        # 只对有向量的产品计算相似度
        if isinstance(emb, list) and emb:
            sim = cosine_similarity(query_vector, emb)
            if sim >= threshold:
                row["_score"] = sim     # 把相似度分数存入字典
                scored.append(row)

    # 按相似度降序排序（最相似的在前）
    scored.sort(key=lambda r: r["_score"], reverse=True)
    # 切片取前 top_k 个
    return scored[:top_k]


def search_products_by_text(
    query_text: str,
    top_k: int = 5,
    threshold: float = 0.0,
    provider: LLMProvider | None = None,
) -> list[dict]:
    """文本语义搜索：将查询文本转为向量后检索。

    这是面向用户的便捷接口：传入自然语言查询，返回最匹配的产品。

    示例：
        search_products_by_text("适合金融行业的安全防护产品")
        → 返回与查询语义最接近的产品列表
    """
    if provider is None:
        provider = get_provider()
    # 1. 把查询文本转成向量
    query_vector = provider.embed(query_text)
    # 2. 用向量去检索
    return search_products_by_vector(query_vector, top_k=top_k, threshold=threshold)