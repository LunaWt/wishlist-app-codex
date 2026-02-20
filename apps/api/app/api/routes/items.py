from fastapi import APIRouter

from app.api.deps import DbSession
from app.schemas.public import ItemPreviewRequest, ItemPreviewResponse
from app.services.link_preview_service import get_or_fetch_link_preview

router = APIRouter(prefix='/items', tags=['items'])


@router.post('/preview', response_model=ItemPreviewResponse)
async def preview_item(payload: ItemPreviewRequest, db: DbSession) -> ItemPreviewResponse:
    data = await get_or_fetch_link_preview(db, str(payload.url))
    return ItemPreviewResponse(**data)
