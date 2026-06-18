import argparse
import logging
from pathlib import Path

from tqdm import tqdm

from replenishverifier.llm.code_extractor import extract_code
from replenishverifier.llm.prompt_builder import (
    build_generic_repair_prompt,
    build_repair_chat_messages,
    build_repair_prompt,
)
from replenishverifier.llm.run_generation import generate_one, load_model_and_tokenizer
from replenishverifier.utils.io import read_jsonl, write_jsonl

LOGGER = logging.getLogger("replenishverifier.llm.repair")


DRY_RUN_PLACEHOLDER_CODE = """import os
import pulp


def build_model():
    prob = pulp.LpProblem('dry_run_repair_placeholder', pulp.LpMinimize)
    placeholder = pulp.LpVariable('dry_run_placeholder_variable', lowBound=0)
    prob += placeholder, 'total_cost'
    prob += placeholder >= 0, 'dry_run_placeholder_constraint'
    return prob


if __name__ == '__main__':
    prob = build_model()
    if os.environ.get('OUTPUT_LP_PATH'):
        prob.writeLP(os.environ['OUTPUT_LP_PATH'])
    prob.solve(pulp.PULP_CBC_CMD(msg=False))
    print('STATUS:', pulp.LpStatus[prob.status])
    print('OBJECTIVE:', pulp.value(prob.objective))
"""


def setup_logging():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")


def index_candidates(candidates):
    return {(row.get("problem_id"), row.get("candidate_id")): row for row in candidates}


def render_repair_prompt(tokenizer, sample, repair_row, original_code="", use_chat_template=True, repair_type="structure_aware"):
    messages = build_repair_chat_messages(sample, repair_row, original_code=original_code, repair_type=repair_type)
    if use_chat_template and tokenizer is not None and hasattr(tokenizer, "apply_chat_template"):
        try:
            return tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True,
                enable_thinking=False,
            )
        except TypeError:
            try:
                return tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            except Exception:
                LOGGER.warning("Tokenizer chat template failed; falling back to plain repair prompt.")
        except Exception:
            LOGGER.warning("Tokenizer chat template failed; falling back to plain repair prompt.")
    if repair_type == "generic":
        return build_generic_repair_prompt(sample, repair_row, original_code=original_code)
    return build_repair_prompt(sample, repair_row, original_code=original_code)


def run_repair_generation(
    benchmark_path,
    repair_prompts_path,
    candidates_path,
    out_path,
    model_name_or_path,
    max_repairs=None,
    max_new_tokens=2048,
    temperature=0.2,
    top_p=0.95,
    trust_remote_code=True,
    use_chat_template=True,
    repair_type="structure_aware",
    dry_run=False,
):
    if repair_type not in {"structure_aware", "generic"}:
        raise ValueError("repair_type must be 'structure_aware' or 'generic'")

    benchmark = {row["id"]: row for row in read_jsonl(benchmark_path)}
    repair_rows = read_jsonl(repair_prompts_path)
    if max_repairs is not None:
        repair_rows = repair_rows[:max_repairs]
    if not repair_rows:
        raise ValueError(f"No repair prompt rows found: {repair_prompts_path}")

    candidates = index_candidates(read_jsonl(candidates_path)) if candidates_path else {}
    model = tokenizer = None
    if not dry_run:
        model, tokenizer = load_model_and_tokenizer(model_name_or_path, trust_remote_code=trust_remote_code)
    else:
        LOGGER.info("Dry run enabled: no model will be loaded and no LLM generation will be executed.")

    outputs = []
    for repair_row in tqdm(repair_rows, desc="generate repair candidates"):
        pid = repair_row.get("problem_id")
        cid = repair_row.get("candidate_id")
        sample = benchmark.get(pid)
        if sample is None:
            LOGGER.warning("Skipping repair row with unknown problem_id=%s", pid)
            continue
        original = candidates.get((pid, cid), {})
        original_code = original.get("generated_code", "")
        prompt = render_repair_prompt(
            tokenizer,
            sample,
            repair_row,
            original_code=original_code,
            use_chat_template=use_chat_template,
            repair_type=repair_type,
        )
        prefix = "generic_repair" if repair_type == "generic" else "repair"
        out = {
            "problem_id": pid,
            "candidate_id": f"{prefix}_{cid}",
            "source_candidate_id": cid,
            "method": "generic_llm_repair" if repair_type == "generic" else "llm_repair",
            "repair_type": repair_type,
            "source_repair_type": repair_row.get("repair_type", repair_type),
            "model_name_or_path": str(model_name_or_path),
            "prompt_type": repair_row.get("prompt_type"),
            "generation_config": {
                "repair_type": repair_type,
                "max_new_tokens": max_new_tokens,
                "temperature": temperature,
                "top_p": top_p,
                "use_chat_template": use_chat_template,
                "trust_remote_code": trust_remote_code,
            },
            "prompt": prompt,
            "generated_text": "",
            "generated_code": "",
            "dry_run": bool(dry_run),
            "error": None,
        }
        if dry_run:
            out["generated_text"] = "```python\n" + DRY_RUN_PLACEHOLDER_CODE + "```"
            out["generated_code"] = DRY_RUN_PLACEHOLDER_CODE
            outputs.append(out)
            continue
        try:
            generated_text = generate_one(
                model,
                tokenizer,
                prompt,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                top_p=top_p,
            )
            out["generated_text"] = generated_text
            out["generated_code"] = extract_code(generated_text)
        except Exception as exc:
            LOGGER.exception("Repair generation failed for %s/%s", pid, cid)
            out["error"] = repr(exc)
        outputs.append(out)

    write_jsonl(out_path, outputs)
    LOGGER.info("Wrote %d repaired candidates to %s", len(outputs), out_path)
    return outputs


def main():
    parser = argparse.ArgumentParser(description="Generate second-round LLM repair candidates from ReplenishVerifier repair prompts.")
    parser.add_argument("--benchmark", required=True, help="Benchmark JSONL path.")
    parser.add_argument("--repair_prompts", required=True, help="repair_prompts.jsonl produced by run_all_methods.")
    parser.add_argument("--candidates", required=True, help="Original candidate JSONL path.")
    parser.add_argument("--out", required=True, help="Output repaired candidate JSONL path.")
    parser.add_argument("--model", required=True, help="Local path or Hugging Face model name. Not loaded when --dry_run is set.")
    parser.add_argument("--max_repairs", type=int, default=None)
    parser.add_argument("--max_new_tokens", type=int, default=2048)
    parser.add_argument("--temperature", type=float, default=0.2)
    parser.add_argument("--top_p", type=float, default=0.95)
    parser.add_argument("--trust_remote_code", action="store_true", default=True)
    parser.add_argument("--no_trust_remote_code", action="store_false", dest="trust_remote_code")
    parser.add_argument("--no_chat_template", action="store_false", dest="use_chat_template")
    parser.add_argument("--repair_type", choices=["structure_aware", "generic"], default="structure_aware")
    parser.add_argument("--dry_run", action="store_true", help="Render prompts and placeholder candidate code without loading or calling an LLM.")
    args = parser.parse_args()

    setup_logging()
    run_repair_generation(
        benchmark_path=args.benchmark,
        repair_prompts_path=args.repair_prompts,
        candidates_path=args.candidates,
        out_path=args.out,
        model_name_or_path=args.model,
        max_repairs=args.max_repairs,
        max_new_tokens=args.max_new_tokens,
        temperature=args.temperature,
        top_p=args.top_p,
        trust_remote_code=args.trust_remote_code,
        use_chat_template=args.use_chat_template,
        repair_type=args.repair_type,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
