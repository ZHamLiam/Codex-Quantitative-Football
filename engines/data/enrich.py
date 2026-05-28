from engines.data.sources.clubelo import ClubEloClient
from db.database import SessionLocal
from db.models import Team

# Map football-data.org names to ClubElo names
NAME_MAP = {
    "Arsenal FC": "Arsenal", "Chelsea FC": "Chelsea", "Liverpool FC": "Liverpool",
    "Manchester City FC": "Man City", "Manchester United FC": "Man United",
    "Tottenham Hotspur FC": "Tottenham", "Newcastle United FC": "Newcastle",
    "Aston Villa FC": "Aston Villa", "Everton FC": "Everton",
    "West Ham United FC": "West Ham", "Brighton & Hove Albion FC": "Brighton",
    "Crystal Palace FC": "Crystal Palace", "Fulham FC": "Fulham",
    "Wolverhampton Wanderers FC": "Wolves", "Nottingham Forest FC": "Nottm Forest",
    "AFC Bournemouth": "Bournemouth", "Brentford FC": "Brentford",
    "FC Barcelona": "Barcelona", "Real Madrid CF": "Real Madrid",
    "Atletico de Madrid": "Atletico", "Sevilla FC": "Sevilla",
    "Real Sociedad": "Real Sociedad", "Real Betis": "Betis",
    "Villarreal CF": "Villarreal", "Athletic Club": "Athletic",
    "Valencia CF": "Valencia", "FC Bayern Munchen": "Bayern",
    "Borussia Dortmund": "Dortmund", "RB Leipzig": "RB Leipzig",
    "Bayer 04 Leverkusen": "Leverkusen", "Eintracht Frankfurt": "Eintracht Frankfurt",
    "VfB Stuttgart": "Stuttgart", "VfL Wolfsburg": "Wolfsburg",
    "Borussia Monchengladbach": "M'gladbach", "SC Freiburg": "Freiburg",
    "TSG 1899 Hoffenheim": "Hoffenheim", "1. FSV Mainz 05": "Mainz",
    "FC Augsburg": "Augsburg", "SV Werder Bremen": "Werder Bremen",
    "1. FC Union Berlin": "Union Berlin", "1. FC Heidenheim": "Heidenheim",
    "Juventus FC": "Juventus", "Inter Milan": "Inter", "AC Milan": "Milan",
    "SSC Napoli": "Napoli", "Atalanta BC": "Atalanta", "AS Roma": "Roma",
    "SS Lazio": "Lazio", "ACF Fiorentina": "Fiorentina",
    "Bologna FC 1909": "Bologna", "Torino FC": "Torino",
    "Paris Saint-Germain FC": "Paris SG", "Olympique Lyonnais": "Lyon",
    "Olympique de Marseille": "Marseille", "AS Monaco FC": "Monaco",
    "LOSC Lille": "Lille", "Stade Rennais FC": "Rennes", "RC Lens": "Lens",
    "OGC Nice": "Nice", "Stade de Reims": "Reims",
    "AFC Ajax": "Ajax", "PSV": "PSV", "Feyenoord Rotterdam": "Feyenoord",
    "FC Porto": "Porto", "SL Benfica": "Benfica", "Sporting CP": "Sporting CP",
    "FC Salzburg": "Salzburg", "Celtic FC": "Celtic", "Club Brugge KV": "Club Brugge",
    "FC Shakhtar Donetsk": "Shakhtar", "GNK Dinamo Zagreb": "Dinamo Zagreb",
    "FK Crvena Zvezda": "Red Star",
}

def enrich_elo():
    client = ClubEloClient()
    ratings = client.get_ratings()
    elo_dict = {r["Club"].lower(): float(r["Elo"]) for r in ratings}
    print(f"Loaded {len(ratings)} club Elo ratings")

    db = SessionLocal()
    teams = db.query(Team).all()
    matched = 0
    unmatched = []

    for team in teams:
        name = NAME_MAP.get(team.name)
        if name and name.lower() in elo_dict:
            team.elo_rating = elo_dict[name.lower()]
            matched += 1
            continue
        # Try direct lowercase match
        if team.name.lower() in elo_dict:
            team.elo_rating = elo_dict[team.name.lower()]
            matched += 1
            continue
        # Try substring match
        found = False
        for club_name, elo in elo_dict.items():
            if len(club_name) > 3 and club_name in team.name.lower():
                team.elo_rating = elo
                matched += 1
                found = True
                break
        if not found:
            unmatched.append(team.name)

    db.commit()
    db.close()
    print(f"Matched {matched}/{len(teams)} teams with Elo ratings")
    if unmatched:
        print(f"Unmatched ({len(unmatched)}): {unmatched[:10]}...")
    return matched

if __name__ == "__main__":
    enrich_elo()