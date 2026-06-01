def recommend_response(symptoms: dict, unknown_risk: str = "low") -> dict:
    active = {k: v for k, v in symptoms.items() if float(v) >= 0.7}

    actions = []
    severity = "Low"
    policy = "monitor_only"

    if "file_write_burst" in active and "high_entropy_write" in active:
        actions += [
            "Create emergency backup of protected folders",
            "Temporarily block write access to protected folders",
            "Collect file activity evidence"
        ]
        severity = "High"
        policy = "isolate_and_backup"

    if "file_rename_burst" in active:
        actions += [
            "Enable protected folder read-only mode",
            "Alert analyst about mass rename behavior"
        ]
        severity = "High"
        policy = "isolate_and_backup"

    if "shadow_copy_delete_attempt" in active or "backup_disable_attempt" in active:
        actions += [
            "Block destructive system action",
            "Raise incident severity to Critical",
            "Recommend endpoint isolation"
        ]
        severity = "Critical"
        policy = "protective_lockdown"

    if "c2_beaconing" in active or "data_exfiltration_pattern" in active:
        actions += [
            "Block suspicious outbound connection",
            "Recommend network isolation",
            "Preserve network evidence"
        ]
        severity = "Critical"
        policy = "protective_lockdown"

    if unknown_risk == "high":
        actions += [
            "Unknown high-risk behavior detected",
            "Trigger emergency backup",
            "Lock protected files temporarily",
            "Move case to analyst review queue",
            "Store unknown behavior for future retraining"
        ]
        severity = "Critical"
        policy = "protective_lockdown"

    if not actions:
        actions = [
            "Continue monitoring",
            "Collect more telemetry"
        ]

    return {
        "severity": severity,
        "policy": policy,
        "active_symptoms": list(active.keys()),
        "recommended_actions": actions
    }
