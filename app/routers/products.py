"""产品知识库管理 API：CRUD + 关键词检索 + 语义搜索 + 自动向量嵌入。

本模块提供产品知识库的所有 HTTP 接口，包括：
- F1-1 产品信息录入：POST /api/products
- F1-2 产品信息管理：GET/PUT/DELETE /api/products/{id}
- F1-3 知识库检索：GET /api/products?keyword=xxx + POST /api/products/search
- F1-4 初始数据：见 seed_data.py

FastAPI 路由概念：
- @router.get("/path")：处理 GET 请求（查询数据）
- @router.post("/path")：处理 POST 请求（创建数据）
- @router.put("/path")：处理 PUT 请求（更新数据）
- @router.delete("/path")：处理 DELETE 请求（删除数据）
- response_model：指定响应数据的结构（自动序列化+文档生成）
"""
import uuid
import os
import shutil
from fastapi import APIRouter, HTTPException, Query, UploadFile, File, Depends
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, Field
from psycopg2.extras import Json
from app.database import query, query_one, transaction, _parse_json_fields
from app.models import ProductCreate, Product, ImportDocxResponse
from app.vector_search import embed_product, search_products_by_text
from app.docx_parser import parse_product_from_manual
from app.auth import get_current_user, is_owner_or_admin, require_admin

# 创建路由器实例
# prefix="/api/products" 表示所有路由都以 /api/products 开头
# tags=["产品知识库"] 用于 API 文档分组
router = APIRouter(prefix="/api/products", tags=["产品知识库"])

# 文件上传根目录
UPLOAD_ROOT = "uploads/products"
os.makedirs(UPLOAD_ROOT, exist_ok=True)

# 上传限制配置
MAX_IMAGES_PER_PRODUCT = 10      # 每产品最多 10 张图片
MAX_DOCUMENTS_PER_PRODUCT = 5    # 每产品最多 5 个文档
MAX_IMAGE_SIZE = 5 * 1024 * 1024     # 图片最大 5MB
MAX_DOCUMENT_SIZE = 50 * 1024 * 1024  # 文档最大 50MB

# JSON_FIELDS 是产品表中的 JSONB 字段列表
# 这些字段在数据库中是 JSONB 类型，读取后需要做空值处理
JSON_FIELDS = ["category", "features", "target_customers", "selling_points", "competitors", "images", "documents"]


# ===== F1-2: 产品列表查询（含关键词检索 F1-3）=====

# 两个装饰器叠加：同时支持 /api/products 和 /api/products/ 两种路径
# include_in_schema=False 表示后者不显示在 API 文档中（避免重复）
@router.get("", response_model=list[Product])
@router.get("/", response_model=list[Product], include_in_schema=False)
def list_products(
    keyword: str | None = Query(None, description="按名称/类别关键词检索"),
    member: str | None = Query(None, description="按创建人(member id)筛选（加分项：团队协作）"),
    limit: int = Query(200, ge=1, le=500, description="返回条数上限（默认 200）"),
    offset: int = Query(0, ge=0, description="偏移量，用于分页"),
    user: dict = Depends(get_current_user),
):
    """查询产品列表，支持关键词检索 + 按创建人筛选，两个条件可叠加。

    默认返回最近 200 条；可用 limit/offset 翻页。
    """
    # 动态拼 WHERE：避免无筛选时带空 WHERE
    conds, args = [], []
    if keyword:
        like = f"%{keyword}%"
        # category 现在是 JSONB 数组，用 ::text 转为文本进行模糊匹配
        conds.append("(name LIKE %s OR category::text LIKE %s OR description LIKE %s)")
        args.extend([like, like, like])
    if member:
        conds.append("created_by = %s")
        args.append(member)
    where = ("WHERE " + " AND ".join(conds)) if conds else ""
    args.extend([limit, offset])
    rows = query(
        f"SELECT * FROM products {where} ORDER BY created_at DESC LIMIT %s OFFSET %s",
        tuple(args),
    )
    return [_parse_json_fields(r, JSON_FIELDS) for r in rows]


@router.get("/{product_id}", response_model=Product)
def get_product(product_id: str, user: dict = Depends(get_current_user)):
    """查询单个产品详情。

    GET /api/products/P001 → 返回 P001 产品的完整信息
    """
    row = query_one("SELECT * FROM products WHERE id = %s", (product_id,))
    if not row:
        # 产品不存在，返回 404 错误
        raise HTTPException(404, f"产品 {product_id} 不存在")
    return _parse_json_fields(row, JSON_FIELDS)


