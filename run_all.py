"""Re-run the whole study from the repository root:  python run_all.py
Download (cached) -> simulation -> SQL and tests -> statistics -> budget allocation -> key numbers -> planner -> PDF
-> glance check -> notebook. Stops at the first failing step.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PDF = "site/report/alan_freelancer_growth_case_study.pdf"
STEPS = [
    ["src/download_public.py"], ["src/simulate_growth.py"], ["src/run_sql.py"], ["src/stats.py"], ["src/allocate_budget.py"],
    ["src/key_numbers.py"], ["src/compare_truth.py"], ["src/build_dashboard.py"], ["src/build_pdf.py"],
    ["tools/glance_check.py", PDF],
    ["-m", "jupyter", "nbconvert", "--to", "notebook", "--execute", "--inplace", "notebooks/freelancer_growth.ipynb"],
]


def main() -> int:
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    for step in STEPS:
        print(f"\n=== {' '.join(step)}", flush=True)
        r = subprocess.run([sys.executable, *step], cwd=ROOT, env=env)
        if r.returncode:
            print(f"FAILED: {' '.join(step)}")
            return r.returncode
    print("\nall steps passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
