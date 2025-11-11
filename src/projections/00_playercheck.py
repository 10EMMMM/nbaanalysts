from nba_api.stats.static import players, teams
from nba_api.stats.endpoints import playergamelog, leaguestandings
import pandas as pd
import argparse
from datetime import datetime, timedelta
import os
from thefuzz import process

def get_player_id(player_name):
    """
    Gets the player ID for a given player name, using fuzzy matching if necessary.
    """
    player = players.find_players_by_full_name(player_name)
    if not player:
        print(f"Could not find an exact match for {player_name}, trying fuzzy matching...")
        all_players = players.get_active_players()
        all_player_names = [p['full_name'] for p in all_players]
        best_match = process.extractOne(player_name, all_player_names)
        if best_match and best_match[1] > 80: # Confidence threshold
            print(f"Found best match: {best_match[0]}")
            return players.find_players_by_full_name(best_match[0])[0]['id']
        else:
            return None
    return player[0]['id']

def get_last_n_seasons(n):
    """
    Gets a list of the last n season strings.
    """
    now = datetime.now()
    current_year = now.year
    if now.month < 10:
        current_year -= 1
    
    seasons = []
    for i in range(n):
        start_year = current_year - i
        end_year = (start_year + 1) % 100
        seasons.append(f"{start_year}-{end_year:02d}")
    return seasons

def get_player_game_log(player_id, seasons):
    """
    Gets the game log for a given player ID and a list of seasons.
    """
    all_games = []
    for season in seasons:
        gamelog = playergamelog.PlayerGameLog(player_id=player_id, season=season)
        df = gamelog.get_data_frames()[0]
        df['SEASON'] = season
        all_games.append(df)
    
    if not all_games:
        return pd.DataFrame()
        
    return pd.concat(all_games, ignore_index=True)

def get_team_win_percentages(seasons):
    """
    Gets the win percentages for all teams for a list of seasons.
    """
    win_percentages = {}
    for season in seasons:
        standings = leaguestandings.LeagueStandings(season=season).get_data_frames()[0]
        season_percentages = {}
        for index, row in standings.iterrows():
            team_id = row['TeamID']
            team_abbreviation = teams.find_team_name_by_id(team_id)['abbreviation']
            season_percentages[team_abbreviation] = row['WinPCT']
        win_percentages[season] = season_percentages
    return win_percentages

def calculate_aas(stats):
    """
    Calculates the All-Around Score (AAS) for a single game.
    """
    aas = 0
    aas += stats["PTS"] * 1
    aas += stats["REB"] * 1.2
    aas += stats["AST"] * 1.5
    aas += stats["BLK"] * 3
    aas += stats["STL"] * 3
    aas += stats["TOV"] * -2
    aas += stats["FG3M"] * 1

    # Check for double-double and triple-double
    double_digit_stats = 0
    for stat in ["PTS", "REB", "AST", "STL", "BLK"]:
        if stats[stat] >= 10:
            double_digit_stats += 1
    
    if double_digit_stats >= 2:
        aas += 1
    if double_digit_stats >= 3:
        aas += 1 # An additional point for a triple-double

    return aas

def calculate_baseline_stats(df):
    """
    Calculates the baseline AAS and standard deviation from a DataFrame of games.
    """
    if df.empty:
        return 0, 0, pd.DataFrame()
        
    df['AAS'] = df.apply(calculate_aas, axis=1)
    baseline_aas = df['AAS'].mean()
    std_dev_aas = df['AAS'].std()
    return baseline_aas, std_dev_aas, df

def calculate_short_term_trends(df):
    """
    Calculates the L10, L30, and L50 AAS from a DataFrame of games.
    """
    trends = {}
    for n in [10, 30, 50]:
        if len(df) >= n:
            trends[f"L{n}"] = df.head(n)['AAS'].mean()
        else:
            trends[f"L{n}"] = None
    return trends

def identify_back_to_backs(df):
    """
    Identifies back-to-back games in a game log.
    """
    df['GAME_DATE'] = pd.to_datetime(df['GAME_DATE'])
    df = df.sort_values(by='GAME_DATE', ascending=False)
    df['IS_B2B'] = df['GAME_DATE'].diff(-1) == timedelta(days=1)
    return df

def calculate_individual_stat_projections(df):
    """
    Calculates projected individual stats based on a weighted average of long-term and short-term performance.
    """
    stats_to_project = ["PTS", "REB", "AST", "STL", "BLK", "TOV", "FG3M"]
    projections = {}

    for stat in stats_to_project:
        long_term_avg = df[stat].mean()
        short_term_avg = df.head(10)[stat].mean()
        projected_stat = (long_term_avg * 0.5) + (short_term_avg * 0.5)
        projections[f"Projected_{stat}"] = projected_stat

    return projections

