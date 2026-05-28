from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime
from db.database import get_db
from db.models import Match
from engines.data.team_names import get_zh_name

router = APIRouter(prefix="/api/matches", tags=["matches"])

@router.get("")
def list_matches(
    league: str = None,
    date_from: str = None,
    date_to: str = None,
    search: str = None,
    mode: str = "upcoming",  # upcoming / history / all
    db: Session = Depends(get_db)
):
    q = db.query(Match)
    now = datetime.utcnow()

    if mode == "upcoming":
        q = q.filter(Match.match_date >= now).order_by(Match.match_date.asc())
    elif mode == "history":
        q = q.filter(Match.match_date < now).order_by(Match.match_date.desc())
    else:
        q = q.order_by(Match.match_date.desc())

    if league:
        q = q.filter(Match.league == league)
    if date_from:
        q = q.filter(Match.match_date >= date_from)
    if date_to:
        q = q.filter(Match.match_date <= date_to)

    matches = q.limit(200).all()

    # Search filter (post-query)
    if search:
        s = search.lower()
        matches = [m for m in matches if
            (m.home_team and s in m.home_team.name.lower()) or
            (m.away_team and s in m.away_team.name.lower()) or
            s in get_zh_name(m.home_team.name if m.home_team else "").lower() or
            s in get_zh_name(m.away_team.name if m.away_team else "").lower()]

    return [{
        "id": m.id,
        "match_date": m.match_date.isoformat(),
        "league": m.league,
        "stage": m.stage,
        "status": m.status,
        "home_team": {
            "id": m.home_team_id,
            "name": m.home_team.name if m.home_team else "?",
            "name_zh": get_zh_name(m.home_team.name) if m.home_team else "?",
        },
        "away_team": {
            "id": m.away_team_id,
            "name": m.away_team.name if m.away_team else "?",
            "name_zh": get_zh_name(m.away_team.name) if m.away_team else "?",
        },
        "home_score": m.home_score,
        "away_score": m.away_score,
    } for m in matches]

@router.get("/{match_id}")
def get_match(match_id: int, db: Session = Depends(get_db)):
    m = db.query(Match).filter_by(id=match_id).first()
    if not m:
        raise HTTPException(404, "Match not found")
    return {
        "id": m.id, "match_date": m.match_date.isoformat(),
        "league": m.league, "stage": m.stage, "status": m.status,
        "home_team": {
            "id": m.home_team.id if m.home_team else 0,
            "name": m.home_team.name if m.home_team else "?",
            "name_zh": get_zh_name(m.home_team.name) if m.home_team else "?",
        },
        "away_team": {
            "id": m.away_team.id if m.away_team else 0,
            "name": m.away_team.name if m.away_team else "?",
            "name_zh": get_zh_name(m.away_team.name) if m.away_team else "?",
        },
        "home_score": m.home_score, "away_score": m.away_score,
    }