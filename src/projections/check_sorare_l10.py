"""
Quick helper to inspect a player's last-N Sorare scores (default L10).

Usage:
    python -m src.projections.check_sorare_l10 --player-slug lebron-james --games 10

You will be prompted for your Sorare email/password and optional JWT audience.
"""

from __future__ import annotations

import argparse
import statistics
from typing import Dict, List

import requests

from .sorare_auth import GRAPHQL_URL, SorareAuthenticator
from .credentials import EMAIL, PASSWORD

PLAYER_L10_QUERY = """
query PlayerRecentScores($slug: String!, $limit: Int!) {
  anyPlayer(slug: $slug) {
    __typename
    ... on NBAPlayer {
      slug
      displayName
      playerGameScores(last: $limit, lowCoverage: true) {
        __typename
        ... on BasketballPlayerGameScore {
          score
          basketballGame {
            date
            homeTeam { code name }
            awayTeam { code name }
          }
        }
      }
    }
  }
}
"""


def _graphql_with_token(
    session: requests.Session,
    *,
    token: str,
    audience: str,
    variables: Dict[str, object],
) -> Dict[str, object]:
    response = session.post(
        GRAPHQL_URL,
        json={"query": PLAYER_L10_QUERY, "variables": variables},
        headers={
            "Authorization": f"Bearer {token}",
            "JWT-AUD": audience,
            "Content-Type": "application/json",
        },
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()
    if "errors" in payload:
        raise RuntimeError(payload["errors"])
    return payload["data"]


def format_game(game: Dict[str, object]) -> str:
    date = (game or {}).get("date") or "unknown-date"
    home = ((game or {}).get("homeTeam") or {}).get("code") or ((game or {}).get("homeTeam") or {}).get("name")
    away = ((game or {}).get("awayTeam") or {}).get("code") or ((game or {}).get("awayTeam") or {}).get("name")
    matchup = f"{away or 'AWAY'} @ {home or 'HOME'}"
    return f"{date[:10]} | {matchup}"


def main() -> None:
    parser = argparse.ArgumentParser(description="Print Sorare L10 scores for an NBA player.")
    parser.add_argument("--player-slug", required=True, help="Sorare player slug, e.g. lebron-james")
    parser.add_argument("--games", type=int, default=10, help="Number of recent games (default: 10)")
    parser.add_argument("--jwt-audience", default="nbaanalysts-cli", help="JWT audience string (default: nbaanalysts-cli)")
    args = parser.parse_args()

    email = EMAIL
    password = PASSWORD
    if not email or not password:
        raise SystemExit("Email and password are required.")

    session = requests.Session()
    auth = SorareAuthenticator(user_agent="nbaanalysts-l10-check/0.1", session=session)
    try:
        result = auth.authenticate_with_password(email, password, args.jwt_audience)
    except RuntimeError as exc:
        raise SystemExit(f"Authentication failed: {exc}") from exc

    data = _graphql_with_token(
        session,
        token=result.token,
        audience=args.jwt_audience,
        variables={"slug": args.player_slug, "limit": args.games},
    )
    player = data.get("anyPlayer") or {}
    if player.get("__typename") not in ["NBAPlayer", "Player"]:
        raise SystemExit(f"Slug {args.player_slug} is not an NBA player.")
    scores = [
        node
        for node in (player.get("playerGameScores") or [])
        if node.get("__typename") == "BasketballPlayerGameScore" and node.get("score") is not None
    ]
    if not scores:
        raise SystemExit("No Sorare scores returned for this player.")

    print(f"{player.get('displayName')} – last {len(scores)} Sorare scores")
    printable: List[float] = []
    for entry in scores:
        score = float(entry["score"])
        printable.append(score)
        game = entry.get("basketballGame") or {}
        print(f"{format_game(game)} -> {score:.1f}")

    avg = statistics.mean(printable)
    print(f"\nAverage: {avg:.2f}")


if __name__ == "__main__":
    main()