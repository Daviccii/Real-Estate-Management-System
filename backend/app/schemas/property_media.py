from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class PropertyMediaCreate(BaseModel):
    url: str = Field(min_length=1, max_length=1000)
    media_type: str = Field(default="image", max_length=30)
    source_type: str = Field(default="OWNER_UPLOADED", max_length=50)
    source_name: Optional[str] = Field(default=None, max_length=255)
    license_reference: Optional[str] = Field(default=None, max_length=500)
    caption: Optional[str] = Field(default=None, max_length=500)
    is_primary: bool = False
    is_public: bool = True


class PropertyMediaOut(PropertyMediaCreate):
    id: int
    property_id: int

    model_config = ConfigDict(from_attributes=True)
