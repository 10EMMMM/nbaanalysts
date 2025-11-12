import nba_api
from nba_api.stats.endpoints import playergamelog
from nba_api.stats.static import players

def main():
    print(f"nba_api version: {nba_api.__version__}")

    player_id = players.find_players_by_full_name("LeBron James")[0]['id']
    season = "2023-24"
    
    print(f"\nTesting playergamelog with measure_type_player_or_team='Advanced'...")
    try:
        gamelog = playergamelog.PlayerGameLog(
            player_id=player_id,
            season=season,
            measure_type_player_or_team='Advanced'
        )
        df = gamelog.get_data_frames()[0]
        print("SUCCESS: playergamelog call with measure_type_player_or_team='Advanced' was successful.")
        print(df.head())
    except TypeError as e:
        print(f"FAILURE: Caught a TypeError. This likely means the 'measure_type_player_or_team' parameter is not supported in this version of the library.")
        print(f"Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()

