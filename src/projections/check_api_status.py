import requests
import json

GRAPHQL_URL = "https://api.sorare.com/graphql"

def check_sorare_api_status():
    try:
        # A simple GraphQL query to check if the API is reachable and responds
        query = """
        query {
          __typename
        }
        """
        response = requests.post(
            GRAPHQL_URL,
            json={"query": query},
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)
        
        payload = response.json()
        if "errors" in payload:
            print(f"Sorare API is reachable, but returned errors: {json.dumps(payload['errors'], indent=2)}")
            return False
        elif "__typename" in payload.get("data", {}):
            print(f"Sorare API is working! Typename: {payload['data']['__typename']}")
            return True
        else:
            print(f"Sorare API is reachable, but unexpected response: {json.dumps(payload, indent=2)}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"Failed to connect to Sorare API: {e}")
        return False
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return False

if __name__ == "__main__":
    check_sorare_api_status()
