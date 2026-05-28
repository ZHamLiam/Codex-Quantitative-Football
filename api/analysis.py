from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from db.database import get_db
from db.models import SimulationResult, Match
from engines.simulation.runner import run_simulation
from engines.strategy.bet import generate_advice

router = APIRouter(prefix="/api/matches", tags=["analysis"])

@router.post("/{match_id}/analyze")
def analyze_match(match_id: int, profile_id: int = Query(None), db: Session = Depends(get_db)):
    m = db.query(Match).filter_by(id=match_id).first()
    if not m:
        raise HTTPException(404, "Match not found")

    sim_result = run_simulation(match_id, profile_id, n=10000)
    advice = generate_advice(sim_result)

    return {"simulation": sim_result, "advice": advice}

@router.get("/{match_id}/history")
def match_history(match_id: int, db: Session = Depends(get_db)):
    sims = db.query(SimulationResult).filter_by(match_id=match_id).order_by(SimulationResult.created_at.desc()).limit(5).all()
    return sims
