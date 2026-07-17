import json
import subprocess
import sys
from pathlib import Path


def test_synthetic_pipeline_smoke(tmp_path):
    output_dir = tmp_path / "outputs"
    cmd = [
        sys.executable,
        "scripts/run_synthetic_aid_lab.py",
        "--regions",
        "12",
        "--warehouses",
        "3",
        "--seed",
        "11",
        "--output-dir",
        str(output_dir),
    ]
    subprocess.run(cmd, check=True)
    summary_path = output_dir / "results" / "synthetic_aid_summary.json"
    assert summary_path.exists()
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert summary["region_count"] == 12
    assert summary["total_allocated_units"] > 0
    assert summary["audit_log"]["valid"] is True
