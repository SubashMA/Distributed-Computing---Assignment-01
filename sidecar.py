import requests
import logging
import time
from typing import Any, Optional
from requests import Response


class Sidecar:
    def __init__(self, node_name: str, log_level: int = logging.INFO) -> None:

        self.node_name = node_name
        self._setup_logging(log_level)

    def _setup_logging(self, log_level: int) -> None:

        logger = logging.getLogger()
        if not logger.hasHandlers():
            logging.basicConfig(
                filename=f"{self.node_name}.log",
                level=log_level,
                format='%(asctime)s - %(levelname)s - %(message)s'
            )

    def send(self, url: str, data: Any, retries: int = 3, delay: float = 1.0) -> Optional[Response]:

        for attempt in range(1, retries + 1):
            try:
                logging.info(f"Attempt {attempt} - Sending to {url}: {data}")
                response = requests.post(url, json=data)
                logging.info(f"Response: {response.status_code}")
                return response
            except requests.RequestException as e:
                logging.error(f"Attempt {attempt} failed: {e}")
                if attempt < retries:
                    time.sleep(delay)

        logging.error(f"All {retries} attempts failed for {url}")
        return None


if __name__ == "__main__":
    # Example usage for testing
    sidecar = Sidecar("test_node")
    response = sidecar.send("http://127.0.0.1:1000/test", {"test": "data"})
    print(f"Test response: {response.status_code if response else 'Failed'}")