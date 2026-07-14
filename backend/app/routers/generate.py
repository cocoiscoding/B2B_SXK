"""内容生成 API：调用多 Agent 编排器生成营销内容。

对应需求：F3-1 ~ F3-6

这个接口是整个系统的核心：
用户选择产品 + 场景 + 渠道 → 5 个 Agent 串行协作 → 输出多版本营销内容
"""
from fastapi import APIRouter, HTTPException, Depends
from app.models import GenerateRequest, GenerateResponse
from app.agents.orchestrator import get_orchestrator
from app.auth import get_current_user

router = APIRouter(prefix="/api/generate", tags=["内容生成"])


@router.post("", response_model=GenerateResponse)
@router.post("/", response_model=GenerateResponse, include_in_schema=False)
def generate(req: GenerateRequest, user: dict = Depends(get_current_user)):
    """生成营销内容。需登录；生成结果归属到当前用户（created_by）。"""
    try:
        orch = get_orchestrator()
        return orch.run(
            product_id=req.product_id,
            scenario_id=req.scenario_id,
            channel=req.channel,
            style=req.style,
            params=req.params,
            version_count=req.version_count,
            created_by=user["id"],    # 归属：当前登录用户
            template_id=req.template_id or None,
        )
    except ValueError as e:
        # ValueError 通常是"产品/场景不存在"，返回 400
        raise HTTPException(400, str(e))