# ===== F1-1: 产品信息录入 =====

@router.post("", response_model=Product)
@router.post("/", response_model=Product, include_in_schema=False)
def create_product(body: ProductCreate, user: dict = Depends(get_current_user)):
    """创建新产品。

    请求体是 ProductCreate 模型（自动校验字段类型）。
    创建时自动生成向量嵌入，用于后续的语义检索。
    created_by 由后端从登录令牌取，不信任前端传入。
    """
    # 如果前端传了 id 就用前端的，否则自动生成（P + 6位随机大写字母数字）
    pid = body.id or f"P{uuid.uuid4().hex[:6].upper()}"
    created_by = user["id"]    # 归属：当前登录用户

    # 先构建产品字典，用于生成 embedding 向量
    # model_dump() 是 Pydantic 方法，把模型转成字典
    product_dict = {
        "id": pid, "name": body.name, "category": body.category,
        "description": body.description,
        "features": [f.model_dump() for f in body.features],
        "target_customers": body.target_customers,
        "pricing": body.pricing,
        "selling_points": body.selling_points,
    }
    # 生成向量嵌入（用于语义搜索）
    embedding = embed_product(product_dict)

    # 写入数据库
    with transaction() as cur:
        cur.execute(
            """INSERT INTO products
            (id, name, category, description, features, target_customers,
             pricing, selling_points, competitors, images, documents, embedding, created_by)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (
                pid, body.name,
                Json(body.category),
                body.description,
                Json([f.model_dump() for f in body.features]),
                Json(body.target_customers),
                body.pricing,
                Json(body.selling_points),
                Json(body.competitors),
                Json([img.model_dump() for img in body.images]),
                Json([doc.model_dump() for doc in body.documents]),
                Json(embedding),
                created_by,
            ),
        )
    # 返回创建好的产品（包含数据库自动生成的 created_at 等字段）
    return get_product(pid)


# ===== F1-2: 产品信息编辑 =====

@router.put("/{product_id}", response_model=Product)
def update_product(product_id: str, body: ProductCreate, user: dict = Depends(get_current_user)):
    """更新产品信息。仅创建者或管理员可改。

    PUT /api/products/P001 → 更新 P001 产品的信息
    更新时自动重新生成向量嵌入。created_by 不可改（保留原归属）。
    """
    # 先检查产品是否存在，并取 created_by 做归属校验
    existing = query_one("SELECT id, created_by FROM products WHERE id = %s", (product_id,))
    if not existing:
        raise HTTPException(404, f"产品 {product_id} 不存在")
    if not is_owner_or_admin(user, existing.get("created_by")):
        raise HTTPException(403, "无权修改他人的产品")

    # 重新生成 embedding(因为产品信息变了,向量也要更新)
    product_dict = {
        "id": product_id, "name": body.name, "category": body.category,
        "description": body.description,
        "features": [f.model_dump() for f in body.features],
        "target_customers": body.target_customers,
        "pricing": body.pricing,
        "selling_points": body.selling_points,
    }
    embedding = embed_product(product_dict)

    with transaction() as cur:
        cur.execute(
            """UPDATE products SET
            name=%s, category=%s, description=%s, features=%s,
            target_customers=%s, pricing=%s, selling_points=%s, competitors=%s,
            images=%s, documents=%s, embedding=%s, updated_at=NOW()
            WHERE id=%s""",
            (
                body.name, Json(body.category), body.description,
                Json([f.model_dump() for f in body.features]),
                Json(body.target_customers),
                body.pricing,
                Json(body.selling_points),
                Json(body.competitors),
                Json([img.model_dump() for img in body.images]),
                Json([doc.model_dump() for doc in body.documents]),
                Json(embedding),
                product_id,
            ),
        )
    return get_product(product_id)


# ===== F1-2: 产品信息删除 =====

@router.delete("/{product_id}")
def delete_product(product_id: str, user: dict = Depends(get_current_user)):
    """删除产品。仅创建者或管理员可删。"""
    existing = query_one("SELECT id, created_by, images, documents FROM products WHERE id = %s", (product_id,))
    if not existing:
        raise HTTPException(404, f"产品 {product_id} 不存在")
    if not is_owner_or_admin(user, existing.get("created_by")):
        raise HTTPException(403, "无权删除他人的产品")
    
    # 删除关联的上传文件
    images = existing.get("images") or []
    documents = existing.get("documents") or []
    deleted_files = 0
    
    for img in images:
        if isinstance(img, dict) and img.get("url"):
            file_path = os.path.join(".", img["url"].lstrip("/"))
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    deleted_files += 1
                except Exception:
                    pass  # 文件删除失败不影响产品删除
    
    for doc in documents:
        if isinstance(doc, dict) and doc.get("url"):
            file_path = os.path.join(".", doc["url"].lstrip("/"))
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    deleted_files += 1
                except Exception:
                    pass
    
    with transaction() as cur:
        cur.execute("DELETE FROM products WHERE id = %s", (product_id,))
    
    msg = f"产品 {product_id} 已删除"
    if deleted_files > 0:
        msg += f"，清理了 {deleted_files} 个关联文件"
    return {"message": msg}


# ===== F1-3: 语义搜索（向量检索）=====

class SemanticSearchRequest(BaseModel):
    """语义搜索请求体。"""
    query: str = Field(..., description="自然语言查询，如「适合金融行业的数据分析产品」")
    top_k: int = Field(default=5, ge=1, le=20, description="返回结果数量")
    threshold: float = Field(default=0.0, ge=0.0, le=1.0, description="相似度阈值")


class SemanticSearchResult(BaseModel):
    """语义搜索单个结果。"""
    product_id: str
    product_name: str
    category: list[str] = Field(default_factory=list)
    score: float           # 相似度分数（0-1，越高越相似）
    description: str = ""


@router.post("/search", response_model=list[SemanticSearchResult])
def semantic_search(req: SemanticSearchRequest, user: dict = Depends(get_current_user)):
    """语义搜索：用自然语言查询产品。

    示例：
        POST /api/products/search
        {"query": "适合金融行业的安全防护产品"}

    与 GET /api/products?keyword=xxx 的区别：
    - keyword 是字符级模糊匹配（LIKE）
    - 语义搜索理解"意思"，能找到关键词不完全匹配但语义相近的产品
    """
    results = search_products_by_text(req.query, top_k=req.top_k, threshold=req.threshold)
    return [
        SemanticSearchResult(
            product_id=r.get("id", ""),
            product_name=r.get("name", ""),
            category=r.get("category", []) if isinstance(r.get("category"), list) else [],
            score=round(r.get("_score", 0), 4),
            description=(r.get("description", "") or "")[:200],
        )
        for r in results
    ]


@router.post("/reindex")
def reindex_products(user: dict = Depends(require_admin)):
    """重建所有产品的向量嵌入。仅管理员可调用。

    用途：数据库迁移或 Embedding 模型切换后，重新生成所有产品的向量。
    """
    rows = query("SELECT * FROM products")
    count = 0
    for row in rows:
        embedding = embed_product(row)
        with transaction() as cur:
            cur.execute(
                "UPDATE products SET embedding=%s, updated_at=NOW() WHERE id=%s",
                (Json(embedding), row["id"]),
            )
        count += 1
    return {"message": f"已重建 {count} 个产品的向量嵌入", "count": count}


# ===== 加分项：上传产品手册（PDF/Word）自动解析建库 =====

@router.post("/import-docx", response_model=ImportDocxResponse)
async def import_docx(
    file: UploadFile = File(..., description="上传 PDF 或 Word(.docx) 产品手册"),
    user: dict = Depends(get_current_user),
):
    """上传产品手册（PDF/Word），自动解析为结构化产品草稿。

    流程：
    1. 接收 .pdf / .docx 文件（multipart/form-data 上传）
    2. 根据扩展名选择解析器：PDF 用 pdfplumber，Word 用 python-docx
    3. LLM 启用 → 大模型抽取；否则 → 启发式规则抽取
    4. 返回产品草稿（不入库），前端加载到编辑弹窗供用户核对后保存

    注意：本接口不直接写库，因为自动抽取不一定准确，需人工确认。
    """
    # 校验文件扩展名（仅支持 .pdf 和 .docx）
    filename = file.filename or ""
    ext = os.path.splitext(filename)[1].lower()
    if ext not in (".pdf", ".docx"):
        raise HTTPException(400, "仅支持 .pdf 和 .docx 格式（旧版 .doc 请另存为 .docx 后上传）")

    # 读取文件字节流（UploadFile.read 是异步方法，需 await）
    data = await file.read()
    if not data:
        raise HTTPException(400, "文件内容为空")

    # 解析（可能抛异常，如文件损坏）
    # pdfplumber/python-docx 解析 + 可能的 LLM 调用是同步重负载，放到线程池执行，
    # 避免阻塞主事件循环导致其他请求卡住（async def 默认在事件循环上同步跑）
    try:
        result = await run_in_threadpool(parse_product_from_manual, data, filename=filename)
    except Exception as e:
        raise HTTPException(400, f"解析失败：{type(e).__name__}: {e}")

    # 把解析出的草稿字典转成 ProductCreate 模型（顺带做类型校验）
    product = ProductCreate(**result["product"])
    return ImportDocxResponse(
        product=product,
        char_count=result["char_count"],
        extractor=result["extractor"],
        note=result["note"],
    )


# ===== 文件上传接口 =====

@router.post("/{product_id}/upload-image")
async def upload_product_image(
    product_id: str,
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user)
):
    """上传产品图片。"""
    # 检查产品是否存在
    existing = query_one("SELECT id, created_by, images FROM products WHERE id = %s", (product_id,))
    if not existing:
        raise HTTPException(404, f"产品 {product_id} 不存在")
    if not is_owner_or_admin(user, existing.get("created_by")):
        raise HTTPException(403, "无权修改他人的产品")
    
    # 检查文件类型
    allowed_types = ["image/jpeg", "image/png", "image/gif", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(400, "仅支持 JPG、PNG、GIF、WebP 格式的图片")
    
    # 检查文件大小
    file_size = 0
    content = await file.read()
    file_size = len(content)
    if file_size > MAX_IMAGE_SIZE:
        raise HTTPException(400, f"图片大小超过限制（最大 {MAX_IMAGE_SIZE // 1024 // 1024}MB）")
    
    # 检查数量限制
    images = existing.get("images") or []
    if len(images) >= MAX_IMAGES_PER_PRODUCT:
        raise HTTPException(400, f"图片数量已达上限（最多 {MAX_IMAGES_PER_PRODUCT} 张）")
    
    # 创建产品专属目录
    product_dir = os.path.join(UPLOAD_ROOT, product_id)
    os.makedirs(product_dir, exist_ok=True)
    
    # 生成唯一文件名
    file_ext = os.path.splitext(file.filename)[1] if file.filename else ".jpg"
    unique_name = f"{uuid.uuid4().hex[:8]}{file_ext}"
    file_path = os.path.join(product_dir, unique_name)
    
    # 保存文件
    with open(file_path, "wb") as buffer:
        buffer.write(content)
    
    # 返回文件信息
    return {
        "url": f"/uploads/products/{product_id}/{unique_name}",
        "name": file.filename or unique_name,
        "size": file_size
    }


@router.post("/{product_id}/upload-document")
async def upload_product_document(
    product_id: str,
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user)
):
    """上传产品文档（PDF、Word、Excel、PPT、TXT、ZIP）。"""
    # 检查产品是否存在
    existing = query_one("SELECT id, created_by, documents FROM products WHERE id = %s", (product_id,))
    if not existing:
        raise HTTPException(404, f"产品 {product_id} 不存在")
    if not is_owner_or_admin(user, existing.get("created_by")):
        raise HTTPException(403, "无权修改他人的产品")
    
    # 检查文件类型
    allowed_extensions = [".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".txt", ".zip"]
    file_ext = os.path.splitext(file.filename)[1].lower() if file.filename else ""
    if file_ext not in allowed_extensions:
        raise HTTPException(400, f"不支持的文件格式: {file_ext}，仅支持 {', '.join(allowed_extensions)}")
    
    # 检查文件大小
    content = await file.read()
    file_size = len(content)
    if file_size > MAX_DOCUMENT_SIZE:
        raise HTTPException(400, f"文档大小超过限制（最大 {MAX_DOCUMENT_SIZE // 1024 // 1024}MB）")
    
    # 检查数量限制
    documents = existing.get("documents") or []
    if len(documents) >= MAX_DOCUMENTS_PER_PRODUCT:
        raise HTTPException(400, f"文档数量已达上限（最多 {MAX_DOCUMENTS_PER_PRODUCT} 个）")
    
    # 创建产品专属目录
    product_dir = os.path.join(UPLOAD_ROOT, product_id)
    os.makedirs(product_dir, exist_ok=True)
    
    # 生成唯一文件名
    unique_name = f"{uuid.uuid4().hex[:8]}{file_ext}"
    file_path = os.path.join(product_dir, unique_name)
    
    # 保存文件
    with open(file_path, "wb") as buffer:
        buffer.write(content)
    
    # 返回文件信息
    return {
        "url": f"/uploads/products/{product_id}/{unique_name}",
        "name": file.filename or unique_name,
        "size": file_size,
        "type": file_ext[1:]  # 去掉点号，如 "pdf"
    }