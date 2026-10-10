from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


class FavoriteBase(BaseModel):
    user_id: int
    property_id: int


class FavoriteCreate(FavoriteBase):
    pass


class FavoriteOut(BaseModel):
    id: int
    user_id: int
    property_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)