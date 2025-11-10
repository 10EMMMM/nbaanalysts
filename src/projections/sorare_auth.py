"""
Shared Sorare authentication helpers.

Implements the official flow:
1. Retrieve the bcrypt salt for the provided email.
2. Hash the password locally with that salt.
3. Run the signIn mutation with the hashed password.
4. Support OTP-based 2FA and Terms & Conditions requirements.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional
from urllib.parse import quote

import bcrypt
import requests

GRAPHQL_URL = "https://api.sorare.com/graphql"
USER_ENDPOINT = "https://api.sorare.com/api/v1/users/{email}"

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


@dataclass
class AuthResult:
    token: str
    expires_at: Optional[str]
    user: Dict[str, Any]


class SorareAuthenticator:
    def __init__(
        self,
        user_agent: str,
        *,
        session: Optional[requests.Session] = None,
        input_func: Callable[[str], str] = input,
    ) -> None:
        self.session = session or requests.Session()
        self.user_agent = user_agent
        self.session.headers.update({"User-Agent": user_agent})
        self.input_func = input_func

    def _graphql(
        self,
        query: str,
        variables: Dict[str, Any],
    ) -> Dict[str, Any]:
        response = self.session.post(
            GRAPHQL_URL,
            json={"query": query, "variables": variables},
            headers={"Content-Type": "application/json"},
            timeout=30,
        )
        response.raise_for_status()
        payload = response.json()
        if "errors" in payload:
            raise RuntimeError(json.dumps(payload["errors"], indent=2))
        return payload["data"]

    def _fetch_salt(self, email: str) -> str:
        encoded_email = quote(email, safe="")
        response = self.session.get(
            USER_ENDPOINT.format(email=encoded_email),
            headers={"User-Agent": self.user_agent},
            timeout=15,
        )
        response.raise_for_status()
        data = response.json()
        salt = data.get("salt")
        if not salt:
            raise RuntimeError("Salt not returned; verify the Sorare email address.")
        return salt

    @staticmethod
    def _hash_password(password: str, salt: str) -> str:
        hashed = bcrypt.hashpw(password.encode("utf-8"), salt.encode("utf-8"))
        return hashed.decode("utf-8")

    def _sign_in_mutation(self, payload: Dict[str, Any], audience: str) -> Dict[str, Any]:
        data = self._graphql(
            SIGN_IN_MUTATION,
            {"input": payload, "aud": audience},
        )
        return data.get("signIn") or {}

    def authenticate_with_password(self, email: str, password: str, audience: str) -> AuthResult:
        salt = self._fetch_salt(email)
        password_hash = self._hash_password(password, salt)
        payload = self._sign_in_mutation({"email": email, "password": password_hash}, audience)
        if payload.get("tcuToken"):
            raise RuntimeError(
                "Sorare reports updated Terms & Conditions. Accept them on sorare.com before continuing."
            )
        if not payload.get("currentUser") and payload.get("otpSessionChallenge"):
            otp_code = self.input_func("Enter Sorare OTP code: ").strip()
            if not otp_code:
                raise RuntimeError("OTP code required to finish Sorare authentication.")
            payload = self._sign_in_mutation(
                {"otpSessionChallenge": payload["otpSessionChallenge"], "otpAttempt": otp_code},
                audience,
            )

        errors = payload.get("errors") or []
        if errors:
            raise RuntimeError(f"Sorare authentication error: {errors}")
        jwt = payload.get("jwtToken") or {}
        token = jwt.get("token")
        user = payload.get("currentUser") or {}
        if not token or not user:
            raise RuntimeError("Sorare authentication succeeded but token/user info missing.")
        return AuthResult(token=token, expires_at=jwt.get("expiredAt"), user=user)
