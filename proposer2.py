from flask import Flask, request
from sidecar import Sidecar
import threading
import time
import re
from typing import Dict, List, Tuple, Optional


class Proposer:
    def __init__(self, host: str = "127.0.0.1", port: int = 1003):
        self.app = Flask(__name__)
        self.sidecar = Sidecar("proposer2")
        self.host = host
        self.port = port
        self.letter_range: Optional[str] = None
        self.nodes: Dict[str, any] = {"acceptors": [], "learner": None}
        self.word_counts: Dict[str, Dict[str, any]] = {}
        self._setup_routes()

    def _setup_routes(self) -> None:
        """Configure Flask routes."""

        @self.app.route("/line", methods=["POST"])
        def receive_line():
            if not self.letter_range:
                print("Error: Range not set")
                return {"error": "Range not set"}, 400

            line = request.json.get("text", "")
            print(f"Received line: {line}")

            start, end = self.letter_range.split("-")
            words = re.findall(r'\b[a-zA-Z]+\b', line.lower())
            print(f"Words found: {words}")

            count, matched_words = self._process_words(words, start, end)
            self._update_word_counts(count, matched_words)
            self._send_to_acceptors()

            return {"status": f"Processed line for range {self.letter_range}"}

        @self.app.route("/set_range", methods=["POST"])
        def set_range():
            new_range = request.json.get("range", "")
            print(f"Attempting to set range: {new_range}")

            if not self._is_valid_range(new_range):
                return {"error": "Invalid range format"}, 400

            self.letter_range = new_range
            print(f"Set range: {self.letter_range}")
            return {"status": f"Range set to {self.letter_range}"}

        @self.app.route("/nodes", methods=["POST"])
        def update_nodes():
            self.nodes = request.json or {}
            print(f"Updated nodes: {self.nodes}")
            return {"status": "Nodes updated"}

    def _is_valid_range(self, range_str: str) -> bool:

        return (isinstance(range_str, str) and
                "-" in range_str and
                len(range_str.split("-")) == 2)

    def _process_words(self, words: List[str], start: str, end: str) -> Tuple[int, List[str]]:

        count = 0
        matched_words = []
        for word in words:
            if word and start.lower() <= word[0].lower() <= end.lower():
                count += 1
                matched_words.append(word)
        print(f"Matched words for {self.letter_range}: {matched_words}")
        return count, matched_words

    def _update_word_counts(self, count: int, matched_words: List[str]) -> None:

        if self.letter_range not in self.word_counts:
            self.word_counts[self.letter_range] = {"count": 0, "words": []}
        self.word_counts[self.letter_range]["count"] += count
        self.word_counts[self.letter_range]["words"].extend(matched_words)

    def _send_to_acceptors(self) -> None:

        if not self.nodes["acceptors"]:
            print("No acceptors registered")
            return

        for acceptor in self.nodes["acceptors"][:2]:
            print(f"Sending to {acceptor['url']}: {self.word_counts[self.letter_range]}")
            self.sidecar.send(
                f"{acceptor['url']}/accept",
                {
                    "letter_range": self.letter_range,
                    "count": self.word_counts[self.letter_range]["count"],
                    "words": self.word_counts[self.letter_range]["words"]
                },
                retries=3,
                delay=1
            )

    def _send_test_request(self) -> None:
        """Send a test registration request to the coordinator."""
        time.sleep(1)
        self.sidecar.send(
            "http://127.0.0.1:1001/register",
            {"type": "proposer", "url": f"http://{self.host}:{self.port}"},
            retries=3,
            delay=1
        )

    def run(self, letter_range: str) -> None:

        self.letter_range = letter_range
        print(f"Proposer is responsible for letter range: {self.letter_range}")

        test_thread = threading.Thread(target=self._send_test_request)
        test_thread.daemon = True
        test_thread.start()

        self.app.run(host=self.host, port=self.port)


def run_proposer(rng: str) -> None:
    proposer = Proposer()
    proposer.run(rng)


if __name__ == "__main__":
    run_proposer("A-Z")  # Default range for testing