from datetime import date, datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator

from app.models.enums import ItemMode, ItemStatus, WishlistStatus


class WishlistCreateRequest(BaseModel):
    title: str = Field(min_length=2, max_length=180)
    description: str | None = Field(default=None, max_length=3000)
    occasion: str | None = Field(default=None, max_length=120)
    currency: str = Field(default='RUB', min_length=3, max_length=3)
    event_date: date | None = None

    @field_validator('currency')
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        return value.upper()


class WishlistUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=180)
    description: str | None = Field(default=None, max_length=3000)
    occasion: str | None = Field(default=None, max_length=120)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    event_date: date | None = None

    @field_validator('currency')
    @classmethod
    def normalize_currency(cls, value: str | None) -> str | None:
        return value.upper() if value else value


class WishlistItemCreateRequest(BaseModel):
    title: str = Field(min_length=2, max_length=255)
    product_url: HttpUrl | None = None
    image_url: HttpUrl | None = None
    notes: str | None = Field(default=None, max_length=3000)
    price: Decimal | None = Field(default=None, ge=0)
    mode: ItemMode = ItemMode.SINGLE
    target_amount: Decimal | None = Field(default=None, ge=0)
    position: int | None = Field(default=None, ge=0)


class WishlistItemUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=255)
    product_url: HttpUrl | None = None
    image_url: HttpUrl | None = None
    notes: str | None = Field(default=None, max_length=3000)
    price: Decimal | None = Field(default=None, ge=0)
    mode: ItemMode | None = None
    target_amount: Decimal | None = Field(default=None, ge=0)
    status: ItemStatus | None = None


class WishlistItemReorderRequest(BaseModel):
    item_ids: list[UUID]


class WishlistBaseView(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    description: str | None
    occasion: str | None
    currency: str
    event_date: date | None
    status: WishlistStatus
    share_slug: str | None
    created_at: datetime
    updated_at: datetime


class OwnerItemView(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    product_url: str | None
    image_url: str | None
    notes: str | None
    price: Decimal | None
    mode: ItemMode
    target_amount: Decimal | None
    collected_amount: Decimal
    status: ItemStatus
    position: int
    is_reserved: bool
    progress_percent: float


class GuestItemView(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    product_url: str | None
    image_url: str | None
    notes: str | None
    price: Decimal | None
    mode: ItemMode
    target_amount: Decimal | None
    collected_amount: Decimal
    status: ItemStatus
    position: int
    is_reserved: bool
    reserved_by_you: bool
    my_contribution: Decimal
    progress_percent: float


class OwnerWishlistDetail(WishlistBaseView):
    items: list[OwnerItemView]


class WishlistSummary(WishlistBaseView):
    pass


class PublicWishlistView(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    description: str | None
    occasion: str | None
    currency: str
    event_date: date | None
    status: WishlistStatus
    share_slug: str
    viewer_kind: Literal['anonymous', 'guest', 'owner']
    items: list[GuestItemView] | list[OwnerItemView]
