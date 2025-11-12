import argparse
import json
import csv
import os
import re
from gemini import Gemini

def get_player_id_and_name(player_name_query):
    """
    Searches for a player on the NBA stats website and returns their ID and formatted name.
    """
    gemini = Gemini()
    gemini.new_page(f"https://www.nba.com/stats")
    gemini.wait_for("Search for a player or team")
    search_input_uid = gemini.take_snapshot().find_one_by_text("Search for a player or team", role="combobox").uid
    gemini.fill(search_input_uid, player_name_query)
    gemini.wait_for(player_name_query)
    
    # Assuming the first result is the correct one
    snapshot = gemini.take_snapshot()
    player_link = snapshot.find_one_by_text(player_name_query, role="link")
    
    if player_link:
        player_url = player_link.url
        player_id_match = re.search(r'/player/(\d+)/', player_url)
        if player_id_match:
            player_id = player_id_match.group(1)
            # Extract the player's full name from the URL for the filename
            player_name_slug = player_url.split('/')[-2]
            player_name = player_name_slug.replace('-', '_')
            return player_id, player_name
    return None, None

def scrape_advanced_stats(player_id):
    """
    Scrapes the 'Advanced Splits' table for a given player ID.
    """
    gemini = Gemini()
    gemini.new_page(f"https://www.nba.com/stats/player/{player_id}")
    
    # This is the JavaScript function we developed earlier
    script = """
    () => {
        const tables = Array.from(document.querySelectorAll('table'));
        const advancedStatsTable = tables.find(table => {
            const firstHeader = table.querySelector('thead th[colspan="5"]');
            return firstHeader && firstHeader.textContent.includes('Advanced Splits');
        });

        if (advancedStatsTable) {
            const headersRow = advancedStatsTable.querySelector('thead tr.Crom_headers__mzI_m');
            const headers = Array.from(headersRow.querySelectorAll('th')).map(th => th.textContent.trim().replace(/\n/g, ' '));
            
            const rows = Array.from(advancedStatsTable.querySelectorAll('tbody tr')).map(tr => {
                return Array.from(tr.querySelectorAll('td')).map(td => td.textContent.trim());
            });
            return { headers, rows };
        }
        return null;
    }
    """
    stats_data = gemini.evaluate_script(function=script)
    gemini.close_page()
    return stats_data

def save_stats_to_csv(player_name, stats_data, directory="data"):
    """
    Saves the scraped stats to a CSV file.
    """
    if not os.path.exists(directory):
        os.makedirs(directory)
        
    filename = f"{player_name}_advanced_stats.csv"
    filepath = os.path.join(directory, filename)
    
    with open(filepath, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(stats_data['headers'])
        writer.writerows(stats_data['rows'])
        
    print(f"Stats saved to {filepath}")

def main():
    parser = argparse.ArgumentParser(description="Scrape advanced stats for an NBA player.")
    parser.add_argument("player_name", type=str, help="The name of the player to scrape stats for.")
    args = parser.parse_args()
    
    player_id, player_name_for_file = get_player_id_and_name(args.player_name)
    
    if player_id and player_name_for_file:
        print(f"Found player: {player_name_for_file} (ID: {player_id})")
        stats = scrape_advanced_stats(player_id)
        if stats:
            save_stats_to_csv(player_name_for_file, stats)
        else:
            print("Could not find the 'Advanced Splits' table.")
    else:
        print(f"Could not find a player with the name: {args.player_name}")

if __name__ == "__main__":
    main()
