import re
import time
from pathlib import Path

from replenishverifier.experiments.baselines import (
    code_output_format_valid,
    compute_lp_stats,
    compute_objective_consensus_scores,
    compute_optargus_audit,
    generic_repair_feedback,
    optargus_like_audit_score,
    optirepair_like_score,
    or_r1_like_voting_score,
    sirl_like_lp_stats_score,
)
from replenishverifier.experiments.objective_terms import evaluate_objective_terms
from replenishverifier.pipeline.quality_signals import compute_static_validation
from replenishverifier.pipeline.scoring import compute_score, hard_selection_gate
from replenishverifier.solver.code_executor import execute_generated_code
from replenishverifier.verifier.feedback import generate_feedback
from replenishverifier.verifier.lp_parser import parse_lp_file
from replenishverifier.verifier.structure_rules import check_structures


MAIN_METHODS = [
    "Direct",
    "Best-of-K",
    "Solver only",
    "Structure only",
    "Consensus only",
    "ReplenishVerifier-Full",
    "ReplenishVerifier-TypeAware",
    "ReplenishVerifier-TypeAware-Consensus",
]

APPENDIX_METHODS = [
    "Solver-Filter",
    "Solver + Structure",
    "Solver + Consensus",
    "Structure + Consensus",
    "Solver + Structure + Consensus",
    "OR-R1-like Voting",
    "Structure-Grounded Consistency",
    "SIRL-like LP-Stats",
    "OptArgus-like Audit",
    "OptiRepair-like Repair-Prompt",
    "Structure-Only",
    "ReplenishVerifier-Repair",
]

METHODS = MAIN_METHODS + APPENDIX_METHODS


def candidate_sort_key(candidate):
    cid = str(candidate.get("candidate_id", ""))
    return cid


def evaluate_candidate(candidate, reference, work_dir, timeout=30, force_skip_execution=False, allow_feasible_selection=False):
    start = time.perf_counter()
    pid = candidate.get("problem_id")
    cid = candidate.get("candidate_id", "candidate")
    generated_code = candidate.get("generated_code", "")
    static_validation = compute_static_validation(generated_code, problem_type=reference.get("problem_type"))
    parsed = None
    lp_parse_time = None
    structure_check_time = None

    if force_skip_execution:
        execution = {
            "executable": False,
            "status": "NotRun",
            "objective": None,
            "lp_path": None,
            "code_execution_time": None,
            "solver_lp_export_time": None,
            "solver_time": None,
            "error": "Execution skipped by method.",
        }
        structure_dict = None
        feedback = "Execution skipped by method; no structure feedback available."
    else:
        execution = execute_generated_code(
            generated_code,
            run_dir=Path(work_dir) / pid / cid,
            candidate_id=cid,
            timeout=timeout,
        )
        structure_dict = None
        feedback = "LP artifact is unavailable, so structure feedback is unavailable."
        if execution.get("lp_path"):
            try:
                parse_start = time.perf_counter()
                parsed = parse_lp_file(execution["lp_path"])
                lp_parse_time = time.perf_counter() - parse_start
                structure_start = time.perf_counter()
                structure_result = check_structures(parsed, reference["expected_structures"], problem_type=reference.get("problem_type"))
                structure_check_time = time.perf_counter() - structure_start
                structure_dict = structure_result.to_dict()
                feedback = generate_feedback(structure_result)
            except Exception as exc:
                structure_dict = {
                    "expected": reference.get("expected_structures", {}),
                    "detected": {},
                    "passed": {},
                    "missing": [],
                    "extra_detected": [],
                    "structure_score": 0.0,
                    "messages": [f"LP parse or structure check error: {exc}"],
                }
                feedback = f"LP parse or structure check failed: {exc}"

    lp_stats = compute_lp_stats(parsed)
    optargus_audit = compute_optargus_audit(parsed, execution)
    sirl_lp_stats_score = sirl_like_lp_stats_score(execution, lp_stats)
    optargus_audit_score = optargus_like_audit_score(execution, optargus_audit)
    optirepair_repair_score = optirepair_like_score(execution, optargus_audit)
    generic_feedback = generic_repair_feedback(execution, optargus_audit)

    total_runtime = time.perf_counter() - start
    objective_term_result = evaluate_objective_terms(
        {"problem_type": reference.get("problem_type"), "generated_code": generated_code},
        parsed=parsed,
        generated_code=generated_code,
    )
    runtime_fields = {
        "code_execution_time": execution.get("code_execution_time"),
        "solver_lp_export_time": execution.get("solver_lp_export_time"),
        "solver_time": execution.get("solver_time"),
        "lp_parse_time": None if lp_parse_time is None else float(lp_parse_time),
        "structure_check_time": None if structure_check_time is None else float(structure_check_time),
        "total_candidate_evaluation_time": float(total_runtime),
    }
    base = {
        "problem_id": pid,
        "candidate_id": cid,
        "candidate_method": candidate.get("method"),
        "generated_text": candidate.get("generated_text", ""),
        "generated_code": generated_code,
        "prompt_type": candidate.get("prompt_type") or (candidate.get("generation_config") or {}).get("prompt_type"),
        "execution": execution,
        "structure_verification": structure_dict,
        "feedback": feedback,
        "generic_repair_feedback": generic_feedback,
        "lp_stats": lp_stats,
        "optargus_audit": optargus_audit,
        "sirl_like_lp_stats_score": sirl_lp_stats_score,
        "optargus_like_audit_score": optargus_audit_score,
        "optirepair_like_repair_score": optirepair_repair_score,
        "runtime": runtime_fields,
        "code_execution_time": runtime_fields["code_execution_time"],
        "solver_lp_export_time": runtime_fields["solver_lp_export_time"],
        "solver_time": runtime_fields["solver_time"],
        "lp_parse_time": runtime_fields["lp_parse_time"],
        "structure_check_time": runtime_fields["structure_check_time"],
        "total_candidate_evaluation_time": runtime_fields["total_candidate_evaluation_time"],
        "runtime_sec": runtime_fields["total_candidate_evaluation_time"],
        "problem_type": reference.get("problem_type"),
        "difficulty": reference.get("difficulty"),
        "reference_objective": reference.get("reference_objective"),
        "reference_status": reference.get("reference_status"),
        "objective_term_verification": objective_term_result,
        "objective_term_coverage": objective_term_result.get("objective_term_coverage"),
        "objective_term_surface_coverage": objective_term_result.get("objective_term_surface_coverage"),
        "objective_term_lp_coefficient_coverage": objective_term_result.get("objective_term_lp_coefficient_coverage"),
        "expected_objective_terms": objective_term_result.get("expected_objective_terms", []),
        "detected_objective_terms": objective_term_result.get("detected_objective_terms", []),
        "missing_objective_terms": objective_term_result.get("missing_objective_terms", []),
        "surface_detected_objective_terms": objective_term_result.get("surface_detected_objective_terms", []),
        "surface_missing_objective_terms": objective_term_result.get("surface_missing_objective_terms", []),
        "lp_detected_objective_terms": objective_term_result.get("lp_detected_objective_terms", []),
        "lp_missing_objective_terms": objective_term_result.get("lp_missing_objective_terms", []),
        "code_output_format_valid": code_output_format_valid(generated_code),
        "static_validation": static_validation,
        **static_validation,
        "objective_consensus_score": 0.0,
        "or_r1_like_voting_score": 0.0,
    }
    base.update(compute_score(execution, structure_dict, reference.get("reference_objective"), mode="full", allow_feasible_selection=allow_feasible_selection))
    solver_score = compute_score(execution, structure_dict, reference.get("reference_objective"), mode="solver_only", allow_feasible_selection=allow_feasible_selection)
    structure_score = compute_score(execution, structure_dict, reference.get("reference_objective"), mode="structure_only", allow_feasible_selection=allow_feasible_selection)
    base["solver_only_score"] = solver_score["score"]
    base["raw_solver_only_score"] = solver_score.get("raw_inference_score", solver_score["score"])
    base["structure_only_score"] = structure_score["score"]
    base["raw_structure_only_score"] = structure_score.get("raw_inference_score", structure_score["score"])
    base["formal_selection_score"] = base["score"]
    return base


