# NBA API Data Sources for Player Projection Pipeline

This document summarizes the key resources available through the [`nba_api`](https://github.com/swar/nba_api) project that align with the inputs and features required by the player projection workflow in this repository.

## Access Considerations

* All of the endpoints below live under `nba_api.stats.endpoints` and are thin Python wrappers over the NBA Stats API.
* The NBA Stats service enforces request throttling; respect delays (`time.sleep(0.6)`) between calls when running bulk data pulls.
* Endpoints typically return data as JSON tables (list of headers + list of rows). The `nba_api.stats.library.data.DataSet` helper can convert them to pandas DataFrames.
* A modern User-Agent header is required. `nba_api` sets this automatically but you may need to override `proxies`/`headers` if your environment blocks the default settings.

## Inputs for Upcoming Game Context

| Scenario Input | `nba_api` Endpoint(s) | Notes |
| --- | --- | --- |
| Injury report | `InjuryReport` | Provides official game availability, injury descriptions, game date, and team. Update our `data/upcoming_game_context.csv` after pulling the latest report and filtering for the player of interest. |
| Opponent matchup & defensive profile | `TeamGameLog`, `BoxScoreAdvancedV2`, `LeagueDashOppPtShot` | Combine team game logs with advanced box scores to compute recent defensive efficiency, pace, and opponent shot profiles for contextual adjustments. |
| Game pace / expected possessions | `LeagueDashTeamStats` (with `measure_type_base='Advanced'`, `per_mode_detailed='PerGame'`) | Supplies current-season pace values. Blend overall team pace with opponent pace to project tempo. |
| Vegas totals / spreads | _Not available via `nba_api`_ | NBA Stats does not distribute betting lines. Continue sourcing these from external feeds and merge into the context CSV manually. |

## Feature Engineering from Trailing Game Logs

| Feature Need | `nba_api` Endpoint(s) | How It Helps |
| --- | --- | --- |
| Trailing 10–15 game logs | `PlayerGameLog` (`season`, `season_type_all_star`) | Direct replacement for the CSV seeds currently stored in `data/game_logs/<player_id>.csv`. Includes minutes, usage (FGA/FGA3A/FTA), rebounds, assists, turnovers, points, etc. |
| Usage rate proxies | `PlayerGameLog` or `BoxScoreUsageV2` | `BoxScoreUsageV2` adds possessions, usage percentages, and touch data when deeper usage detail is required beyond simple volume metrics. |
| Efficiency splits | `BoxScoreAdvancedV2`, `ShotChartDetail` | Advanced box scores provide true shooting %, offensive rating, rebound percentages. Shot chart data lets you segment efficiency by zone for contextual adjustments. |
| Contextual flags (rest, travel) | `ScoreboardV2`, `TeamGameLog` | Scoreboard data surfaces home/away, back-to-back flags, and rest days to flag schedule-driven adjustments. |

## Backtesting & Validation Data

| Validation Need | `nba_api` Endpoint(s) | Application |
| --- | --- | --- |
| Actual Sorare-esque scoring | `PlayerGameLog` | Use the points/rebounds/assists/steals/blocks/turnovers columns to recompute Sorare fantasy points for backtesting the projection accuracy. |
| Opponent adjustments | `LeagueDashLineups`, `PlayerProfileV2` | Capture on/off splits or lineup-based efficiency deltas to refine matchup adjustments if the model evolves in that direction. |

## Usage Snippets

```python
from nba_api.stats.endpoints import playergamelog, injuryreport
from nba_api.stats.library.data import DataSet

# Trailing game logs
logs = playergamelog.PlayerGameLog(player_id='1629029', season='2024-25')
log_df = DataSet(logs.get_normalized_dict()['PlayerGameLog']).get_data_frame()

# Injury report
injuries = injuryreport.InjuryReport()
injury_df = DataSet(injuries.get_normalized_dict()['InjuryReport']).get_data_frame()
```

## Integration Tips

1. **Caching**: Cache responses locally (e.g., write JSON/CSV snapshots) to avoid repeated API calls during iterative notebook development.
2. **Data Normalization**: Align `GAME_DATE` to the repository's date format (ISO `YYYY-MM-DD`) before appending to `data/upcoming_game_context.csv` or the game log CSVs.
3. **Player ID Mapping**: `nba_api` uses NBA Stats player IDs; maintain a mapping between those IDs and our file naming convention (`<slug>.csv`).
4. **Error Handling**: Wrap calls with retries/backoff to gracefully handle transient NBA Stats outages or rate-limit responses.
5. **Unit Consistency**: Most endpoints return per-game stats; adjust to per-possession or per-36 as needed when engineering trend features.
