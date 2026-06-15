import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from replenishverifier.benchmark.generator import generate_benchmark


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--lp-dir", default=None)
    parser.add_argument("--n-per-type", type=int, default=20)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--unlabeled", action="store_true", help="Write prompt-only rows without reference labels.")
    parser.add_argument("--include-parameters", action="store_true", help="Include parameters in unlabeled prompt rows.")
    args = parser.parse_args()
    if not args.unlabeled and args.lp_dir is None:
        parser.error("--lp-dir is required unless --unlabeled is set")

    rows = generate_benchmark(
        output=args.output,
        lp_dir=args.lp_dir,
        n_per_type=args.n_per_type,
        seed=args.seed,
        include_labels=not args.unlabeled,
        include_parameters=True if not args.unlabeled else args.include_parameters,
    )
    print(f"Wrote {len(rows)} samples to {args.output}")


if __name__ == "__main__":
    main()
