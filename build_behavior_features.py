import pandas as pd
import numpy as np

INPUT = "data/raw/behavior/safe_behavior.csv"
OUTPUT = "data/processed/behavior/behavior_features.csv"
WINDOW_SIZE = 50

df = pd.read_csv(INPUT)
df["timestamp"] = pd.to_datetime(df["timestamp"])
df = df.sort_values("event_index").reset_index(drop=True)
df["window_id"] = df["event_index"] // WINDOW_SIZE

rows = []

for window_id, g in df.groupby("window_id"):
    row = {
        "window_id": int(window_id),
        "first_event_index": int(g["event_index"].min()),
        "last_event_index": int(g["event_index"].max()),
        "event_count": len(g),
        "file_read_count": int((g["event_type"] == "file_read").sum()),
        "file_write_count": int((g["event_type"] == "file_write").sum()),
        "file_rename_count": int((g["event_type"] == "file_rename").sum()),
        "file_delete_count": int((g["event_type"] == "file_delete").sum()),
        "registry_set_count": int((g["event_type"] == "registry_set").sum()),
        "process_create_count": int((g["event_type"] == "process_create").sum()),
        "service_stop_count": int((g["event_type"] == "service_stop").sum()),
        "shadow_copy_delete_count": int((g["event_type"] == "shadow_copy_delete").sum()),
        "dns_query_count": int((g["event_type"] == "dns_query").sum()),
        "network_connect_count": int((g["event_type"] == "network_connect").sum()),
        "unique_object_count": int(g["object"].nunique()),
        "unique_process_count": int(g["process_name"].nunique()),
        "total_bytes_written": int(g["bytes_written"].fillna(0).sum()),
        "avg_entropy_before": float(g["entropy_before"].fillna(0).mean()),
        "avg_entropy_after": float(g["entropy_after"].fillna(0).mean()),
        "entropy_delta": float((g["entropy_after"].fillna(0) - g["entropy_before"].fillna(0)).clip(lower=0).mean()),
        "affected_file_events": int(g["event_type"].isin(["file_write", "file_rename", "file_delete"]).sum()),
        "label": "ransomware" if (g["label"] == "ransomware").any() else "benign",
        "family": "SimRansom" if (g["family"] == "SimRansom").any() else "benign"
    }

    row["rename_burst_score"] = row["file_rename_count"] / max(row["event_count"], 1)
    row["write_burst_score"] = row["file_write_count"] / max(row["event_count"], 1)
    row["high_entropy_flag"] = 1 if row["entropy_delta"] > 2.0 else 0

    rows.append(row)

features = pd.DataFrame(rows)
features.to_csv(OUTPUT, index=False)

print("[+] Created", OUTPUT)
print(features.shape)
print(features["label"].value_counts())
print(features.head())