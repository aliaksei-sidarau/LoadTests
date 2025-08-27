from locust import run_single_user, constant
from AgentUser import AgentUser

class AgentB10(AgentUser):
    batch_size = 10
    wait_time = constant(1)

if __name__ == "__main__":
    # For step-by-step debugging
    run_single_user(AgentB10)
