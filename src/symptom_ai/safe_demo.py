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
        f.write_text(f"Important safe demo document {i}\n", encoding="utf-8")


def simulate_safe_ransomware_like_symptoms():
    for i in range(80):
        p = WATCH / f"demo_doc_{i}.bin"
        p.write_bytes(os.urandom(4096))

    for i in range(20):
        old = WATCH / f"demo_doc_{i}.bin"
        new = WATCH / f"demo_doc_{i}.locked_demo"
        if old.exists():
            old.rename(new)


def build_demo_symptoms():
    """
    In the next phase, this will be replaced by real feature extraction.
    For MVP, we simulate the symptom classifier output.
    """
    return {
        "file_write_burst": 0.95,
        "file_rename_burst": 0.91,
        "high_entropy_write": 0.93,
        "mass_file_modification": 0.88,
        "suspicious_extension_change": 0.86,
        "ransom_note_created": 0.10,
        "backup_disable_attempt": 0.00,
        "shadow_copy_delete_attempt": 0.00,
        "c2_beaconing": 0.00,
        "data_exfiltration_pattern": 0.00
    }


def main():
    reset_lab_folders()
    prepare_protected_docs()
    simulate_safe_ransomware_like_symptoms()

    symptoms = build_demo_symptoms()
    risk_score = calculate_symptom_risk(symptoms)

    similarity = match_known_profile(symptoms)
    best_similarity = similarity["best_match"]["similarity"]

    unknown = detect_unknown_risk(
        best_similarity=best_similarity,
        symptom_risk_score=risk_score
    )

    response = recommend_response(
        symptoms=symptoms,
        unknown_risk=unknown["unknown_risk"]
    )

    case = {
        "timestamp": datetime.now().isoformat(),
        "demo_type": "safe_ransomware_like_symptom_simulation",
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

    out = REPORTS / "safe_demo_result.json"
    out.write_text(json.dumps(case, indent=2), encoding="utf-8")

    print(json.dumps(case, indent=2))


if __name__ == "__main__":
    main()
