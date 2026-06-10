"""
Data holder for user entry of variables for ballistics calculation runs.  Up to 3 sets of data.
Stores each run sent from dataentry.py and makes it accessible to bdc.py.

Data is persisted to a JSON file so it survives between program runs.
"""

import json
import os
from typing import List, Dict

# Path to the persistent data file
DATA_FILE = "ballistics_runs.json"

# List of all runs collected from user entries (loaded from file on import)
runs: List[Dict] = []


def _load_runs_from_file() -> None:
    """Load runs from the JSON file if it exists."""
    global runs
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                runs = json.load(f)
            print(f"✓ Loaded {len(runs)} run(s) from {DATA_FILE}")
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Could not load data file: {e}")
            runs = []
    else:
        runs = []


def _save_runs_to_file() -> None:
    """Save runs to the JSON file."""
    try:
        with open(DATA_FILE, 'w') as f:
            json.dump(runs, f, indent=2)
        print(f"✓ Saved {len(runs)} run(s) to {DATA_FILE}")
    except IOError as e:
        print(f"Error: Could not save data file: {e}")


def add_run(run_data: dict) -> None:
    """Add a validated data set from dataentry.py to the runs list.
    Args: run_data: Dictionary containing one complete set of ballistics parameters
    """
    run_data["run_number"] = len(runs) + 1
    runs.append(run_data)
    _save_runs_to_file()  # ← Persist immediately after adding


def get_runs() -> list:
    """Return all collected runs.
    Returns: List of dictionaries, each containing one run's data
    """
    return runs


def clear_runs() -> None:
    """Clear all runs (useful for testing or resetting)."""
    global runs
    runs = []
    # delete the file
    if os.path.exists(DATA_FILE):
        try:
            os.remove(DATA_FILE)
            print(f"✓ Cleared all runs and deleted {DATA_FILE}")
        except IOError as e:
            print(f"Warning: Could not delete data file: {e}")


# load existing runs when module is imported
_load_runs_from_file()
