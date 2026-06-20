from pathlib import Path
import json
import pandas as pd

REGISTRY = Path("data/raw/dataset_registry.json")
OUT = Path("reports/datasets/dataset_file_details.csv")
OUT.parent.mkdir(parents=True, exist_ok=True)

INTERESTING_EXTS = {
    ".csv", ".json", ".jsonl", ".txt", ".md", ".zip",
    ".npy", ".npz", ".pkl", ".joblib", ".arff", ".log",
    ".xlsx", ".parquet"
}

SKIP_PARTS = {
    ".git",
    "__pycache__",
    ".idea",
    ".vscode"
}


def should_skip(path: Path) -> bool:
    return any(part in SKIP_PARTS for part in path.parts)


def inspect_file(path: Path, root: Path):
    row = {
        "relative_path": str(path.relative_to(root)),
        "suffix": path.suffix.lower(),
        "size_mb": round(path.stat().st_size / (1024 * 1024), 4),
        "preview_columns": "",
        "preview_shape": "",
        "read_error": ""
    }

    if path.suffix.lower() == ".csv":
        try:
            df = pd.read_csv(path, nrows=5)
            row["preview_columns"] = " | ".join(map(str, df.columns[:40]))
            row["preview_shape"] = f"sample_rows={len(df)}, cols={len(df.columns)}"
        except Exception as e:
            row["read_error"] = str(e)[:200]

    elif path.suffix.lower() in [".txt", ".md"]:
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
            lines = [line.strip() for line in text.splitlines() if line.strip()]
            row["preview_columns"] = " / ".join(lines[:3])[:300]
            row["preview_shape"] = f"lines~{len(lines)}"
        except Exception as e:
            row["read_error"] = str(e)[:200]

    return row


def main():
    if not REGISTRY.exists():
        raise SystemExit(f"[!] Registry not found: {REGISTRY}")

    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    rows = []

    for d in registry.get("datasets", []):
        root = Path(d["path"])
        if not root.exists():
            continue

        files = []
        for p in root.rglob("*"):
            if not p.is_file():
                continue
            if should_skip(p):
                continue
            if p.suffix.lower() not in INTERESTING_EXTS:
                continue
            files.append(p)

        files = sorted(files, key=lambda x: (x.suffix.lower(), str(x)))[:120]

        for p in files:
            r = inspect_file(p, root)
            r["dataset"] = d["name"]
            r["dataset_path"] = d["path"]
            rows.append(r)

    df = pd.DataFrame(rows)
    df.to_csv(OUT, index=False)

    if df.empty:
        print("[!] No interesting files found.")
        return

    for dataset in df["dataset"].unique():
        print(f"\n===== {dataset} =====")
        sub = df[df["dataset"] == dataset]
        print(
            sub[
                ["relative_path", "suffix", "size_mb", "preview_shape", "preview_columns"]
            ].head(40).to_string(index=False)
        )

    print(f"\n[+] Details saved to {OUT}")


if __name__ == "__main__":
    main()
