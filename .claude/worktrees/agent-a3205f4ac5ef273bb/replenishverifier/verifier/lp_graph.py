"""Incidence-based weak LP-structure graph evidence.

LPStructureGraph provides only variable-constraint incidence evidence. It is an
auxiliary signal for ReplenishVerifier certificates, not a complete graph-matching
verifier and not proof of algebraic equivalence or coefficient-pattern correctness.
"""

import re
from dataclasses import asdict, dataclass


@dataclass
class WeakEvidence:
    detector: str
    found: bool
    confidence: float
    evidence: list
    evidence_scope: str = "incidence_based_auxiliary"
    limitation: str = "not_complete_graph_matching_or_algebraic_equivalence"

    def to_dict(self):
        return asdict(self)


class LPStructureGraph:
    def __init__(self, parsed):
        self.parsed = parsed
        self.variables = list(parsed.variable_names)
        self.binary_variables = set(parsed.binary_variables)
        self.constraints = dict(parsed.constraints)
        self.objective = parsed.objective or ""
        self.variable_to_constraints = {name: [] for name in self.variables}
        self.constraint_to_variables = {}
        for cname, expr in self.constraints.items():
            vars_in_expr = [name for name in self.variables if _contains_var(expr, name)]
            self.constraint_to_variables[cname] = vars_in_expr
            for name in vars_in_expr:
                self.variable_to_constraints.setdefault(name, []).append(cname)

    def detect_big_m_like_constraints(self):
        """Find upper-bound constraints linking continuous order-like vars and binaries."""
        evidence = []
        continuous_order = [v for v in self.variables if v not in self.binary_variables and _looks_order_like(v)]
        binaries = list(self.binary_variables)
        for cname, expr in self.constraints.items():
            if "<=" not in expr:
                continue
            vars_in_expr = self.constraint_to_variables.get(cname, [])
            has_order = any(v in vars_in_expr for v in continuous_order)
            has_binary = any(v in vars_in_expr for v in binaries)
            if has_order and has_binary:
                evidence.append({
                    "constraint": cname,
                    "expr": expr,
                    "variables": vars_in_expr[:8],
                    "evidence_scope": "incidence_only",
                })
        return WeakEvidence(
            detector="detect_big_m_like_constraints",
            found=bool(evidence),
            confidence=0.6 if evidence else 0.0,
            evidence=evidence[:5],
        )

    def detect_inventory_recurrence_candidates(self):
        """Find weak recurrence-like constraints, including I_t / I_t-1 patterns."""
        evidence = []
        for cname, expr in self.constraints.items():
            vars_in_expr = self.constraint_to_variables.get(cname, [])
            inventory_like = [v for v in vars_in_expr if _looks_inventory_like(v)]
            has_equal = "=" in expr and "<=" not in expr and ">=" not in expr
            has_order = any(_looks_order_like(v) for v in vars_in_expr)
            repeated_family = _has_repeated_time_family(vars_in_expr)
            name_hint = any(term in cname.lower() for term in ["balance", "flow", "inventory"])
            if has_equal and (name_hint or (len(inventory_like) >= 1 and has_order) or repeated_family):
                evidence.append({
                    "constraint": cname,
                    "expr": expr,
                    "variables": vars_in_expr[:10],
                    "inventory_like": inventory_like[:6],
                    "weak_repeated_family": repeated_family,
                    "evidence_scope": "incidence_only",
                })
        confidence = 0.6 if any(item["inventory_like"] for item in evidence) else (0.4 if evidence else 0.0)
        return WeakEvidence(
            detector="detect_inventory_recurrence_candidates",
            found=bool(evidence),
            confidence=confidence,
            evidence=evidence[:5],
        )

    def detect_fixed_cost_binary_terms(self):
        """Find binary variables appearing in the objective."""
        binaries_in_objective = [v for v in self.binary_variables if _contains_var(self.objective, v)]
        evidence = [{
            "binary_variable": v,
            "objective_excerpt": self.objective[:300],
            "evidence_scope": "objective_incidence_only",
        } for v in binaries_in_objective]
        return WeakEvidence(
            detector="detect_fixed_cost_binary_terms",
            found=bool(evidence),
            confidence=0.6 if evidence else 0.0,
            evidence=evidence[:8],
        )

    def weak_evidence(self):
        return {
            "big_m_like_constraints": self.detect_big_m_like_constraints().to_dict(),
            "inventory_recurrence_candidates": self.detect_inventory_recurrence_candidates().to_dict(),
            "fixed_cost_binary_terms": self.detect_fixed_cost_binary_terms().to_dict(),
        }


def _contains_var(expr, name):
    return re.search(rf"(?<![A-Za-z0-9_]){re.escape(name)}(?![A-Za-z0-9_])", expr or "") is not None


def _norm(name):
    return str(name).lower().replace("-", "_")


def _looks_order_like(name):
    n = _norm(name)
    return n == "q" or n.startswith("q_") or any(term in n for term in ["order", "purchase", "replenish"])


def _looks_inventory_like(name):
    n = _norm(name)
    return n == "i" or n.startswith("i_") or any(term in n for term in ["inventory", "stock", "onhand", "on_hand", "inv"])


def _family_key(name):
    # Remove numeric fragments to detect repeated time-indexed variable families.
    return re.sub(r"_?\d+", "", _norm(name))


def _has_repeated_time_family(names):
    counts = {}
    for name in names:
        key = _family_key(name)
        counts[key] = counts.get(key, 0) + 1
    return any(count >= 2 for count in counts.values())
