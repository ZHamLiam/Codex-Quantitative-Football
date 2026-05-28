import httpx, csv
from io import StringIO
from datetime import date

class ClubEloClient:
    def __init__(self):
        pass

    def get_ratings(self) -> list:
        today = date.today().isoformat()
        url = f"http://api.clubelo.com/{today}"
        resp = httpx.get(url, timeout=20)
        resp.raise_for_status()
        reader = csv.DictReader(StringIO(resp.text))
        return list(reader)

    def get_elo_for_team(self, club_name: str, ratings: list = None) -> float:
        if ratings is None:
            ratings = self.get_ratings()
        for r in ratings:
            if r["Club"].lower() == club_name.lower():
                return float(r["Elo"])
        return 1500.0

def normalize_club_name(team_name: str) -> str:
    mapping = {
        "Arsenal FC": "Arsenal", "Chelsea FC": "Chelsea",
        "Liverpool FC": "Liverpool", "Manchester City FC": "Man City",
        "Manchester United FC": "Man United", "Tottenham Hotspur FC": "Tottenham",
        "FC Barcelona": "Barcelona", "Real Madrid CF": "Real Madrid",
        "Atletico de Madrid": "Atletico", "FC Bayern Munchen": "Bayern",
        "Borussia Dortmund": "Dortmund", "Paris Saint-Germain FC": "Paris SG",
        "Juventus FC": "Juventus", "Inter Milan": "Inter",
        "AC Milan": "Milan", "SSC Napoli": "Napoli",
        "Olympique Lyonnais": "Lyon", "Olympique de Marseille": "Marseille",
        "AS Monaco FC": "Monaco", "AFC Ajax": "Ajax",
        "FC Porto": "Porto", "SL Benfica": "Benfica",
    }
    return mapping.get(team_name, team_name)