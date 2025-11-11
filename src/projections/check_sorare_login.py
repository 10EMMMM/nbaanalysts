"""
Minimal Sorare login check that follows the official workflow:

1. Retrieve the bcrypt salt for the provided email.
2. Hash the password locally with that salt.
3. Run the `signIn` mutation requesting a JWT token.
4. Handle 2FA challenges if the account requires it.
5. Use the JWT to confirm we can hit `currentUser`.
"""

from __future__ import annotations

import json
from getpass import getpass
from typing import Dict

from .sorare_auth import GRAPHQL_URL, SorareAuthenticator

CURRENT_USER_QUERY = """
query CurrentUser {
  currentUser {
    slug
    email
  }
}
"""


from .credentials import EMAIL, PASSWORD # Import credentials

def main() -> None:
    email = EMAIL # Use imported email
    password = PASSWORD # Use imported password
    audience = "nbaanalysts-cli" # Hardcoded audience

    if not email or not password:
        raise SystemExit("Email and password are required.")

    auth = SorareAuthenticator(user_agent="nbaanalysts-login-check/0.3")
    try:
        result = auth.authenticate_with_password(email, password, audience)
    except RuntimeError as exc:
        raise SystemExit(str(exc)) from exc

    verification = _graphql_with_token(
        CURRENT_USER_QUERY,
        {},
        token=result.token,
        audience=audience,
        auth=auth,
    )
    verified_user = verification.get("currentUser") if verification else {}

    print("Login successful.")
    print(f"User: {result.user.get('email')} (slug: {result.user.get('slug')})")
    if verified_user:
        print("Verified currentUser call succeeded via JWT.")
    print(f"JWT expires at: {result.expires_at}")


def _graphql_with_token(
    query: str,
    variables: Dict[str, object],
    *,
    token: str,
    audience: str,
    auth: SorareAuthenticator,
) -> Dict[str, object]:
    response = auth.session.post(
        GRAPHQL_URL,
        json={"query": query, "variables": variables},
        headers={
            "User-Agent": auth.user_agent,
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
            "JWT-AUD": audience,
        },
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()
    if "errors" in payload:
        raise RuntimeError(json.dumps(payload["errors"], indent=2))
    return payload["data"]


if __name__ == "__main__":
    main()
