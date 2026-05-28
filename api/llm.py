from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from db.database import get_db
from db.models import Match
from llm.scout import generate_scout_report
from llm.interpreter import interpret_results
from engines.simulation.runner import run_simulation
from engines.strategy.bet import generate_advice

router = APIRouter(prefix="/api/llm", tags=["llm"])

class ScoutRequest(BaseModel):
    match_id: int
    profile_id: int = None

@router.post("/scout")
def scout(req: ScoutRequest, db: Session = Depends(get_db)):
    m = db.query(Match).filter_by(id=req.match_id).first()
    if not m:
        raise HTTPException(404, "Match not found")
    info = {"home_team": m.home_team.name, "away_team": m.away_team.name, "league": m.league, "stage": m.stage}
    sim = run_simulation(req.match_id, req.profile_id, n=5000)
    advice = generate_advice(sim)
    report = generate_scout_report(info, sim.get("score_distribution", {}))
    interpretation = interpret_results(sim, advice, info)
    return {"scout_report": report, "interpretation": interpretation}
