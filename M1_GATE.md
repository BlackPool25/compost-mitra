# M1 Gate — CompostMitra S1 Foundation

**Status: M1 PASS ✅ (2 consecutive green runs)**

Date: 2026-10-02 | Branch: feat/s1-foundation

---

## Gate Runs

| Run | Timestamp (IST) | Result | Checks Passed | Checks Failed |
|-----|-----------------|--------|---------------|---------------|
| 1   | 2026-10-02 10:57 | **M1 PASS** | 14/14 | 0 |
| 2   | 2026-10-02 10:57 | **M1 PASS** | 14/14 | 0 |

---

## Checks Summary

| Check | Result | Details |
|-------|--------|---------|
| a. Cornell 28-32 | ✅ PASS | CN=30.4 PASS (28-32) |
| b. datacheck GOOD (clean data) | ✅ PASS | 5 file(s) checked, 0 rejected |
| c. datacheck BAD (rejected=6) | ✅ PASS | 6/6 bad fixtures rejected |
| d. pytest ≥ 20 passed | ✅ PASS | 26 passed |
| e. Streamlit health ok + load < 3s | ✅ PASS | 0.185s cold startup |
| f. SBOM exists + bomFormat CycloneDX | ✅ PASS | CycloneDX |
| g. Holdout docs + label compliance | ✅ PASS | 3 holdout files checked |
| h. Tier footnotes check | ✅ PASS | All docs compliant |
| i. Forbidden words (proves/causes) | ✅ PASS | Zero hits in *.py |
| j. Zero-syn check | ✅ PASS | 6 files, 0 rejected |
| k. Edge fixtures (empty/all-browns/meat) | ✅ PASS | No tracebacks |
| l. Docker build + in-container datacheck | ✅ PASS | Image 400MB < 800MB, startup < 30s |
| m. USB backup listing | ✅ PASS | usb_backup/ + MANIFEST.TXT present |

---

## Metrics

| Metric | Value | Budget |
|--------|-------|--------|
| Pytest tests | 26 passed | ≥ 20 |
| Streamlit cold startup | 0.185s | < 3s |
| Docker image size | ~400MB | < 800MB |
| Docker startup | < 6s | < 30s |
| Datasets (raw) | Hafsa 452, Mullick 1314, Zhang 310, D1 2200, D3 3100 | — |
| Synthetic training rows | 0 | 0 |

---

## USB Backup Listing

| File | Description |
|------|-------------|
| `EDA_REPORT.HTM` | EDA notebook export (FAT32-safe) |
| `TOMATO_RECIPE.PDF` | Tomato recipe card PDF |
| `ROSE_RECIPE.PDF` | Rose recipe card PDF |
| `SPINACH_RECIPE.PDF` | Spinach recipe card PDF |
| `TOMATO_RECIPE.HTM` | Tomato recipe card HTML |
| `MANIFEST.TXT` | SHA256 checksums and sizes |

---

## S2 Fallback Note

If the ML kill-bar check (Group-5-fold accuracy ≥ majority +5pp) is not met in S2, the system falls back to rules-based maturity estimation (Cornell 28-32 range gate + pH gate + moisture check). This fallback is pre-drafted in `docs/adrs/ADR-003-kill-bar-s2.md`.

---

## Execution Command

```bash
bash scripts/m1_gate.sh
```

Exits 0 and prints `M1 PASS` when all checks pass.
Prints `M1 HOLD (DOCKER_UNAVAILABLE)` if docker daemon is not accessible.
Never silently passes with any failed check.
