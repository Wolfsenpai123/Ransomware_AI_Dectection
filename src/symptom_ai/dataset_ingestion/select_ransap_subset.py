from pathlib import Path
import shutil

SRC = Path("data/raw/ransap")
DST = Path("data/raw/ransap_selected")

BASE = Path("dataset/extra/win2008r2-250gb-ssd")

# Ưu tiên ransomware: 5 runs/family
# Benign đối chứng: 2 runs/app
APPS = {
    "AESCrypt": 5,
    "Cerber-w10dirs": 5,
    "Darkside-w10dirs": 5,
    "GandCrab4-w10dirs": 5,
    "Ryuk-w10dirs": 5,
    "Sodinokibi-w10dirs": 5,
    "TeslaCrypt-w10dirs": 5,
    "WannaCry-w10dirs": 5,

    "Firefox": 2,
    "Excel": 2,
    "Zip": 2,
}

KEEP_FILES = {
    "ata_read.csv",
    "ata_write.csv",
    "ata_read.zip",
    "ata_write.zip",
}

def copy_file(src_file: Path):
    rel = src_file.relative_to(SRC)
    dst_file = DST / rel
    dst_file.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src_file, dst_file)

def main():
    if not SRC.exists():
        raise SystemExit(f"[!] Missing source: {SRC}")

    if DST.exists():
        shutil.rmtree(DST)

    readme = SRC / "README.md"
    if readme.exists():
        DST.mkdir(parents=True, exist_ok=True)
        shutil.copy2(readme, DST / "README.md")

    total = 0

    for app, max_runs in APPS.items():
        app_dir = SRC / BASE / app
        if not app_dir.exists():
            print(f"[!] Missing app folder: {app_dir}")
            continue

        runs = sorted([p for p in app_dir.iterdir() if p.is_dir()])[:max_runs]
        print(f"[+] {app}: selecting {len(runs)} runs")

        for run in runs:
            for fname in KEEP_FILES:
                src_file = run / fname
                if src_file.exists():
                    copy_file(src_file)
                    total += 1

    print(f"\n[+] Copied {total} files")
    print(f"[+] Output: {DST}")

if __name__ == "__main__":
    main()
