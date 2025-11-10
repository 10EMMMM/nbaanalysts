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

API_URL = "https://api.sorare.com/graphql"
USER_AGENT = "nbaanalysts/0.1 (+https://github.com/10EMMMM/nbaanalysts)"

SIGN_IN_MUTATION = """
mutation SignIn($input: signInInput!, $aud: String!) {
  signIn(input: $input) {
    jwtToken(aud: $aud) {
      token
      expiredAt
    }
    currentUser {
      slug
      email
    }
    errors {
      message
    }
  }
}
"""

# NOTE: Field names (nbaPlayer, gameLogs, stats, etc.) are based on the current
# public Sorare API schema. Update them if Sorare renames anything.
PLAYER_GAME_LOGS_QUERY = """
query PlayerGameLogs($slug: String!, $limit: Int!) {
  nbaPlayer(slug: $slug) {
    slug
    displayName
    activeClub {
      slug
      code
      name
    }
    gameLogs(first: $limit, sortBy: START_DATE_DESC) {
      nodes {
        game {
          uuid
          startDate
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
          pace
          defensiveRating
        }
        team {
          slug
          code
          name
        }
        stats {
          minutes
          usageRate
          trueShootingPercentage
          sorareScore
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


def _infer_opponent(node: Dict[str, Any]) -> str:
    game = node.get("game") or {}
    team_info = node.get("team") or {}
    player_team = team_info.get("code") or team_info.get("slug")
    home = game.get("homeTeam", {}) or {}
    away = game.get("awayTeam", {}) or {}

    def _matches(team: Dict[str, Any]) -> bool:
        return bool(
            player_team
            and (team.get("code") == player_team or team.get("slug") == player_team or team.get("name") == player_team)
        )

    if _matches(home):
        opponent = away
    elif _matches(away):
        opponent = home
    else:
        # Default to away team so something is recorded even if team info is missing.
        opponent = away or home
    return opponent.get("code") or opponent.get("slug") or opponent.get("name") or "UNKNOWN"


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

    def _post(self, query: str, variables: Optional[Dict[str, Any]] = None, *, auth: bool = False) -> Dict[str, Any]:
        headers = {"Content-Type": "application/json"}
        if auth:
            if not self.token:
                raise RuntimeError("Attempted authenticated request without a token.")
            headers["Authorization"] = f"Bearer {self.token}"
        response = self.session.post(
            API_URL,
            json={"query": query, "variables": variables or {}},
            headers=headers,
            timeout=30,
        )
        response.raise_for_status()
        payload = response.json()
        if "errors" in payload:
            raise RuntimeError(json.dumps(payload["errors"], indent=2))
        return payload["data"]

    def sign_in(self, email: str, password: str, audience: str = "SORARE") -> None:
        data = self._post(
            SIGN_IN_MUTATION,
            {"input": {"email": email, "password": password}, "aud": audience},
            auth=False,
        )
        payload = data.get("signIn") or {}
        errors = payload.get("errors") or []
        if errors:
            raise RuntimeError(f"Sorare authentication error: {errors}")
        jwt = payload.get("jwtToken") or {}
        token = jwt.get("token")
        if not token:
            raise RuntimeError("Sorare authentication failed; JWT token missing in response.")
        self.token = token

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
    player = payload.get("nbaPlayer")
    if not player:
        raise RuntimeError("Unexpected response shape: nbaPlayer missing.")
    logs = (((player.get("gameLogs") or {}).get("nodes")) or [])
    rows: List[GameLogRow] = []
    for node in logs:
        stats = node.get("stats") or {}
        row = GameLogRow(
            game_date=_iso_date(((node.get("game") or {}).get("startDate"))),
            opponent=_infer_opponent(node),
            minutes=_safe_float(stats.get("minutes")),
            usage_rate=_safe_float(stats.get("usageRate")),
            true_shooting_pct=_safe_float(stats.get("trueShootingPercentage")),
            sorare_score=_safe_float(stats.get("sorareScore")),
            pace=_safe_float((node.get("game") or {}).get("pace")),
            opponent_def_rating=_safe_float((node.get("game") or {}).get("defensiveRating")),
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


def main() -> None:
    args = parse_args()
    output_path = args.output or Path("data/game_logs") / f"{args.player_slug}.csv"

    email = input("Sorare email: ").strip()
    password = getpass("Sorare password (input hidden): ")
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
