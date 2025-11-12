import argparse
import os
import time
import pandas as pd
from nba_api.stats.endpoints import playergamelog
from nba_api.stats.static import players
from requests.exceptions import ReadTimeout

def make_api_request(api_call, max_retries=3, delay=5, **kwargs):
    """
    Makes an API request with a retry mechanism.
    """
    for attempt in range(max_retries):
        try:
            return api_call(**kwargs)
        except ReadTimeout:
            print(f"API call timed out. Retrying in {delay} seconds... (Attempt {attempt + 1}/{max_retries})")
            time.sleep(delay)
    print(f"API call failed after {max_retries} attempts.")
    return None

def get_all_player_game_logs(season):
    """
    Gets the game logs for all players for a given season.
    """
    all_players = players.get_players()
    all_game_logs = pd.DataFrame()
    
    for i, player in enumerate(all_players):
        player_id = player['id']
        player_name = player['full_name']
        print(f"Fetching data for player {i + 1}/{len(all_players)}: {player_name}")
        
        try:
            gamelog = make_api_request(
                playergamelog.PlayerGameLog,
                player_id=player_id,
                season=season,
                measure_type_detailed='Advanced' # Corrected parameter
            )
            if gamelog:
                player_game_log_df = gamelog.get_data_frames()[0]
                if not player_game_log_df.empty:
                    all_game_logs = pd.concat([all_game_logs, player_game_log_df], ignore_index=True)
            time.sleep(0.6) # Add a delay to avoid rate limiting
        except Exception as e:
            print(f"An error occurred for player {player_name}: {e}")

    return all_game_logs

def main():
    parser = argparse.ArgumentParser(description="Download historical NBA game data.")
    parser.add_argument("season", help="The season to download data for (e.g., 2022-23).")
    args = parser.parse_args()

    output_dir = "data/game_logs"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    output_file = os.path.join(output_dir, f"game_log_{args.season}.csv")
    
    if os.path.exists(output_file):
        print(f"Data for season {args.season} already exists. Skipping.")
        return

    print(f"\n--- Downloading data for season: {args.season} ---")
    season_data = get_all_player_game_logs(args.season)
    
    if not season_data.empty:
        season_data.to_csv(output_file, index=False)
        print(f"Successfully saved data for season {args.season} to {output_file}")

if __name__ == "__main__":
    main()
