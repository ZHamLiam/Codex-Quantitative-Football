from db.database import SessionLocal
from db.models import FactorConfig, FactorProfile, FactorProfileItem, Match
from engines.analysis import form, tactics, h2h, squad_factor, environment, psychology, market

STAGE_CONFIDENCE = {
    "league": 1.0, "group_md1": 0.6, "group_md2": 0.8,
    "group_md3": 0.9, "r16": 0.9, "qf": 0.95, "sf": 1.0, "final": 1.0
}

class FactorEngine:
    def __init__(self, profile_id: int = None):
        self.db = SessionLocal()
        self.profile = self._load_profile(profile_id)

    def _load_profile(self, profile_id: int = None):
        if profile_id:
            return self.db.query(FactorProfile).filter_by(id=profile_id).first()
        return self.db.query(FactorProfile).filter_by(is_default=True).first()

    def get_weights(self) -> dict:
        items = self.db.query(FactorProfileItem).filter_by(profile_id=self.profile.id).all()
        result = {}
        for item in items:
            name = item.factor.name
            result[name] = {"weight": item.weight, "enabled": item.enabled}
        return result

    def compute_lambda(self, match: Match, factor_inputs: dict) -> tuple:
        weights = self.get_weights()
        stage_conf = STAGE_CONFIDENCE.get(match.stage, 1.0)

        home_score = 0.0
        uncertainty = 0.0
        total_weight = 0

        for name, config in weights.items():
            if not config["enabled"]:
                continue
            w = config["weight"]
            total_weight += w
            val = factor_inputs.get(name, 50.0)
            confidence = factor_inputs.get(f"{name}_confidence", 1.0) * stage_conf
            normalized = (val - 50) / 50
            home_score += w * normalized
            uncertainty += w * (1 - confidence)

        if total_weight > 0:
            home_score /= total_weight
            uncertainty /= total_weight

        import numpy as np
        lambda_home = 1.4 * np.exp(home_score)
        lambda_away = 1.2 * np.exp(-home_score)

        return lambda_home, lambda_away, uncertainty

    def close(self):
        self.db.close()
