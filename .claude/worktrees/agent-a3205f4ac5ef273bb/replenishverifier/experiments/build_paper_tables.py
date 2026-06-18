import argparse
import csv
import logging
from pathlib import Path

from replenishverifier.experiments.evaluation import save_markdown_table
from replenishverifier.utils.io import read_jsonl, write_jsonl

LOGGER = logging.getLogger("replenishverifier.tables")


def read_summary(path):
    rows = read_jsonl(path)
    if rows:
        return rows
    csv_path = Path(path).with_suffix(".csv")
    if csv_path.exists():
        with csv_path.open("r", encoding="utf-8") as f:
            return list(csv.DictReader(f))
    return []


def write_csv(path, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return

    fieldnames = []
    seen = set()
    for row in rows:
        for key in row.keys():
            if key not in seen:
                seen.add(key)
                fieldnames.append(key)

    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def emit_table(out_dir, name, rows, title):
    out_dir = Path(out_dir)
    write_jsonl(out_dir / f"{name}.jsonl", rows)
    write_csv(out_dir / f"{name}.csv", rows)
    save_markdown_table(out_dir / f"{name}.md", rows, title=title)


def build_paper_tables(exp_dir, out_dir):
    exp_dir = Path(exp_dir)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    tables = {
        "table1_benchmark": (exp_dir / "benchmark_summary.jsonl", "Table 1: Benchmark statistics"),
        "table2_main": (exp_dir / "main_results.jsonl", "Table 2: Main results"),
        "table3_strong_baselines": (exp_dir / "main_results.jsonl", "Table 3: Strong baseline comparison"),
        "table4_ablation": (exp_dir / "ablation_results.jsonl", "Table 4: Ablation study"),
        "table5_low_resource": (exp_dir / "low_resource_results.jsonl", "Table 5: Low-resource K analysis"),
        "table6_difficulty": (exp_dir / "difficulty_results.jsonl", "Table 6: Difficulty-wise results"),
        "table7_error_types": (exp_dir / "error_type_summary.jsonl", "Table 7: Error type analysis"),
        "table8_case_studies": (exp_dir / "case_studies.jsonl", "Table 8: Case studies"),
    }

    for name, (src, title) in tables.items():
        rows = read_summary(src)
        if not rows:
            LOGGER.warning("No rows found for %s from %s", name, src)
        emit_table(out_dir, name, rows, title=title)
        LOGGER.info("Wrote %s to %s", name, out_dir)


def main():
    parser = argparse.ArgumentParser(description="Build paper-style Markdown tables from experiment outputs.")
    parser.add_argument("--exp_dir", required=True, help="Experiment output directory produced by run_all_methods.")
    parser.add_argument("--out_dir", default="runs/paper_tables", help="Paper table output directory.")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
    build_paper_tables(args.exp_dir, args.out_dir)


if __name__ == "__main__":
    main()
