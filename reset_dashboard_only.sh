#!/usr/bin/env bash
set -e

rm -f data/custom_sandbox/control/STOP_SIGNAL.json
rm -f reports/live_monitoring/current_status.json

mkdir -p reports/live_monitoring

cat > reports/live_monitoring/current_status.json <<'JSON'
{
  "window_id": "clean_dashboard_only",
  "time": "clean_dashboard_only",
  "alert_type": "monitor",
  "predicted_label": "benign",
  "risk_score": 0.0,
  "unknown_risk": "low",
  "severity": "Low",
  "policy": "monitor_only",
  "spread_report": {
    "spread_scope": {
      "host_count": 0,
      "hosts": [],
      "unique_path_count": 0,
      "impacted_directory_count": 0,
      "high_impact_event_count": 0
    },
    "host_event_counts": {},
    "top_touched_paths": [],
    "impacted_directories": [],
    "high_impact_paths": []
  },
  "damage": {
    "event_count": 0,
    "host_count": 0,
    "hosts": [],
    "unique_path_count": 0,
    "high_impact_event_count": 0,
    "event_type_counts": {},
    "has_file_impact": false
  },
  "recommended_actions": ["Continue monitoring"],
  "remediation_actions": ["Continue monitoring"],
  "dataset_evidence": {
    "status": "not_requested",
    "top_matches": []
  },
  "symptoms": {},
  "learning_case_file": null,
  "learned_signature_file": null,
  "learned_match": null,
  "error_case_file": null,
  "stop_signal_file": null,
  "api_error": null
}
JSON

echo "[+] Dashboard reset only. Event log and learned signatures were NOT deleted."
