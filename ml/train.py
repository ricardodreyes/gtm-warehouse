#!/usr/bin/env python3
"""Fit XGBoost on mart_ml_training_set and append one line to ml/runs.jsonl.

Out-of-sample AUC needs enough positives to hold some out. Below MIN_POSITIVES the run
still fits the model, but logs auc as null and says why.
"""
import csv
import datetime as dt
import json
import pathlib
import subprocess

import numpy as np
import xgboost as xgb

ROOT = pathlib.Path(__file__).resolve().parents[1]
DB = ROOT / "warehouse" / "gtm.duckdb"
RUNS = ROOT / "ml" / "runs.jsonl"
MIN_POSITIVES = 5
FOLDS = 5

CATEGORICAL = ["campaign_id", "tier", "email_confidence", "verify_result", "mailbox_role"]
NUMERIC = ["declares_protected_customer_data", "has_ai_signal", "rating", "review_count",
           "launched_year", "category_count", "bounced"]


def load():
    out = subprocess.run(
        ["duckdb", str(DB), "-readonly", "-csv", "-c", "select * from mart_ml_training_set order by slug"],
        capture_output=True, text=True, check=True,
    ).stdout
    return list(csv.DictReader(out.splitlines()))


def to_number(v):
    if v in ("", "NULL", None):
        return np.nan
    if v == "true":
        return 1.0
    if v == "false":
        return 0.0
    return float(v)


def matrix(rows):
    codes = {c: {v: i for i, v in enumerate(sorted({r[c] for r in rows}))} for c in CATEGORICAL}
    x = np.array([[codes[c][r[c]] for c in CATEGORICAL] + [to_number(r[c]) for c in NUMERIC] for r in rows])
    y = np.array([1 if r["replied"] == "true" else 0 for r in rows])
    return x, y


def auc(y, p):
    pos, neg = p[y == 1], p[y == 0]
    if len(pos) == 0 or len(neg) == 0:
        return None
    wins = (pos[:, None] > neg[None, :]).sum() + 0.5 * (pos[:, None] == neg[None, :]).sum()
    return float(wins / (len(pos) * len(neg)))


def fit(x, y):
    params = {"objective": "binary:logistic", "max_depth": 3, "eta": 0.1, "seed": 0}
    return xgb.train(params, xgb.DMatrix(x, label=y), num_boost_round=100)


def predict(booster, x):
    return booster.predict(xgb.DMatrix(x))


def cross_val_auc(x, y):
    rng = np.random.default_rng(0)
    pred = np.zeros(len(y))
    for label in (0, 1):
        idx = rng.permutation(np.where(y == label)[0])
        for k, chunk in enumerate(np.array_split(idx, FOLDS)):
            pred[chunk] = -1 - k
    for k in range(FOLDS):
        test = pred == -1 - k
        pred[test] = predict(fit(x[~test], y[~test]), x[test])
    return auc(y, pred)


def main():
    rows = load()
    x, y = matrix(rows)
    n_pos = int(y.sum())
    in_sample = auc(y, predict(fit(x, y), x))
    if n_pos >= MIN_POSITIVES and len(y) - n_pos >= MIN_POSITIVES:
        cv = cross_val_auc(x, y)
        note = f"{FOLDS}-fold stratified cross-validation"
    else:
        cv = None
        note = (f"{n_pos} positive in {len(y)} rows: no held-out fold can contain a positive, "
                f"so no out-of-sample AUC exists. Needs {MIN_POSITIVES} replies.")
    run = {
        "ran_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "rows": len(y),
        "positives": n_pos,
        "features": CATEGORICAL + NUMERIC,
        "auc": cv,
        "in_sample_auc": in_sample,
        "note": note,
    }
    with RUNS.open("a") as fh:
        fh.write(json.dumps(run) + "\n")
    print(json.dumps(run, indent=1))


if __name__ == "__main__":
    main()
