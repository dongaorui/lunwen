#!/usr/bin/env bash
set -euo pipefail

EXP_NAME="qwen3_8b_k8_100_v6_typeaware_consensusrerank"
STAMP="$(date +%Y%m%d_%H%M%S)"

BENCH="data/generated/test_100_v6.jsonl"
CAND="data/candidates/qwen3_8b_k8_100_v6_typeaware.jsonl"
RUN_DIR="runs/${EXP_NAME}"
OUT_DIR="docs/experiment_results/${EXP_NAME}_compare"

PKG_ROOT="experiment_packages"
PKG_DIR="${PKG_ROOT}/${EXP_NAME}_${STAMP}"
LOG_DIR="${PKG_DIR}/logs"

mkdir -p "${LOG_DIR}"

echo "========================================"
echo "Experiment: ${EXP_NAME}"
echo "Timestamp : ${STAMP}"
echo "Benchmark : ${BENCH}"
echo "Candidates: ${CAND}"
echo "Run dir   : ${RUN_DIR}"
echo "Out dir   : ${OUT_DIR}"
echo "Package   : ${PKG_DIR}"
echo "========================================"

echo "[1/8] Saving git state..."
{
  echo "=== git rev-parse HEAD ==="
  git rev-parse HEAD || true
  echo
  echo "=== git branch ==="
  git branch -vv || true
  echo
  echo "=== git status ==="
  git status || true
  echo
  echo "=== git diff --stat ==="
  git diff --stat || true
  echo
  echo "=== git diff --cached --stat ==="
  git diff --cached --stat || true
} | tee "${LOG_DIR}/git_state.txt"

git diff > "${LOG_DIR}/working_tree.diff" || true
git diff --cached > "${LOG_DIR}/staged.diff" || true

echo "[2/8] Checking input files..."
test -f "${BENCH}"
test -f "${CAND}"

{
  echo "Benchmark line count:"
  wc -l "${BENCH}"
  echo
  echo "Candidate line count:"
  wc -l "${CAND}"
  echo
  echo "Candidate per-problem integrity:"
  python - <<PY
import json
from collections import Counter

bench = "${BENCH}"
cand = "${CAND}"

bench_ids = []
with open(bench) as f:
    for line in f:
        if line.strip():
            r = json.loads(line)
            bench_ids.append(r.get("problem_id"))

cnt = Counter()
bad = 0
with open(cand) as f:
    for line in f:
        if not line.strip():
            continue
        try:
            r = json.loads(line)
            cnt[r.get("problem_id")] += 1
        except Exception:
            bad += 1

print("num benchmark problems:", len(bench_ids))
print("num candidate problems:", len(cnt))
print("total candidates:", sum(cnt.values()))
print("bad json lines:", bad)
if cnt:
    print("min candidates per problem:", min(cnt.values()))
    print("max candidates per problem:", max(cnt.values()))
    print("candidate count distribution:", dict(sorted(Counter(cnt.values()).items())))
missing = sorted(set(bench_ids) - set(cnt))
extra = sorted(set(cnt) - set(bench_ids))
print("missing problem ids:", len(missing))
print("extra problem ids:", len(extra))
if missing[:10]:
    print("first missing:", missing[:10])
if extra[:10]:
    print("first extra:", extra[:10])
PY
} | tee "${LOG_DIR}/input_integrity.txt"

echo "[3/8] Running pytest..."
pytest \
  tests/test_diagnose_selection_metrics.py \
  tests/test_leakage_audit.py \
  tests/test_paper_metrics.py \
  tests/test_selection_gating.py \
  2>&1 | tee "${LOG_DIR}/pytest_selected.log"

echo "[4/8] Running full paper metrics..."
mkdir -p "${RUN_DIR}" "${OUT_DIR}"

python -m replenishverifier.experiments.paper_metrics \
  --benchmark "${BENCH}" \
  --candidates "${CAND}" \
  --out_dir "${OUT_DIR}" \
  --exp_dir "${RUN_DIR}" \
  --write_report \
  2>&1 | tee "${LOG_DIR}/paper_metrics.log"

echo "[5/8] Snapshot important reports..."
{
  echo "=== main_results.md ==="
  if [ -f "${OUT_DIR}/main_results.md" ]; then
    cat "${OUT_DIR}/main_results.md"
  else
    echo "MISSING: ${OUT_DIR}/main_results.md"
  fi

  echo
  echo "=== diagnostic files ==="
  find "${RUN_DIR}/diagnostics" -maxdepth 2 -type f 2>/dev/null | sort || true

  echo
  echo "=== docs result files ==="
  find "${OUT_DIR}" -maxdepth 2 -type f 2>/dev/null | sort || true
} | tee "${LOG_DIR}/report_snapshot.txt"

echo "[6/8] Copying experiment records..."
mkdir -p "${PKG_DIR}/data/generated"
mkdir -p "${PKG_DIR}/data/candidates"
mkdir -p "${PKG_DIR}/runs"
mkdir -p "${PKG_DIR}/docs/experiment_results"

cp -v "${BENCH}" "${PKG_DIR}/data/generated/" | tee -a "${LOG_DIR}/copy_files.log"
cp -v "${CAND}" "${PKG_DIR}/data/candidates/" | tee -a "${LOG_DIR}/copy_files.log"

if [ -d "${RUN_DIR}" ]; then
  cp -av "${RUN_DIR}" "${PKG_DIR}/runs/" | tee -a "${LOG_DIR}/copy_files.log"
fi

if [ -d "${OUT_DIR}" ]; then
  cp -av "${OUT_DIR}" "${PKG_DIR}/docs/experiment_results/" | tee -a "${LOG_DIR}/copy_files.log"
fi

cp -v findings.md progress.md task_plan.md "${PKG_DIR}/" 2>/dev/null || true

echo "[7/8] Creating README for package..."
cat > "${PKG_DIR}/README.md" <<EOF
# ${EXP_NAME} Experiment Package

Generated at: ${STAMP}

## Inputs

- Benchmark: ${BENCH}
- Candidates: ${CAND}
- Run dir: ${RUN_DIR}
- Report dir: ${OUT_DIR}

## Main commands

\`\`\`bash
pytest \\
  tests/test_diagnose_selection_metrics.py \\
  tests/test_leakage_audit.py \\
  tests/test_paper_metrics.py \\
  tests/test_selection_gating.py

python -m replenishverifier.experiments.paper_metrics \\
  --benchmark ${BENCH} \\
  --candidates ${CAND} \\
  --out_dir ${OUT_DIR} \\
  --exp_dir ${RUN_DIR} \\
  --write_report
\`\`\`

## Important files

- \`docs/experiment_results/${EXP_NAME}_compare/main_results.md\`
- \`runs/${EXP_NAME}/diagnostics/\`
- \`logs/pytest_selected.log\`
- \`logs/paper_metrics.log\`
- \`logs/git_state.txt\`
- \`logs/working_tree.diff\`
- \`logs/input_integrity.txt\`

## Notes

This package is intended to preserve the full local experiment record, including code state, logs, inputs, reports, and diagnostics.
EOF

echo "[8/8] Compressing package..."
tar -czf "${PKG_ROOT}/${EXP_NAME}_${STAMP}.tar.gz" -C "${PKG_ROOT}" "${EXP_NAME}_${STAMP}"

echo
echo "========================================"
echo "DONE"
echo "Package directory:"
echo "${PKG_DIR}"
echo
echo "Compressed package:"
echo "${PKG_ROOT}/${EXP_NAME}_${STAMP}.tar.gz"
echo "========================================"
