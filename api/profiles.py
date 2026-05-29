from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from pydantic import BaseModel
from db.database import get_db
from db.models import FactorProfile, FactorProfileItem, FactorConfig

router = APIRouter(prefix="/api/profiles", tags=["profiles"])

class ProfileCreate(BaseModel):
    name: str
    description: str = ""

class ProfileItemUpdate(BaseModel):
    factor_config_id: int
    weight: int
    enabled: bool = True

@router.get("")
def list_profiles(db: Session = Depends(get_db)):
    return db.query(FactorProfile).all()

@router.get("/{profile_id}")
def get_profile(profile_id: int, db: Session = Depends(get_db)):
    p = db.query(FactorProfile).filter_by(id=profile_id).first()
    if not p:
        raise HTTPException(404, "Profile not found")
    items = db.query(FactorProfileItem).options(joinedload(FactorProfileItem.factor)).filter_by(profile_id=profile_id).all()
    result_items = []
    for item in items:
        result_items.append({
            "id": item.id,
            "profile_id": item.profile_id,
            "factor_config_id": item.factor_config_id,
            "weight": item.weight,
            "enabled": item.enabled,
            "factor": {
                "id": item.factor.id,
                "name": item.factor.name,
                "category": item.factor.category,
                "description": item.factor.description,
                "is_custom": item.factor.is_custom,
            } if item.factor else None,
        })
    return {"profile": p, "items": result_items}

@router.post("")
def create_profile(data: ProfileCreate, base_profile_id: int = None, db: Session = Depends(get_db)):
    profile = FactorProfile(name=data.name, description=data.description)
    db.add(profile)
    db.flush()

    base = None
    if base_profile_id:
        base = db.query(FactorProfile).filter_by(id=base_profile_id).first()
    else:
        base = db.query(FactorProfile).filter_by(is_default=True).first()

    if base:
        for item in db.query(FactorProfileItem).filter_by(profile_id=base.id).all():
            new_item = FactorProfileItem(profile_id=profile.id, factor_config_id=item.factor_config_id, weight=item.weight, enabled=item.enabled)
            db.add(new_item)

    db.commit()
    db.refresh(profile)
    return profile

@router.put("/{profile_id}/items")
def update_profile_items(profile_id: int, items_input: list[ProfileItemUpdate], db: Session = Depends(get_db)):
    profile = db.query(FactorProfile).filter_by(id=profile_id).first()
    if not profile:
        raise HTTPException(404, "Profile not found")
    for item_data in items_input:
        existing = db.query(FactorProfileItem).filter_by(profile_id=profile_id, factor_config_id=item_data.factor_config_id).first()
        if existing:
            existing.weight = item_data.weight
            existing.enabled = item_data.enabled
    db.commit()
    return {"status": "updated"}

@router.delete("/{profile_id}")
def delete_profile(profile_id: int, db: Session = Depends(get_db)):
    p = db.query(FactorProfile).filter_by(id=profile_id).first()
    if not p:
        raise HTTPException(404, "Profile not found")
    if p.is_default:
        raise HTTPException(400, "Cannot delete default profile")
    db.delete(p)
    db.commit()
    return {"status": "deleted"}