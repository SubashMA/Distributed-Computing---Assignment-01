from flask import Flask, request
from sidecar import Sidecar
import threading
import time
from typing import Dict, List, Optional


class Acceptor:
    def __init__(self, host: str = "127.0.0.1", port: int = 1004):
        self.app = Flask(__name__)
        self.sidecar = Sidecar("acceptor")
        self.host = host
        self.port = port
        self.nodes: Dict[str, Optional[Dict]] = {"learner": None}
        self._setup_routes()

    def _setup_routes(self) -> None:

        @self.app.route("/accept", methods=["POST"])
        def accept_result():
            data = request.json or {}
            letter_range = data.get("letter_range")
            count = data.get("count", 0)
            words = data.get("words", [])

            print(f"Received: {data}")

            if not letter_range:
                print("Error: Invalid data")
                return {"error": "Invalid data"}, 400

            if not self._validate_data(letter_range, count, words):
                print("Error: Validation failed")
                return {"error": "Validation failed"}, 400

            self._forward_to_learner(letter_range, count, words)
            return {"status": "Accepted"}

        @self.app.route("/nodes", methods=["POST"])
        def update_nodes():
            self.nodes = request.json or {}
            print(f"Updated nodes: {self.nodes}")
            return {"status": "Nodes updated"}

    def _validate_data(self, letter_range: str, count: int, words: List[str]) -> bool:
        try:
            start, end = letter_range.split("-")
            valid_words = all(start.lower() <= word[0].lower() <= end.lower() for word in words) if words else True
            count_matches = len(words) == count
            print(f"Validation: valid_words={valid_words}, count_matches={count_matches}")
            return valid_words and count_matches
        except ValueError:
            return False

    def _forward_to_learner(self, letter_range: str, count: int, words: List[str]) -> None:
        if self.nodes["learner"]:
            print(f"Sending to learner: {self.nodes['learner']['url']}")
            self.sidecar.send(
                f"{self.nodes['learner']['url']}/learn",
                {"letter_range": letter_range, "count": count, "words": words},
                retries=3,
                delay=1
            )
        else:
            print("No learner registered")

    def _send_test_request(self) -> None:
        time.sleep(1)
        self.sidecar.send(
            "http://127.0.0.1:1001/register",
            {"type": "acceptor", "url": f"http://{self.host}:{self.port}"},
            retries=3,
            delay=1
        )

    def run(self) -> None:
        print(f"Acceptor is running on port {self.port}")

        test_thread = threading.Thread(target=self._send_test_request)
        test_thread.daemon = True
        test_thread.start()

        self.app.run(host=self.host, port=self.port)


def run_acceptor() -> None:
    acceptor = Acceptor()
    acceptor.run()


if __name__ == "__main__":
    run_acceptor()