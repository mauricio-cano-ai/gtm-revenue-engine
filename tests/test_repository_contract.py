from pathlib import Path


REQUIRED = [
    Path("README.md"),
    Path("docs/architecture.md"),
    Path("docs/clay-setup.md"),
    Path("docs/crm-mapping.md"),
    Path("docs/failure-modes.md"),
    Path("docs/handoff.md"),
    Path("docs/runbook.md"),
    Path("docs/loom-walkthrough.md"),
    Path("scripts/demo.ps1"),
    Path("config/scoring.yaml"),
    Path("data/sample_prospects.csv"),
    Path("n8n/gtm-revenue-engine.workflow.json"),
]


def test_required_repository_artifacts_exist():
    missing = [str(path) for path in REQUIRED if not path.exists()]
    assert not missing, f"missing artifacts: {missing}"


def test_public_docs_cover_clay_and_failure_modes():
    clay = Path("docs/clay-setup.md").read_text(encoding="utf-8").lower()
    for phrase in ["waterfall", "claygent", "formula", "http api", "freshness", "conditional"]:
        assert phrase in clay

    failures = Path("docs/failure-modes.md").read_text(encoding="utf-8").lower()
    for phrase in [
        "duplicate webhook",
        "partial enrichment",
        "stale signal",
        "missing domain",
        "conflicting company",
        "http 429",
        "5xx",
        "invalid structured output",
        "crm upsert failure",
        "timeout",
        "replay",
    ]:
        assert phrase in failures


def test_public_artifacts_do_not_leak_secrets_or_employer_specific_framing():
    paths = [Path("README.md"), *Path("docs").glob("*.md"), Path("scripts/demo.ps1"), Path("n8n/gtm-revenue-engine.workflow.json")]
    combined = "\n".join(path.read_text(encoding="utf-8") for path in paths).lower()
    assert "atqleads" not in combined
    for secret_pattern in ["pat-na1-", "sk-proj-", "sk-ant-", "ghp_"]:
        assert secret_pattern not in combined


def test_demo_script_runs_tests_and_cli():
    script = Path("scripts/demo.ps1").read_text(encoding="utf-8").lower()
    assert "pytest" in script
    assert "gtm_engine.cli" in script
    assert "sample_prospects.csv" in script
