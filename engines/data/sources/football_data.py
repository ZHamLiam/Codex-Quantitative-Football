import httpx
from config import settings

BASE_URL = "https://api.football-data.org/v4"

class FootballDataClient:
    def __init__(self):
        self.headers = {"X-Auth-Token": settings.football_data_api_key}

    def _get(self, path: str, params: dict = None):
        url = f"{BASE_URL}{path}"
        resp = httpx.get(url, headers=self.headers, params=params, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def get_competitions(self):
        target = {
            "PL": "英超", "PD": "西甲", "BL1": "德甲",
            "SA": "意甲", "FL1": "法甲", "CL": "欧冠", "WC": "世界杯"
        }
        data = self._get("/competitions")
        return [c for c in data.get("competitions", []) if c["code"] in target]

    def get_matches(self, competition_code: str, date_from: str, date_to: str):
        return self._get(f"/competitions/{competition_code}/matches", {
            "dateFrom": date_from, "dateTo": date_to
        })

    def get_team(self, team_id: int):
        return self._get(f"/teams/{team_id}")

    def get_team_matches(self, team_id: int, limit: int = 10, status: str = "FINISHED"):
        return self._get(f"/teams/{team_id}/matches", {
            "limit": limit, "status": status
        })
