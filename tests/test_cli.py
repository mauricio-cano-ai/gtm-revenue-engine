import json
from pathlib import Path

import pandas as pd

from gtm_engine.cli import main


def test_demo_cli_writes_processed_artifacts(tmp_path: Path):
    input_path = tmp_path / "prospects.csv"
    pd.DataFrame([
        {
            "company_name": "Acme",
            "domain": "acme.com",
            "source": "clay",
            "firmographic_fit": 1,
            "technographic_fit": 1,
            "intent_signal": 1,
        }
    ]).to_csv(input_path, index=False)

    output_dir = tmp_path / "artifacts"
    exit_code = main([
        "demo",
        "--input", str(input_path),
        "--output", str(output_dir),
        "--config", "config/scoring.yaml",
    ])

    assert exit_code == 0
    processed = json.loads((output_dir / "processed_prospects.json").read_text(encoding="utf-8"))
    summary = json.loads((output_dir / "summary.json").read_text(encoding="utf-8"))
    assert processed[0]["prospect"]["domain"] == "acme.com"
    assert summary["processed_records"] == 1
    assert summary["crm_mode"] == "mock"
