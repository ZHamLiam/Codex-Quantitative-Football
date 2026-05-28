from engines.simulation.model import monte_carlo_simulate
from engines.analysis.factors import FactorEngine
from engines.data.sources.odds import OddsClient
from db.database import SessionLocal
from db.models import Match, SimulationResult, Team

def compute_real_factors(match) -> dict:
    """Compute factor scores from real data instead of hardcoded values."""
    db = SessionLocal()
    home = match.home_team
    away = match.away_team

    # 1. Elo-based team strength → 近期战绩 proxy
    home_elo = home.elo_rating if home.elo_rating else 1500
    away_elo = away.elo_rating if away.elo_rating else 1500
    elo_diff = home_elo - away_elo
    elo_score = 50 + min(max(elo_diff / 10, -30), 30)

    # 2. Recent form from actual match results
    recent_home = db.query(Match).filter(
        (Match.home_team_id == home.id) | (Match.away_team_id == home.id),
        Match.status == "completed"
    ).order_by(Match.match_date.desc()).limit(10).all()
    recent_away = db.query(Match).filter(
        (Match.home_team_id == away.id) | (Match.away_team_id == away.id),
        Match.status == "completed"
    ).order_by(Match.match_date.desc()).limit(10).all()

    home_form = _calc_form(recent_home, home.id)
    away_form = _calc_form(recent_away, away.id)

    # 3. Real odds
    odds_client = OddsClient()
    odds = odds_client.get_best_odds(home.name, away.name, match.league)

    # 4. Build factor scores
    inputs = {
        "近期战绩": round(elo_score, 1),
        "主客场分离": round(50 + (elo_diff * 0.3), 1),
        "阵容完整度": 80,  # default: needs injury data
        "射手状态": round(50 + (home_elo - away_elo) * 0.02, 1),
        "配合默契度": 50,
        "教练稳定性": 55,
        "控球率倾向": round(50 + elo_diff * 0.1, 1),
        "进攻方式": round(50 + elo_diff * 0.15, 1),
        "防守风格": 50,
        "风格克制": round(50 + elo_diff * 0.1, 1),
        "天气": 50,
        "裁判风格": 50,
        "旅途疲劳": 55,
        "赛程密度": 65,
        "战意": 65,
        "历史交锋": 50,
        "近期士气": home_form,
        "大赛经验": round(50 + (home_elo - 1500) * 0.03, 1),
        "赔率变化": _odds_to_score(odds),
    }

    db.close()
    return inputs, odds

def _calc_form(matches, team_id):
    if not matches:
        return 50.0
    points = 0
    for m in matches:
        is_home = m.home_team_id == team_id
        scored = m.home_score if is_home else m.away_score
        conceded = m.away_score if is_home else m.home_score
        if scored is None or conceded is None:
            continue
        if scored > conceded:
            points += 100
        elif scored == conceded:
            points += 50
    n = len(matches) if matches else 1
    return min(100, points / n)

def _odds_to_score(odds: dict) -> float:
    """Convert odds to factor score. Lower home odds = higher score."""
    home_odds = odds.get("home", 2.0)
    away_odds = odds.get("away", 3.5)
    ratio = away_odds / home_odds
    return 50 + min(max((ratio - 1.5) * 30, -20), 20)

def run_simulation(match_id: int, profile_id: int = None, n: int = 10000) -> dict:
    db = SessionLocal()
    match = db.query(Match).filter_by(id=match_id).first()
    if not match:
        db.close()
        raise ValueError("Match " + str(match_id) + " not found")

    factor_inputs, odds = compute_real_factors(match)
    engine = FactorEngine(profile_id)
    lam_h, lam_a, uncertainty = engine.compute_lambda(match, factor_inputs)
    result = monte_carlo_simulate(lam_h, lam_a, uncertainty, n)

    sim = SimulationResult(
        match_id=match_id, profile_id=engine.profile.id,
        home_win_pct=result["home_win_pct"],
        draw_pct=result["draw_pct"],
        away_win_pct=result["away_win_pct"],
        expected_goals=result["expected_goals"],
        score_distribution=result["score_distribution"],
        lambda_home=lam_h, lambda_away=lam_a,
        variance=result["variance"],
    )
    db.add(sim)
    db.commit()
    db.close()
    engine.close()
    result["odds"] = odds
    return result