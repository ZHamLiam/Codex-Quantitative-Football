def calc_weather_impact(weather: str, home_possession: float) -> float:
    weather_map = {"rain": -0.08, "wind": -0.05, "hot": -0.05, "clear": 0.0}
    base = weather_map.get(weather, 0)
    if weather in ("rain", "wind") and home_possession > 55:
        base *= 1.5
    return 50 + base * 100

def calc_referee_impact(ref_avg_cards: float, team_fouls_per_game: float) -> float:
    if ref_avg_cards is None or team_fouls_per_game is None:
        return 50.0
    ratio = ref_avg_cards * team_fouls_per_game / 20
    return max(0, min(100, 50 - (ratio - 2) * 10))

def calc_travel_fatigue(distance_km: float, rest_days: int) -> float:
    if distance_km is None or rest_days is None:
        return 50.0
    fatigue = distance_km / 1000 - rest_days * 5
    return max(0, min(100, 50 + fatigue))

def calc_fixture_congestion(matches_7d: int) -> float:
    if matches_7d <= 1:
        return 100.0
    if matches_7d == 2:
        return 70.0
    return 40.0
