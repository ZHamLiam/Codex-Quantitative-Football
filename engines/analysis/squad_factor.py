def calc_squad_integrity(available_starters: int, ideal_starters: int = 11) -> float:
    return (available_starters / ideal_starters) * 100

def calc_chemistry(players: list[str], co_appearances: dict) -> float:
    if len(players) < 2:
        return 50.0
    total = 0
    count = 0
    for i in range(len(players)):
        for j in range(i+1, len(players)):
            key = (players[i], players[j])
            total += co_appearances.get(key, 0)
            count += 1
    avg = total / count if count > 0 else 0
    return min(avg * 10, 100.0)
