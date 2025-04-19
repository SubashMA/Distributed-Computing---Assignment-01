from flask import Flask, request
from sidecar import Sidecar
import threading
import time
import math
from typing import Dict, List, Optional


class Coordinator:
    def __init__(self, host: str = "127.0.0.1", port: int = 1001):
        self.app = Flask(__name__)
        self.sidecar = Sidecar("coordinator")
        self.host = host
        self.port = port
        self.nodes: Dict[str, any] = {
            "proposers": [],
            "acceptors": [],
            "learner": None
        }
        self._setup_routes()

    def _setup_routes(self) -> None:

        @self.app.route("/", methods=["GET"])
        def home():
            return {"message": "Welcome to the Coordinator Node!"}

        @self.app.route("/register", methods=["POST"])
        def register():
            data = request.json or {}
            node_type = data.get("type")
            node_url = data.get("url")

            if not (node_type and node_url):
                print("Registration error: Missing type or url")
                return {"error": "Missing type or url"}, 400

            print(f"Registering: {node_type} at {node_url}")

            if node_type == "proposer":
                self._register_proposer(node_url)
            elif node_type == "acceptor":
                self._register_acceptor(node_url)
            elif node_type == "learner":
                self.nodes["learner"] = {"url": node_url}
            else:
                return {"error": "Invalid node type"}, 400

            self._assign_ranges()
            self._broadcast_nodes()
            print(f"Current nodes: {self.nodes}")
            return {"status": "Registered"}

        @self.app.route("/start", methods=["POST"])
        def start():
            data = request.json or {}
            filename = data.get("filename", "sample.txt")
            print(f"Processing file: {filename}")
            try:
                with open(filename, "r") as file:
                    lines = file.readlines()
                    print(f"Read {len(lines)} lines")
                    for line in lines:
                        line = line.strip()
                        if line:
                            print(f"Sending line to {len(self.nodes['proposers'])} proposers: {line}")
                            for proposer in self.nodes["proposers"]:
                                self.sidecar.send(
                                    f"{proposer['url']}/line",
                                    {"text": line},
                                    retries=3,
                                    delay=1
                                )
                return {"status": "Document processed"}
            except Exception as e:
                print(f"Error: {e}")
                return {"error": str(e)}, 500

    def _register_proposer(self, node_url: str) -> None:
        """Register a proposer node if not already registered."""
        if not any(p["url"] == node_url for p in self.nodes["proposers"]):
            self.nodes["proposers"].append({"url": node_url, "range": None})
        else:
            print(f"Proposer {node_url} already registered")

    def _register_acceptor(self, node_url: str) -> None:
        """Register an acceptor node if not already registered."""
        if not any(a["url"] == node_url for a in self.nodes["acceptors"]):
            self.nodes["acceptors"].append({"url": node_url})

    def _assign_ranges(self) -> None:
        """Assign letter ranges to proposers."""
        num_proposers = len(self.nodes["proposers"])
        print(f"Assigning ranges to {num_proposers} proposers")
        if num_proposers == 0:
            return

        for proposer in self.nodes["proposers"]:
            proposer["range"] = None

        letters = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
        letters_per_proposer = max(1, math.ceil(len(letters) / num_proposers))

        for i, proposer in enumerate(self.nodes["proposers"]):
            start_idx = i * letters_per_proposer
            end_idx = min(start_idx + letters_per_proposer - 1, len(letters) - 1)
            if start_idx < len(letters):
                letter_range = f"{letters[start_idx]}-{letters[end_idx]}"
                proposer["range"] = letter_range
                print(f"Assigned {letter_range} to {proposer['url']}")
                self.sidecar.send(
                    f"{proposer['url']}/set_range",
                    {"range": letter_range},
                    retries=3,
                    delay=1
                )

    def _broadcast_nodes(self) -> None:
        """Broadcast node information to all nodes."""
        node_info = {
            "proposers": self.nodes["proposers"],
            "acceptors": self.nodes["acceptors"],
            "learner": self.nodes["learner"]
        }
        print(f"Broadcasting nodes: {node_info}")

        for node_type in ["proposers", "acceptors"]:
            for node in self.nodes[node_type]:
                self.sidecar.send(
                    f"{node['url']}/nodes",
                    node_info,
                    retries=3,
                    delay=1
                )

        if self.nodes["learner"]:
            self.sidecar.send(
                f"{self.nodes['learner']['url']}/nodes",
                node_info,
                retries=3,
                delay=1
            )

    def _send_test_request(self) -> None:
        """Send a test registration request."""
        time.sleep(1)
        self.sidecar.send(
            f"http://{self.host}:{self.port}/register",
            {"type": "proposer", "url": "http://127.0.0.1:1002"},
            retries=3,
            delay=1
        )

    def run(self) -> None:
        """Run the coordinator server."""
        print(f"Coordinator is running on port {self.port}")

        test_thread = threading.Thread(target=self._send_test_request)
        test_thread.daemon = True
        test_thread.start()

        self.app.run(host=self.host, port=self.port)


def run_coordinator():
    coordinator = Coordinator()
    coordinator.run()


if __name__ == "__main__":
    run_coordinator()