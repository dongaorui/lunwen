from collections import defaultdict
from pathlib import Path

from tqdm import tqdm

from replenishverifier.pipeline.scoring import compute_score
from replenishverifier.solver.code_executor import execute_generated_code
from replenishverifier.utils.io import read_jsonl, write_jsonl
from replenishverifier.verifier.feedback import generate_feedback
from replenishverifier.verifier.lp_parser import parse_lp_file
from replenishverifier.verifier.structure_rules import check_structures


def run_candidate_selection(benchmark_path, candidates_path, out_path, work_dir, timeout=30):
    benchmark = {row["id"]: row for row in read_jsonl(benchmark_path)}
    candidates = read_jsonl(candidates_path)
    work_dir = Path(work_dir)

    evaluated = []
    by_problem = defaultdict(list)

    for cand in tqdm(candidates, desc="evaluate candidates"):
        pid = cand["problem_id"]
        ref = benchmark.get(pid)
        if ref is None:
            row = {**cand, "error": f"Unknown problem_id: {pid}", "score": 0.0}
            evaluated.append(row)
            continue

        cid = cand.get("candidate_id", "candidate")
        run_dir = work_dir / pid / cid
        exec_result = execute_generated_code(
            cand.get("generated_code", ""),
            run_dir=run_dir,
            candidate_id=cid,
            timeout=timeout,
        )

        structure_dict = None
        feedback = "候选代码没有成功导出 LP，因此无法执行结构验证。"

        if exec_result.get("lp_path"):
            try:
                parsed = parse_lp_file(exec_result["lp_path"])
                structure_result = check_structures(parsed, ref["expected_structures"], problem_type=ref.get("problem_type"))
                structure_dict = structure_result.to_dict()
                feedback = generate_feedback(structure_result)
            except Exception as exc:
                structure_dict = {
                    "structure_score": 0.0,
                    "missing": [],
                    "messages": [f"LP parse or structure check error: {exc}"],
                }
                feedback = f"LP 解析或结构验证失败：{exc}"

        score_parts = compute_score(
            exec_result,
            structure_dict,
            reference_objective=ref.get("reference_objective"),
        )

        row = {
            **cand,
            "execution": exec_result,
            "structure_verification": structure_dict,
            "feedback": feedback,
            **score_parts,
            "reference_objective": ref.get("reference_objective"),
            "reference_status": ref.get("reference_status"),
        }
        evaluated.append(row)
        by_problem[pid].append(row)

    selected_keys = set()
    for pid, rows in by_problem.items():
        best = max(rows, key=lambda item: item.get("score", 0.0))
        selected_keys.add((best["problem_id"], best["candidate_id"]))

    output_rows = []
    for row in evaluated:
        row = dict(row)
        row["selected"] = (row.get("problem_id"), row.get("candidate_id")) in selected_keys
        output_rows.append(row)

    write_jsonl(out_path, output_rows)
    return output_rows
