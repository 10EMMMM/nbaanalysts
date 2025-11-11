"""
CLI helper to pull Sorare NBA game logs straight from the public GraphQL API.

The projection pipeline expects these columns per game:
    game_date, opponent, minutes, usage_rate, true_shooting_pct,
    sorare_score, pace, opponent_def_rating

This script signs into Sorare (by prompting for your credentials), requests the
latest game logs for a player, and writes a CSV compatible with
`data/game_logs/*.csv`.

Sorare occasionally tweaks field names in their schema. If the default query
below stops working, adjust `PLAYER_GAME_LOGS_QUERY` accordingly or pass a
custom `--query-file`.
"""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from datetime import datetime
from getpass import getpass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import requests

from .sorare_auth import SorareAuthenticator

API_URL = "https://api.sorare.com/graphql"
USER_AGENT = "nbaanalysts/0.1 (+https://github.com/10EMMMM/nbaanalysts)"

# NOTE: Field names are based on the current public Sorare API schema.
# Update them if Sorare renames anything.
PLAYER_GAME_LOGS_QUERY = """
query PlayerGameLogs($slug: String!, $limit: Int!) {
  anyPlayer(slug: $slug) {
    __typename
    ... on NBAPlayer {
      slug
      displayName
      playerGameScores(last: $limit, lowCoverage: true) {
        __typename
        ... on BasketballPlayerGameScore {
          score
          position
          basketballGame {
            date
            homeTeam {
              slug
              code
              name
            }
            awayTeam {
              slug
              code
              name
            }
            homeStats {
              stats {
                name
                value
              }
            }
            awayStats {
              stats {
                name
                value
              }
            }
          }
          basketballPlayerGameStats {
            minsPlayed
            points
            rebounds
            assists
            steals
            blocks
            turnovers
            threePointsMade
            anyTeam {
              __typename
              ... on Club {
                slug
                code
                name
              }
              ... on NationalTeam {
                slug
                code
                name
              }
            }
          }
        }
      }
    }
  }
}
"""


def _iso_date(value: Optional[str]) -> str:
    if not value:
        return ""
    # Sorare returns ISO8601 with trailing Z; protect against missing timezone.
    cleaned = value.replace("Z", "+00:00") if value.endswith("Z") else value
    try:
        dt = datetime.fromisoformat(cleaned)
    except ValueError:
        return value
    return dt.date().isoformat()


def _safe_float(value: Any) -> Optional[float]:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _team_identifier(team: Optional[Dict[str, Any]]) -> Optional[str]:
    if not team:
        return None
    for key in ("slug", "code", "name"):
        value = team.get(key)
        if value:
            return str(value).lower()
    return None


def _team_matches(team: Optional[Dict[str, Any]], identifier: Optional[str]) -> bool:
    if not team or not identifier:
        return False
    identifier = identifier.lower()
    for key in ("slug", "code", "name"):
        value = team.get(key)
        if isinstance(value, str) and value.lower() == identifier:
            return True
    return False


def _team_side(player_team_id: Optional[str], home: Dict[str, Any], away: Dict[str, Any]) -> Optional[str]:
    if _team_matches(home, player_team_id):
        return "home"
    if _team_matches(away, player_team_id):
        return "away"
    return None


def _choose_opponent(
    player_team_id: Optional[str],
    home: Dict[str, Any],
    away: Dict[str, Any],
) -> tuple[Dict[str, Any], str]:
    side = _team_side(player_team_id, home, away)
    if side == "home":
        return away or {}, "away"
    if side == "away":
        return home or {}, "home"
    # Default to away team to record something even if mapping failed.
    return (away or home or {}), ("away" if away else "home")


def _stat_from_team(stats_section: Optional[Dict[str, Any]], *names: str) -> Optional[float]:
    if not stats_section:
        return None
    stats_list = stats_section.get("stats") or []
    lowered = [name.lower() for name in names]
    for stat in stats_list:
        label = str(stat.get("name") or "").lower()
        if label in lowered:
            return _safe_float(stat.get("value"))
    return None


@dataclass
class GameLogRow:
    game_date: str
    opponent: str
    minutes: Optional[float]
    usage_rate: Optional[float]
    true_shooting_pct: Optional[float]
    sorare_score: Optional[float]
    pace: Optional[float]
    opponent_def_rating: Optional[float]

    def as_csv_row(self) -> Dict[str, Any]:
        return {
            "game_date": self.game_date,
            "opponent": self.opponent,
            "minutes": "" if self.minutes is None else f"{self.minutes:.2f}",
            "usage_rate": "" if self.usage_rate is None else f"{self.usage_rate:.2f}",
            "true_shooting_pct": "" if self.true_shooting_pct is None else f"{self.true_shooting_pct:.3f}",
            "sorare_score": "" if self.sorare_score is None else f"{self.sorare_score:.1f}",
            "pace": "" if self.pace is None else f"{self.pace:.1f}",
            "opponent_def_rating": "" if self.opponent_def_rating is None else f"{self.opponent_def_rating:.1f}",
        }


