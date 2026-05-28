from engines.data.sources.football_data import FootballDataClient
from db.database import SessionLocal
from db.models import Team, Match
from datetime import datetime

LEAGUE_MAP = {
    "PL": "英超", "PD": "西甲", "BL1": "德甲",
    "SA": "意甲", "FL1": "法甲", "CL": "欧冠", "WC": "世界杯"
}

def sync_all():
    client = FootballDataClient()
    db = SessionLocal()
    competitions = client.get_competitions()
    total_matches = 0
    total_teams = 0

    for comp in competitions:
        code = comp["code"]
        league_name = LEAGUE_MAP.get(code, code)
        print(f"\n{'='*50}")
        print(f"Syncing {league_name} ({code})...")

        try:
            data = client.get_matches(code, "2026-01-01", "2026-12-31")
        except Exception as e:
            print(f"  API error for {code}: {e}")
            continue

        matches_data = data.get("matches", [])
        if not matches_data:
            print(f"  No matches found for {code}")
            continue
        print(f"  Found {len(matches_data)} matches")

        teams_seen = set()
        for m in matches_data:
            for side in ["homeTeam", "awayTeam"]:
                t = m.get(side, {})
                if not t or "id" not in t:
                    continue
                ext_id = t["id"]
                if ext_id in teams_seen:
                    continue
                teams_seen.add(ext_id)
                existing = db.query(Team).filter_by(external_id=ext_id).first()
                if not existing:
                    name = t.get("name") or t.get("shortName") or t.get("tla") or f"Team-{ext_id}"
                    team = Team(
                        name=name,
                        short_name=t.get("tla", ""),
                        external_id=ext_id,
                        league=league_name,
                    )
                    db.add(team)
        db.commit()
        total_teams += len(teams_seen)
        print(f"  Teams: {len(teams_seen)}")

        synced = 0
        for m in matches_data:
            mid = m.get("id")
            if not mid:
                continue
            existing = db.query(Match).filter_by(external_id=mid).first()
            if existing:
                continue
            home_t = m.get("homeTeam", {})
            away_t = m.get("awayTeam", {})
            home = db.query(Team).filter_by(external_id=home_t.get("id")).first()
            away = db.query(Team).filter_by(external_id=away_t.get("id")).first()
            if not home or not away:
                continue
            dt_str = m.get("utcDate", "")
            try:
                dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                continue
            score = m.get("score", {})
            full = score.get("fullTime", {})
            status = "completed" if m.get("status") == "FINISHED" else "scheduled"
            stage_name = m.get("stage", "")
            stage = "league"
            if "ROUND_OF_16" in stage_name: stage = "r16"
            elif "QUARTER" in stage_name: stage = "qf"
            elif "SEMI" in stage_name: stage = "sf"
            elif "FINAL" in stage_name: stage = "final"
            if m.get("group", "").startswith("Group"): stage = "group_md1"

            match = Match(
                home_team_id=home.id, away_team_id=away.id,
                match_date=dt, league=league_name, stage=stage,
                status=status, home_score=full.get("home"), away_score=full.get("away"),
                external_id=mid
            )
            db.add(match)
            synced += 1
        db.commit()
        total_matches += synced
        print(f"  Matches synced: {synced}")

    db.close()
    print(f"\n{'='*50}")
    print(f"Total: {total_teams} teams, {total_matches} matches")

if __name__ == "__main__":
    sync_all()