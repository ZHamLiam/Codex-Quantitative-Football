def calc_expected_value(sim_prob: float, odds: float) -> float:
    edge = (sim_prob / 100) * odds - 1
    return round(edge, 4)

def calc_risk_level(variance: float, edge: float) -> str:
    if variance > 3 or edge < 0:
        return "high"
    if variance > 2 or edge < 0.05:
        return "medium"
    return "low"
