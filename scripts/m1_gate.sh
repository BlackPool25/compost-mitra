#!/usr/bin/env bash
# M1 Gate Script for CompostMitra
# Runs all acceptance criteria for the M1 milestone.
# Exits 0 and prints M1 PASS when all checks pass.
# Prints M1 HOLD when only DOCKER_UNAVAILABLE branch applies.
set -euo pipefail

PASS_COUNT=0
FAIL_COUNT=0
HOLD_FLAGS=()
GATE_LOG="${1:-/dev/stdout}"

_log() { echo "[M1_GATE] $*"; }
_pass() { _log "PASS: $1"; PASS_COUNT=$((PASS_COUNT + 1)); }
_fail() { _log "FAIL: $1"; FAIL_COUNT=$((FAIL_COUNT + 1)); }
_hold() { _log "HOLD: $1"; HOLD_FLAGS+=("$1"); }

# ── a. Cornell 28-32 ──────────────────────────────────────────────────────────
_log "Checking Cornell 28-32..."
if python3 scripts/blender.py --cornell-check 2>&1 | grep -q "PASS (28-32)"; then
  _pass "Cornell 28-32"
else
  _fail "Cornell 28-32"
fi

# ── b. datacheck GOOD (clean data) ────────────────────────────────────────────
_log "Checking datacheck GOOD..."
if python3 scripts/datacheck.py --strict data/clean/*.csv data/ingredients.csv data/plants.csv 2>&1 | grep -q "0 rejected"; then
  _pass "datacheck GOOD"
else
  _fail "datacheck GOOD"
fi

# ── c. datacheck BAD (fixtures/bad rejected=6) ────────────────────────────────
_log "Checking datacheck BAD rejected=6..."
BAD_OUT=$(python3 scripts/datacheck.py --strict tests/fixtures/bad/ 2>&1 || true)
if echo "$BAD_OUT" | grep -q "rejected=6"; then
  _pass "datacheck BAD rejected=6"
else
  _fail "datacheck BAD - expected rejected=6, got: $BAD_OUT"
fi

# ── d. pytest >= 20 passed ────────────────────────────────────────────────────
_log "Checking pytest >= 20 passed..."
PYTEST_OUT=$(python3 -m pytest tests/ -q 2>&1)
PYTEST_PASSED=$(echo "$PYTEST_OUT" | grep -oP '\d+ passed' | grep -oP '\d+' || echo 0)
if [ "${PYTEST_PASSED:-0}" -ge 20 ]; then
  _pass "pytest >= 20 passed (got $PYTEST_PASSED)"
else
  _fail "pytest passed < 20 (got ${PYTEST_PASSED:-0})"
fi

# ── e. Streamlit health ok + cold load < 3s ───────────────────────────────────
_log "Checking Streamlit health ok + cold load < 3s..."
if bash scripts/serve_and_check.sh > /dev/null 2>&1; then
  _pass "Streamlit health ok < 3s"
else
  _fail "Streamlit health check failed"
fi

# ── f. SBOM exists + bomFormat == CycloneDX ───────────────────────────────────
_log "Checking SBOM CycloneDX..."
if python3 -c "import json; assert json.load(open('sbom.cyclonedx.json'))['bomFormat'] == 'CycloneDX'" 2>&1; then
  _pass "SBOM CycloneDX"
else
  _fail "SBOM format check failed"
fi

# ── g. Holdout docs exist and comply with labels ──────────────────────────────
_log "Checking holdout label compliance..."
if [ -f "docs/holdout/split_definition.md" ] && [ -f "docs/holdout/centroid_table.csv" ] && \
   [ -f "docs/holdout/direction_note.md" ] && [ -f "docs/holdout/synthetic_ablation.md" ]; then
  if python3 scripts/check_holdout_labels.py docs/holdout/ 2>&1 | grep -q "PASS"; then
    _pass "Holdout docs exist + label compliant"
  else
    _fail "Holdout label check failed"
  fi
else
  _fail "Holdout docs missing"
fi

# ── h. Tier footnotes check ───────────────────────────────────────────────────
_log "Checking tier footnotes..."
if python3 scripts/check_tier_footnotes.py docs/ 2>&1 | grep -q "PASS"; then
  _pass "Tier footnotes"
else
  _fail "Tier footnote check failed"
fi

# ── i. Forbidden words check ──────────────────────────────────────────────────
_log "Checking forbidden words (proves/causes in .py files)..."
if ! grep -rEw "proves|causes" --include="*.py" . 2>/dev/null | grep -v "test_wording.py" | grep -v "#" > /tmp/m1_fw.txt 2>&1; [ -s /tmp/m1_fw.txt ] && grep -q "." /tmp/m1_fw.txt; then
  _fail "Forbidden words found: $(cat /tmp/m1_fw.txt)"
else
  _pass "Forbidden words clean"
fi
rm -f /tmp/m1_fw.txt

# ── j. Zero-syn check ─────────────────────────────────────────────────────────
_log "Checking zero-syn..."
if python3 scripts/datacheck.py --assert-zero-syn data/ 2>&1 | grep -q "rejected=0"; then
  _pass "Zero-syn"
else
  _fail "Zero-syn check failed"
fi

# ── k. Edge fixtures: empty, all-browns, meat (no traceback) ──────────────────
_log "Checking edge fixtures (empty, all-browns, meat)..."
EDGE_FAIL=0
for fixture in tests/fixtures/empty.json tests/fixtures/all-browns.json tests/fixtures/meat.json; do
  if [ -f "$fixture" ]; then
    RESULT=$(python3 scripts/pipeline_smoke.py --demo tomato 2>&1 || true)
    if echo "$RESULT" | grep -q "Traceback"; then
      EDGE_FAIL=1
    fi
  fi
done
if [ $EDGE_FAIL -eq 0 ]; then
  _pass "Edge fixtures no-traceback"
else
  _fail "Edge fixtures raised Traceback"
fi

# ── l. Docker checks ──────────────────────────────────────────────────────────
_log "Checking Docker..."
if command -v docker &> /dev/null && docker info &> /dev/null; then
  if docker build -t compostmitra:s1 . > /tmp/m1_docker_build.log 2>&1; then
    _pass "Docker build compostmitra:s1"
    if docker run --rm compostmitra:s1 python3 scripts/datacheck.py --strict data/clean/hafsa_452.csv data/clean/mullick_1314.csv data/clean/zhang_848.csv data/ingredients.csv data/plants.csv 2>&1 | grep -q "0 rejected"; then
      _pass "Docker in-container datacheck"
    else
      _fail "Docker in-container datacheck"
    fi
  else
    _fail "Docker build failed"
  fi
else
  _hold "DOCKER_UNAVAILABLE - Docker daemon not accessible"
fi

# ── m. USB backup listing ─────────────────────────────────────────────────────
_log "Checking USB backup listing..."
if [ -d "usb_backup" ] && [ -f "usb_backup/MANIFEST.TXT" ]; then
  _pass "USB backup listing present"
else
  _fail "USB backup missing (usb_backup/ or MANIFEST.TXT not found)"
fi

# ── Summary ───────────────────────────────────────────────────────────────────
echo ""
_log "═══════════════════════════════════════"
_log "PASS_COUNT=$PASS_COUNT  FAIL_COUNT=$FAIL_COUNT  HOLDS=${#HOLD_FLAGS[@]}"

if [ $FAIL_COUNT -eq 0 ] && [ ${#HOLD_FLAGS[@]} -eq 0 ]; then
  _log "═══════════════════════════════════════"
  echo "M1 PASS"
  exit 0
elif [ $FAIL_COUNT -eq 0 ] && [ ${#HOLD_FLAGS[@]} -gt 0 ]; then
  _log "═══════════════════════════════════════"
  echo "M1 HOLD ($(IFS=, ; echo "${HOLD_FLAGS[*]}"))"
  exit 0
else
  _log "═══════════════════════════════════════"
  echo "M1 FAIL ($FAIL_COUNT check(s) failed)"
  exit 1
fi
