"""SEO 分析 API（加分项）。

对应需求：「接入 SEO 分析，为生成的文案提供 SEO 优化建议」。
无状态接口：传入标题 + 正文，返回评分与建议，不写库。
"""
from fastapi import APIRouter, Depends
from app.models import SeoAnalyzeRequest, SeoAnalyzeResponse
from app.seo_analyzer import analyze
from app.auth import get_current_user

router = APIRouter(prefix="/api/seo", tags=["SEO分析"])


@router.post("/analyze", response_model=SeoAnalyzeResponse)
def seo_analyze(req: SeoAnalyzeRequest, user: dict = Depends(get_current_user)):
    """分析文案 SEO 友好度，返回评分 + 分级建议 + 关键词 + 统计。需登录。"""
    result = analyze(req.title, req.body)
    return SeoAnalyzeResponse(**result)
