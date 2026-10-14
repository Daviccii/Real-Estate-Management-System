from pydantic import ConfigDict
from .base import ApiSchema
from typing import Optional
from datetime import datetime


class FavoriteBase(ApiSchema):
    user_id: int
    property_id: int


class FavoriteCreate(FavoriteBase):
    pass


class FavoriteOut(ApiSchema):
    id: int
    user_id: int
    property_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)