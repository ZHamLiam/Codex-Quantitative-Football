from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from db.database import get_db
from db.models import Match

router = APIRouter(prefix="/api/matches", tags=["matches"])

@router.get("")
def list_matches(league: str = None, date_from: str = None, date_to: str = None, db: Session = Depends(get_db)):
    q = db.query(Match)
    if league:
        q = q.filter(Match.league == league)
    if date_from:
        q = q.filter(Match.match_date >= date_from)
    if date_to:
        q = q.filter(Match.match_date <= date_to)
    return q.order_by(Match.match_date).all()

@router.get("/{match_id}")
def get_match(match_id: int, db: Session = Depends(get_db)):
    m = db.query(Match).filter_by(id=match_id).first()
    if not m:
        raise HTTPException(404, "Match not found")
    return {
        "id": m.id, "match_date": m.match_date.isoformat(),
        "league": m.league, "stage": m.stage, "status": m.status,
        "home_team": {"id": m.home_team.id, "name": m.home_team.name} if m.home_team else None,
        "away_team": {"id": m.away_team.id, "name": m.away_team.name} if m.away_team else None,
        "home_score": m.home_score, "away_score": m.away_score,
    }
