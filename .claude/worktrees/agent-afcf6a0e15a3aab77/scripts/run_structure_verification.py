import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tqdm import tqdm

from replenishverifier.utils.io import read_jsonl, write_jsonl
from replenishverifier.verifier.feedback import generate_feedback
from replenishverifier.verifier.lp_parser import parse_lp_file
from replenishverifier.verifier.structure_rules import check_structures


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmark", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    rows = []
    for sample in tqdm(read_jsonl(args.benchmark), desc="verify structure"):
        parsed = parse_lp_file(sample["reference_lp_path"])
        result = check_structures(parsed, sample["expected_structures"], problem_type=sample.get("problem_type"))
        rows.append({
            "id": sample["id"],
            "problem_type": sample["problem_type"],
            "difficulty": sample["difficulty"],
            "reference_lp_path": sample["reference_lp_path"],
            "structure_verification": result.to_dict(),
            "feedback": generate_feedback(result),
            "structure_score": result.structure_score,
        })

    write_jsonl(args.out, rows)
    print(f"Wrote {len(rows)} rows to {args.out}")


if __name__ == "__main__":
    main()
