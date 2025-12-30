import os
from locust import HttpUser, task, between

USERNAME = os.getenv("LOCUST_USER", "loadtest")
PASSWORD = os.getenv("LOCUST_PASS", "LoadTest!1234")


class LoginStorm(HttpUser):
    wait_time = between(0.0, 0.2)

    @task
    def login(self):
        # Many logins per second
        self.client.post(
            "/api/auth/token/",
            json={"username": USERNAME, "password": PASSWORD},
            name="/api/auth/token/",
        )
