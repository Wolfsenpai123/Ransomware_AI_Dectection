from pathlib import Path
import shutil

SRC = Path("data/raw/ransmap")
DST = Path("data/raw/ransmap_selected")

BASE = Path("dataset/extra/i5-gen12/ddr4-2133-16g")

APPS = {
    "AESCrypt": 3,
    "Conti": 3,
    "Darkside": 3,
    "Firefox": 3,
}

KEEP_FILES = {
    "ata_read.csv",
    "ata_write.csv",
    "ata_write.zip",
    "mem_exec.csv",
    "mem_read.csv",
    "mem_readwrite.csv",
    "mem_write.csv",
}

def copy_readme():
    readme = SRC / "README.md"
    if readme.exists():
        DST.mkdir(parents=True, exist_ok=True)
        shutil.copy2(readme, DST / "README.md")

def main():
    if not SRC.exists():
        raise SystemExit(f"Source not found: {SRC}")

    if DST.exists():
        shutil.rmtree(DST)

    copy_readme()

    total = 0

    for app, max_runs in APPS.items():
        app_dir = SRC / BASE / app
        if not app_dir.exists():
            print(f"[!] Missing app folder: {app_dir}")
            continue

        runs = sorted([p for p in app_dir.iterdir() if p.is_dir()])[:max_runs]

        for run in runs:
            for fname in KEEP_FILES:
                src_file = run / fname
                if src_file.exists():
                    rel = src_file.relative_to(SRC)
                    dst_file = DST / rel
                    dst_file.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src_file, dst_file)
                    total += 1

    print(f"[+] Copied {total} files")
    print(f"[+] Selected subset saved to: {DST}")

if __name__ == "__main__":
    main()
