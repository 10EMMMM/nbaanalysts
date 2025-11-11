from nba_api.stats.static import players
from nba_api.stats.endpoints import playergamelog
import pandas as pd
import argparse
from datetime import datetime
import os

def get_player_id(player_name):
    """
    Gets the player ID for a given player name.
    """
    player = players.find_players_by_full_name(player_name)
    if not player:
        return None
    return player[0]['id']

def get_player_game_log(player_id, season):
    """
    Gets the game log for a given player ID and season.
    """
    gamelog = playergamelog.PlayerGameLog(player_id=player_id, season=season)
    return gamelog.get_data_frames()[0]

def calculate_aas(stats):
    """
    Calculates the All-Around Score (AAS) for a single game.
    """
    aas = 0
    aas += stats["PTS"] * 1
    aas += stats["REB"] * 1.2
    aas += stats["AST"] * 1.5
    aas += stats["BLK"] * 3  # Corrected from *2 to *3
    aas += stats["STL"] * 3
    aas += stats["TOV"] * -2
    aas += stats["FG3M"] * 1 # Added Made 3pt FG bonus

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

def get_current_season():
    """
    Gets the current NBA season string.
    """
    now = datetime.now()
    if now.month >= 10:
        return f"{now.year}-{(now.year + 1) % 100:02d}"
    else:
        return f"{now.year - 1}-{now.year % 100:02d}"

def main():
    current_season = get_current_season()
    parser = argparse.ArgumentParser(description="Calculate the L10 AAS for a given NBA player.")
    parser.add_argument("player_name", nargs="?", default="Taylor Hendricks", help="The name of the player to calculate the L10 AAS for.")
    parser.add_argument("--season", default=current_season, help=f"The season to fetch the game log for (e.g., '2023-24'). Defaults to the current season: {current_season}")
    parser.add_argument("--output", help="The path to the CSV file to save the results to.")
    args = parser.parse_args()

    player_name = args.player_name
    season = args.season
    output_file = args.output
    
    player_id = get_player_id(player_name)

    if not player_id:
        print(f"Could not find player ID for {player_name}")
        return

    game_log_df = get_player_game_log(player_id, season)
    if game_log_df.empty:
        print(f"No games found for {player_name} in the {season} season.")
        return

    last_10_games = game_log_df.head(10)
    
    results = []
    print(f"L10 AAS for {player_name} ({season} season):\n")
    for index, game in last_10_games.iterrows():
        aas = calculate_aas(game)
        
        # Extract team from MATCHUP
        matchup = game['MATCHUP']
        if " vs. " in matchup:
            team = matchup.split(" vs. ")[0]
        elif " @ " in matchup:
            team = matchup.split(" @ ")[0]
        else:
            team = "" # Should not happen if MATCHUP is always in expected format

        results.append({
            "Player": player_name,
            "Team": team, # Added Team to results
            "Date": game['GAME_DATE'],
            "PTS": game['PTS'],
            "REB": game['REB'],
            "AST": game['AST'],
            "STL": game['STL'],
            "BLK": game['BLK'],
            "TOV": game['TOV'],
            "FG3M": game['FG3M'],
            "AAS": aas
        })
        print(f"Date: {game['GAME_DATE']}, Team: {team}, PTS: {game['PTS']}, REB: {game['REB']}, AST: {game['AST']}, STL: {game['STL']}, BLK: {game['BLK']}, TOV: {game['TOV']}, FG3M: {game['FG3M']}, AAS: {aas:.2f}")

    if results:
        average_l10_aas = sum(r['AAS'] for r in results) / len(results)
        print(f"\nAverage L10 AAS: {average_l10_aas:.2f}")

        if output_file:
            results_df = pd.DataFrame(results)
            file_exists = os.path.isfile(output_file)
            results_df.to_csv(output_file, mode='a', header=not file_exists, index=False)
            print(f"\nResults saved to {output_file}")

if __name__ == "__main__":
    main()