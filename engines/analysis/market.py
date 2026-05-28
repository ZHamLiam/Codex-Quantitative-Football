def calc_odds_movement(initial: float, current: float) -> float:
    if initial is None or current is None:
        return 50.0
    change_pct = (initial - current) / initial
    return max(0, min(100, 50 + change_pct * 200))
