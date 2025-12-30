"""
Locust load-test suite for the Energy Island Django API.

Scenarios (run via --tags):
- baseline_public_state     : hits PUBLIC_STATE only (legitimate baseline)
- secure_valid_only         : hits SECURE_PING + SECURE_STATE with valid token (legitimate baseline)
- secure_mixed_80_20        : 20% valid token + 80% invalid/missing token to SECURE_* (attack traffic)
- auth_login_storm          : login brute-force against AUTH_TOKEN (mostly invalid credentials)

Environment variables:
  LOCUST_HOST        (default http://127.0.0.1:8000)
  LOCUST_USER        (required for valid-token scenarios)
  LOCUST_PASS        (required for valid-token scenarios)
  TOKEN_PATH         (default /api/auth/token/)
  PUBLIC_STATE_PATH  (default /api/public/state/)
  SECURE_PING_PATH   (default /api/secure/ping/)
  SECURE_STATE_PATH  (default /api/secure/state/)

Token parsing:
  Tries common fields: access, token, access_token, key.

Notes:
- We mark 401/403/429 as *failures* so they show in failures.csv (useful for "blocked/denied" metrics).
- 200/201/204/302 are treated as success.
"""

import json
import os
import random
import string
from typing import Optional

from locust import HttpUser, task, tag, between

OK_STATUS = {200, 201, 202, 204, 302}


def env(name: str, default: str) -> str:
    v = os.getenv(name)
    return v if v not in (None, "") else default


def rand_str(n: int = 10) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(random.choice(alphabet) for _ in range(n))


