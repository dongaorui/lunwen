import argparse
import random
import re
from pathlib import Path

from replenishverifier.utils.io import read_jsonl, write_jsonl


SEMANTIC_MAP = {
    "Q": "order_qty",
    "I": "ending_inventory",
    "B": "backlog_qty",
    "Y": "setup_trigger",
}

ADVERSARIAL_MAP = {
    "Q": "xorder",
    "I": "state_stock",
    "B": "unmet_qty",
    "Y": "activate",
}

DESCRIPTIVE_TO_ANONYMOUS_MAP = {
    "order_qty": "x_order",
    "order_quantity": "x_order",
    "ending_inventory": "x_inventory",
    "inventory": "x_inventory",
    "stock": "x_inventory",
    "backlog_qty": "x_shortage",
    "shortage": "x_shortage",
    "setup_trigger": "x_binary",
    "order_flag": "x_binary",
}


def _random_name(prefix, rng):
    alphabet = "abcdefghijklmnopqrstuvwxyz"
    return f"{prefix}_{''.join(rng.choice(alphabet) for _ in range(6))}"


def _replacement_map(mode, seed=0):
    rng = random.Random(seed)
    if mode == "semantic":
        return dict(SEMANTIC_MAP)
    if mode == "adversarial":
        return dict(ADVERSARIAL_MAP)
    if mode == "random":
        return {key: _random_name("v", rng) for key in SEMANTIC_MAP}
    if mode == "descriptive_to_anonymous":
        return dict(DESCRIPTIVE_TO_ANONYMOUS_MAP)
    raise ValueError("mode must be random, descriptive_to_anonymous, semantic, or adversarial")


def rename_code(code, mode="random", seed=0):
    """Lightweight textual renamer for robustness experiments.

    This deliberately avoids complex AST rewriting. It is intended to perturb the
    common PuLP variable-family names used in generated candidates. Review a sample
    before running large evaluations.
    """
    mapping = _replacement_map(mode, seed=seed)
    renamed = code or ""
    for old, new in mapping.items():
        renamed = re.sub(rf"(?<![A-Za-z0-9_]){re.escape(old)}(?![A-Za-z0-9_])", new, renamed)
        renamed = re.sub(rf"(['\"]){re.escape(old)}(['\"])", rf"\1{new}\2", renamed)
    return renamed, mapping


def rename_candidates(candidates_path, out_path, mode="random", seed=0):
    rows = read_jsonl(candidates_path)
    outputs = []
    for idx, row in enumerate(rows):
        renamed_code, mapping = rename_code(row.get("generated_code", ""), mode=mode, seed=seed + idx)
        out = dict(row)
        out["candidate_id"] = f"{row.get('candidate_id', 'candidate')}_renamed_{mode}"
        out["source_candidate_id"] = row.get("candidate_id")
        out["generated_code"] = renamed_code
        out["renaming_mode"] = mode
        out["renaming_map"] = mapping
        out["renaming_warning"] = "lightweight text-level perturbation; not AST-safe; manually inspect samples before formal experiments"
        out["method"] = f"{row.get('method', 'candidate')}_renamed_{mode}"
        outputs.append(out)
    write_jsonl(out_path, outputs)
    return outputs


def main():
    parser = argparse.ArgumentParser(description="Create renamed candidate JSONL files for naming-variation robustness experiments.")
    parser.add_argument("--candidates", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--mode", choices=["random", "descriptive_to_anonymous", "semantic", "adversarial"], default="random")
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()
    rename_candidates(args.candidates, args.out, mode=args.mode, seed=args.seed)


if __name__ == "__main__":
    main()
