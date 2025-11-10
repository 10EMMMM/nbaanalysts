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
from typing import Any, Dict, Optional
from urllib.parse import quote

import bcrypt
import requests

GRAPHQL_URL = "https://api.sorare.com/graphql"
USER_ENDPOINT = "https://api.sorare.com/api/v1/users/{email}"
USER_AGENT = "nbaanalysts-login-check/0.2"

SIGN_IN_MUTATION = """
mutation SignIn($input: signInInput!, $aud: String!) {
  signIn(input: $input) {
    currentUser {
      slug
      email
    }
    jwtToken(aud: $aud) {
      token
      expiredAt
    }
    otpSessionChallenge
    tcuToken
    errors {
      message
    }
  }
}
"""

CURRENT_USER_QUERY = """
query CurrentUser {
  currentUser {
    slug
    email
  }
}
"""


def _http_headers(extra: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    headers = {"User-Agent": USER_AGENT, "Content-Type": "application/json"}
    if extra:
        headers.update(extra)
    return headers


def _graphql(
    query: str,
    variables: Dict[str, Any],
    *,
    auth_token: Optional[str] = None,
    audience: Optional[str] = None,
) -> Dict[str, Any]:
    headers: Dict[str, str] = {}
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"
    if audience:
        headers["JWT-AUD"] = audience

    response = requests.post(
        GRAPHQL_URL,
        json={"query": query, "variables": variables},
        headers=_http_headers(headers),
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()
    if "errors" in payload:
        raise RuntimeError(json.dumps(payload["errors"], indent=2))
    return payload["data"]


def _fetch_salt(email: str) -> str:
    encoded_email = quote(email, safe="")
    response = requests.get(
        USER_ENDPOINT.format(email=encoded_email),
        headers={"User-Agent": USER_AGENT},
        timeout=15,
    )
    response.raise_for_status()
    data = response.json()
    salt = data.get("salt")
    if not salt:
        raise RuntimeError("Salt not returned; verify the email address.")
    return salt


def _hash_password(password: str, salt: str) -> str:
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt.encode("utf-8"))
    return hashed.decode("utf-8")


def _run_sign_in(email: str, password_hash: str, audience: str) -> Dict[str, Any]:
    data = _graphql(
        SIGN_IN_MUTATION,
        {"input": {"email": email, "password": password_hash}, "aud": audience},
    )
    return data.get("signIn") or {}


def _complete_otp_flow(challenge: str, audience: str) -> Dict[str, Any]:
    otp_code = input("Enter 2FA/OTP code: ").strip()
    if not otp_code:
        raise SystemExit("OTP code required to finish authentication.")
    data = _graphql(
        SIGN_IN_MUTATION,
        {"input": {"otpSessionChallenge": challenge, "otpAttempt": otp_code}, "aud": audience},
    )
    return data.get("signIn") or {}


def main() -> None:
    email = input("Sorare email: ").strip()
    password = getpass("Sorare password (input hidden): ")
    audience = input("JWT audience (default: nbaanalysts-cli): ").strip() or "nbaanalysts-cli"

    if not email or not password:
        raise SystemExit("Email and password are required.")

    salt = _fetch_salt(email)
    password_hash = _hash_password(password, salt)

    payload = _run_sign_in(email, password_hash, audience)
    errors = payload.get("errors") or []
    if errors:
        raise SystemExit(f"Sorare auth returned errors: {errors}")

    if payload.get("tcuToken"):
        raise SystemExit(
            "Sorare reports updated Terms & Conditions. Visit sorare.com to accept the latest terms before continuing."
        )

    if not payload.get("currentUser") and payload.get("otpSessionChallenge"):
        print("Account requires 2FA. Please provide the OTP code from your authenticator/email.")
        payload = _complete_otp_flow(payload["otpSessionChallenge"], audience)
        errors = payload.get("errors") or []
        if errors:
            raise SystemExit(f"Sorare auth returned errors after OTP: {errors}")

    jwt = payload.get("jwtToken") or {}
    token = jwt.get("token")
    user = payload.get("currentUser") or {}
    if not token or not user:
        raise SystemExit("Signed in but missing token or user info in response.")

    verification = _graphql(
        CURRENT_USER_QUERY,
        {},
        auth_token=token,
        audience=audience,
    )
    verified_user = (verification.get("currentUser") or {}) if verification else {}

    print("Login successful.")
    print(f"User: {user.get('email')} (slug: {user.get('slug')})")
    if verified_user:
        print("Verified currentUser call succeeded via JWT.")
    print(f"JWT expires at: {jwt.get('expiredAt')}")


if __name__ == "__main__":
    main()
