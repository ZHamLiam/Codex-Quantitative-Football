from db.database import SessionLocal
from db.models import StartingXI

def predict_starting_xi(match_id: int, team_id: int, squad_list: list, recent_lineups: list, formation: str = "4-3-3") -> list:
    available = [p for p in squad_list if not p.get("is_injured") and not p.get("is_suspended")]

    starter_freq = {}
    for lineup in recent_lineups[-5:]:
        for name in lineup:
            starter_freq[name] = starter_freq.get(name, 0) + 1

    position_slots = {"GK": 1, "DEF": 4, "MID": 3, "FWD": 3}

    result = []
    for pos, count in position_slots.items():
        candidates = [p for p in available if p.get("position") == pos]
        candidates.sort(key=lambda p: starter_freq.get(p["name"], 0), reverse=True)
        for p in candidates[:count]:
            confidence = min(100, starter_freq.get(p["name"], 0) * 20 + 40)
            result.append({
                "player_name": p["name"], "position": pos,
                "predicted_role": "starter", "confidence": confidence,
                "formation": formation,
            })

    starter_names = {r["player_name"] for r in result}
    for p in available:
        if p["name"] not in starter_names:
            result.append({
                "player_name": p["name"], "position": p.get("position", "MID"),
                "predicted_role": "bench", "confidence": 70,
                "formation": formation,
            })

    return result

def save_starting_xi(match_id: int, team_id: int, predictions: list):
    db = SessionLocal()
    db.query(StartingXI).filter_by(match_id=match_id, team_id=team_id).delete()
    for p in predictions:
        xi = StartingXI(match_id=match_id, team_id=team_id, **p)
        db.add(xi)
    db.commit()
    db.close()
