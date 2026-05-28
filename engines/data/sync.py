import httpx
from datetime import datetime
from db.database import SessionLocal
from db.models import Team, Match

# World Cup 2026 groups - known teams
WC_TEAMS = {
    "A": [("加拿大", "CAN"), ("墨西哥", "MEX"), ("牙买加", "JAM"), ("待定", "TBD")],
    "B": [("阿根廷", "ARG"), ("秘鲁", "PER"), ("乌拉圭", "URU"), ("待定", "TBD")],
    "C": [("巴西", "BRA"), ("哥伦比亚", "COL"), ("塞内加尔", "SEN"), ("待定", "TBD")],
    "D": [("法国", "FRA"), ("摩洛哥", "MAR"), ("日本", "JPN"), ("待定", "TBD")],
    "E": [("英格兰", "ENG"), ("荷兰", "NED"), ("韩国", "KOR"), ("待定", "TBD")],
    "F": [("德国", "GER"), ("西班牙", "ESP"), ("埃及", "EGY"), ("待定", "TBD")],
    "G": [("葡萄牙", "POR"), ("比利时", "BEL"), ("伊朗", "IRN"), ("待定", "TBD")],
    "H": [("意大利", "ITA"), ("克罗地亚", "CRO"), ("澳大利亚", "AUS"), ("待定", "TBD")],
}

WC_MATCHES = [
    # Group A - June 11
    ("墨西哥", "加拿大", "2026-06-11T21:00:00", "世界杯", "group_md1"),
    # Group B - June 12
    ("阿根廷", "秘鲁", "2026-06-12T18:00:00", "世界杯", "group_md1"),
    # Group C - June 13
    ("巴西", "哥伦比亚", "2026-06-13T21:00:00", "世界杯", "group_md1"),
    # Group D - June 14
    ("法国", "摩洛哥", "2026-06-14T21:00:00", "世界杯", "group_md1"),
    # Group E - June 15
    ("英格兰", "荷兰", "2026-06-15T21:00:00", "世界杯", "group_md1"),
    # Group F - June 16
    ("德国", "西班牙", "2026-06-16T21:00:00", "世界杯", "group_md1"),
    # Group G - June 17
    ("葡萄牙", "比利时", "2026-06-17T21:00:00", "世界杯", "group_md1"),
    # Group H - June 18
    ("意大利", "克罗地亚", "2026-06-18T21:00:00", "世界杯", "group_md1"),
]

def sync_openligadb(league: str = "bl1", season: str = "2025"):
    """Sync Bundesliga data from OpenLigaDB"""
    db = SessionLocal()
    try:
        resp = httpx.get(f"https://api.openligadb.de/getmatchdata/{league}/{season}", timeout=30)
        matches = resp.json()
        teams_seen = set()

        for m in matches:
            for side in ["team1", "team2"]:
                t = m[side]
                tid = t["teamId"]
                if tid not in teams_seen:
                    teams_seen.add(tid)
                    existing = db.query(Team).filter_by(external_id=tid).first()
                    if not existing:
                        team = Team(
                            name=t["teamName"], short_name=t.get("shortName", ""),
                            external_id=tid, league="德甲", country="德国"
                        )
                        db.add(team)
        db.commit()

        # Sync matches
        for m in matches:
            mid = m["matchID"]
            existing = db.query(Match).filter_by(external_id=mid).first()
            if existing:
                continue
            t1 = m["team1"]
            t2 = m["team2"]
            home = db.query(Team).filter_by(external_id=t1["teamId"]).first()
            away = db.query(Team).filter_by(external_id=t2["teamId"]).first()
            if not home or not away:
                continue
            dt_str = m.get("matchDateTimeUTC", m.get("matchDateTime", ""))
            try:
                dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                continue
            results = m.get("matchResults", [])
            h_score = a_score = None
            for r in results:
                if r.get("resultName") == "Endergebnis":
                    h_score = r.get("pointsTeam1")
                    a_score = r.get("pointsTeam2")
            status = "completed" if m.get("matchIsFinished") else "scheduled"
            match = Match(
                home_team_id=home.id, away_team_id=away.id,
                match_date=dt, league="德甲", stage="league",
                status=status, home_score=h_score, away_score=a_score,
                external_id=mid
            )
            db.add(match)
        db.commit()
        print(f"Synced {len(matches)} Bundesliga matches")
    finally:
        db.close()

def seed_world_cup():
    """Seed World Cup 2026 teams and sample matches"""
    db = SessionLocal()
    existing = db.query(Match).filter_by(league="世界杯").count()
    if existing > 0:
        print(f"World Cup data already exists ({existing} matches), skipping.")
        db.close()
        return

    # Create teams
    team_map = {}
    for group, teams in WC_TEAMS.items():
        for name, code in teams:
            if name == "待定":
                continue
            t = Team(name=name, short_name=code, league="世界杯", country=name)
            db.add(t)
            db.flush()
            team_map[name] = t.id

    db.commit()

    # Create matches
    for home_name, away_name, dt_str, league, stage in WC_MATCHES:
        if home_name not in team_map or away_name not in team_map:
            continue
        dt = datetime.fromisoformat(dt_str)
        match = Match(
            home_team_id=team_map[home_name], away_team_id=team_map[away_name],
            match_date=dt, league=league, stage=stage,
            status="scheduled", external_id=None
        )
        db.add(match)

    db.commit()
    db.close()
    print(f"Seeded {len(WC_MATCHES)} World Cup matches + {len(team_map)} teams")

if __name__ == "__main__":
    print("Syncing Bundesliga...")
    sync_openligadb()
    print("Seeding World Cup...")
    seed_world_cup()
    print("Done!")