def process_player(player_name, num_seasons, output_file):
    """
    Processes a single player and prints their stats.
    """
    player_id = get_player_id(player_name)

    if not player_id:
        print(f"Could not find player ID for {player_name}")
        return

    seasons_to_fetch = get_last_n_seasons(num_seasons)
    print(f"\nFetching data for {player_name} for the following seasons: {', '.join(seasons_to_fetch)}")
    
    game_log_df = get_player_game_log(player_id, seasons_to_fetch)
    if game_log_df.empty:
        print(f"No games found for {player_name} in the specified seasons.")
        return

    team_win_percentages = get_team_win_percentages(seasons_to_fetch)

    baseline_aas, std_dev_aas, game_log_df_with_aas = calculate_baseline_stats(game_log_df)
    trends = calculate_short_term_trends(game_log_df_with_aas)
    game_log_df_with_aas = identify_back_to_backs(game_log_df_with_aas)
    individual_projections = calculate_individual_stat_projections(game_log_df_with_aas)

    home_games = game_log_df_with_aas[game_log_df_with_aas['MATCHUP'].str.contains('vs.')]
    away_games = game_log_df_with_aas[game_log_df_with_aas['MATCHUP'].str.contains('@')]
    b2b_games = game_log_df_with_aas[game_log_df_with_aas['IS_B2B']]

    home_aas = home_games['AAS'].mean()
    away_aas = away_games['AAS'].mean()
    b2b_aas = b2b_games['AAS'].mean()

    print(f"\n--- Long-Term Player Profile (Last {num_seasons} Seasons) ---")
    print(f"Baseline AAS: {baseline_aas:.2f}")
    print(f"AAS Standard Deviation (Consistency): {std_dev_aas:.2f}")

    print(f"\n--- Short-Term Performance Trends ---")
    for trend, value in trends.items():
        if value is not None:
            print(f"{trend} AAS: {value:.2f}")
        else:
            print(f"{trend} AAS: Not enough data")

    print(f"\n--- Contextual Performance Analysis (Last {num_seasons} Seasons) ---")
    print(f"Home AAS: {home_aas:.2f}")
    print(f"Away AAS: {away_aas:.2f}")
    print(f"Back-to-Back AAS: {b2b_aas:.2f}")

    print(f"\n--- Opponent-Adjusted AAS (Last 10 Games) ---")
    last_10_games = game_log_df_with_aas.head(10)
    opponent_adjusted_aas_list = []
    for index, game in last_10_games.iterrows():
        matchup = game['MATCHUP']
        if " vs. " in matchup:
            opponent_abbr = matchup.split(" vs. ")[1]
        elif " @ " in matchup:
            opponent_abbr = matchup.split(" @ ")[1]
        else:
            opponent_abbr = ""

        game_season = game['SEASON']
        opponent_win_pct = team_win_percentages.get(game_season, {}).get(opponent_abbr, 0.5)
        
        opponent_adjusted_aas = game['AAS'] * opponent_win_pct
        opponent_adjusted_aas_list.append(opponent_adjusted_aas)

        print(f"Date: {game['GAME_DATE'].date()}, Opp: {opponent_abbr} (Win %: {opponent_win_pct:.3f}), Opponent-Adjusted AAS: {opponent_adjusted_aas:.2f}")

    # Composite Score
    l10_aas = trends.get('L10', baseline_aas)
    l10_opponent_adjusted_aas = sum(opponent_adjusted_aas_list) / len(opponent_adjusted_aas_list) if opponent_adjusted_aas_list else 0
    
    composite_score = (baseline_aas * 0.4) + (l10_aas * 0.4) + (l10_opponent_adjusted_aas * 0.2)
    print(f"\n--- Composite Score ---")
    print(f"Predictive AAS: {composite_score:.2f}")

    print(f"\n--- Individual Stat Projections ---")
    for stat, value in individual_projections.items():
        print(f"{stat}: {value:.2f}")

    # Save results to CSV
    if output_file:
        results_to_save = {
            "Player": player_name,
            "Baseline_AAS": baseline_aas,
            "AAS_Std_Dev": std_dev_aas,
            "L10_AAS": trends.get('L10'),
            "L30_AAS": trends.get('L30'),
            "L50_AAS": trends.get('L50'),
            "Home_AAS": home_aas,
            "Away_AAS": away_aas,
            "B2B_AAS": b2b_aas,
            "Composite_Predictive_AAS": composite_score,
            **individual_projections
        }
        results_df = pd.DataFrame([results_to_save])
        file_exists = os.path.isfile(output_file)
        results_df.to_csv(output_file, mode='a', header=not file_exists, index=False)
        print(f"\nResults for {player_name} saved to {output_file}")

def main():
    parser = argparse.ArgumentParser(description="Calculate advanced stats for a list of NBA players based on historical data.")
    parser.add_argument("--input-file", default="data/player_list.txt", help="Path to a text file with player names (one per line).")
    parser.add_argument("--seasons", type=int, default=3, help="The number of past seasons to analyze.")
    args = parser.parse_args()

    try:
        with open(args.input_file, "r") as f:
            player_names = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        raise SystemExit(f"Input file not found: {args.input_file}")

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    output_file = f"outputs/player_analysis_{timestamp}.csv"

    for player_name in player_names:
        process_player(player_name, args.seasons, output_file)



if __name__ == "__main__":
    main()