def annotate_consensus_scores(evaluated):
    """Attach ground-truth-free objective consensus and OR-R1-like scores."""
    for rows in evaluated.values():
        consensus_scores = compute_objective_consensus_scores(rows)
        for row, consensus_score in zip(rows, consensus_scores):
            row["objective_consensus_score"] = float(consensus_score)
            row["or_r1_like_voting_score"] = or_r1_like_voting_score(
                row.get("execution") or {},
                consensus_score=consensus_score,
                code_format_valid=row.get("code_output_format_valid", False),
            )
    return evaluated


def apply_objective_consensus_to_full_scores(evaluated, weight=0.10, allow_feasible_selection=False):
    """Optionally blend objective-consensus into ReplenishVerifier-Full selection.

    Consensus is computed only from candidate objectives within the same problem,
    never from the reference objective.
    """
    for rows in evaluated.values():
        for row in rows:
            base_score = float(row.get("raw_inference_score", row.get("score", 0.0)) or 0.0)
            consensus = float(row.get("objective_consensus_score", 0.0) or 0.0)
            raw_score = float((1.0 - weight) * base_score + weight * consensus)
            gated_score = hard_selection_gate(row.get("execution") or {}, raw_score, allow_feasible_selection=allow_feasible_selection)
            row["base_replenishverifier_score"] = base_score
            row["raw_inference_score"] = raw_score
            row["score"] = gated_score
            row["selection_score"] = gated_score
            row["formal_selection_score"] = gated_score
            row["selection_policy"] = (
                "Hard Selection Gate over executable + optimal + LP structure + semantic consistency + "
                "candidate objective consensus; no reference objective"
            )
    return evaluated


