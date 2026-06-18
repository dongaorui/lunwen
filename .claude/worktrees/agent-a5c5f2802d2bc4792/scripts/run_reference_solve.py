import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tqdm import tqdm

from replenishverifier.solver.code_executor import execute_generated_code
from replenishverifier.utils.io import read_jsonl, write_jsonl


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmark", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--work-dir", default="outputs/reference_rerun")
    parser.add_argument("--timeout", type=int, default=30)
    args = parser.parse_args()

    rows = []
    for sample in tqdm(read_jsonl(args.benchmark), desc="rerun reference"):
        result = execute_generated_code(
            sample["reference_code"],
            run_dir=Path(args.work_dir) / sample["id"],
            candidate_id="reference",
            timeout=args.timeout,
        )
        rows.append({
            "id": sample["id"],
            "problem_type": sample["problem_type"],
            "reference_status": sample["reference_status"],
            "reference_objective": sample["reference_objective"],
            "rerun": result,
        })

    write_jsonl(args.out, rows)
    print(f"Wrote {len(rows)} rows to {args.out}")


if __name__ == "__main__":
    main()
