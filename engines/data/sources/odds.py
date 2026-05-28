import httpx
from config import settings

BASE_URL = "https://api.the-odds-api.com/v4"

SPORT_MAP = {
    "世界杯": "soccer_fifa_world_cup",
    "欧冠": "soccer_uefa_champs_league",
    "法甲": "soccer_france_ligue_one",
}

class OddsClient:
    def __init__(self):
        self.key = settings.odds_api_key

    def get_odds(self, sport: str) -> list:
        sport_key = SPORT_MAP.get(sport, "")
        if not sport_key:
            return []
        url = BASE_URL + "/sports/" + sport_key + "/odds/"
        params = {"apiKey": self.key, "regions": "eu", "markets": "h2h", "oddsFormat": "decimal"}
        resp = httpx.get(url, params=params, timeout=15)
        if resp.status_code != 200:
            return []
        return resp.json()

    def get_best_odds(self, match_name_home: str, match_name_away: str, sport: str) -> dict:
        """Get best h2h odds for a match. Returns {home, draw, away}"""
        data = self.get_odds(sport)
        for m in data:
            if match_name_home.lower() in m["home_team"].lower() and match_name_away.lower() in m["away_team"].lower():
                best = {}
                for bm in m.get("bookmakers", []):
                    for market in bm.get("markets", []):
                        for o in market.get("outcomes", []):
                            name = o["name"].lower()
                            price = o["price"]
                            key = "home" if name == match_name_home.lower() else ("away" if name == match_name_away.lower() else "draw")
                            if key not in best or price > best[key]:
                                best[key] = price
                return best
        return {"home": 2.0, "draw": 3.5, "away": 3.5}