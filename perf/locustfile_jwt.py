import os
from locust import HttpUser, task, between

USERNAME = os.getenv("LOCUST_USER", "loadtest")
PASSWORD = os.getenv("LOCUST_PASS", "LoadTest!1234")
GOOD_WEIGHT = int(os.getenv("LOCUST_GOOD_WEIGHT", "8"))
BAD_WEIGHT = int(os.getenv("LOCUST_BAD_WEIGHT", "2"))


class JWTBase(HttpUser):
    abstract = True
    wait_time = between(0.1, 0.4)  # tune for more/less pressure

    def _get_token(self) -> str:
        # SimpleJWT endpoint under /api/
        r = self.client.post(
            "/api/auth/token/",
            json={"username": USERNAME, "password": PASSWORD},
            name="/api/auth/token/",
        )
        r.raise_for_status()
        return r.json()["access"]


class GoodJWTUser(JWTBase):
    """
    Valid user: logs in once and repeatedly calls secure endpoints.
    """

    weight = GOOD_WEIGHT  # 80% if BadJWTUser weight is 2
    token = None

    def on_start(self):
        self.token = self._get_token()

    @task(6)
    def secure_ping(self):
        self.client.get(
            "/api/secure/ping",
            headers={"Authorization": f"Bearer {self.token}"},
            name="/api/secure/ping (valid)",
        )

    @task(4)
    def secure_state(self):
        self.client.get(
            "/api/secure/state",
            headers={"Authorization": f"Bearer {self.token}"},
            name="/api/secure/state (valid)",
        )


class BadJWTUser(JWTBase):
    """
    Malicious: uses an invalid token and expects 401.
    We mark 401 as SUCCESS so Locust failure rate reflects unexpected errors only.
    """

    weight = BAD_WEIGHT  # 20% of traffic
    bad_token = "this.is.not.a.jwt"

    @task(10)
    def secure_ping_invalid(self):
        with self.client.get(
            "/api/secure/ping",
            headers={"Authorization": f"Bearer {self.bad_token}"},
            name="/api/secure/ping (invalid)",
            catch_response=True,
        ) as resp:
            if resp.status_code == 401:
                resp.success()  # expected block
            else:
                resp.failure(f"Expected 401, got {resp.status_code}")

    @task(10)
    def secure_state_invalid(self):
        with self.client.get(
            "/api/secure/state",
            headers={"Authorization": f"Bearer {self.bad_token}"},
            name="/api/secure/state (invalid)",
            catch_response=True,
        ) as resp:
            if resp.status_code == 401:
                resp.success()
            else:
                resp.failure(f"Expected 401, got {resp.status_code}")
