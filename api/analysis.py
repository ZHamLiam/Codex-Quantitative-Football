from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from db.database import get_db
from db.models import SimulationResult, Match
from engines.simulation.runner import run_simulation, compute_real_factors
from engines.strategy.bet import generate_advice
from llm.interpreter import interpret_results

router = APIRouter(prefix="/api/matches", tags=["analysis"])

@router.post("/{match_id}/analyze")
def analyze_match(match_id: int, profile_id: int = Query(None), db: Session = Depends(get_db)):
    m = db.query(Match).filter_by(id=match_id).first()
    if not m:
        raise HTTPException(404, "Match not found")

    # Run full pipeline
    sim_result = run_simulation(match_id, profile_id, n=10000)
    odds = sim_result.get("odds", {"home": 2.0, "draw": 3.5, "away": 3.5})
    advice = generate_advice(sim_result, odds["home"], odds["draw"], odds["away"])

    # Get real factor scores
    factor_inputs, _, _, _ = compute_real_factors(m)
    factor_summary = {}
    for k, v in sorted(factor_inputs.items()):
        if v != 50 and not k.startswith("_"):
            factor_summary[k] = v

    # LLM interpretation
    match_info = {
        "home_team": m.home_team.name, "away_team": m.away_team.name,
        "league": m.league, "stage": m.stage,
    }
    llm_summary = interpret_results(sim_result, advice, match_info)

    return {
        "simulation": sim_result,
        "advice": advice,
        "factors": factor_summary,
        "llm_summary": llm_summary,
    }

@router.get("/{match_id}/history")
def match_history(match_id: int, db: Session = Depends(get_db)):
    sims = db.query(SimulationResult).filter_by(match_id=match_id).order_by(SimulationResult.created_at.desc()).limit(5).all()
    return sims