import random

# Lottery weights, matched by position after sorting teams by points
# (index 0 = fewest points = most tickets).
WEIGHTS = [35, 22, 15, 10, 7, 5, 4, 2]

NUM_TEAMS = len(WEIGHTS)


def prompt_for_teams(n):
    """Ask for n team names and point totals. Returns a list of (name, points)."""
    entries = []
    print(f"\nEnter the {n} non-playoff teams and their point totals.\n")
    for i in range(1, n + 1):
        name = input(f"Team {i} name: ").strip()
        while not name:
            name = input(f"Team {i} name (can't be blank): ").strip()

        while True:
            raw = input(f"  {name} points: ").strip()
            try:
                points = float(raw)
                break
            except ValueError:
                print("  Please enter a number.")

        entries.append((name, points))
    return entries


def order_teams(entries):
    """Sort by points, least to greatest. Ties keep the order they were entered."""
    return sorted(entries, key=lambda e: e[1])


def print_odds_table(entries, weights):
    total = sum(weights)
    print(f"{'Rank':<6}{'Team':<35}{'Points':<10}{'Tickets':<10}{'Odds (top pick)'}")
    print("-" * 78)
    for i, ((team, pts), w) in enumerate(zip(entries, weights), start=1):
        pct = 100 * w / total
        print(f"{i:<6}{team:<35}{pts:<10g}{w:<10}{pct:.1f}%")
    print()


def run_lottery(teams, weights):
    """
    Draws the full pick order (1st through Nth). Each remaining team's weight
    determines their odds of winning the NEXT available pick. Once a team is
    drawn, they're removed from the pool and the process repeats.
    """
    pool = list(zip(teams, weights))
    draft_order = []

    pick_num = 1
    while pool:
        names, wts = zip(*pool)
        winner = random.choices(names, weights=wts, k=1)[0]
        draft_order.append((pick_num, winner))
        pool = [(n, w) for n, w in pool if n != winner]
        pick_num += 1

    return draft_order


if __name__ == "__main__":
    entries = prompt_for_teams(NUM_TEAMS)
    ordered = order_teams(entries)
    team_names = [name for name, _ in ordered]

    print("\n=== LOTTERY ODDS (chance at the #1 overall pick) ===\n")
    print_odds_table(ordered, WEIGHTS)

    print("=== DRAWING FULL DRAFT ORDER ===\n")
    result = run_lottery(team_names, WEIGHTS)

    print(f"{'Pick #':<10}{'Team'}")
    print("-" * 40)
    for pick_num, team in result:
        print(f"{pick_num:<10}{team}")