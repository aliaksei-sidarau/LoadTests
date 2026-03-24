from locust import constant, between
from locust import run_single_user, LoadTestShape
from AgentUser import AgentUser

class AgentB100(AgentUser):
    batch_size = constant(100)
    wait_time = between(0.9, 1.1)
    
class StageShape(LoadTestShape):

    def tick(self):
        run_time = self.get_run_time()

        iteration = run_time // 30 + 1
        return (iteration * 1000, 100)

if __name__ == "__main__":
    # For step-by-step debugging
    run_single_user(AgentB100)
    