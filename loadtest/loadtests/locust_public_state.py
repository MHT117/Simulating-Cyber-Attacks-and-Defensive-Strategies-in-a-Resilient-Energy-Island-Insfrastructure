from locust import HttpUser, task, between

class PublicStateUser(HttpUser):
    # Baseline should be "normal use", not a DDoS.
    wait_time = between(0.8, 1.6)

    @task
    def read_public_state(self):
        # URL is correct; name is just the label
        self.client.get("/api/state", name="/api/state", timeout=10)
