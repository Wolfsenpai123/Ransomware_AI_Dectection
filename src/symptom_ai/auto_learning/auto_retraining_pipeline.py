from pathlib import Path
from datetime import datetime
import json
import shutil
import subprocess
import sys

import pandas as pd


BASE_DATASET = Path("data/symptom_labels/unified_symptom_dataset.csv")
QUEUE_DIR = Path("data/learning_queue")
AUGMENTED_DATASET = Path("data/symptom_labels/unified_symptom_dataset_auto_augmented.csv")
MODEL_DIR = Path("models")
VERSIONS_DIR = Path("models/versions")
REPORT_DIR = Path("reports/auto_learning")

NON_FEATURE_META = {
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


def stamp():
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def load_learning_cases():
    cases = []

    for p in sorted(QUEUE_DIR.glob("*.json")):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            data["_case_file"] = str(p)
            cases.append(data)
        except Exception as e:
            print(f"[!] Skip {p}: {e}")

    return cases


def cases_to_dataframe(cases, base_columns):
    rows = []

    for i, case in enumerate(cases):
        symptoms = case.get("symptoms", {})

        row = {c: 0.0 for c in base_columns}

        row["sample_id"] = f"auto_learning_{stamp()}_{i}"
        row["dataset_source"] = "AutoLearning_UnknownCases"
        row["family"] = case.get("family", "unknown_ransomware_candidate")
        row["behavior_type"] = "live_sandbox_unknown_behavior"
        row["collection_type"] = "live_log_watcher"
        row["platform"] = "windows"
        row["is_simulated"] = 1
        row["is_real_malware_executed"] = 0
        row["label"] = case.get("label", "known_ransomware_like")
        row["response_policy"] = case.get("response_policy", "protective_lockdown")

        for k, v in symptoms.items():
            if k in row:
                try:
                    row[k] = float(v)
                except Exception:
                    row[k] = 0.0

        if "retraining_candidate" in row:
            row["retraining_candidate"] = 1.0
        if "analyst_review_required" in row:
            row["analyst_review_required"] = 1.0
        if "unknown_high_risk" in row:
            row["unknown_high_risk"] = max(float(row.get("unknown_high_risk", 0.0)), 0.9)

        rows.append(row)

    return pd.DataFrame(rows)


def archive_current_models(version_name):
    version_dir = VERSIONS_DIR / version_name
    version_dir.mkdir(parents=True, exist_ok=True)

    for p in MODEL_DIR.glob("*.joblib"):
        shutil.copy2(p, version_dir / p.name)

    meta = MODEL_DIR / "model_metadata.json"
    if meta.exists():
        shutil.copy2(meta, version_dir / meta.name)

    return version_dir


def main():
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    VERSIONS_DIR.mkdir(parents=True, exist_ok=True)

    if not BASE_DATASET.exists():
        raise SystemExit(f"[!] Missing base dataset: {BASE_DATASET}")

    cases = load_learning_cases()

    print(f"[+] Learning cases found: {len(cases)}")

    if not cases:
        print("[+] No learning cases. Nothing to retrain.")
        return

    base = pd.read_csv(BASE_DATASET)
    new_rows = cases_to_dataframe(cases, list(base.columns))

    print(f"[+] Base dataset rows: {len(base)}")
    print(f"[+] New auto-learning rows: {len(new_rows)}")

    final = pd.concat([base, new_rows], ignore_index=True)
    final.to_csv(AUGMENTED_DATASET, index=False)

    print(f"[+] Augmented dataset saved: {AUGMENTED_DATASET}")
    print(f"[+] Augmented rows: {len(final)}")

    version_name = f"before_auto_retrain_{stamp()}"
    version_dir = archive_current_models(version_name)
    print(f"[+] Current models archived to: {version_dir}")

    # Replace training dataset temporarily by backing up original and copying augmented.
    backup = BASE_DATASET.with_suffix(".before_auto_retrain.csv")
    shutil.copy2(BASE_DATASET, backup)
    shutil.copy2(AUGMENTED_DATASET, BASE_DATASET)

    print("[+] Running training script...")
    cmd = [
        sys.executable,
        "src/symptom_ai/models/train_symptom_models.py"
    ]

    result = subprocess.run(
        cmd,
        env={**dict(), "PYTHONPATH": "src"},
        capture_output=True,
        text=True
    )

    train_log = REPORT_DIR / f"auto_retrain_log_{stamp()}.txt"
    train_log.write_text(
        result.stdout + "\n\nSTDERR:\n" + result.stderr,
        encoding="utf-8"
    )

    if result.returncode != 0:
        print("[!] Auto retraining failed. Restoring original dataset.")
        shutil.copy2(backup, BASE_DATASET)
        print(f"[!] Train log: {train_log}")
        raise SystemExit(result.returncode)

    # Keep augmented dataset as new base.
    print("[+] Auto retraining completed.")
    print(f"[+] Train log: {train_log}")

    summary = {
        "time": datetime.now().isoformat(timespec="seconds"),
        "learning_cases": len(cases),
        "augmented_dataset": str(AUGMENTED_DATASET),
        "backup_dataset": str(backup),
        "archived_previous_models": str(version_dir),
        "train_log": str(train_log),
        "status": "completed"
    }

    summary_path = REPORT_DIR / f"auto_retrain_summary_{stamp()}.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"[+] Summary saved: {summary_path}")


if __name__ == "__main__":
    main()
