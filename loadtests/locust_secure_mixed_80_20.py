import os
import random
from locust import HttpUser, task, between

USER = os.getenv("LOCUST_USER", "testuser")
PASS = os.getenv("LOCUST_PASS", "testpass")

class SecureMixedUser(HttpUser):
    wait_time = between(0.05, 0.3)

    def on_start(self):
        self.token = None
        self._get_token()

    def _get_token(self):
        payload = {"username": USER, "password": PASS}
        r = self.client.post("/api/auth/token/", json=payload, name="/api/auth/token/", timeout=10)
        if r.status_code == 200:
            data = r.json()
            self.token = data.get("access") or data.get("token")

    def _valid_headers(self):
        return {"Authorization": f"Bearer {self.token}"} if self.token else {}

    def _invalid_headers(self):
        return {"Authorization": "Bearer definitely_invalid_token"}

    @task
    def secure_mixed(self):
        # 80% invalid, 20% valid
        valid = random.random() < 0.2
        headers = self._valid_headers() if valid else self._invalid_headers()

        # REAL URL; label using name=
        self.client.get(
            "/api/secure/ping",
            name="/api/secure/ping (valid)" if valid else "/api/secure/ping (invalid)",
            headers=headers,
            timeout=10,
        )
