import argparse
import logging
import random
import time
from pathlib import Path

from tqdm import tqdm

from replenishverifier.experiments.baselines import code_output_format_valid
from replenishverifier.llm.code_extractor import extract_code
from replenishverifier.llm.prompt_builder import build_chat_messages, build_prompt
from replenishverifier.pipeline.quality_signals import compute_static_validation
from replenishverifier.utils.io import read_jsonl, write_jsonl

LOGGER = logging.getLogger("replenishverifier.llm")


REPRODUCIBILITY_NOTE = (
    "Seed improves reproducibility, but exact determinism is not guaranteed across GPU sampling, "
    "Transformers versions, CUDA kernels, hardware, and model backends."
)


def setup_logging():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")


def set_generation_seed(seed):
    if seed is None:
        return
    random.seed(seed)
    try:
        import numpy as np
        np.random.seed(seed)
    except Exception:
        pass
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except Exception:
        pass


def load_model_and_tokenizer(model_name_or_path, trust_remote_code=True, dtype="auto"):
    try:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
    except Exception as exc:
        raise RuntimeError(
            "LLM generation requires torch and transformers. Install them with: "
            "python -m pip install torch transformers accelerate"
        ) from exc

    cuda_available = torch.cuda.is_available()
    device_map = "auto" if cuda_available else None
    LOGGER.info("CUDA available: %s", cuda_available)
    LOGGER.info("Loading tokenizer: %s", model_name_or_path)
    tokenizer = AutoTokenizer.from_pretrained(model_name_or_path, trust_remote_code=trust_remote_code)
    if tokenizer.pad_token is None and tokenizer.eos_token is not None:
        tokenizer.pad_token = tokenizer.eos_token

    LOGGER.info("Loading model: %s", model_name_or_path)
    model = AutoModelForCausalLM.from_pretrained(
        model_name_or_path,
        trust_remote_code=trust_remote_code,
        torch_dtype=dtype,
        device_map=device_map,
    )
    if not cuda_available:
        model.to("cpu")
    model.eval()
    return model, tokenizer


def render_prompt(tokenizer, sample, use_chat_template=True, prompt_type="hidden_verifier"):
    messages = build_chat_messages(sample, prompt_type=prompt_type)
    if use_chat_template and hasattr(tokenizer, "apply_chat_template"):
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
                LOGGER.warning("Tokenizer chat template failed; falling back to plain prompt.")
        except Exception:
            LOGGER.warning("Tokenizer chat template failed; falling back to plain prompt.")
    return build_prompt(sample, prompt_type=prompt_type)


def generate_one(model, tokenizer, prompt, max_new_tokens=2048, temperature=0.2, top_p=0.95):
    import torch

    inputs = tokenizer(prompt, return_tensors="pt")
    device = next(model.parameters()).device
    inputs = {k: v.to(device) for k, v in inputs.items()}
    do_sample = temperature is not None and temperature > 0
    with torch.no_grad():
        output = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=do_sample,
            temperature=temperature if do_sample else None,
            top_p=top_p if do_sample else None,
            pad_token_id=tokenizer.pad_token_id or tokenizer.eos_token_id,
            eos_token_id=tokenizer.eos_token_id,
        )
    generated_ids = output[0][inputs["input_ids"].shape[-1]:]
    return tokenizer.decode(generated_ids, skip_special_tokens=True)


def _attempt_metadata(attempt_index, raw_generated_text, generated_code, static_validation, accepted, error=None):
    return {
        "attempt_index": attempt_index,
        "raw_contains_think": "<think" in (raw_generated_text or "").lower(),
        "extracted_code_chars": len(generated_code or ""),
        "code_output_format_valid": code_output_format_valid(generated_code),
        "static_validation_score": float(static_validation.get("static_validation_score", 0.0)),
        "static_validation_errors": list(static_validation.get("static_validation_errors", [])),
        "accepted": bool(accepted),
        "error": error,
    }


def _should_accept_generation(raw_generated_text, generated_code, static_validation, require_static_valid_code=False):
    if "<think" in (raw_generated_text or "").lower():
        return False
    if not code_output_format_valid(generated_code):
        return False
    if require_static_valid_code and static_validation.get("static_validation_errors"):
        return False
    return True


