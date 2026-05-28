def calc_h2h_advantage(h2h_matches: list[dict], team_a_id: int, team_b_id: int) -> float:
    if not h2h_matches:
        return 50.0
    a_wins = sum(1 for m in h2h_matches if m.get("winner_id") == team_a_id)
    b_wins = sum(1 for m in h2h_matches if m.get("winner_id") == team_b_id)
    draws = len(h2h_matches) - a_wins - b_wins
    score = (a_wins * 100 + draws * 50) / len(h2h_matches)
    return max(0, min(100, score))
