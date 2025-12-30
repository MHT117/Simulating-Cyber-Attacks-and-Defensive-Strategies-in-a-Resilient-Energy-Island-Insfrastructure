import os
import random
from locust import HttpUser, task, between

API_STATE = os.getenv("API_STATE", "/api/state")
API_TOKEN = os.getenv("API_TOKEN", "/api/auth/token")
API_SECURE_PING = os.getenv("API_SECURE_PING", "/api/secure/ping")
API_SECURE_STATE = os.getenv("API_SECURE_STATE", "/api/secure/state")

SCENARIO = os.getenv("SCENARIO", "baseline_public_state")  # pick which run to execute
VALID_RATIO = float(os.getenv("VALID_RATIO", "0.8"))       # for mixed scenario

LOCUST_USER = os.getenv("LOCUST_USER", "")
LOCUST_PASS = os.getenv("LOCUST_PASS", "")


def _extract_token(json_data: dict) -> str | None:
    # support {"token": "..."} OR {"access": "..."} (JWT-style)
    return json_data.get("token") or json_data.get("access")


class SuiteUser(HttpUser):
    wait_time = between(0.5, 1.5)

    def on_start(self):
        self.token = None
        if SCENARIO in ("secure_valid_only", "secure_mixed"):
            if not LOCUST_USER or not LOCUST_PASS:
                # Let the run proceed, but secure requests will likely 401
                return

            with self.client.post(
                API_TOKEN,
                json={"username": LOCUST_USER, "password": LOCUST_PASS},
                name="AUTH_TOKEN",
                catch_response=True,
            ) as r:
                if r.status_code == 200:
                    t = _extract_token(
                        r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
                    )
                    if t:
                        self.token = t
                        r.success()
                    else:
                        r.failure("Token missing in response JSON")
                else:
                    r.failure(f"token_endpoint_status={r.status_code}")

    def _auth_headers_valid(self):
        # Adjust prefix if your API expects "Token" instead of "Bearer"
        if not self.token:
            return {}
        return {"Authorization": f"Bearer {self.token}"}

    def _auth_headers_invalid(self):
        return {"Authorization": "Bearer invalidtoken"}

    @task
    def run_suite(self):
        # 1) Baseline public endpoint only (should be ~all 200)
        if SCENARIO == "baseline_public_state":
            self.client.get(API_STATE, name="PUBLIC_STATE")
            return

        # 2) Auth login storm (should be mostly 401/403)
        if SCENARIO == "auth_login_storm":
            # bad creds on purpose
            self.client.post(
                API_TOKEN,
                json={"username": "baduser", "password": "badpass"},
                name="AUTH_TOKEN_BAD",
            )
            return

        # 3) Secure valid only (should be ~all 200 if token works)
        if SCENARIO == "secure_valid_only":
            h = self._auth_headers_valid()
            self.client.get(API_SECURE_PING, headers=h, name="SECURE_PING_VALID")
            self.client.get(API_SECURE_STATE, headers=h, name="SECURE_STATE_VALID")
            return

        # 4) Secure mixed 80/20 (valid vs invalid token)
        if SCENARIO == "secure_mixed":
            if random.random() < VALID_RATIO:
                h = self._auth_headers_valid()
                self.client.get(API_SECURE_PING, headers=h, name="SECURE_PING_VALID")
                self.client.get(API_SECURE_STATE, headers=h, name="SECURE_STATE_VALID")
            else:
                h = self._auth_headers_invalid()
                self.client.get(API_SECURE_PING, headers=h, name="SECURE_PING_INVALID")
                self.client.get(API_SECURE_STATE, headers=h, name="SECURE_STATE_INVALID")
            return
