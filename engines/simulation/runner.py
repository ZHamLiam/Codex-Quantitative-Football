from engines.simulation.model import monte_carlo_simulate
from engines.analysis.factors import FactorEngine
from db.database import SessionLocal
from db.models import Match, SimulationResult

def run_simulation(match_id: int, profile_id: int = None, n: int = 10000) -> dict:
    db = SessionLocal()
    match = db.query(Match).filter_by(id=match_id).first()
    if not match:
        db.close()
        raise ValueError(f"Match {match_id} not found")

    engine = FactorEngine(profile_id)
    factor_inputs = {
        "近期战绩": 60, "主客场分离": 65, "阵容完整度": 80,
        "射手状态": 55, "配合默契度": 50, "教练稳定性": 60,
        "控球率倾向": 50, "进攻方式": 50, "防守风格": 50,
        "风格克制": 50, "天气": 50, "裁判风格": 50,
        "旅途疲劳": 50, "赛程密度": 70, "战意": 60,
        "历史交锋": 50, "近期士气": 55, "大赛经验": 50,
        "赔率变化": 50,
    }
    lam_h, lam_a, uncertainty = engine.compute_lambda(match, factor_inputs)
    result = monte_carlo_simulate(lam_h, lam_a, uncertainty, n)

    sim = SimulationResult(
        match_id=match_id,
        profile_id=engine.profile.id,
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
    return result
