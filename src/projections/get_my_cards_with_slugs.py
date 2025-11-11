
import json
import requests

from src.projections.sorare_auth import SorareAuthenticator
from src.projections.credentials import EMAIL, PASSWORD

GRAPHQL_URL = "https://api.sorare.com/graphql"

MY_CARDS_WITH_SLUGS_QUERY = """
query MyCardsWithPlayerSlugs($first: Int!, $after: String) {
  currentUser {
    cards(first: $first, after: $after) {
      nodes {
        ... on NBACard {
          player {
            slug
            displayName
          }
        }
      }
      pageInfo {
        endCursor
        hasNextPage
      }
    }
  }
}
"""

def main():
    auth = SorareAuthenticator(user_agent="nba-my-cards-with-slugs/0.1")
    auth_result = auth.authenticate_with_password(EMAIL, PASSWORD, "nba-my-cards-with-slugs")

    all_player_slugs = []
    has_next_page = True
    end_cursor = None

    while has_next_page:
        variables = {"first": 50}
        if end_cursor:
            variables["after"] = end_cursor

        response = requests.post(
            GRAPHQL_URL,
            json={"query": MY_CARDS_WITH_SLUGS_QUERY, "variables": variables},
            headers={
                "Authorization": f"Bearer {auth_result.token}",
                "JWT-AUD": "nba-my-cards-with-slugs",
            },
        )

        response_data = response.json()
        if "errors" in response_data:
            print(json.dumps(response_data["errors"], indent=2))
            break

        cards_data = response_data["data"]["currentUser"]["cards"]
        for card in cards_data["nodes"]:
            if card.get("player"):
                all_player_slugs.append(card["player"])
        
        page_info = cards_data["pageInfo"]
        has_next_page = page_info["hasNextPage"]
        end_cursor = page_info["endCursor"]
    
    # Remove duplicate slugs
    unique_slugs = [dict(t) for t in {tuple(d.items()) for d in all_player_slugs}]
    
    print(json.dumps(unique_slugs, indent=2))

if __name__ == "__main__":
    main()
