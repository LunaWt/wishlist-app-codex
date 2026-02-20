from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl

from app.models.enums import EventType


class GuestSessionCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=120)


class GuestSessionResponse(BaseModel):
    token: str
    guest_session_id: UUID
    guest_name: str
    expires_at: datetime


class ReservationResponse(BaseModel):
    message: str
    item_id: UUID
    is_reserved: bool


class ContributionRequest(BaseModel):
    amount: Decimal = Field(gt=0)


class ContributionResponse(BaseModel):
    message: str
    item_id: UUID
    accepted_amount: Decimal
    collected_amount: Decimal
    progress_percent: float


class RealtimeEventView(BaseModel):
    id: int
    event_type: EventType
    item_id: UUID | None
    payload: dict
    created_at: datetime


class EventsResponse(BaseModel):
    events: list[RealtimeEventView]
    next_cursor: int | None


class ItemPreviewRequest(BaseModel):
    url: HttpUrl


class ItemPreviewResponse(BaseModel):
    title: str | None
    image_url: str | None
    price: Decimal | None
    currency: str | None
    source_url: str
    from_cache: bool
