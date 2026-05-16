#!/usr/bin/env python3
"""
Fetch and expand SOLVE-IT data from data.solveit-df.org into the directory
structure expected by solve_it_library.KnowledgeBase.

Usage:
    python3 fetch_solveit_data.py [--output /app/solve-it-main]

Output structure:
    <output>/
        solve-it.json          # objectives list (KnowledgeBase mapping file)
        data/
            techniques/        # DFT-XXXX.json per technique
            weaknesses/        # DFW-XXXX.json per weakness
            mitigations/       # DFM-XXXX.json per mitigation
"""

import argparse
import json
import sys
import urllib.request
from pathlib import Path

DATA_URL = "https://data.solveit-df.org/solve-it.json"


def fetch(url: str) -> dict:
    print(f"Fetching {url} ...", flush=True)
    with urllib.request.urlopen(url, timeout=60) as response:
        return json.loads(response.read().decode())


def expand(data: dict, output: Path) -> None:
    # Create directory structure
    dirs = {
        "techniques": output / "data" / "techniques",
        "weaknesses": output / "data" / "weaknesses",
        "mitigations": output / "data" / "mitigations",
    }
    for d in dirs.values():
        d.mkdir(parents=True, exist_ok=True)

    # Write individual entity files
    for entity_type, dir_path in dirs.items():
        entities = data[entity_type]
        # API returns a dict keyed by ID
        items = entities.values() if isinstance(entities, dict) else entities
        count = 0
        for item in items:
            entity_id = item["id"]
            (dir_path / f"{entity_id}.json").write_text(
                json.dumps(item, indent=2), encoding="utf-8"
            )
            count += 1
        print(f"  Wrote {count} {entity_type}", flush=True)

    # Write objectives as solve-it.json (KnowledgeBase mapping file)
    objectives = data["objectives"]
    mapping_path = output / "solve-it.json"
    mapping_path.write_text(json.dumps(objectives, indent=2), encoding="utf-8")
    print(f"  Wrote {len(objectives)} objectives → solve-it.json", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch live SOLVE-IT data")
    parser.add_argument(
        "--output",
        default="/app/solve-it-main",
        help="Output directory (default: /app/solve-it-main)",
    )
    parser.add_argument(
        "--url",
        default=DATA_URL,
        help=f"Source URL (default: {DATA_URL})",
    )
    args = parser.parse_args()

    output = Path(args.output)

    try:
        data = fetch(args.url)
    except Exception as e:
        print(f"ERROR: Failed to fetch data: {e}", file=sys.stderr)
        sys.exit(1)

    for key in ("techniques", "weaknesses", "mitigations", "objectives"):
        if key not in data:
            print(f"ERROR: Missing key '{key}' in response", file=sys.stderr)
            sys.exit(1)

    expand(data, output)
    print(f"Done. Data written to {output}", flush=True)


if __name__ == "__main__":
    main()
