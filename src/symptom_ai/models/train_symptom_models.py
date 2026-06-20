from pathlib import Path
import json
import joblib
import pandas as pd
import numpy as np

from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score

from xgboost import XGBClassifier


DATASET = Path("data/symptom_labels/unified_symptom_dataset.csv")
MODEL_DIR = Path("models")
REPORT_DIR = Path("reports/symptom_ai")

MODEL_DIR.mkdir(parents=True, exist_ok=True)
REPORT_DIR.mkdir(parents=True, exist_ok=True)

NON_FEATURE_COLS = {
    "sample_id",
    "dataset_source",
    "family",
    "behavior_type",
    "collection_type",
    "platform",
    "is_simulated",
    "is_real_malware_executed",
    "label",
    "response_policy",
}

MAX_TRAIN_ROWS = 300000
MAX_ISOLATION_ROWS = 100000


def balanced_sample(df: pd.DataFrame, max_rows: int) -> pd.DataFrame:
    if len(df) <= max_rows:
        return df

    labels = sorted(df["label"].unique())
    per_label = max_rows // len(labels)

    sampled = []
    for label in labels:
        part = df[df["label"] == label]
        n = min(len(part), per_label)
        sampled.append(part.sample(n=n, random_state=42))

    result = pd.concat(sampled, ignore_index=True)
    return result.sample(frac=1, random_state=42).reset_index(drop=True)


def evaluate_model(name, model, X_test, y_test, labels):
    y_pred = model.predict(X_test)

    acc = accuracy_score(y_test, y_pred)
    report_text = classification_report(y_test, y_pred)
    report_dict = classification_report(y_test, y_pred, output_dict=True)
    cm = confusion_matrix(y_test, y_pred, labels=labels)

    print(f"\n===== {name} =====")
    print(f"[+] Accuracy: {acc:.4f}")
    print(report_text)

    return {
        "accuracy": float(acc),
        "classification_report": report_dict,
        "confusion_matrix_labels": labels,
        "confusion_matrix": cm.tolist(),
    }


