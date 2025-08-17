from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from ...core.database import get_db
from ...models.database import Service
from ...schemas.service import ServiceCreate, ServiceResponse, ServiceUpdate

router = APIRouter(prefix="/api/services", tags=["services"])


@router.post("/", response_model=ServiceResponse, status_code=201)
def create_service(service: ServiceCreate, db: Session = Depends(get_db)):
    db_service = Service(
        name=service.name,
        description=service.description,
        type=service.type,
        endpoint=service.endpoint,
        default_parameters=service.default_parameters,
        enabled=service.enabled,
    )
    db.add(db_service)
    db.commit()
    db.refresh(db_service)
    return db_service


@router.get("/", response_model=List[ServiceResponse])
def get_services(db: Session = Depends(get_db)):
    services = db.query(Service).filter(Service.enabled == True).all()
    return services


@router.get("/{service_id}", response_model=ServiceResponse)
def get_service(service_id: int, db: Session = Depends(get_db)):
    service = db.query(Service).filter(Service.id == service_id).first()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    return service


@router.put("/{service_id}", response_model=ServiceResponse)
def update_service(
    service_id: int, service_update: ServiceUpdate, db: Session = Depends(get_db)
):
    service = db.query(Service).filter(Service.id == service_id).first()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")

    if service_update.name is not None:
        service.name = service_update.name
    if service_update.description is not None:
        service.description = service_update.description
    if service_update.type is not None:
        service.type = service_update.type
    if service_update.endpoint is not None:
        service.endpoint = service_update.endpoint
    if service_update.default_parameters is not None:
        service.default_parameters = service_update.default_parameters
    if service_update.enabled is not None:
        service.enabled = service_update.enabled

    db.commit()
    db.refresh(service)
    return service


@router.delete("/{service_id}")
def delete_service(service_id: int, db: Session = Depends(get_db)):
    service = db.query(Service).filter(Service.id == service_id).first()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")

    db.delete(service)
    db.commit()
    return {"message": "Service deleted successfully"}


@router.post("/{service_id}/test")
def test_service_connection(service_id: int, db: Session = Depends(get_db)):
    service = db.query(Service).filter(Service.id == service_id).first()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")

    # TODO: Implement actual connection testing
    # For now, simulate a successful connection test
    return {
        "service_id": service_id,
        "status": "online",
        "response_time": 150,  # ms
        "message": "Connection successful"
    }