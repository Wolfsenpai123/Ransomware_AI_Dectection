SYMPTOM_LABELS = [
    "file_write_burst",
    "file_rename_burst",
    "high_entropy_write",
    "mass_file_modification",
    "suspicious_extension_change",
    "ransom_note_created",

    "backup_disable_attempt",
    "shadow_copy_delete_attempt",
    "security_tool_tamper",
    "persistence_attempt",
    "privilege_escalation_attempt",

    "c2_beaconing",
    "suspicious_dns",
    "tor_or_proxy_usage",
    "network_share_scan",
    "data_exfiltration_pattern",

    "packed_binary",
    "crypto_api_usage",
    "file_api_usage",
    "anti_analysis",
    "suspicious_string"
]

RESPONSE_POLICIES = {
    "benign": "monitor_only",
    "known_ransomware_like": "isolate_and_backup",
    "partial_match": "warn_and_snapshot",
    "unknown_low_risk": "monitor_and_collect_more",
    "unknown_high_risk": "protective_lockdown"
}
