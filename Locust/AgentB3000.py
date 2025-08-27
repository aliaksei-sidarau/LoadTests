from locust import run_single_user, constant, LoadTestShape
from AgentUser import AgentUser

class AgentB3000(AgentUser):
    batch_size = 3000
    wait_time = constant(1)

class StageShape: #(LoadTestShape):
    stages = [
        {"duration": 80, "users": 500, "spawn_rate": 10},
        {"duration": 160, "users": 800, "spawn_rate": 10},
        {"duration": 200, "users": 1000, "spawn_rate": 10},
        {"duration": 400, "users": 1000, "spawn_rate": 10}
    ]

    def tick(self):
        run_time = self.get_run_time()

        for stage in self.stages:
            if run_time < stage["duration"]:
                tick_data = (stage["users"], stage["spawn_rate"])
                return tick_data

        return None

if __name__ == "__main__":
    # For step-by-step debugging
    run_single_user(AgentB3000)
    