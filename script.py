import argparse
from typing import Optional

class NodeRunner:
    PORTS = {
        "proposer": 1002,
        "proposer2": 1003,
        "acceptor": 1004,
        "acceptor2": 1005
    }

    @staticmethod
    def run_coordinator():
        print("Starting Coordinator node...")
        from coordinator import run_coordinator
        run_coordinator()

    @staticmethod
    def run_proposer(letter_range: str, module: str):
        print(f"Starting Proposer node for range {letter_range}...")
        module = __import__(module)
        module.run_proposer(letter_range)

    @staticmethod
    def run_acceptor(module: str):
        print("Starting Acceptor node...")
        module = __import__(module)
        module.run_acceptor()

    @staticmethod
    def run_learner():
        print("Starting Learner node...")
        from learner import run_learner
        run_learner()

def main():
    parser = argparse.ArgumentParser(description="Run a node in a distributed consensus system.")
    parser.add_argument("--role", type=str, required=True,
                       choices=["coordinator", "proposer", "proposer2", "acceptor", "acceptor2", "learner"])
    parser.add_argument("--range", type=str, help="Letter range assigned to proposer (e.g., A-C)")
    parser.add_argument("--port", type=int, default=0, help="Port for proposer or acceptor")
    args = parser.parse_args()

    runner = NodeRunner()

    if args.role == "coordinator":
        runner.run_coordinator()
    elif args.role in ("proposer", "proposer2"):
        if not args.range:
            print(f"Error: --range is required for {args.role} role.")
            return
        module = "proposer" if args.role == "proposer" else "proposer2"
        runner.run_proposer(args.range, module)
    elif args.role in ("acceptor", "acceptor2"):
        module = "acceptor" if args.role == "acceptor" else "acceptor2"
        runner.run_acceptor(module)
    elif args.role == "learner":
        runner.run_learner()

if __name__ == "__main__":
    main()