class ApiUser(HttpUser):
    wait_time = between(0.05, 0.15)  # tweak with users/spawn to reach desired RPS

    host = env("LOCUST_HOST", "http://127.0.0.1:8000")
    token_path = env("TOKEN_PATH", "/api/auth/token/")
    public_state_path = env("PUBLIC_STATE_PATH", "/api/public/state/")
    secure_ping_path = env("SECURE_PING_PATH", "/api/secure/ping/")
    secure_state_path = env("SECURE_STATE_PATH", "/api/secure/state/")

    username = os.getenv("LOCUST_USER", "")
    password = os.getenv("LOCUST_PASS", "")

    token: Optional[str] = None

    def _extract_token(self, payload: dict) -> Optional[str]:
        for k in ("access", "token", "access_token", "key"):
            v = payload.get(k)
            if isinstance(v, str) and v:
                return v
        # sometimes nested: {"data":{"access":...}}
        for k in ("data", "result"):
            inner = payload.get(k)
            if isinstance(inner, dict):
                t = self._extract_token(inner)
                if t:
                    return t
        return None

    def get_valid_token(self) -> Optional[str]:
        """
        Fetch a valid token if we don't have one. Returns token or None.
        """
        if self.token:
            return self.token
        if not (self.username and self.password):
            # Allow running attack-only / baseline without creds, but secure_valid_only needs creds.
            return None

        body = {"username": self.username, "password": self.password}
        headers = {"Content-Type": "application/json"}

        with self.client.post(
            self.token_path,
            data=json.dumps(body),
            headers=headers,
            name="AUTH_TOKEN",
            catch_response=True,
        ) as resp:
            if resp.status_code in OK_STATUS:
                try:
                    payload = resp.json()
                except Exception:
                    resp.failure(f"AUTH_TOKEN bad json ({resp.status_code})")
                    return None
                token = self._extract_token(payload)
                if token:
                    self.token = token
                    resp.success()
                    return token
                resp.failure("AUTH_TOKEN missing token field")
                return None

            # Non-OK => treat 401/403/429 as blocked/denied failures, others as general failures
            resp.failure(f"AUTH_TOKEN HTTP {resp.status_code}")
            return None

    def auth_header(self) -> dict:
        t = self.get_valid_token()
        if not t:
            return {}
        # Common patterns: Bearer <token> (SimpleJWT)
        return {"Authorization": f"Bearer {t}"}

    # -------------------------
    # Baseline: Public endpoint
    # -------------------------
    @task(1)
    @tag("baseline_public_state")
    def public_state(self):
        with self.client.get(self.public_state_path, name="PUBLIC_STATE", catch_response=True) as resp:
            if resp.status_code in OK_STATUS:
                resp.success()
            else:
                resp.failure(f"PUBLIC_STATE HTTP {resp.status_code}")

    # -----------------------------------------
    # Valid-only: Secure endpoints (legitimate)
    # -----------------------------------------
    @task(1)
    @tag("secure_valid_only", "secure_mixed_80_20")
    def secure_ping_valid(self):
        headers = self.auth_header()
        with self.client.get(self.secure_ping_path, headers=headers, name="SECURE_PING", catch_response=True) as resp:
            if resp.status_code in OK_STATUS:
                resp.success()
            else:
                # if token expired/invalid, drop token so next call re-auths
                if resp.status_code == 401:
                    self.token = None
                resp.failure(f"SECURE_PING HTTP {resp.status_code}")

    @task(1)
    @tag("secure_valid_only", "secure_mixed_80_20")
    def secure_state_valid(self):
        headers = self.auth_header()
        with self.client.get(self.secure_state_path, headers=headers, name="SECURE_STATE", catch_response=True) as resp:
            if resp.status_code in OK_STATUS:
                resp.success()
            else:
                if resp.status_code == 401:
                    self.token = None
                resp.failure(f"SECURE_STATE HTTP {resp.status_code}")

    # -------------------------------------------------
    # Mixed 80/20: invalid/missing token (attack traffic)
    # -------------------------------------------------
    @task(4)  # 4 + 4 invalid vs 1 + 1 valid => 80% invalid overall
    @tag("secure_mixed_80_20")
    def secure_ping_invalid(self):
        # Missing or garbage token
        hdr = {"Authorization": f"Bearer {rand_str(24)}"}
        with self.client.get(self.secure_ping_path, headers=hdr, name="SECURE_PING", catch_response=True) as resp:
            if resp.status_code in OK_STATUS:
                # If your secure endpoint accidentally accepts invalid tokens, treat as failure (important!)
                resp.failure("SECURE_PING accepted invalid token")
            else:
                resp.failure(f"SECURE_PING HTTP {resp.status_code}")

    @task(4)
    @tag("secure_mixed_80_20")
    def secure_state_invalid(self):
        hdr = {"Authorization": f"Bearer {rand_str(24)}"}
        with self.client.get(self.secure_state_path, headers=hdr, name="SECURE_STATE", catch_response=True) as resp:
            if resp.status_code in OK_STATUS:
                resp.failure("SECURE_STATE accepted invalid token")
            else:
                resp.failure(f"SECURE_STATE HTTP {resp.status_code}")

    # -------------------------
    # Login storm (brute force)
    # -------------------------
    @task(19)
    @tag("auth_login_storm")
    def login_invalid(self):
        # Wrong password on purpose.
        body = {"username": self.username or "user", "password": (self.password or "pass") + "_WRONG"}
        headers = {"Content-Type": "application/json"}

        with self.client.post(self.token_path, data=json.dumps(body), headers=headers, name="AUTH_TOKEN", catch_response=True) as resp:
            if resp.status_code in OK_STATUS:
                # If brute-force succeeds, that's a security smell. Count as failure.
                resp.failure("AUTH_TOKEN login_invalid unexpectedly succeeded")
            else:
                resp.failure(f"AUTH_TOKEN HTTP {resp.status_code}")

    @task(1)
    @tag("auth_login_storm")
    def login_valid_small(self):
        # A small trickle of legitimate logins during the storm (more realistic).
        if not (self.username and self.password):
            return
        body = {"username": self.username, "password": self.password}
        headers = {"Content-Type": "application/json"}
        with self.client.post(self.token_path, data=json.dumps(body), headers=headers, name="AUTH_TOKEN", catch_response=True) as resp:
            if resp.status_code in OK_STATUS:
                resp.success()
            else:
                resp.failure(f"AUTH_TOKEN(valid) HTTP {resp.status_code}")
