from pathlib import Path
import os
import json
from datetime import datetime

from symptom_ai.models.risk_scorer import calculate_symptom_risk
from symptom_ai.models.unknown_detector import detect_unknown_risk
from symptom_ai.similarity.similarity_matcher import match_known_profile
from symptom_ai.response_engine.response_policy import recommend_response
from symptom_ai.response_engine.protective_lockdown import run_protective_lockdown


ROOT = Path(".")
WATCH = ROOT / "data/live_watch"
PROTECTED = ROOT / "data/protected_docs"
REPORTS = ROOT / "reports/symptom_ai"

for p in [WATCH, PROTECTED, REPORTS]:
    p.mkdir(parents=True, exist_ok=True)


def reset_lab_folders():
    for p in WATCH.glob("*"):
        if p.is_file():
            p.unlink()

    for p in PROTECTED.glob("*"):
        if p.is_file():
            p.chmod(0o644)
            p.unlink()


def prepare_protected_docs():
    for i in range(1, 4):
        f = PROTECTED / f"important_report_{i}.txt"
        f.write_text(f"Important protected document {i}\n", encoding="utf-8")


def simulate_unknown_high_risk_behavior():
    for i in range(40):
        p = WATCH / f"unknown_blob_{i}.tmp"
        p.write_bytes(os.urandom(2048))

    for i in range(5):
        old = WATCH / f"unknown_blob_{i}.tmp"
        new = WATCH / f"unknown_blob_{i}.weird_demo"
        if old.exists():
            old.rename(new)


def build_unknown_symptoms():
    return {
        "file_write_burst": 0.82,
        "file_rename_burst": 0.25,
        "high_entropy_write": 0.91,
        "mass_file_modification": 0.60,
        "suspicious_extension_change": 0.35,
        "ransom_note_created": 0.00,
        "backup_disable_attempt": 0.88,
        "shadow_copy_delete_attempt": 0.82,
        "c2_beaconing": 0.76,
        "data_exfiltration_pattern": 0.74
    }


def main():
    reset_lab_folders()
    prepare_protected_docs()
    simulate_unknown_high_risk_behavior()

    symptoms = build_unknown_symptoms()
    risk_score = calculate_symptom_risk(symptoms)

    similarity = match_known_profile(symptoms)
    best_similarity = similarity["best_match"]["similarity"]

    unknown = detect_unknown_risk(
        best_similarity=best_similarity,
        symptom_risk_score=risk_score
    )

    if (
        symptoms["backup_disable_attempt"] >= 0.7
        or symptoms["shadow_copy_delete_attempt"] >= 0.7
    ):
        unknown["unknown_risk"] = "high"

    response = recommend_response(
        symptoms=symptoms,
        unknown_risk=unknown["unknown_risk"]
    )

    case = {
        "timestamp": datetime.now().isoformat(),
        "demo_type": "unknown_high_risk_safe_simulation",
        "real_ransomware_executed": False,
        "symptoms": symptoms,
        "risk_score": risk_score,
        "similarity": similarity,
        "unknown_detection": unknown,
        "response": response
    }

    lockdown_result = None
    if response["policy"] == "protective_lockdown":
        lockdown_result = run_protective_lockdown(case)

    case["lockdown_result"] = lockdown_result

    out = REPORTS / "unknown_demo_result.json"
    out.write_text(json.dumps(case, indent=2), encoding="utf-8")

    print(json.dumps(case, indent=2))


if __name__ == "__main__":
    main()