def evaluate_all_candidates(benchmark, candidates_by_problem, work_dir, timeout=30, max_k=None, use_objective_consensus=False, allow_feasible_selection=False):
    evaluated = {}
    for pid, reference in benchmark.items():
        candidates = sorted(candidates_by_problem.get(pid, []), key=candidate_sort_key)
        if max_k is not None:
            candidates = candidates[:max_k]
        rows = []
        for candidate in candidates:
            rows.append(evaluate_candidate(candidate, reference, work_dir=work_dir, timeout=timeout, allow_feasible_selection=allow_feasible_selection))
        evaluated[pid] = rows
    annotate_consensus_scores(evaluated)
    if use_objective_consensus:
        apply_objective_consensus_to_full_scores(evaluated, allow_feasible_selection=allow_feasible_selection)
    return evaluated


def _first_or_empty(pid, reference):
    return {
        "problem_id": pid,
        "candidate_id": "missing_candidate",
        "candidate_method": None,
        "execution": {"executable": False, "status": "Missing", "objective": None, "lp_path": None, "error": "No candidate for this problem."},
        "structure_verification": None,
        "feedback": "No candidate available.",
        "runtime_sec": 0.0,
        "problem_type": reference.get("problem_type"),
        "difficulty": reference.get("difficulty"),
        "reference_objective": reference.get("reference_objective"),
        "reference_status": reference.get("reference_status"),
        "score": 0.0,
        "executable_score": 0.0,
        "feasible_score": 0.0,
        "optimal_score": 0.0,
        "objective_score": 0.0,
        "objective_correct": 0.0,
        "relative_error": None,
        "structure_score": 0.0,
        "semantic_consistency_score": 0.0,
        "solver_only_score": 0.0,
        "structure_only_score": 0.0,
    }


REWARD_ABLATION_METHODS = {
    "Solver only": ("solver",),
    "Structure only": ("structure",),
    "Consensus only": ("consensus",),
    "Solver + Structure": ("solver", "structure"),
    "Solver + Consensus": ("solver", "consensus"),
    "Structure + Consensus": ("structure", "consensus"),
    "Solver + Structure + Consensus": ("solver", "structure", "consensus"),
    "ReplenishVerifier full": ("solver", "structure", "consensus"),
}

STRUCTURE_AWARE_METHODS = {
    "Structure-Only",
    "Structure only",
    "Solver + Structure",
    "Structure + Consensus",
    "Solver + Structure + Consensus",
    "Structure-Grounded Consistency",
    "ReplenishVerifier-TypeAware",
    "ReplenishVerifier-Full",
    "ReplenishVerifier-Repair",
    "ReplenishVerifier full",
}


def _row_problem_type(row):
    return row.get("problem_type") or ((row.get("reference") or {}).get("problem_type"))


def _required_missing_for_row(row):
    structure = row.get("structure_verification") or {}
    missing = set(structure.get("missing") or [])
    required = structure.get("required_structures")
    if required is None:
        expected = structure.get("expected") or {}
        required = [key for key, value in expected.items() if value]
    if required:
        missing &= set(required)
    return missing


def _critical_missing_structures(row):
    missing = _required_missing_for_row(row)
    problem_type = _row_problem_type(row)
    critical = set()
    if "inventory_balance" in missing:
        critical.add("inventory_balance")
    if problem_type == "multi_item_capacity" and "capacity_constraint" in missing:
        critical.add("capacity_constraint")
    if problem_type == "single_item_multi_period_shortage":
        critical.update(missing & {"shortage_variable", "shortage_cost"})
    if problem_type == "fixed_order_cost_big_m":
        critical.update(missing & {"binary_order_variable", "big_m_constraint", "fixed_order_cost"})
    return sorted(critical)


def _critical_structure_penalty(row, method_name):
    if method_name not in STRUCTURE_AWARE_METHODS:
        return {"enabled": False, "passed": True, "missing": [], "multiplier": 1.0}
    critical_missing = _critical_missing_structures(row)
    return {
        "enabled": True,
        "passed": not critical_missing,
        "missing": critical_missing,
        "multiplier": 1.0 if not critical_missing else 0.01,
    }


def _rule_score(row, rule_name):
    structure = row.get("structure_verification") or {}
    for cert in structure.get("certificates") or []:
        if cert.get("rule_name") == rule_name:
            return float(cert.get("score", 0.0) or 0.0)
    missing = set(structure.get("missing") or [])
    required = structure.get("required_structures") or []
    if rule_name in required:
        return 0.0 if rule_name in missing else 1.0
    return 0.0


def _constraint_coverage(row):
    structure = row.get("structure_verification") or {}
    required = structure.get("required_structures") or []
    missing = set(structure.get("missing") or [])
    if not required:
        return float(structure.get("structure_score", row.get("structure_score", 0.0)) or 0.0)
    return float(len([key for key in required if key not in missing]) / max(len(required), 1))


def _repair_feedback_count(row):
    feedback = row.get("feedback") or ""
    if not feedback:
        return 0
    return len([line for line in str(feedback).splitlines() if line.strip()])


def _type_aware_validation(row):
    return row.get("type_aware_static_validation") or ((row.get("static_validation") or {}).get("type_aware_static_validation")) or {}


def _type_aware_errors(row):
    direct = row.get("type_aware_static_validation_errors")
    if direct is not None:
        return list(direct or [])
    nested = row.get("static_validation") or {}
    return list(nested.get("type_aware_static_validation_errors") or [])