def main():
    if not DATASET.exists():
        raise SystemExit(f"[!] Missing dataset: {DATASET}")

    print(f"[+] Loading dataset: {DATASET}")
    df = pd.read_csv(DATASET)

    print(f"[+] Original dataset shape: {df.shape}")
    print("\nOriginal label counts:")
    print(df["label"].value_counts().to_string())

    df = balanced_sample(df, MAX_TRAIN_ROWS)

    print(f"\n[+] Training dataset shape: {df.shape}")
    print("\nTraining label counts:")
    print(df["label"].value_counts().to_string())

    feature_cols = [
        c for c in df.columns
        if c not in NON_FEATURE_COLS
        and pd.api.types.is_numeric_dtype(df[c])
    ]

    print(f"\n[+] Feature columns: {len(feature_cols)}")

    X = df[feature_cols].fillna(0)
    y_text = df["label"].astype(str)

    labels = sorted(y_text.unique())
    label_to_id = {label: i for i, label in enumerate(labels)}
    id_to_label = {i: label for label, i in label_to_id.items()}

    y = y_text.map(label_to_id).astype(int)

    X_train, X_test, y_train, y_test, y_text_train, y_text_test = train_test_split(
        X,
        y,
        y_text,
        test_size=0.2,
        random_state=42,
        stratify=y_text
    )

    print("\n[+] Training RandomForest classifier...")
    rf = RandomForestClassifier(
        n_estimators=150,
        max_depth=22,
        random_state=42,
        n_jobs=-1,
        class_weight="balanced"
    )
    rf.fit(X_train, y_text_train)

    rf_result = evaluate_model(
        "RandomForestClassifier",
        rf,
        X_test,
        y_text_test,
        labels
    )

    print("\n[+] Training XGBoost classifier...")
    xgb = XGBClassifier(
        n_estimators=250,
        max_depth=7,
        learning_rate=0.08,
        subsample=0.85,
        colsample_bytree=0.85,
        objective="binary:logistic" if len(labels) == 2 else "multi:softprob",
        eval_metric="logloss" if len(labels) == 2 else "mlogloss",
        tree_method="hist",
        random_state=42,
        n_jobs=-1
    )
    xgb.fit(X_train, y_train)

    y_xgb_pred_id = xgb.predict(X_test)
    y_xgb_pred_text = pd.Series(y_xgb_pred_id).map(id_to_label).values

    xgb_acc = accuracy_score(y_text_test, y_xgb_pred_text)
    xgb_report_text = classification_report(y_text_test, y_xgb_pred_text)
    xgb_report_dict = classification_report(y_text_test, y_xgb_pred_text, output_dict=True)
    xgb_cm = confusion_matrix(y_text_test, y_xgb_pred_text, labels=labels)

    print("\n===== XGBoostClassifier =====")
    print(f"[+] Accuracy: {xgb_acc:.4f}")
    print(xgb_report_text)

    xgb_result = {
        "accuracy": float(xgb_acc),
        "classification_report": xgb_report_dict,
        "confusion_matrix_labels": labels,
        "confusion_matrix": xgb_cm.tolist(),
    }

    print("\n[+] Training IsolationForest unknown detector...")
    iso_train = X_train
    if len(iso_train) > MAX_ISOLATION_ROWS:
        iso_train = iso_train.sample(n=MAX_ISOLATION_ROWS, random_state=42)

    iso = IsolationForest(
        n_estimators=150,
        contamination=0.05,
        random_state=42,
        n_jobs=-1
    )
    iso.fit(iso_train)

    # Choose primary model by validation accuracy
    primary_classifier = "xgboost_classifier.joblib" if xgb_acc >= rf_result["accuracy"] else "random_forest_classifier.joblib"

    metadata = {
        "dataset": str(DATASET),
        "training_rows": int(len(df)),
        "feature_count": int(len(feature_cols)),
        "feature_columns": feature_cols,
        "labels": labels,
        "label_to_id": label_to_id,
        "id_to_label": {str(k): v for k, v in id_to_label.items()},
        "models": {
            "random_forest": "RandomForestClassifier",
            "xgboost": "XGBClassifier",
            "unknown_detector": "IsolationForest"
        },
        "primary_classifier": primary_classifier,
        "lstm_status": "optional_future_work_for_api_sequence_or_time_series_data"
    }

    joblib.dump(rf, MODEL_DIR / "random_forest_classifier.joblib")
    joblib.dump(xgb, MODEL_DIR / "xgboost_classifier.joblib")
    joblib.dump(iso, MODEL_DIR / "unknown_behavior_detector.joblib")

    # Backward compatible filename for current API.
    if primary_classifier == "xgboost_classifier.joblib":
        joblib.dump(xgb, MODEL_DIR / "ransomware_symptom_classifier.joblib")
    else:
        joblib.dump(rf, MODEL_DIR / "ransomware_symptom_classifier.joblib")

    with open(MODEL_DIR / "model_metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    report = {
        "dataset": str(DATASET),
        "training_rows": int(len(df)),
        "feature_count": int(len(feature_cols)),
        "labels": labels,
        "random_forest": rf_result,
        "xgboost": xgb_result,
        "primary_classifier": primary_classifier,
        "unknown_detector": {
            "model": "IsolationForest",
            "training_rows": int(len(iso_train)),
            "contamination": 0.05
        }
    }

    with open(REPORT_DIR / "training_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print("\n[+] Saved models:")
    print(f"    {MODEL_DIR / 'random_forest_classifier.joblib'}")
    print(f"    {MODEL_DIR / 'xgboost_classifier.joblib'}")
    print(f"    {MODEL_DIR / 'unknown_behavior_detector.joblib'}")
    print(f"    {MODEL_DIR / 'ransomware_symptom_classifier.joblib'}")
    print(f"    {MODEL_DIR / 'model_metadata.json'}")
    print(f"[+] Training report: {REPORT_DIR / 'training_report.json'}")
    print(f"[+] Primary classifier: {primary_classifier}")


if __name__ == "__main__":
    main()
