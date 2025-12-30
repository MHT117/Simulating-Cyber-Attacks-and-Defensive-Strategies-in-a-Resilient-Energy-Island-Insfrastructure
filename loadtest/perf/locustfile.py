from locust import HttpUser, task, between


class PublicStateUser(HttpUser):
    # Wait between requests: controls RPS along with user count
    wait_time = between(0.1, 0.5)  # 2-10 req/s per user approx

    @task(8)
    def read_public_state(self):
        # target: Nginx front
        self.client.get("/api/state", name="/api/state")

    # later we can add JWT-based tasks, /api/secure/state etc.
