from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from db.database import get_db
from db.models import FactorConfig

router = APIRouter(prefix="/api/factors", tags=["factors"])

class FactorCreate(BaseModel):
    name: str
    category: str
    description: str = ""
    default_weight: int = 5

class FactorUpdate(BaseModel):
    name: str = None
    description: str = None
    default_weight: int = None

@router.get("")
def list_factors(db: Session = Depends(get_db)):
    return db.query(FactorConfig).all()

@router.post("")
def create_factor(data: FactorCreate, db: Session = Depends(get_db)):
    f = FactorConfig(name=data.name, category=data.category, description=data.description, default_weight=data.default_weight, is_custom=True)
    db.add(f)
    db.commit()
    db.refresh(f)
    return f

@router.put("/{factor_id}")
def update_factor(factor_id: int, data: FactorUpdate, db: Session = Depends(get_db)):
    f = db.query(FactorConfig).filter_by(id=factor_id).first()
    if not f:
        raise HTTPException(404, "Factor not found")
    if data.name is not None: f.name = data.name
    if data.description is not None: f.description = data.description
    if data.default_weight is not None: f.default_weight = data.default_weight
    db.commit()
    return f

@router.delete("/{factor_id}")
def delete_factor(factor_id: int, db: Session = Depends(get_db)):
    f = db.query(FactorConfig).filter_by(id=factor_id).first()
    if not f:
        raise HTTPException(404, "Factor not found")
    db.delete(f)
    db.commit()
    return {"status": "deleted"}
