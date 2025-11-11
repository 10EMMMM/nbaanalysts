"""
Fallback roster viewer that uses the static data in nba_data.py.
"""

from __future__ import annotations

from .nba_data import NBA_ROSTERS


def main() -> None:
    slug = input("Team slug (e.g. los-angeles-lakers): ").strip()
    if not slug:
        raise SystemExit("Team slug required.")
    roster = NBA_ROSTERS.get(slug)
    if not roster:
        print("No static roster entry for that slug. Update src/projections/nba_data.py to add it.")
        return
    print(f"{slug} roster ({len(roster)} players):")
    for player in roster:
        print(f"- {player['displayName']} ({player['slug']})")


if __name__ == "__main__":
    main()

