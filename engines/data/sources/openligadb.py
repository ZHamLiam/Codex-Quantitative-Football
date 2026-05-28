import httpx
from datetime import datetime

BASE_URL = "https://api.openligadb.de"

LEAGUES = {
    "bl1": "德甲", "bl2": "德乙", "bl3": "德丙",
    "uefacl": "欧冠", "uefael": "欧联",
    "wm2026": "世界杯",
}

class OpenLigaDBClient:
    def __init__(self):
        self.base = BASE_URL

    def _get(self, path: str):
        url = f"{self.base}{path}"
        resp = httpx.get(url, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def get_available_leagues(self):
        return self._get("/getavailableleagues")

    def get_matchdata(self, league: str, season: str):
        return self._get(f"/getmatchdata/{league}/{season}")

    def get_teams(self, league: str, season: str):
        return self._get(f"/getavailableteams/{league}/{season}")

    def get_current_season(self, league: str):
        return self._get(f"/getcurrentgroup/{league}")

def parse_match(m: dict) -> dict:
    dt_str = m.get("matchDateTimeUTC", m.get("matchDateTime", ""))
    try:
        dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        dt = datetime.now()

    team1 = m.get("team1", {})
    team2 = m.get("team2", {})
    results = m.get("matchResults", [])
    home_score = None
    away_score = None
    for r in results:
        if r.get("resultName") == "Endergebnis":
            home_score = r.get("pointsTeam1")
            away_score = r.get("pointsTeam2")

    return {
        "external_id": m.get("matchID"),
        "home_team": {"name": team1.get("teamName", ""), "short_name": team1.get("shortName", ""), "external_id": team1.get("teamId")},
        "away_team": {"name": team2.get("teamName", ""), "short_name": team2.get("shortName", ""), "external_id": team2.get("teamId")},
        "match_date": dt,
        "home_score": home_score,
        "away_score": away_score,
        "status": "completed" if m.get("matchIsFinished") else "scheduled",
        "group_name": m.get("group", {}).get("groupName", ""),
    }
