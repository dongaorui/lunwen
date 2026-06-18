import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from replenishverifier.pipeline.run_candidate_selection import run_candidate_selection


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmark", required=True)
    parser.add_argument("--candidates", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--work-dir", default="outputs/candidate_runs")
    parser.add_argument("--timeout", type=int, default=30)
    args = parser.parse_args()

    rows = run_candidate_selection(
        benchmark_path=args.benchmark,
        candidates_path=args.candidates,
        out_path=args.out,
        work_dir=args.work_dir,
        timeout=args.timeout,
    )
    print(f"Wrote {len(rows)} evaluated candidates to {args.out}")


if __name__ == "__main__":
    main()
