import os
from locust import HttpUser, task, between

USER = os.getenv("LOCUST_USER", "testuser")
PASS = os.getenv("LOCUST_PASS", "testpass")

class SecureValidOnlyUser(HttpUser):
    wait_time = between(0.3, 0.9)

    def on_start(self):
        self.token = None
        self._get_token()

    def _get_token(self):
        payload = {"username": USER, "password": PASS}
        r = self.client.post("/api/auth/token/", json=payload, name="/api/auth/token/", timeout=10)
        if r.status_code == 200:
            data = r.json()
            self.token = data.get("access") or data.get("token")

    def _headers(self):
        return {"Authorization": f"Bearer {self.token}"} if self.token else {}

    @task(3)
    def secure_ping_valid(self):
        if not self.token:
            self._get_token()
            return
        # REAL URL, label in name:
        self.client.get("/api/secure/ping", name="/api/secure/ping (valid)", headers=self._headers(), timeout=10)

    @task(2)
    def secure_state_valid(self):
        if not self.token:
            self._get_token()
            return
        self.client.get("/api/secure/state", name="/api/secure/state (valid)", headers=self._headers(), timeout=10)
