from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Sequence

import pandas as pd

from .crm import MockCRMAdapter
from .pipeline import process_dataframe
from .scoring import load_scoring_config


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="gtm-engine")
    subparsers = parser.add_subparsers(dest="command", required=True)

    demo = subparsers.add_parser("demo", help="Run the offline GTM pipeline against CSV data")
    demo.add_argument("--input", required=True, help="Path to prospect CSV")
    demo.add_argument("--output", default="artifacts", help="Directory for generated artifacts")
    demo.add_argument("--config", default="config/scoring.yaml", help="Scoring configuration YAML")
    return parser


def _run_demo(input_path: Path, output_dir: Path, config_path: Path) -> int:
    df = pd.read_csv(input_path)
    config = load_scoring_config(config_path)
    results = process_dataframe(df, config, MockCRMAdapter())

    output_dir.mkdir(parents=True, exist_ok=True)
    processed_path = output_dir / "processed_prospects.json"
    summary_path = output_dir / "summary.json"

    processed_path.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    tier_counts = Counter(item["routing"]["tier"] for item in results)
    summary = {
        "input_rows": int(len(df)),
        "processed_records": len(results),
        "deduplicated_records": int(len(df) - len(results)),
        "tier_counts": dict(sorted(tier_counts.items())),
        "crm_mode": "mock",
        "processed_artifact": str(processed_path),
    }
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"Processed {len(results)} unique prospect records")
    print(f"Artifacts: {processed_path} | {summary_path}")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.command == "demo":
        return _run_demo(Path(args.input), Path(args.output), Path(args.config))
    parser.error(f"unsupported command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
