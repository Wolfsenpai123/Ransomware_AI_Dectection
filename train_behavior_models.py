import os
import joblib
import pandas as pd
import numpy as np

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.metrics import precision_score, recall_score, f1_score, classification_report, confusion_matrix
from xgboost import XGBClassifier 

INPUT = "data/processed/behavior/behavior_features.csv"
METRICS_OUT = "reports/behavior_metrics.csv"
SCORED_OUT = "reports/behavior_scored_windows"

os.makedirs("models", exist_ok=True)
os.makedirs("reports", exist_ok=True)

df = pd.read_csv(INPUT)
df["y"] = (df["label"] == "ransomware").astype(int)

drop_cols = ["window_id", "first_event_index", "last_event_index", "label", "family", "y"]
feature_cols = [c for c in df.columns if c not in drop_cols]

X = df[feature_cols].fillna(0)
y = df["y"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

results = []

def fpr_from_cm(y_true, y_pred):
    cm = confusion_matrix(y_true, y_pred, labels=[0, 1])
    tn, fp, fn, tp = cm.ravel()
    return fp / max(fp + tn, 1)

def evaluate(name, model, y_pred):
    results.append({
        "model": name,
        "precision": precision_score(y_test, y_pred, zero_division=0),
        "recall": recall_score(y_test, y_pred, zero_division=0),
        "f1": f1_score(y_test, y_pred, zero_division=0),
        "false_positive_rate": fpr_from_cm(y_test, y_pred)
    })

rf = RandomForestClassifier(n_estimators=100, random_state=42)
rf.fit(X_train, y_train)
rf_pred = rf.predict(X_test)
evaluate("Random Forest", rf, rf_pred)
joblib.dump({"model": rf, "feature_cols": feature_cols}, "models/random_forest_behavior.joblib")

xgb = XGBClassifier(
    n_estimators=200, max_depth=4, learning_rate=0.05, random_state=42, subsample=0.9, eval_metric="logloss", colsample_bytree=0.9
)
xgb.fit(X_train, y_train)
xgb_pred = xgb.predict(X_test)
evaluate("XGBoost", xgb, xgb_pred)
joblib.dump({"model": xgb, "feature_cols": feature_cols}, "models/xgboost_behavior.joblib")

benign_train = X_train[y_train == 0]
iso = IsolationForest(n_estimators=200, contamination=0.20, random_state=42)
iso.fit(benign_train)
iso_raw = iso.predict(X_test)
iso_pred = (iso_raw == -1).astype(int)
evaluate("Isolation Forest", iso, iso_pred)
joblib.dump({"model": iso, "feature_cols": feature_cols}, "models/isolation_forest_behavior.joblib")

metrics = pd.DataFrame(results)
metrics.to_csv(METRICS_OUT, index = False)

# Score all windows with RF, XGB, IF
scored = df.copy()
scored["rf_score"] = rf.predict_proba(X)[:, 1]
scored["rf_pred"] = rf.predict(X)
scored["xgb_pred"] = xgb.predict(X)
scored["xgb_score"] = xgb.predict_proba(X)[:, 1]
scored["iso_pred"] = (iso.predict(X) == -1).astype(int)
scored["iso_score"] = -iso.decision_function(X)

# Detection lead events using RF
ransom_start_rows = scored[scored["y"] == 1]
lead_events = None

if len(ransom_start_rows) > 0:
    start_idx = ransom_start_rows["first_event_index"].min()
    after_start = scored[scored["first_event_index"] >= start_idx].copy()
    after_start["cum_affected"] = after_start["affected_file_events"].cumsum()

    critical = after_start[after_start["cum_affected"] >= 50]
    alert = after_start[after_start["rf_pred"] == 1]

    if len(critical) > 0 and len(alert) > 0:
        critical_event = int(critical.iloc[0]["first_event_index"])
        alert_event = int(alert.iloc[0]["first_event_index"])
        lead_events = critical_event - alert_event

scored["rf_detection_lead_events"] = lead_events if lead_events is not None else np.nan
scored.to_csv(SCORED_OUT, index=False)

print("[+] Metrics: ")
print(metrics)
print()
print("[+] Detection lead events:", lead_events)
print("[+] Saved:", METRICS_OUT)
print("[+} Saved:", SCORED_OUT)
