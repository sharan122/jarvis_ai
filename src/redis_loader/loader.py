"""
Redis data loader.

Reads value-store JSON files from data/ and loads them into Redis.
Run this before starting Agent 2 sessions.

Usage:
    python -m redis_loader.loader
    python -m redis_loader.loader --file data/aws_ec2_values.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from agent.tools.redis_client import get_redis_client

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def load_values_file(file_path: Path) -> None:
    """Load a single value-store JSON file into Redis."""
    client = get_redis_client()

    with open(file_path) as f:
        data = json.load(f)

    count = 0
    for service_id, fields in data.items():
        for key, value in fields.items():
            redis_key = f"{service_id}:{key}"
            client.set_json(redis_key, value)
            count += 1
            print(f"  Loaded {redis_key}")

    print(f"  Total keys loaded: {count}")


def load_all() -> None:
    """Load every *_values.json file found in data/."""
    files = sorted(DATA_DIR.glob("*_values.json"))
    if not files:
        print(f"No *_values.json files found in {DATA_DIR}")
        return

    for f in files:
        print(f"\nLoading {f.name} ...")
        load_values_file(f)

    print("\nDone.")


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "--file":
        load_values_file(Path(sys.argv[2]))
    else:
        load_all()