def run_generation(
    benchmark_path,
    out_path,
    model_name_or_path,
    k=4,
    max_samples=None,
    max_new_tokens=2048,
    temperature=0.2,
    top_p=0.95,
    trust_remote_code=True,
    use_chat_template=True,
    prompt_type="hidden_verifier",
    seed=None,
    max_generation_attempts_per_candidate=1,
    require_static_valid_code=False,
    retry_on_invalid_code=False,
    model_label=None,
):
    max_generation_attempts_per_candidate = max(1, int(max_generation_attempts_per_candidate or 1))
    benchmark = read_jsonl(benchmark_path)
    if max_samples is not None:
        benchmark = benchmark[:max_samples]
    if not benchmark:
        raise ValueError(f"No benchmark samples found: {benchmark_path}")

    set_generation_seed(seed)
    model, tokenizer = load_model_and_tokenizer(model_name_or_path, trust_remote_code=trust_remote_code)
    rows = []
    generation_config = {
        "prompt_type": prompt_type,
        "seed": seed,
        "max_new_tokens": max_new_tokens,
        "temperature": temperature,
        "top_p": top_p,
        "use_chat_template": use_chat_template,
        "trust_remote_code": trust_remote_code,
        "max_generation_attempts_per_candidate": max_generation_attempts_per_candidate,
        "require_static_valid_code": require_static_valid_code,
        "retry_on_invalid_code": retry_on_invalid_code,
        "model": str(model_name_or_path),
        "model_label": model_label,
    }
    for sample in tqdm(benchmark, desc="generate candidates"):
        prompt = render_prompt(tokenizer, sample, use_chat_template=use_chat_template, prompt_type=prompt_type)
        for idx in range(k):
            candidate_prefix = str(model_label) if model_label else Path(str(model_name_or_path)).name
            candidate_id = f"{candidate_prefix}_k{idx}"
            row = {
                "problem_id": sample["id"],
                "candidate_id": candidate_id,
                "method": "llm_generation",
                "model": str(model_name_or_path),
                "model_label": model_label,
                "model_name_or_path": str(model_name_or_path),
                "prompt_type": prompt_type,
                "prompt": prompt,
                "seed": seed,
                "generation_config": dict(generation_config),
                "reproducibility_note": REPRODUCIBILITY_NOTE,
                "raw_generated_text": "",
                "generated_text": "",
                "generated_code": "",
                "code_output_format_valid": False,
                "generation_time_sec": 0.0,
                "error": None,
            }
            attempts = []
            max_attempts = max_generation_attempts_per_candidate if retry_on_invalid_code else 1
            for attempt_index in range(1, max_attempts + 1):
                raw_generated_text = ""
                generated_code = ""
                try:
                    attempt_start = time.perf_counter()
                    raw_generated_text = generate_one(
                        model,
                        tokenizer,
                        prompt,
                        max_new_tokens=max_new_tokens,
                        temperature=temperature,
                        top_p=top_p,
                    )
                    generation_time_sec = time.perf_counter() - attempt_start
                    generated_code = extract_code(raw_generated_text)
                    static_validation = compute_static_validation(generated_code, problem_type=sample.get("problem_type"))
                    accepted = _should_accept_generation(
                        raw_generated_text,
                        generated_code,
                        static_validation,
                        require_static_valid_code=require_static_valid_code,
                    )
                    attempts.append(
                        _attempt_metadata(attempt_index, raw_generated_text, generated_code, static_validation, accepted)
                    )
                    row["raw_generated_text"] = raw_generated_text
                    row["generated_text"] = generated_code
                    row["generated_code"] = generated_code
                    row["generation_time_sec"] = float(generation_time_sec)
                    row["code_output_format_valid"] = code_output_format_valid(generated_code)
                    row["static_validation"] = static_validation
                    row.update(static_validation)
                    if accepted:
                        break
                except Exception as exc:
                    LOGGER.exception("Generation failed for %s candidate %d attempt %d", sample["id"], idx, attempt_index)
                    static_validation = compute_static_validation(generated_code, problem_type=sample.get("problem_type"))
                    attempts.append(
                        _attempt_metadata(
                            attempt_index,
                            raw_generated_text,
                            generated_code,
                            static_validation,
                            False,
                            error=repr(exc),
                        )
                    )
                    row["error"] = repr(exc)
            row["attempts"] = attempts
            row["attempt_count"] = len(attempts)
            if "static_validation" not in row:
                static_validation = compute_static_validation(row.get("generated_code", ""), problem_type=sample.get("problem_type"))
                row["static_validation"] = static_validation
                row.update(static_validation)
            rows.append(row)

    write_jsonl(out_path, rows)
    LOGGER.info("Wrote %d candidates to %s", len(rows), out_path)
    return rows


def main():
    parser = argparse.ArgumentParser(description="Generate LLM candidates for ReplenishVerifier benchmark problems.")
    parser.add_argument("--benchmark", required=True, help="Benchmark JSONL path.")
    parser.add_argument("--out", required=True, help="Output candidate JSONL path.")
    parser.add_argument("--model", required=True, help="Local path or Hugging Face model name.")
    parser.add_argument("--model_label", default=None, help="Optional stable label used in candidate_id and candidate metadata.")
    parser.add_argument("--k", type=int, default=4, help="Candidates per problem.")
    parser.add_argument("--max_samples", type=int, default=None, help="Optional sample cap.")
    parser.add_argument("--max_new_tokens", type=int, default=2048)
    parser.add_argument("--temperature", type=float, default=0.2)
    parser.add_argument("--top_p", type=float, default=0.95)
    parser.add_argument("--trust_remote_code", action="store_true", default=True)
    parser.add_argument("--no_trust_remote_code", action="store_false", dest="trust_remote_code")
    parser.add_argument("--no_chat_template", action="store_false", dest="use_chat_template")
    parser.add_argument("--prompt_type", choices=["hidden_verifier", "plain", "structured"], default="hidden_verifier")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--max_generation_attempts_per_candidate", type=int, default=1)
    parser.add_argument("--require_static_valid_code", action="store_true", default=False)
    parser.add_argument("--retry_on_invalid_code", action="store_true", default=False)
    args = parser.parse_args()

    setup_logging()
    run_generation(
        benchmark_path=args.benchmark,
        out_path=args.out,
        model_name_or_path=args.model,
        k=args.k,
        max_samples=args.max_samples,
        max_new_tokens=args.max_new_tokens,
        temperature=args.temperature,
        top_p=args.top_p,
        trust_remote_code=args.trust_remote_code,
        use_chat_template=args.use_chat_template,
        prompt_type=args.prompt_type,
        seed=args.seed,
        max_generation_attempts_per_candidate=args.max_generation_attempts_per_candidate,
        require_static_valid_code=args.require_static_valid_code,
        retry_on_invalid_code=args.retry_on_invalid_code,
        model_label=args.model_label,
    )


if __name__ == "__main__":
    main()
