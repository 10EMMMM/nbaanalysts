
from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from statistics import mean, pstdev
from typing import Dict, List, Optional
import csv
from datetime import datetime


@dataclass
class ProjectionResult:
    player_id: str
    expected_score: float
    expected_minutes: float
    expected_usage: float
    expected_efficiency: float
    lower_ci: float
    upper_ci: float
    notes: str = ""

    def to_dict(self) -> Dict[str, float]:
        return asdict(self)


def load_game_logs(path: Path | str, trailing_games: int = 15) -> List[Dict[str, float]]:
    """Load the player's game logs limited to the most recent games."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Game log not found at {path}")

    with path.open() as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    for row in rows:
        row["game_date"] = datetime.fromisoformat(row["game_date"]) if row["game_date"] else None
        for key in ("minutes", "usage_rate", "true_shooting_pct", "sorare_score", "pace", "opponent_def_rating"):
            row[key] = float(row[key]) if row[key] != "" else float("nan")
    rows.sort(key=lambda r: r["game_date"] or datetime.min)
    return rows[-trailing_games:]


def _rolling(values: List[float], window: int) -> List[Optional[float]]:
    result: List[Optional[float]] = []
    for idx in range(len(values)):
        if idx + 1 < window:
            result.append(None)
            continue
        window_values = values[idx + 1 - window : idx + 1]
        result.append(mean(window_values))
    return result


def _rolling_std(values: List[float], window: int) -> List[Optional[float]]:
    result: List[Optional[float]] = []
    for idx in range(len(values)):
        if idx + 1 < window:
            result.append(None)
            continue
        window_values = values[idx + 1 - window : idx + 1]
        if len(set(window_values)) == 1:
            result.append(0.0)
        else:
            result.append(pstdev(window_values))
    return result


def _rolling_slope(values: List[float], window: int) -> List[Optional[float]]:
    result: List[Optional[float]] = []
    for idx in range(len(values)):
        if idx + 1 < window:
            result.append(None)
            continue
        window_values = values[idx + 1 - window : idx + 1]
        n = len(window_values)
        x_vals = list(range(n))
        x_mean = mean(x_vals)
        y_mean = mean(window_values)
        numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_vals, window_values))
        denominator = sum((x - x_mean) ** 2 for x in x_vals) or 1.0
        result.append(numerator / denominator)
    return result


def engineer_features(rows: List[Dict[str, float]]) -> List[Dict[str, float]]:
    """Engineer trend and context features for the projection checklist."""
    if not rows:
        return []

    minutes = [row["minutes"] for row in rows]
    usage = [row["usage_rate"] for row in rows]
    ts = [row["true_shooting_pct"] for row in rows]
    pace = [row["pace"] for row in rows]
    opp_def = [row["opponent_def_rating"] for row in rows]
    sorare = [row["sorare_score"] for row in rows]

    minutes_avg_5 = _rolling(minutes, 5)
    minutes_avg_10 = _rolling(minutes, 10)
    minutes_trend = _rolling_slope(minutes, 5)
    usage_avg_5 = _rolling(usage, 5)
    usage_avg_10 = _rolling(usage, 10)
    ts_avg_5 = _rolling(ts, 5)
    ts_avg_10 = _rolling(ts, 10)
    pace_avg_5 = _rolling(pace, 5)
    opp_def_avg_5 = _rolling(opp_def, 5)
    sorare_mean_10 = _rolling(sorare, 10)
    sorare_std_10 = _rolling_std(sorare, 10)

    enriched: List[Dict[str, float]] = []
    for idx, row in enumerate(rows):
        enriched_row = dict(row)
        enriched_row["minutes_avg_5"] = minutes_avg_5[idx]
        enriched_row["minutes_avg_10"] = minutes_avg_10[idx]
        enriched_row["minutes_trend"] = minutes_trend[idx] if minutes_trend[idx] is not None else 0.0
        enriched_row["usage_avg_5"] = usage_avg_5[idx]
        enriched_row["usage_avg_10"] = usage_avg_10[idx]
        enriched_row["ts_avg_5"] = ts_avg_5[idx]
        enriched_row["ts_avg_10"] = ts_avg_10[idx]
        enriched_row["pace_avg_5"] = pace_avg_5[idx]
        enriched_row["opp_def_avg_5"] = opp_def_avg_5[idx]
        enriched_row["sorare_mean_10"] = sorare_mean_10[idx]
        enriched_row["sorare_std_10"] = sorare_std_10[idx]

        enriched_row["flag_high_pace"] = int(pace[idx] > (pace_avg_5[idx] or pace[idx]) * 1.02) if pace_avg_5[idx] else 0
        enriched_row["flag_low_minutes"] = int(minutes[idx] < (minutes_avg_5[idx] or minutes[idx]) * 0.9) if minutes_avg_5[idx] else 0
        enriched_row["flag_efficiency_spike"] = int(ts[idx] > (ts_avg_5[idx] or ts[idx]) * 1.05) if ts_avg_5[idx] else 0
        enriched.append(enriched_row)
    return enriched


def _injury_minutes_modifier(status: Optional[str]) -> float:
    if not status:
        return 1.0
    status = status.lower()
    if "questionable" in status:
        return 0.92
    if "probable" in status:
        return 0.97
    if "out" in status:
        return 0.0
    return 1.0


def project_player_game(features: List[Dict[str, float]], context: Dict[str, float | str]) -> ProjectionResult:
    """Project the upcoming game based on feature priors and contextual adjustments."""
    if not features:
        raise ValueError("Feature set is empty; cannot project player.")

    latest = features[-1]
    player_id = str(context.get("player_id") or context.get("player_name") or "unknown_player")

    base_minutes = latest.get("minutes_avg_5") or latest["minutes"]
    projected_minutes = float(context.get("projected_minutes", base_minutes))
    minutes_trend = latest.get("minutes_trend", 0.0)
    minutes_blend = 0.55 * projected_minutes + 0.45 * base_minutes + minutes_trend
    minutes_blend *= _injury_minutes_modifier(context.get("injury_status"))
    minutes_blend = max(minutes_blend, 0.0)

    base_usage = latest.get("usage_avg_5") or latest["usage_rate"]
    pace_context = float(context.get("pace_context", latest.get("pace_avg_5") or latest["pace"]))
    pace_anchor = latest.get("pace_avg_5") or pace_context
    usage_adjustment = 1 + (pace_context - pace_anchor) / 100.0
    expected_usage = base_usage * usage_adjustment

    base_eff = latest.get("ts_avg_5") or latest["true_shooting_pct"]
    opp_def_anchor = latest.get("opp_def_avg_5") or latest.get("opponent_def_rating", 110.0)
    opp_scheme = float(context.get("opponent_def_rating", opp_def_anchor))
    efficiency_adjustment = 1 - (opp_scheme - opp_def_anchor) / 250.0 if opp_def_anchor else 1.0
    expected_efficiency = base_eff * efficiency_adjustment

    sorare_prior = latest.get("sorare_mean_10") or latest["sorare_score"]
    pace_bonus = (pace_context - pace_anchor) * 0.25
    vegas_total = float(context.get("vegas_total", 220.0))
    vegas_adjustment = (vegas_total - 220.0) * 0.1

    expected_score = (
        0.45 * sorare_prior
        + 0.35 * (minutes_blend * 1.15 + expected_usage * 0.55)
        + 0.20 * (expected_efficiency * 60 + pace_bonus)
        + vegas_adjustment
    )

    sorare_std = latest.get("sorare_std_10") or 7.5
    ci_width = max(5.0, sorare_std * 1.2)
    lower_ci = max(0.0, expected_score - ci_width)
    upper_ci = expected_score + ci_width

    notes: List[str] = []
    if latest.get("flag_high_pace"):
        notes.append("Recent games at above-average pace")
    if latest.get("flag_low_minutes"):
        notes.append("Recent minutes dip to monitor")
    if context.get("injury_status"):
        notes.append(f"Injury status: {context['injury_status']}")

    return ProjectionResult(
        player_id=player_id,
        expected_score=float(expected_score),
        expected_minutes=float(minutes_blend),
        expected_usage=float(expected_usage),
        expected_efficiency=float(expected_efficiency),
        lower_ci=float(lower_ci),
        upper_ci=float(upper_ci),
        notes="; ".join(notes),
    )


def backtest_recent_games(rows: List[Dict[str, float]], lookback: int = 5) -> List[Dict[str, float]]:
    """Backtest the projection process over the last N games."""
    if len(rows) <= lookback:
        raise ValueError("Not enough games to run a backtest.")

    results: List[Dict[str, float]] = []
    for idx in range(len(rows) - lookback, len(rows)):
        history = rows[:idx]
        actual = rows[idx]
        if len(history) < 5:
            continue
        features = engineer_features(history)
        recent_minutes = [h["minutes"] for h in history[-5:]]
        pace_context = actual.get("pace") or mean([h["pace"] for h in history[-5:]])
        opp_def_context = actual.get("opponent_def_rating") or mean([h["opponent_def_rating"] for h in history[-5:]])
        context = {
            "player_id": actual.get("player_id", "unknown_player"),
            "projected_minutes": mean(recent_minutes),
            "injury_status": "Healthy",
            "pace_context": pace_context,
            "vegas_total": 220.0 + (pace_context - 100) * 1.5,
            "opponent_def_rating": opp_def_context,
        }
        projection = project_player_game(features, context)
        results.append(
            {
                "game_date": actual["game_date"].date().isoformat() if isinstance(actual["game_date"], datetime) else actual["game_date"],
                "opponent": actual.get("opponent"),
                "projected_score": projection.expected_score,
                "actual_score": actual["sorare_score"],
                "projection_minutes": projection.expected_minutes,
                "actual_minutes": actual["minutes"],
                "notes": projection.notes,
            }
        )
    return results


def prepare_upcoming_context(path: Path | str, player_id: str) -> Dict[str, str | float]:
    """Return the latest context row for the given player."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Upcoming context not found at {path}")

    with path.open() as f:
        reader = csv.DictReader(f)
        rows = [row for row in reader if row.get("player_id") == player_id]
    if not rows:
        raise ValueError(f"No context rows found for player_id={player_id}")
    latest = rows[-1]
    for key in ("projected_minutes", "pace_context", "vegas_total", "opponent_def_rating"):
        if key in latest and latest[key] != "":
            latest[key] = float(latest[key])
    return latest


def write_csv(path: Path | str, rows: List[Dict[str, str | float]], fieldnames: List[str]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