class SorareClient:
    def __init__(self) -> None:
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})
        self.token: Optional[str] = None
        self.audience: Optional[str] = None
        self.authenticator = SorareAuthenticator(user_agent=USER_AGENT, session=self.session)

    def _post(
        self,
        query: str,
        variables: Optional[Dict[str, Any]] = None,
        *,
        auth: bool = False,
    ) -> Dict[str, Any]:
        headers = {"Content-Type": "application/json"}
        if auth:
            if not self.token:
                raise RuntimeError("Attempted authenticated request without a token.")
            headers["Authorization"] = f"Bearer {self.token}"
            if self.audience:
                headers["JWT-AUD"] = self.audience
        response = self.session.post(
            API_URL,
            json={"query": query, "variables": variables or {}},
            headers=headers,
            timeout=30,
        )
        try:
            response.raise_for_status()
        except requests.HTTPError as exc:
            detail = self._format_error(response)
            raise requests.HTTPError(f"{exc} | Response: {detail}") from exc
        payload = response.json()
        if "errors" in payload:
            raise RuntimeError(json.dumps(payload["errors"], indent=2))
        return payload["data"]
    
    @staticmethod
    def _format_error(response: requests.Response) -> str:
        try:
            return json.dumps(response.json(), indent=2)
        except ValueError:
            return response.text

    def sign_in(self, email: str, password: str, audience: str = "SORARE") -> None:
        self.audience = audience
        result = self.authenticator.authenticate_with_password(email, password, audience)
        self.token = result.token

    def fetch_game_logs(self, player_slug: str, limit: int, query: str) -> Dict[str, Any]:
        if not self.token:
            raise RuntimeError("Authenticate first by calling sign_in.")
        data = self._post(
            query,
            {"slug": player_slug, "limit": limit},
            auth=True,
        )
        return data


def _rows_from_payload(payload: Dict[str, Any]) -> List[GameLogRow]:
    player = payload.get("anyPlayer")
    if not player:
        raise RuntimeError("Unexpected response shape: anyPlayer missing.")
    if player.get("__typename") != "NBAPlayer":
        raise RuntimeError(f"Slug does not reference an NBA player: typename={player.get('__typename')}")
    scores = player.get("playerGameScores") or []
    rows: List[GameLogRow] = []
    for node in scores:
        if node.get("__typename") != "BasketballPlayerGameScore":
            continue
        stats = node.get("basketballPlayerGameStats") or {}
        game = node.get("basketballGame") or {}
        home_team = game.get("homeTeam") or {}
        away_team = game.get("awayTeam") or {}
        player_team_id = _team_identifier(stats.get("anyTeam"))
        opponent_team, opponent_side = _choose_opponent(player_team_id, home_team, away_team)
        opponent_name = opponent_team.get("code") or opponent_team.get("slug") or opponent_team.get("name") or "UNKNOWN"

        player_side = _team_side(player_team_id, home_team, away_team)
        player_stats_section = (
            game.get("homeStats")
            if player_side == "home"
            else game.get("awayStats")
            if player_side == "away"
            else None
        )
        opponent_stats_section = (
            game.get("homeStats")
            if opponent_side == "home"
            else game.get("awayStats")
            if opponent_side == "away"
            else None
        )

        pace = _stat_from_team(player_stats_section, "pace") or _stat_from_team(
            game.get("homeStats"), "pace"
        ) or _stat_from_team(game.get("awayStats"), "pace")
        opponent_def_rating = _stat_from_team(
            opponent_stats_section,
            "defensive_rating",
            "def_rating",
            "defrating",
        )

        row = GameLogRow(
            game_date=_iso_date(game.get("date")),
            opponent=opponent_name,
            minutes=_safe_float(stats.get("minsPlayed")),
            usage_rate=None,
            true_shooting_pct=None,
            sorare_score=_safe_float(node.get("score")),
            pace=pace,
            opponent_def_rating=opponent_def_rating,
        )
        rows.append(row)
    rows.sort(key=lambda r: r.game_date)
    return rows


def _write_csv(path: Path, rows: Iterable[GameLogRow]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "game_date",
                "opponent",
                "minutes",
                "usage_rate",
                "true_shooting_pct",
                "sorare_score",
                "pace",
                "opponent_def_rating",
            ],
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(row.as_csv_row())


def _load_query_from_file(path: Optional[Path]) -> str:
    if not path:
        return PLAYER_GAME_LOGS_QUERY
    return path.read_text(encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download Sorare NBA game logs and save them into data/game_logs/*.csv",
    )
    parser.add_argument("--player-slug", required=True, help="Sorare player slug (e.g. lebron-james)")
    parser.add_argument("--games", type=int, default=15, help="Number of most recent games to pull (default: 15)")
    parser.add_argument(
        "--output",
        type=Path,
        help="Destination CSV path. Defaults to data/game_logs/<player_slug>.csv",
    )
    parser.add_argument(
        "--query-file",
        type=Path,
        help="Optional path to a .graphql file that overrides the default game-log query.",
    )
    parser.add_argument(
        "--print-only",
        action="store_true",
        help="Print rows to stdout instead of writing the CSV.",
    )
    parser.add_argument(
        "--jwt-audience",
        default="SORARE",
        help="Audience enum passed to jwtToken(aud: ...). Defaults to SORARE.",
    )
    return parser.parse_args()


from .credentials import EMAIL, PASSWORD # Import credentials

def main(email: Optional[str] = None, password: Optional[str] = None) -> None:
    args = parse_args()
    output_path = args.output or Path("data/game_logs") / f"{args.player_slug}.csv"

    # Use imported credentials
    email = EMAIL
    password = PASSWORD

    if not email or not password:
        raise SystemExit("Email and password are required.")

    client = SorareClient()
    client.sign_in(email=email, password=password, audience=args.jwt_audience)

    query = _load_query_from_file(args.query_file)
    payload = client.fetch_game_logs(player_slug=args.player_slug, limit=args.games, query=query)
    rows = _rows_from_payload(payload)
    if not rows:
        raise SystemExit(f"No game logs returned for slug={args.player_slug}")

    if args.print_only:
        for row in rows:
            print(json.dumps(row.as_csv_row()))
    else:
        _write_csv(output_path, rows)
        print(f"Wrote {len(rows)} rows to {output_path}")


if __name__ == "__main__":
    main()
