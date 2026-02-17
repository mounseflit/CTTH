"""
Manual data fetch script: trigger any agent from the command line.

Usage:
    docker compose exec backend python scripts/manual_fetch.py --agent eurostat
    docker compose exec backend python scripts/manual_fetch.py --agent comtrade
    docker compose exec backend python scripts/manual_fetch.py --agent federal_register
    docker compose exec backend python scripts/manual_fetch.py --agent general_watcher
    docker compose exec backend python scripts/manual_fetch.py --agent all
"""
import argparse
import logging
import sys

sys.path.insert(0, "/app")

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")

from app.database import SyncSessionLocal
from app.agents.eurostat_agent import EurostatAgent
from app.agents.comtrade_agent import ComtradeAgent
from app.agents.federal_register_agent import FederalRegisterAgent
from app.agents.general_watcher import GeneralWatcher

AGENTS = {
    "eurostat": EurostatAgent,
    "comtrade": ComtradeAgent,
    "federal_register": FederalRegisterAgent,
    "general_watcher": GeneralWatcher,
}


def run_agent(name: str):
    agent_class = AGENTS.get(name)
    if not agent_class:
        print(f"Unknown agent: {name}")
        print(f"Available: {', '.join(AGENTS.keys())}")
        return

    print(f"\n{'='*60}")
    print(f"Running agent: {name}")
    print(f"{'='*60}")

    with SyncSessionLocal() as db:
        agent = agent_class(db)
        try:
            count = agent.fetch_data()
            agent.update_status("active", records=count)
            print(f"\n[OK] {name}: {count} records fetched/updated")
        except Exception as e:
            agent.update_status("error", error_msg=str(e))
            print(f"\n[ERROR] {name}: {e}")
            logging.exception(f"Agent {name} failed")


def main():
    parser = argparse.ArgumentParser(description="Manual data fetch")
    parser.add_argument(
        "--agent",
        required=True,
        choices=list(AGENTS.keys()) + ["all"],
        help="Agent to run",
    )
    args = parser.parse_args()

    if args.agent == "all":
        for name in AGENTS:
            run_agent(name)
    else:
        run_agent(args.agent)


if __name__ == "__main__":
    main()
