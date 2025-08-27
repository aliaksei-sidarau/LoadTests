from locust import run_single_user, between, LoadTestShape
from AgentUser import AgentUser

class AgentB1000(AgentUser):
    batch_size = 1000
    wait_time = between(0.9, 1.1)
    
class StageShape(LoadTestShape):

    def tick(self):
        run_time = self.get_run_time()

        iteration = run_time // 10 + 1
        return (iteration * 100, 100)


if __name__ == "__main__":
    # For step-by-step debugging
    run_single_user(AgentB1000)
    