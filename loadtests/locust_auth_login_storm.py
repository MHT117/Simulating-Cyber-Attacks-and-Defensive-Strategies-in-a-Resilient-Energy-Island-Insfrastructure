import os
from locust import HttpUser, task, between

USER = os.getenv("LOCUST_USER", "testuser")
PASS = os.getenv("LOCUST_PASS", "testpass")

class AuthLoginStormUser(HttpUser):
    # This is intentionally aggressive
    wait_time = between(0.05, 0.2)

    @task
    def token_storm(self):
        payload = {"username": USER, "password": PASS}
        self.client.post("/api/auth/token/", json=payload, name="/api/auth/token/", timeout=10)
