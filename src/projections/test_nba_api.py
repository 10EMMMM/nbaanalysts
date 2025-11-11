import argparse
import time
from nba_api.stats.endpoints import playergamelog, leaguestandings
from nba_api.stats.static import players
from requests.exceptions import ReadTimeout

def get_player_id(player_name):
    """
    Gets the player ID for a given player name.
    """
    player = players.find_players_by_full_name(player_name)
    if not player:
        return None
    return player[0]['id']

def test_player_gamelog(player_id, season, timeout):
    """
    Tests the playergamelog endpoint.
    """
    print(f"Testing playergamelog for season {season} with a {timeout}-second timeout...")
    try:
        start_time = time.time()
        gamelog = playergamelog.PlayerGameLog(player_id=player_id, season=season, timeout=timeout)
        df = gamelog.get_data_frames()[0]
        end_time = time.time()
        print(f"SUCCESS: playergamelog for {season} took {end_time - start_time:.2f} seconds.")
        return True
    except ReadTimeout:
        print(f"FAILURE: playergamelog for {season} timed out after {timeout} seconds.")
        return False
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return False

def test_leaguestandings(season, timeout):
    """
    Tests the leaguestandings endpoint.
    """
    print(f"Testing leaguestandings for season {season} with a {timeout}-second timeout...")
    try:
        start_time = time.time()
        standings = leaguestandings.LeagueStandings(season=season, timeout=timeout)
        df = standings.get_data_frames()[0]
        end_time = time.time()
        print(f"SUCCESS: leaguestandings for {season} took {end_time - start_time:.2f} seconds.")
        return True
    except ReadTimeout:
        print(f"FAILURE: leaguestandings for {season} timed out after {timeout} seconds.")
        return False
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Test nba_api endpoints for timeout issues.")
    parser.add_argument("player_name", help="The name of the player to test.")
    parser.add_argument("--timeout", type=int, default=60, help="The timeout in seconds for API requests.")
    args = parser.parse_args()

    player_id = get_player_id(args.player_name)
    if not player_id:
        print(f"Could not find player ID for {args.player_name}")
        return

    print(f"\n--- Testing for player: {args.player_name} (ID: {player_id}) ---")

    seasons = ["2023-24", "2022-23", "2021-22"]

    for season in seasons:
        test_player_gamelog(player_id, season, args.timeout)
        test_leaguestandings(season, args.timeout)
        print("-" * 20)

if __name__ == "__main__":
    main()
