from flask import Flask, request
from sidecar import Sidecar
import threading
import time
from typing import Dict, List, Optional


class Learner:
    def __init__(self, host: str = "127.0.0.1", port: int = 1006):
        self.app = Flask(__name__)
        self.sidecar = Sidecar("learner")
        self.host = host
        self.port = port
        self.results: Dict[str, Dict[str, any]] = {}
        self._setup_routes()

    def _setup_routes(self) -> None:

        @self.app.route("/learn", methods=["POST"])
        def learn():
            data = request.json or {}
            letter_range = data.get("letter_range")
            count = data.get("count", 0)
            words = data.get("words", [])

            print(f"Learning: {letter_range} -> count={count}, words={words}")

            if letter_range:
                self._process_words(words)

            return {"status": "Learned"}

        @self.app.route("/results", methods=["GET"])
        def get_results():
            table = self._generate_results_table()
            print(f"Returning results: {table}")
            return {"results": table}

        @self.app.route("/nodes", methods=["POST"])
        def update_nodes():
            return {"status": "Nodes updated"}

    def _process_words(self, words: List[str]) -> None:

        for word in words:
            if word:
                start_letter = word[0].lower()
                if start_letter not in self.results:
                    self.results[start_letter] = {"count": 0, "words": []}
                if word not in self.results[start_letter]["words"]:
                    self.results[start_letter]["count"] += 1
                    self.results[start_letter]["words"].append(word)

    def _generate_results_table(self) -> List[Dict[str, str]]:

        table = []
        for start_letter, data in sorted(self.results.items()):
            table.append({
                "Starting letter": start_letter.upper(),
                "Count": str(data["count"]),  # Convert to string for JSON serialization
                "Words": ", ".join(data["words"]) if data["words"] else ""
            })
        return table

    def _send_test_request(self) -> None:

        time.sleep(1)
        self.sidecar.send(
            "http://127.0.0.1:1001/register",
            {"type": "learner", "url": f"http://{self.host}:{self.port}"},
            retries=3,
            delay=1
        )

    def run(self) -> None:
        print(f"Learner is running on port {self.port}")

        test_thread = threading.Thread(target=self._send_test_request)
        test_thread.daemon = True
        test_thread.start()

        self.app.run(host=self.host, port=self.port)


def run_learner() -> None:
    learner = Learner()
    learner.run()


if __name__ == "__main__":
    run_learner()