def _objective_term_coverage(row):
    value = row.get("objective_term_coverage")
    if value is None:
        value = (row.get("objective_term_verification") or {}).get("objective_term_coverage")
    return float(value or 0.0)


def _type_aware_validation_score(row):
    validation = _type_aware_validation(row)
    return float(validation.get("score", 1.0) if validation else 1.0)


def _type_aware_hard_gate_score(row):
    validation = _type_aware_validation(row)
    return float(validation.get("hard_gate_score", 1.0) if validation else 1.0)


def _type_aware_hard_gate_failures(row):
    validation = _type_aware_validation(row)
    return list(validation.get("hard_gate_failures") or [])


def _type_aware_repair_feedback_count(row):
    missing = set(_type_aware_errors(row))
    missing.update(_critical_missing_structures(row))
    return len(missing)


def type_aware_selection_components(row):
    execution = row.get("execution") or {}
    status = str(execution.get("status") or "")
    executable = 1.0 if execution.get("executable") else 0.0
    solver_optimal = 1.0 if status == "Optimal" else 0.0
    structure_completeness = float(row.get("structure_score", ((row.get("structure_verification") or {}).get("structure_score", 0.0))) or 0.0)
    constraint_coverage = _constraint_coverage(row)
    objective_term_coverage = _objective_term_coverage(row)
    type_aware_score = _type_aware_validation_score(row)
    hard_gate_score = _type_aware_hard_gate_score(row)
    consensus_score = float(row.get("objective_consensus_score", 0.0) or 0.0)
    repair_feedback_count = float(_type_aware_repair_feedback_count(row))
    runtime_sec = float(row.get("runtime_sec", row.get("total_candidate_evaluation_time", 0.0)) or 0.0)
    return {
        "executable": executable,
        "solver_optimal": solver_optimal,
        "structure_completeness": structure_completeness,
        "constraint_coverage": constraint_coverage,
        "objective_term_coverage": objective_term_coverage,
        "type_aware_score": type_aware_score,
        "hard_gate_score": hard_gate_score,
        "consensus_score": consensus_score,
        "repair_feedback_count": repair_feedback_count,
        "runtime_sec": runtime_sec,
    }


def type_aware_selection_score(row):
    c = type_aware_selection_components(row)
    return float(
        1000.0 * c["executable"]
        + 500.0 * c["solver_optimal"]
        + 100.0 * c["structure_completeness"]
        + 80.0 * c["constraint_coverage"]
        + 80.0 * c["objective_term_coverage"]
        + 50.0 * c["hard_gate_score"]
        + 20.0 * c["type_aware_score"]
        + 30.0 * c["consensus_score"]
        - 5.0 * c["repair_feedback_count"]
        - 0.1 * c["runtime_sec"]
    )


def type_aware_consensus_selection_components(row):
    base = type_aware_selection_components(row)
    critical_missing = _critical_missing_structures(row)
    base["critical_missing_count"] = float(len(critical_missing))
    base["critical_structure_pass"] = 1.0 if not critical_missing else 0.0
    base["critical_missing_structures"] = critical_missing
    base["consensus_bucket"] = round(base["consensus_score"] / 0.05) * 0.05
    return base


def type_aware_consensus_selection_score(row):
    c = type_aware_consensus_selection_components(row)
    return float(
        10000.0 * c["executable"]
        + 5000.0 * c["solver_optimal"]
        + 1000.0 * c["consensus_score"]
        + 120.0 * c["structure_completeness"]
        + 90.0 * c["constraint_coverage"]
        + 80.0 * c["objective_term_coverage"]
        + 40.0 * c["hard_gate_score"]
        + 20.0 * c["type_aware_score"]
        - 25.0 * c["critical_missing_count"]
        - 2.0 * c["repair_feedback_count"]
        - 0.1 * c["runtime_sec"]
    )


def _candidate_index(row):
    if row.get("candidate_index") is not None:
        return int(row.get("candidate_index") or 0)
    cid = str(row.get("candidate_id", ""))
    match = re.search(r"(?:^|[_-])k(\d+)(?:\D|$)", cid, flags=re.IGNORECASE)
    if match:
        return int(match.group(1))
    digits = "".join(ch for ch in cid if ch.isdigit())
    return int(digits) if digits else 0


def _runtime_sec(row):
    return float(row.get("runtime_sec", row.get("total_candidate_evaluation_time", 0.0)) or 0.0)


def _static_validation_score(row):
    return float(row.get("static_validation_score", ((row.get("static_validation") or {}).get("static_validation_score", 0.0))) or 0.0)


def _code_validity_score(row):
    return 1.0 if row.get("code_output_format_valid") else 0.0


def _solver_status_score(row, allow_feasible_selection=False):
    execution = row.get("execution") or {}
    status = str(execution.get("status") or "").strip().lower().replace(" ", "_").replace("-", "_")
    if status in {"optimal", "optimum"}:
        return 2.0
    if allow_feasible_selection and status in {"feasible", "integer_feasible", "solution_found"}:
        return 1.0
    return 0.0


