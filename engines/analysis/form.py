def calc_recent_form(team_matches: list[dict], n: int = 5) -> float:
    if not team_matches:
        return 50.0
    recent = team_matches[-n:]
    wins = sum(1 for m in recent if _is_win(m))
    draws = sum(1 for m in recent if _is_draw(m))
    score = (wins * 100 + draws * 50) / len(recent)
    return score

def calc_home_away_split(team_matches: list[dict], is_home: bool) -> float:
    filtered = [m for m in team_matches if m.get("is_home") == is_home]
    if not filtered:
        return 50.0
    wins = sum(1 for m in filtered if _is_win(m))
    draws = sum(1 for m in filtered if _is_draw(m))
    return (wins * 100 + draws * 50) / len(filtered)

def calc_striker_form(team_matches: list[dict], striker_goals: float = 0) -> float:
    if not team_matches:
        return 50.0
    if striker_goals > 0:
        goals = striker_goals
    else:
        goals = sum(m.get("goals_for", 0) for m in team_matches[-5:]) / min(len(team_matches), 5)
    return min(goals * 25, 100.0)

def _is_win(m: dict) -> bool:
    return m.get("goals_for", 0) > m.get("goals_against", 0)

def _is_draw(m: dict) -> bool:
    return m.get("goals_for", 0) == m.get("goals_against", 0)
