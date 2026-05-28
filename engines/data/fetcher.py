from engines.data.sources.football_data import FootballDataClient
from db.database import SessionLocal
from db.models import Team, Match
from datetime import datetime

LEAGUE_MAP = {
    "PL": "英超", "PD": "西甲", "BL1": "德甲",
    "SA": "意甲", "FL1": "法甲", "CL": "欧冠", "WC": "世界杯"
}

class DataFetcher:
    def __init__(self):
        self.client = FootballDataClient()
        self.db = SessionLocal()

    def sync_teams_for_competition(self, competition_code: str):
        data = self.client.get_matches(competition_code, "2026-01-01", "2026-12-31")
        teams_seen = set()
        for match in data.get("matches", []):
            for side in ["homeTeam", "awayTeam"]:
                t = match[side]
                ext_id = t["id"]
                if ext_id not in teams_seen:
                    teams_seen.add(ext_id)
                    existing = self.db.query(Team).filter_by(external_id=ext_id).first()
                    if not existing:
                        team = Team(name=t["name"], short_name=t.get("shortName", ""), external_id=ext_id, league=LEAGUE_MAP.get(competition_code, ""))
                        self.db.add(team)
        self.db.commit()

    def sync_matches(self, competition_code: str, date_from: str, date_to: str):
        data = self.client.get_matches(competition_code, date_from, date_to)
        for m in data.get("matches", []):
            ext_id = m["id"]
            existing = self.db.query(Match).filter_by(external_id=ext_id).first()
            if existing:
                continue
            home = self.db.query(Team).filter_by(external_id=m["homeTeam"]["id"]).first()
            away = self.db.query(Team).filter_by(external_id=m["awayTeam"]["id"]).first()
            if not home or not away:
                continue
            match = Match(
                home_team_id=home.id, away_team_id=away.id,
                match_date=datetime.fromisoformat(m["utcDate"].replace("Z", "+00:00")),
                league=LEAGUE_MAP.get(competition_code, ""),
                stage="league", status="scheduled",
                external_id=ext_id
            )
            self.db.add(match)
        self.db.commit()
        print(f"Synced {len(data.get('matches', []))} matches for {competition_code}")

    def close(self):
        self.db.close()