def _has_objective_score(row):
    return 1.0 if (row.get("execution") or {}).get("objective") is not None else 0.0


def _critical_structure_pass_score(row):
    return 1.0 if not _critical_missing_structures(row) else 0.0


def lp_artifact_structure_signal(row):
    structure = row.get("structure_verification") or {}
    execution = row.get("execution") or {}
    if not execution.get("lp_path") or not structure:
        return 0.0
    required = structure.get("required_structures") or []
    missing = set(structure.get("missing") or [])
    if required:
        covered = [key for key in required if key not in missing]
        return float(len(covered) / max(len(required), 1))
    return float(structure.get("structure_score", 0.0) or 0.0)


def reward_components(row):
    execution = row.get("execution") or {}
    solver_status = str(execution.get("status") or "")
    rcode = 1.0 if execution.get("executable") else 0.0
    rsolver = 1.0 if solver_status == "Optimal" else 0.0
    rstructure = float(row.get("structure_score", ((row.get("structure_verification") or {}).get("structure_score", 0.0))) or 0.0)
    rlp_structure = lp_artifact_structure_signal(row)
    rconsensus = float(row.get("objective_consensus_score", 0.0) or 0.0)
    return {
        "Rcode": rcode,
        "Rsolver": rsolver,
        "Rstructure": rstructure,
        "Rrequired_structure_coverage": rstructure,
        "Rlp_artifact_structure": rlp_structure,
        "Robjective_consensus": rconsensus,
    }


def structure_grounded_consistency_score(row):
    """Replenishment-specific candidate-only consistency score.

    The score combines code execution, solver status, required replenishment
    structure coverage from the LP artifact, and objective consensus among
    candidates. It never reads the reference objective.
    """
    components = reward_components(row)
    return float(
        0.20 * components["Rcode"]
        + 0.20 * components["Rsolver"]
        + 0.30 * components["Rrequired_structure_coverage"]
        + 0.15 * components["Rlp_artifact_structure"]
        + 0.15 * components["Robjective_consensus"]
    )


def reward_ablation_score(row, method_name):
    if method_name == "Structure-Grounded Consistency":
        return structure_grounded_consistency_score(row)
    components = reward_components(row)
    parts = REWARD_ABLATION_METHODS[method_name]
    score = 0.0
    if "solver" in parts:
        score += components["Rcode"] + components["Rsolver"]
    if "structure" in parts:
        score += 0.67 * components["Rstructure"] + 0.33 * components["Rlp_artifact_structure"]
    if "consensus" in parts:
        score += components["Robjective_consensus"]
    return float(score)


def _method_raw_score(row, method_name):
    if method_name == "Structure-Grounded Consistency":
        return structure_grounded_consistency_score(row)
    if method_name in REWARD_ABLATION_METHODS:
        return reward_ablation_score(row, method_name)
    if method_name == "OR-R1-like Voting":
        return row.get("or_r1_like_voting_score", 0.0)
    if method_name == "SIRL-like LP-Stats":
        return row.get("sirl_like_lp_stats_score", 0.0)
    if method_name == "OptArgus-like Audit":
        return row.get("optargus_like_audit_score", 0.0)
    if method_name == "OptiRepair-like Repair-Prompt":
        return row.get("optirepair_like_repair_score", 0.0)
    if method_name == "Solver-Filter":
        return row.get("raw_solver_only_score", row.get("solver_only_score", 0.0))
    if method_name == "Structure-Only":
        return row.get("structure_score", row.get("structure_only_score", 0.0))
    if method_name == "ReplenishVerifier-TypeAware":
        return type_aware_selection_score(row)
    if method_name == "ReplenishVerifier-TypeAware-Consensus":
        return type_aware_consensus_selection_score(row)
    if method_name in {"ReplenishVerifier-Full", "ReplenishVerifier-Repair"}:
        return row.get("raw_inference_score", row.get("score", 0.0))
    if method_name in {"Direct", "Best-of-K"}:
        return 1.0
    raise ValueError(f"Unknown method: {method_name}")


def _method_gated_score(row, method_name, allow_feasible_selection=False):
    raw_score = float(_method_raw_score(row, method_name) or 0.0)
    penalty = _critical_structure_penalty(row, method_name)
    raw_score *= float(penalty["multiplier"])
    return hard_selection_gate(row.get("execution") or {}, raw_score, allow_feasible_selection=allow_feasible_selection)


def _structure_score(row):
    return float(row.get("structure_score", ((row.get("structure_verification") or {}).get("structure_score", 0.0))) or 0.0)


