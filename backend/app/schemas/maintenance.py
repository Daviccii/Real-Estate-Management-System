from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


class MaintenanceBase(BaseModel):
    property_id: int
    title: str
    description: Optional[str] = None
    category: Optional[str] = None
    priority: str = "medium"
    status: str = "pending"
    tenant_id: Optional[int] = None
    unit_id: Optional[int] = None
    assigned_manager_id: Optional[int] = None
    cost: Optional[str] = None
    notes: Optional[str] = None


class MaintenanceCreate(MaintenanceBase):
    pass


class MaintenanceUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    assigned_manager_id: Optional[int] = None
    cost: Optional[str] = None
    notes: Optional[str] = None
    resolved_at: Optional[datetime] = None


class MaintenanceAssign(BaseModel):
    assigned_manager_id: int
    notes: Optional[str] = None


class MaintenanceResolve(BaseModel):
    resolution_notes: Optional[str] = None
    cost: Optional[str] = None


class MaintenanceOut(MaintenanceBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)