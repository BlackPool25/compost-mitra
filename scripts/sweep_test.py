#!/usr/bin/env python3
"""Offline stress sweep over recipe quality across inputs.

Matrix (--full): 5 pools x 3 quantities x 3 crops = 45 combos capped to
36 runs per spec (first 36 in deterministic order). Each run calls
optimize() directly (seed 42 inside optimizer) with try/except so one
failure never aborts the matrix. Verdict tiers: PASS, WARN (all-equal
clamped scores or moist outside the 50-60 start band), FAIL (exception,
weights sum drift, hard cn/ph range violation). Writes
reports/sweep_results.json.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))
sys.path.insert(0, str(REPO_ROOT))

from optimize import benefits, loo, load_plant_needs, match_raw, optimize  # noqa: E402

SEED = 42

POOLS: dict[str, list[str]] = {
    "veg_only_greens": [
        "vegetable_scraps",
        "grass_clippings",
        "banana_peel",
        "tea_waste",
        "onion_peels",
        "cow_dung",
    ],
    "balanced_greens_browns": [
        "vegetable_scraps",
        "coffee_grounds",
        "dry_leaves",
        "straw",
        "newspaper",
        "tea_waste",
    ],
    "brown_heavy": [
        "dry_leaves",
        "straw",
        "sawdust",
        "newspaper",
        "cardboard",
        "vegetable_scraps",
    ],
    "full_10_cap": [
        "vegetable_scraps",
        "coffee_grounds",
        "banana_peel",
        "eggshell",
        "tea_waste",
        "onion_peels",
        "citrus_peels",
        "newspaper",
        "sawdust",
        "straw",
    ],
    "canteen_mix": [
        "vegetable_scraps",
        "coffee_grounds",
        "cooked_rice",
        "dry_leaves",
    ],
}

QUANTITIES: dict[str, float] = {
    "low_1_5_kg": 1.5,
    "med_3_5_kg": 3.5,
    "high_7_kg": 7.0,
}

CROPS = ["tomato", "spinach", "rose"]
MAX_RUNS = 36


def _is_citrus(ing_id: str) -> bool:
    return "citrus" in ing_id.lower()


def _is_meat(ing_id: str) -> bool:
    return "meat" in ing_id.lower()


def _check_run(top3: list[dict]) -> tuple[str, list[str], list[str]]:
    """Verdict with WARN tier for soft signals.

    FAIL only on exception, weights sum drift, or hard cn/ph range
    violation. All-equal clamped scores are a correct all-rejected
    signal (WARN, ties still resolve on raw scores). Moist outside the
    50-60 start band is a WARN gate, not a rejection.
    """
    reasons: list[str] = []
    warnings: list[str] = []
    try:
        scores = [float(r.get("score", 0.0)) for r in top3]
        if len(set(scores)) == 1 and len(scores) > 1:
            raws = [float(r.get("score_raw", 0.0)) for r in top3]
            if len(set(raws)) == 1:
                warnings.append("score_tie_all_equal")
            else:
                warnings.append("score_tie_display_only_raw_resolved")
        for r in top3:
            weights = r.get("recipe", {}) or {}
            s = sum(float(v) for v in weights.values())
            if abs(s - 1.0) > 1e-6:
                reasons.append(f"weights_sum_{s:.6f}")
            cn = float(r.get("cn", 0.0))
            if not (4.0 <= cn <= 150.0):
                reasons.append(f"cn_out_of_range_{cn}")
            ph = float(r.get("ph", 7.0))
            if not (0.0 <= ph <= 14.0):
                reasons.append(f"ph_out_of_range_{ph}")
            moist = float(r.get("moist_pct", 55.0))
            if not (50.0 <= moist <= 60.0):
                warnings.append(f"moist_outside_start_band_{moist}")
    except Exception as exc:  # noqa: BLE001
        reasons.append(f"check_exception_{exc}")
    warnings = list(dict.fromkeys(warnings))
    if reasons:
        return ("FAIL", reasons, warnings)
    if warnings:
        return ("WARN", reasons, warnings)
    return ("PASS", reasons, warnings)


def _run_one(pool_name: str, pool: list[str], qty_name: str, qty_kg: float, crop: str) -> dict:
    random.seed(SEED)
    entry: dict = {
        "pool": pool_name,
        "quantity": qty_name,
        "total_waste_kg": qty_kg,
        "crop": crop,
        "status": "PASS",
        "fail_reasons": [],
        "warnings": [],
        "top3": [],
        "guardrail_hits": {"citrus": False, "meat": False, "p_cap": False},
    }
    try:
        needs = load_plant_needs(crop)
        p_cap = float(needs.get("p_cap", 0.0))
        per_item = qty_kg / max(1, len(pool))
        waste = {ing_id: per_item for ing_id in pool}
        results = optimize(needs, waste, k=3)
        citrus_hit = False
        meat_hit = False
        p_cap_hit = False
        top3_out = []
        for res in results[:3]:
            weights = {k: float(v) for k, v in (res.get("recipe", {}) or {}).items()}
            if any(_is_citrus(i) and w > 0.10 + 1e-12 for i, w in weights.items()):
                citrus_hit = True
            if any(_is_meat(i) for i in weights):
                meat_hit = True
            if p_cap > 0.0 and float(res.get("p", 0.0)) > p_cap:
                p_cap_hit = True
            try:
                loo_deltas = loo({"recipe": weights}, needs)
                loo_top_delta = float(loo_deltas[0][1]) if loo_deltas else 0.0
                loo_top_id = str(loo_deltas[0][0]) if loo_deltas else ""
            except Exception:  # noqa: BLE001
                loo_top_delta = 0.0
                loo_top_id = ""
            try:
                ben = benefits({"recipe": weights, "total_waste_kg": qty_kg, "pots": 4})
            except Exception:  # noqa: BLE001
                ben = {"kg_mo": 0.0, "rs_mo": 0.0, "co2e": 0.0}
            top3_out.append(
                {
                    "weights": weights,
                    "cn": float(res.get("cn", 0.0)),
                    "n": float(res.get("n", 0.0)),
                    "p": float(res.get("p", 0.0)),
                    "k": float(res.get("k", 0.0)),
                    "moist_pct": float(res.get("moist_pct", 0.0)),
                    "ph": float(res.get("ph", 0.0)),
                    "match_score": float(res.get("score", 0.0)),
                    "match_score_raw": round(match_raw(needs, res), 4),
                    "loo_top_id": loo_top_id,
                    "loo_top_delta": loo_top_delta,
                    "benefits": ben,
                    "heuristic_grade": str(res.get("heuristic_grade", "")),
                }
            )
        entry["top3"] = top3_out
        entry["guardrail_hits"] = {
            "citrus": citrus_hit,
            "meat": meat_hit,
            "p_cap": p_cap_hit,
        }
        status, fail_reasons, warn_reasons = _check_run(
            [dict(res, score_raw=round(match_raw(needs, res), 4)) for res in results[:3]]
        )
        entry["status"] = status
        entry["fail_reasons"] = fail_reasons
        entry["warnings"] = warn_reasons
    except Exception as exc:  # noqa: BLE001
        entry["status"] = "FAIL"
        entry["fail_reasons"] = [f"exception_{type(exc).__name__}_{exc}"]
    return entry


def build_matrix(full: bool) -> list[tuple[str, list[str], str, float, str]]:
    combos = [
        (p_name, p_ids, q_name, q_kg, crop)
        for q_name, q_kg in QUANTITIES.items()
        for crop in CROPS
        for p_name, p_ids in POOLS.items()
    ]
    if full:
        return combos[:MAX_RUNS]
    p_name = "balanced_greens_browns"
    return [(p_name, POOLS[p_name], "med_3_5_kg", QUANTITIES["med_3_5_kg"], "tomato")]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Offline recipe quality stress sweep.")
    parser.add_argument("--full", action="store_true", help="run full 36-run matrix")
    args = parser.parse_args(argv)
    random.seed(SEED)

    combos = build_matrix(args.full)
    runs: list[dict] = []
    for pool_name, pool, qty_name, qty_kg, crop in combos:
        entry = _run_one(pool_name, pool, qty_name, qty_kg, crop)
        runs.append(entry)
        tag = entry["status"]
        extra = " ".join(entry["fail_reasons"] + entry["warnings"])
        print(f"{tag} pool={pool_name} qty={qty_name} crop={crop}" + (f" {extra}" if extra else ""))

    out_path = REPO_ROOT / "reports" / "sweep_results.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    n_pass = sum(1 for r in runs if r["status"] == "PASS")
    n_warn = sum(1 for r in runs if r["status"] == "WARN")
    n_fail = sum(1 for r in runs if r["status"] == "FAIL")
    payload = {
        "seed": SEED,
        "n_runs": len(runs),
        "n_pass": n_pass,
        "n_warn": n_warn,
        "n_fail": n_fail,
        "pass_or_warn_rate": round((n_pass + n_warn) / max(1, len(runs)), 4),
        "runs": runs,
    }
    out_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    print(f"wrote {out_path} runs={len(runs)} pass={n_pass} warn={n_warn} fail={n_fail}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