def _selection_tie_break_key_for_method(row, method_name, allow_feasible_selection=False):
    gated = _method_gated_score(row, method_name, allow_feasible_selection=allow_feasible_selection)
    candidate_order = -_candidate_index(row)
    runtime = -_runtime_sec(row)

    if method_name == "Best-of-K":
        return (
            gated,
            _solver_status_score(row, allow_feasible_selection=allow_feasible_selection),
            _has_objective_score(row),
            _structure_score(row),
            _constraint_coverage(row),
            _code_validity_score(row),
            _static_validation_score(row),
            runtime,
            candidate_order,
        )

    if method_name in {"Solver-Filter", "Solver only"}:
        return (
            gated,
            _solver_status_score(row, allow_feasible_selection=allow_feasible_selection),
            _has_objective_score(row),
            _code_validity_score(row),
            _static_validation_score(row),
            runtime,
            candidate_order,
        )

    if method_name in {"Structure-Only", "Structure only", "Solver + Structure", "Structure + Consensus", "Solver + Structure + Consensus", "Structure-Grounded Consistency"}:
        return (
            gated,
            _structure_score(row),
            _constraint_coverage(row),
            _critical_structure_pass_score(row),
            _rule_score(row, "inventory_balance"),
            candidate_order,
        )

    if method_name in {"Consensus only", "OR-R1-like Voting", "Solver + Consensus"}:
        return (
            gated,
            float(row.get("objective_consensus_score", 0.0) or 0.0),
            _solver_status_score(row, allow_feasible_selection=allow_feasible_selection),
            _has_objective_score(row),
            _code_validity_score(row),
            runtime,
            candidate_order,
        )

    if method_name in {"SIRL-like LP-Stats", "OptArgus-like Audit", "OptiRepair-like Repair-Prompt"}:
        return (
            gated,
            _code_validity_score(row),
            _solver_status_score(row, allow_feasible_selection=allow_feasible_selection),
            _has_objective_score(row),
            runtime,
            candidate_order,
        )

    if method_name == "ReplenishVerifier-TypeAware":
        return (
            gated,
            _critical_structure_pass_score(row),
            _objective_term_coverage(row),
            _constraint_coverage(row),
            _type_aware_hard_gate_score(row),
            -_type_aware_repair_feedback_count(row),
            -_repair_feedback_count(row),
            runtime,
            candidate_order,
        )

    if method_name == "ReplenishVerifier-TypeAware-Consensus":
        components = type_aware_consensus_selection_components(row)
        return (
            gated,
            components["consensus_score"],
            components["consensus_bucket"],
            components["critical_structure_pass"],
            -components["critical_missing_count"],
            components["constraint_coverage"],
            components["objective_term_coverage"],
            components["structure_completeness"],
            components["hard_gate_score"],
            -components["repair_feedback_count"],
            runtime,
            candidate_order,
        )

    if method_name in {"ReplenishVerifier-Full", "ReplenishVerifier-Repair", "ReplenishVerifier full"}:
        return (
            gated,
            _structure_score(row),
            _constraint_coverage(row),
            _objective_term_coverage(row),
            _rule_score(row, "inventory_balance"),
            _static_validation_score(row),
            candidate_order,
        )

    return (gated, candidate_order)


def _selection_tie_break_key(row, method_name, allow_feasible_selection=False):
    return _selection_tie_break_key_for_method(row, method_name, allow_feasible_selection=allow_feasible_selection)


def _type_aware_candidate_pool_filter(rows, allow_feasible_selection=False):
    viable = [
        row for row in rows
        if _method_gated_score(row, "ReplenishVerifier-TypeAware", allow_feasible_selection=allow_feasible_selection) > 0.0
    ]
    metadata = {
        "type_aware_pool_filter_applied": True,
        "type_aware_pool_filter_fallback": False,
        "type_aware_pool_filter_candidate_count": 0,
    }
    if not viable:
        metadata["type_aware_pool_filter_fallback"] = True
        return list(rows), metadata
    critical_pass = [row for row in viable if not _critical_missing_structures(row)]
    if critical_pass:
        metadata["type_aware_pool_filter_candidate_count"] = len(critical_pass)
        return critical_pass, metadata
    metadata["type_aware_pool_filter_fallback"] = True
    metadata["type_aware_pool_filter_candidate_count"] = len(viable)
    return viable, metadata


def _annotate_selected_score(best, method_name, allow_feasible_selection=False):
    raw_score = float(_method_raw_score(best, method_name) or 0.0)
    penalty = _critical_structure_penalty(best, method_name)
    raw_score *= float(penalty["multiplier"])
    gated_score = _method_gated_score(best, method_name, allow_feasible_selection=allow_feasible_selection)
    best["raw_inference_score"] = raw_score
    best["score"] = gated_score
    best["selection_score"] = gated_score
    best["formal_selection_score"] = gated_score
    best["hard_selection_gate"] = {
        "enabled": True,
        "allow_feasible_selection": bool(allow_feasible_selection),
        "rule": "Only executable + Optimal candidates can be selected." if not allow_feasible_selection else "Executable + Optimal candidates can be selected; Feasible is allowed by explicit flag.",
        "passed": gated_score > 0.0,
    }
    if method_name == "ReplenishVerifier-TypeAware":
        best["selection_components"] = type_aware_selection_components(best)
        best["hard_gate_failures"] = _type_aware_hard_gate_failures(best)
        best["hard_gate_score"] = best["selection_components"]["hard_gate_score"]
        best["constraint_coverage"] = best["selection_components"]["constraint_coverage"]
        best["objective_term_coverage"] = best["selection_components"]["objective_term_coverage"]
        best["repair_feedback_count"] = best["selection_components"]["repair_feedback_count"]
    if method_name == "ReplenishVerifier-TypeAware-Consensus":
        best["selection_components"] = type_aware_consensus_selection_components(best)
        best["hard_gate_failures"] = _type_aware_hard_gate_failures(best)
        best["hard_gate_score"] = best["selection_components"]["hard_gate_score"]
        best["constraint_coverage"] = best["selection_components"]["constraint_coverage"]
        best["objective_term_coverage"] = best["selection_components"]["objective_term_coverage"]
        best["repair_feedback_count"] = best["selection_components"]["repair_feedback_count"]
    if penalty["enabled"]:
        best["critical_structure_penalty"] = penalty
    return best


