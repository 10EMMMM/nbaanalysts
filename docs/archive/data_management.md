# Data Management for NBA Analysts

This document outlines the process for downloading and managing historical NBA game data to improve the performance and reliability of the analysis scripts.

## Downloading Historical Data

To avoid making a large number of API calls every time you run the analysis, you can download the historical game data for past seasons using the `download_historical_data.py` script.

### Usage

1.  **Open a terminal in the project root.**
2.  **Run the script with the number of past seasons you want to download.** For example, to download data for the last 3 seasons:

    ```bash
    python -m src.projections.download_historical_data 3
    ```

    The script will fetch the game logs and advanced stats for all players for each of the specified past seasons and save the data to CSV files in the `data/game_logs` directory.

    **Note:** This script can take a long time to run, as it makes a large number of API calls. It's recommended to run it once to download the historical data, and then re-run it periodically (e.g., once a year) to get the data for the most recently completed season.

## Data Storage

The historical data is stored in CSV files in the `data/game_logs` directory. Each file is named with the corresponding season (e.g., `game_log_2022-23.csv`).

## Using the Data in the Analysis

The `00_playercheck.py` script is designed to automatically use the downloaded historical data.

*   When you run the script, for each past season, it will first check if a corresponding `game_log_{season}.csv` file exists in the `data/game_logs` directory.
*   If the file exists, it will load the data from the CSV file, which is much faster than making API calls.
*   If the file does not exist (e.g., for the current season), it will fall back to fetching the data from the `nba_api`.

This approach ensures that the analysis script is both fast and up-to-date, as it uses local data for past seasons and live data for the current season.
