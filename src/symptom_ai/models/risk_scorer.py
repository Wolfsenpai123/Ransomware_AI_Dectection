HIGH_WEIGHT_SYMPTOMS = {
    "file_write_burst": 0.15,
    "file_rename_burst": 0.15,
    "high_entropy_write": 0.18,
    "mass_file_modification": 0.12,
    "suspicious_extension_change": 0.10,
    "ransom_note_created": 0.15,
    "shadow_copy_delete_attempt": 0.20,
    "backup_disable_attempt": 0.20,
    "c2_beaconing": 0.12,
    "data_exfiltration_pattern": 0.15
}


def calculate_symptom_risk(symptoms: dict) -> float:
    score = 0.0
    max_score = 0.0

    for symptom, weight in HIGH_WEIGHT_SYMPTOMS.items():
        value = float(symptoms.get(symptom, 0.0))
        score += value * weight
        max_score += weight

    if max_score == 0:
        return 0.0

    normalized = score / max_score
    return round(min(max(normalized, 0.0), 1.0), 4)