def select_for_method(method_name, evaluated_by_problem, benchmark, allow_feasible_selection=False):
    selected = []
    for pid, reference in benchmark.items():
        rows = list(evaluated_by_problem.get(pid, []))
        pool_metadata = {}
        if not rows:
            best = _first_or_empty(pid, reference)
        elif method_name == "Direct":
            best = rows[0]
        elif method_name == "Best-of-K":
            viable = [row for row in rows if _method_gated_score(row, method_name, allow_feasible_selection=allow_feasible_selection) > 0.0]
            executable = [row for row in rows if row.get("execution", {}).get("executable")]
            best = max(viable, key=lambda row: _selection_tie_break_key_for_method(row, method_name, allow_feasible_selection=allow_feasible_selection)) if viable else (executable[0] if executable else rows[0])
        elif method_name == "ReplenishVerifier-TypeAware":
            pool, pool_metadata = _type_aware_candidate_pool_filter(rows, allow_feasible_selection=allow_feasible_selection)
            best = max(pool, key=lambda row: _selection_tie_break_key_for_method(row, method_name, allow_feasible_selection=allow_feasible_selection))
        else:
            best = max(rows, key=lambda row: _selection_tie_break_key_for_method(row, method_name, allow_feasible_selection=allow_feasible_selection))

        best = dict(best)
        if method_name == "ReplenishVerifier-TypeAware":
            best.update(pool_metadata)
        best["method_name"] = method_name
        _annotate_selected_score(best, method_name, allow_feasible_selection=allow_feasible_selection)
        if method_name == "OR-R1-like Voting":
            best["selection_policy"] = "Hard Selection Gate over executable + optimal + valid code/LP output + candidate objective consensus; no replenishment semantics; no reference objective"
        elif method_name == "SIRL-like LP-Stats":
            best["selection_policy"] = "Hard Selection Gate over generic solver + LP artifact statistics; no replenishment semantics; no reference objective"
        elif method_name == "OptArgus-like Audit":
            best["selection_policy"] = "Hard Selection Gate over generic hallucination audit signals; no replenishment semantics; no reference objective"
        elif method_name == "OptiRepair-like Repair-Prompt":
            best["selection_policy"] = "Hard Selection Gate over generic repair-readiness score from execution and audit issues; no replenishment semantics; no reference objective"
            best["feedback"] = best.get("generic_repair_feedback", best.get("feedback", ""))
        elif method_name == "Solver-Filter":
            best["selection_policy"] = "Hard Selection Gate over executable > optimal > has_objective; no reference objective"
        elif method_name == "Structure-Only":
            best["selection_policy"] = "Hard Selection Gate over replenishment LP structure completeness only; no reference objective"
        elif method_name == "Direct":
            best["selection_policy"] = "candidate order only, with Hard Selection Gate for formal score; no reference objective"
        elif method_name == "Best-of-K":
            best["selection_policy"] = "best executable/optimal candidate by no-reference tie-breaker, with Hard Selection Gate for formal score; no reference objective"
        elif method_name == "Structure-Grounded Consistency":
            best["selection_policy"] = "Hard Selection Gate over replenishment structure-grounded consistency: executable code + optimal solver status + required LP structure coverage + LP artifact key structures + candidate objective consensus; no reference objective"
        elif method_name == "ReplenishVerifier-TypeAware":
            best["selection_policy"] = "Hard Selection Gate over executable + optimal candidates, ranked by TypeAware-first no-reference score using structure completeness, constraint coverage, objective-term coverage, type-aware hard gates, candidate objective consensus, repair feedback count, and runtime; no reference objective"
        elif method_name == "ReplenishVerifier-TypeAware-Consensus":
            best["selection_policy"] = "Hard Selection Gate over executable + optimal candidates, ranked consensus-first with TypeAware-safe reranking over critical missing structures, structure completeness, constraint coverage, objective-term coverage, type-aware hard gates, repair feedback count, and runtime; no reference objective"
        elif method_name in REWARD_ABLATION_METHODS:
            parts = ", ".join(REWARD_ABLATION_METHODS[method_name])
            best["selection_policy"] = f"replenishment structure-grounded reward ablation over {parts}; no reference objective"
        if method_name == "Structure-Grounded Consistency" or method_name in REWARD_ABLATION_METHODS:
            best["reward_components"] = reward_components(best)
        best["uses_reference_objective_for_selection"] = False
        best["selected"] = True
        selected.append(best)
    return selected


