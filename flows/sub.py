from prefect import flow, get_run_logger
from platform import node, platform


@flow
def sub(user_input: str = "World") -> None:
    logger = get_run_logger()
    logger.info("Hello from Prefect, %s! 🚀", user_input)
    logger.info("Network: %s. Instance: %s. Agent is healthy ✅️", node(), platform())


if __name__ == "__main__":
    sub()
