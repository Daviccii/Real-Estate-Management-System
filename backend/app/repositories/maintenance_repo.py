from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.maintenance import Maintenance as MaintenanceModel
from app.models.property import Property


def get_maintenance(db: Session, maintenance_id: int) -> Optional[MaintenanceModel]:
    return db.query(MaintenanceModel).filter(MaintenanceModel.id == maintenance_id).first()


def list_maintenance(db: Session, skip: int = 0, limit: int = 100, *, property_id: Optional[int] = None, unit_id: Optional[int] = None, tenant_id: Optional[int] = None, status: Optional[str] = None, priority: Optional[str] = None, assigned_manager_id: Optional[int] = None, authorized_user_id: Optional[int] = None) -> List[MaintenanceModel]:
    q = db.query(MaintenanceModel)
    if property_id:
        q = q.filter(MaintenanceModel.property_id == property_id)
    if unit_id:
        q = q.filter(MaintenanceModel.unit_id == unit_id)
    if tenant_id:
        q = q.filter(MaintenanceModel.tenant_id == tenant_id)
    if status:
        q = q.filter(MaintenanceModel.status == status)
    if priority:
        q = q.filter(MaintenanceModel.priority == priority)
    if assigned_manager_id:
        q = q.filter(MaintenanceModel.assigned_manager_id == assigned_manager_id)
    if authorized_user_id is not None:
        q = q.join(Property, MaintenanceModel.property_id == Property.id).filter(
            (Property.owner_id == authorized_user_id) |
            (Property.manager_id == authorized_user_id)
        )
    return q.order_by(MaintenanceModel.id.desc()).offset(skip).limit(limit).all()


def create_maintenance(db: Session, *, property_id: int, **data) -> MaintenanceModel:
    maintenance = MaintenanceModel(property_id=property_id, **data)
    db.add(maintenance)
    db.commit()
    db.refresh(maintenance)
    return maintenance


def update_maintenance(db: Session, maintenance_obj: MaintenanceModel, **data) -> MaintenanceModel:
    for key, value in data.items():
        if hasattr(maintenance_obj, key) and value is not None:
            setattr(maintenance_obj, key, value)
    db.add(maintenance_obj)
    db.commit()
    db.refresh(maintenance_obj)
    return maintenance_obj


def delete_maintenance(db: Session, maintenance_obj: MaintenanceModel) -> None:
    db.delete(maintenance_obj)
    db.commit()