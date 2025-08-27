from locust import run_single_user, constant
from AgentUser import AgentUser

class AgentB100(AgentUser):
    batch_size = 100
    wait_time = constant(1)

if __name__ == "__main__":
    # For step-by-step debugging
    run_single_user(AgentB100)
    