"""
Manual data fetch script: trigger any agent from the command line.

Usage:
    cd backend && python -m scripts.manual_fetch --agent eurostat
    -- or --
    python scripts/manual_fetch.py --agent comtrade
    python scripts/manual_fetch.py --agent federal_register
    python scripts/manual_fetch.py --agent general_watcher
    python scripts/manual_fetch.py --agent otexa
    python scripts/manual_fetch.py --agent all
"""
import argparse
import logging
import os
import sys

# Ensure the backend package is importable
_here = os.path.dirname(os.path.abspath(__file__))
_backend = os.path.join(os.path.dirname(_here), "backend")
if _backend not in sys.path:
    sys.path.insert(0, _backend)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")

from app.agents.comtrade_agent import ComtradeAgent
from app.agents.eurostat_agent import EurostatAgent
from app.agents.federal_register_agent import FederalRegisterAgent
from app.agents.general_watcher import GeneralWatcher
from app.database import get_sync_db

# Try to import OtexaAgent (may not exist yet)
try:
    from app.agents.otexa_agent import OtexaAgent
    _HAS_OTEXA = True
except ImportError:
    _HAS_OTEXA = False

AGENTS: dict = {
    "eurostat": EurostatAgent,
    "comtrade": ComtradeAgent,
    "federal_register": FederalRegisterAgent,
    "general_watcher": GeneralWatcher,
}
if _HAS_OTEXA:
    AGENTS["otexa"] = OtexaAgent


def run_agent(name: str):
    agent_class = AGENTS.get(name)
    if not agent_class:
        print(f"Unknown agent: {name}")
        print(f"Available: {', '.join(AGENTS.keys())}")
        return

    print(f"\n{'='*60}")
    print(f"Running agent: {name}")
    print(f"{'='*60}")

    db = get_sync_db()
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