def _certificate_summary(certificates):
    return [
        {
            "rule_name": cert.get("rule_name"),
            "required": cert.get("required"),
            "passed": cert.get("passed"),
            "score": cert.get("score"),
            "evidence_strength": cert.get("evidence_strength"),
        }
        for cert in (certificates or [])
    ]


def _evidence_strength_by_rule(certificates):
    return {cert.get("rule_name"): cert.get("evidence_strength") for cert in (certificates or []) if cert.get("rule_name")}


def _static_validation_errors(row):
    return list(row.get("static_validation_errors") or ((row.get("static_validation") or {}).get("static_validation_errors") or []))


def _base_repair_prompt_row(row, repair_type, missing_structures, feedback, repair_prompt):
    structure = row.get("structure_verification") or {}
    certificates = structure.get("certificates", [])
    return {
        "problem_id": row["problem_id"],
        "candidate_id": row["candidate_id"],
        "method_name": row.get("method_name", "candidate"),
        "candidate_method": row.get("candidate_method"),
        "repair_type": repair_type,
        "repair_feedback_count": len(missing_structures),
        "missing_structures": list(missing_structures),
        "low_score_required": structure.get("low_score_required", []) if repair_type == "structure_aware" else [],
        "structure_certificates": _certificate_summary(certificates) if repair_type == "structure_aware" else [],
        "evidence_strength_by_rule": _evidence_strength_by_rule(certificates) if repair_type == "structure_aware" else {},
        "execution": row.get("execution") or {},
        "generic_repair_feedback": row.get("generic_repair_feedback", ""),
        "static_validation_errors": _static_validation_errors(row),
        "feedback": feedback,
        "repair_prompt": repair_prompt,
        "original_candidate_text": row.get("generated_text", ""),
        "original_candidate_code": row.get("generated_code", ""),
        "prompt_type": row.get("prompt_type") or (row.get("generation_config") or {}).get("prompt_type"),
        "type_aware_static_validation": _type_aware_validation(row),
        "type_aware_static_validation_errors": _type_aware_errors(row),
        "repair_generation_executed": False,
        "is_evaluated_repair_result": False,
        "uses_reference_objective_for_repair": False,
    }


def build_structure_aware_repair_prompts(rows):
    """Build structure-aware repair prompts for candidates with missing required structures."""
    prompts = []
    for row in rows:
        structure = row.get("structure_verification") or {}
        missing = structure.get("missing") or []
        if not missing:
            continue
        feedback = row.get("feedback", "")
        repair_prompt = (
            "You are fixing a PuLP optimization model for an inventory replenishment problem.\n"
            "Revise the generated code according to the replenishment structure feedback below.\n"
            "Keep variable names interpretable and explicitly name every PuLP constraint; do not rely on anonymous _C1/_C2 names.\n\n"
            f"Problem ID: {row.get('problem_id')}\n"
            f"Candidate ID: {row.get('candidate_id')}\n\n"
            f"Missing structures: {', '.join(missing)}\n\n"
            f"Feedback:\n{feedback}\n"
        )
        static_errors = _static_validation_errors(row)
        if static_errors:
            repair_prompt += "\nStatic validation errors:\n" + "\n".join(f"- {error}" for error in static_errors) + "\n"
        type_aware = _type_aware_validation(row)
        type_aware_missing = list(type_aware.get("missing_items") or _type_aware_errors(row))
        type_aware_feedback = list(type_aware.get("repair_feedback") or [])
        if type_aware_missing:
            repair_prompt += "\nType-aware static validation missing items:\n" + "\n".join(f"- {item}" for item in type_aware_missing) + "\n"
        if type_aware_feedback:
            repair_prompt += "\nType-aware repair requirements:\n" + "\n".join(f"- {item}" for item in type_aware_feedback) + "\n"
        if type_aware_missing or type_aware_feedback:
            repair_prompt += "\nReturn only raw Python source code with no Markdown fences or explanations.\n"
        prompts.append(_base_repair_prompt_row(row, "structure_aware", missing, feedback, repair_prompt))
    return prompts


def build_generic_repair_prompts(rows):
    """Build generic repair prompts without replenishment-specific missing-structure labels."""
    prompts = []
    for row in rows:
        feedback = row.get("generic_repair_feedback", "")
        audit = row.get("optargus_audit") or {}
        execution = row.get("execution") or {}
        if not feedback and execution.get("executable") and not audit.get("generic_issue_count"):
            continue
        if not feedback:
            feedback = "- Inspect generic execution, objective, variables, constraints, bounds, and solver status."
        repair_prompt = (
            "You are fixing a PuLP optimization model using only generic execution, solver, and LP-artifact feedback.\n"
            "Do not use task-specific verifier rule names.\n\n"
            f"Problem ID: {row.get('problem_id')}\n"
            f"Candidate ID: {row.get('candidate_id')}\n\n"
            f"Generic feedback:\n{feedback}\n"
        )
        prompts.append(_base_repair_prompt_row(row, "generic", [], feedback, repair_prompt))
    return prompts


def build_repair_prompts(rows):
    """Backward-compatible alias for structure-aware repair prompts."""
    return build_structure_aware_repair_prompts(rows)
