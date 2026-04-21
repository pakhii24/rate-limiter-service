from locust import HttpUser, task, between
import random

class RateLimiterUser(HttpUser):
    wait_time = between(0.1, 0.5)

    @task(3)
    def check_allowed(self):
        self.client.post("/check", json={
            "user_id": f"user{random.randint(1, 50)}",
            "ip": f"192.168.1.{random.randint(1, 50)}",
            "endpoint": "/api/products"
        })

    @task(1)
    def check_health(self):
        self.client.get("/health")