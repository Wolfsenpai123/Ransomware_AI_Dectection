from pathlib import Path
import json
import pandas as pd


REGISTRY = Path("data/raw/dataset_registry.json")
OUT = Path("reports/datasets/dataset_inventory.csv")
OUT.parent.mkdir(parents=True, exist_ok=True)


EXTENSIONS = [
    ".csv", ".json", ".jsonl", ".parquet", ".txt", ".md",
    ".xlsx", ".pkl", ".joblib", ".npy", ".npz", ".arff",
    ".log", ".zip"
]


def scan_dataset(dataset: dict) -> dict:
    root = Path(dataset["path"])

    row = {
        "dataset": dataset.get("name", ""),
        "path": dataset.get("path", ""),
        "type": dataset.get("type", ""),
        "priority": dataset.get("priority", ""),
        "status": dataset.get("status", ""),
        "exists": root.exists(),
        "file_count": 0,
        "total_size_mb": 0.0,
        "sample_files": ""
    }

    for ext in EXTENSIONS:
        row[f"{ext.replace('.', '')}_count"] = 0

    if not root.exists():
        return row

    files = [p for p in root.rglob("*") if p.is_file()]
    row["file_count"] = len(files)
    row["total_size_mb"] = round(
        sum(p.stat().st_size for p in files) / (1024 * 1024),
        2
    )

    for p in files:
        ext = p.suffix.lower()
        if ext in EXTENSIONS:
            row[f"{ext.replace('.', '')}_count"] += 1

    sample_files = []
    for p in files[:10]:
        try:
            sample_files.append(str(p.relative_to(root)))
        except ValueError:
            sample_files.append(str(p))

    row["sample_files"] = " | ".join(sample_files)
    return row


def main():
    if not REGISTRY.exists():
        raise SystemExit(f"[!] Registry not found: {REGISTRY}")

    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    rows = [scan_dataset(d) for d in registry.get("datasets", [])]

    df = pd.DataFrame(rows)
    df.to_csv(OUT, index=False)

    show_cols = [
        "dataset", "exists", "file_count", "total_size_mb",
        "csv_count", "json_count", "zip_count", "status"
    ]

    existing_show_cols = [c for c in show_cols if c in df.columns]
    print(df[existing_show_cols].to_string(index=False))
    print(f"\n[+] Inventory saved to {OUT}")


if __name__ == "__main__":
    main()
