"""
Run predefined Sorare basketball queries from the CLI.

Example:
    python -m src.projections.query_sorare_games --player-slug lebron-james --query recent_scores --limit 10
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from getpass import getpass
from pathlib import Path
import csv
from typing import Dict, List, Optional, Tuple

import requests

from .sorare_auth import GRAPHQL_URL, SorareAuthenticator


RECENT_SCORES_QUERY = """
query PlayerRecentScores($slug: String!, $limit: Int!) {
  anyPlayer(slug: $slug) {
    __typename
    ... on NBAPlayer {
      displayName
      playerGameScores(last: $limit, lowCoverage: true) {
        __typename
        ... on BasketballPlayerGameScore {
          score
          projectedScore
          basketballGame {
            uuid
            date
            homeTeam { code name }
            awayTeam { code name }
            statusTyped
            scoresByQuarter { quarter score }
          }
        }
      }
    }
  }
}
"""

BOX_SCORE_QUERY = """
query PlayerBoxScores($slug: String!, $limit: Int!) {
  anyPlayer(slug: $slug) {
    __typename
    ... on NBAPlayer {
      playerGameScores(last: $limit, lowCoverage: true) {
        __typename
        ... on BasketballPlayerGameScore {
          basketballGame { uuid date }
          basketballPlayerGameStats {
            minsPlayed
            points
            rebounds
            assists
            steals
            blocks
            turnovers
            threePointsMade
            doubleDouble
            tripleDouble
          }
        }
      }
    }
  }
}
"""

GAME_CONTEXT_QUERY = """
query PlayerGameContext($slug: String!, $limit: Int!) {
  anyPlayer(slug: $slug) {
    __typename
    ... on NBAPlayer {
      playerGameScores(last: $limit, lowCoverage: true) {
        __typename
        ... on BasketballPlayerGameScore {
          basketballGame {
            uuid
            date
            homeTeam { code name }
            awayTeam { code name }
            homeStats { stats { name value } }
            awayStats { stats { name value } }
          }
        }
      }
    }
  }
}
"""

PLAYER_AVERAGES_QUERY = """
query PlayerAverages($slug: String!) {
  anyPlayer(slug: $slug) {
    __typename
    ... on NBAPlayer {
      displayName
      averageStats(limit: LAST_10, type: POINTS)
      averageStats(limit: LAST_10, type: ASSISTS)
      averageStats(limit: LAST_10, type: REBOUNDS)
      nextClassicFixtureProjectedScore
      nextClassicFixtureProjectedGrade { grade score }
    }
  }
}
"""

FUTURE_GAMES_QUERY = """
query PlayerFutureGames($slug: String!) {
  anyPlayer(slug: $slug) {
    __typename
    ... on NBAPlayer {
      displayName
      anyFutureGames(first: 5) {
        nodes {
          ... on GameOfBasketball {
            uuid
            date
            statusTyped
            homeTeam { code name }
            awayTeam { code name }
            so5Fixture { slug name deadline }
          }
        }
      }
    }
  }
}
"""

QUERY_MAP = {
    "recent_scores": {
        "query": RECENT_SCORES_QUERY,
        "requires_limit": True,
        "description": "Recent Sorare scores with projected score + game metadata",
    },
    "box_scores": {
        "query": BOX_SCORE_QUERY,
        "requires_limit": True,
        "description": "Box score stats from basketballPlayerGameStats",
    },
    "game_context": {
        "query": GAME_CONTEXT_QUERY,
        "requires_limit": True,
        "description": "Team-level stats (pace/def rating) for recent games",
    },
    "averages": {
        "query": PLAYER_AVERAGES_QUERY,
        "requires_limit": False,
        "description": "Last-10 averages and projections",
    },
    "future_games": {
        "query": FUTURE_GAMES_QUERY,
        "requires_limit": False,
        "description": "Upcoming schedule snapshot",
    },
}

def _format_error(response: requests.Response) -> str:
    try:
        return json.dumps(response.json(), indent=2)
    except ValueError:
        return response.text


def _graphql(
    session: requests.Session,
    *,
    token: str,
    audience: str,
    query: str,
    variables: Dict[str, object],
) -> Dict[str, object]:
    response = session.post(
        GRAPHQL_URL,
        json={"query": query, "variables": variables},
        headers={
            "Authorization": f"Bearer {token}",
            "JWT-AUD": audience,
            "Content-Type": "application/json",
        },
        timeout=30,
    )
    try:
        response.raise_for_status()
    except requests.HTTPError as exc:
        raise requests.HTTPError(f"{exc} | Response: {_format_error(response)}") from exc
    payload = response.json()
    if "errors" in payload:
        raise RuntimeError(json.dumps(payload["errors"], indent=2))
    return payload["data"]


def _filter_clubs(search_term: Optional[str]) -> List[Dict[str, object]]:
    clubs = NBA_CLUBS
    if search_term:
        term = search_term.lower()
        clubs = [
            club
            for club in NBA_CLUBS
            if term in club["name"].lower()
            or term in club.get("code", "").lower()
            or term in club["slug"].lower()
        ]
    if not clubs:
        raise SystemExit(f"No NBA clubs matched '{search_term}'.")
    return clubs


def _select_club(
    clubs: List[Dict[str, object]],
    *,
    interactive: bool,
) -> Dict[str, object]:
    if not clubs:
        raise SystemExit("No NBA clubs available.")
    if len(clubs) == 1 or not interactive:
        return clubs[0]
    print("Select a team:")
    for idx, club in enumerate(clubs, start=1):
        print(f"{idx}. {club.get('name')} ({club.get('code')}) – slug: {club.get('slug')}")
    selection = input("Enter number: ").strip()
    try:
        idx = int(selection) - 1
        return clubs[idx]
    except (ValueError, IndexError):
        raise SystemExit("Invalid team selection.") from None


def _fetch_roster(club_slug: str) -> List[Dict[str, str]]:
    roster = NBA_ROSTERS.get(club_slug)
    if not roster:
        raise SystemExit(
            f"No static roster available for '{club_slug}'. Update src/projections/nba_data.py to add it."
        )
    return roster


def _select_player(roster: List[Dict[str, str]], *, interactive: bool) -> str:
    if not roster:
        raise SystemExit("Roster is empty.")
    if not interactive:
        return roster[0]["slug"]
    print("Select a player:")
    for idx, player in enumerate(roster, start=1):
        print(f"{idx}. {player.get('displayName')} – {player.get('slug')}")
    selection = input("Enter number: ").strip()
    try:
        idx = int(selection) - 1
        return roster[idx]["slug"]
    except (ValueError, IndexError):
        raise SystemExit("Invalid player selection.") from None


def parse_args() -> argparse.Namespace:
    available = "\n  ".join(
        f"{idx + 1}. {name} – {meta['description']}" for idx, (name, meta) in enumerate(QUERY_MAP.items())
    )
    parser = argparse.ArgumentParser(
        description="Run Sorare basketball queries (recent scores, box score stats, averages, future games).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"Queries:\n  {available}",
    )
    parser.add_argument("--team", help="Team name/slug/code to pre-filter (e.g. lakers)")
    parser.add_argument("--player-slug", help="Sorare player slug (e.g. lebron-james)")
    parser.add_argument("--query", choices=QUERY_MAP.keys(), help="Which query to run")
    parser.add_argument("--limit", type=int, help="Number of recent games (default: 10)")
    parser.add_argument("--jwt-audience", help="JWT audience string (default: nbaanalysts-cli)")
    parser.add_argument("--output", type=Path, help="File path to write JSON results")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output.")
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Prompt for missing parameters (query selection, limits, etc.).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    query_name = args.query
    if not query_name and not args.interactive:
        raise SystemExit("Specify --query or enable --interactive mode.")
    if args.interactive:
        if not args.team and not args.player_slug:
            args.team = input("Team name/slug (e.g. lakers): ").strip()
        if not query_name:
            print("Select a query:")
            for idx, (name, meta) in enumerate(QUERY_MAP.items(), start=1):
                print(f"{idx}. {name} – {meta['description']}")
            selection = input("Enter number: ").strip()
            try:
                idx = int(selection) - 1
                query_name = list(QUERY_MAP.keys())[idx]
            except (ValueError, IndexError):
                raise SystemExit("Invalid selection.") from None
        if args.limit is None:
            args.limit = 10
        if not args.jwt_audience:
            args.jwt_audience = input("JWT audience (default nbaanalysts-cli): ").strip() or "nbaanalysts-cli"
    if not args.player_slug and not args.team:
        raise SystemExit("Provide --player-slug or --team (or enable --interactive).")
    if not query_name:
        raise SystemExit("No query selected.")
    config = QUERY_MAP[query_name]
    if config["requires_limit"]:
        if args.limit is None:
            raise SystemExit("--limit is required for this query (or run in --interactive mode).")
        if args.limit <= 0:
            raise SystemExit("--limit must be positive.")
    if not args.jwt_audience:
        args.jwt_audience = "nbaanalysts-cli"

    email = input("Sorare email: ").strip()
    password = getpass("Sorare password (input hidden): ")
    if not email or not password:
        raise SystemExit("Email and password are required.")

    session = requests.Session()
    auth = SorareAuthenticator(user_agent="nbaanalysts-query/0.2", session=session)
    try:
        result = auth.authenticate_with_password(email, password, args.jwt_audience)
    except RuntimeError as exc:
        raise SystemExit(f"Authentication failed: {exc}") from exc

    if not args.player_slug:
        if not args.interactive:
            raise SystemExit("Player selection requires --interactive mode when --player-slug is omitted.")
        clubs = _filter_clubs(args.team)
        selected_club = _select_club(clubs, interactive=True)
        roster = _fetch_roster(selected_club["slug"])
        args.player_slug = _select_player(roster, interactive=True)

    variables: Dict[str, object] = {"slug": args.player_slug}
    if config["requires_limit"]:
        variables["limit"] = args.limit

    data = _graphql(
        session,
        token=result.token,
        audience=args.jwt_audience,
        query=config["query"],
        variables=variables,
    )
    csv_rows: List[Dict[str, str]] = []
    player_section = data.get("anyPlayer") or {}
    display_name = player_section.get("displayName") or args.player_slug

    if query_name in {"recent_scores", "box_scores", "game_context"}:
        scores = [
            node
            for node in (player_section.get("playerGameScores") or [])
            if node.get("__typename") == "BasketballPlayerGameScore"
        ]
        if not scores:
            raise SystemExit("No game scores returned for this query.")
        for entry in scores:
            game = entry.get("basketballGame") or {}
            stats = entry.get("basketballPlayerGameStats") or {}
            csv_rows.append(
                {
                    "player": display_name,
                    "game_date": (game.get("date") or "")[:10],
                    "home_team": (game.get("homeTeam") or {}).get("code") or (game.get("homeTeam") or {}).get("name") or "",
                    "away_team": (game.get("awayTeam") or {}).get("code") or (game.get("awayTeam") or {}).get("name") or "",
                    "score": str(entry.get("score") or ""),
                    "projected_score": str(entry.get("projectedScore") or ""),
                    "mins": str(stats.get("minsPlayed") or ""),
                    "points": str(stats.get("points") or ""),
                    "rebounds": str(stats.get("rebounds") or ""),
                    "assists": str(stats.get("assists") or ""),
                    "steals": str(stats.get("steals") or ""),
                    "blocks": str(stats.get("blocks") or ""),
                    "turnovers": str(stats.get("turnovers") or ""),
                    "threes": str(stats.get("threePointsMade") or ""),
                }
            )
    elif query_name == "averages":
        csv_rows.append(
            {
                "player": display_name,
                "points_avg_l10": str(player_section.get("averageStats")),
                "next_projected_score": str(player_section.get("nextClassicFixtureProjectedScore") or ""),
            }
        )
    elif query_name == "future_games":
        games = (((player_section.get("anyFutureGames") or {}).get("nodes")) or [])
        if not games:
            raise SystemExit("No upcoming games returned.")
        for game in games:
            csv_rows.append(
                {
                    "player": display_name,
                    "game_date": (game.get("date") or "")[:10],
                    "status": game.get("statusTyped") or "",
                    "home_team": (game.get("homeTeam") or {}).get("code") or (game.get("homeTeam") or {}).get("name") or "",
                    "away_team": (game.get("awayTeam") or {}).get("code") or (game.get("awayTeam") or {}).get("name") or "",
                    "fixture": ((game.get("so5Fixture") or {}).get("slug") or ""),
                }
            )
    else:
        raise SystemExit(f"Unsupported query for CSV export: {query_name}")

    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    safe_player = args.player_slug.replace("/", "_")
    default_path = Path("outputs/sorare_queries") / f"{safe_player}_{query_name}_{timestamp}.csv"
    output_path = args.output or default_path
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if csv_rows:
        fieldnames = list(csv_rows[0].keys())
    else:
        fieldnames = ["player"]
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in csv_rows:
            writer.writerow(row)
    print(f"Saved results to {output_path}")


if __name__ == "__main__":
    main()
