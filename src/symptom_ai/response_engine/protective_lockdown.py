from pathlib import Path
from datetime import datetime
import shutil
import json


def emergency_backup(protected_dir: str, backup_root: str) -> str:
    protected_path = Path(protected_dir)
    backup_path = Path(backup_root)
    backup_path.mkdir(parents=True, exist_ok=True)

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    current_backup = backup_path / f"backup_{stamp}"
    current_backup.mkdir(parents=True, exist_ok=True)

    if protected_path.exists():
        for item in protected_path.glob("*"):
            if item.is_file():
                shutil.copy2(item, current_backup / item.name)

    return str(current_backup)


def lock_protected_files_demo(protected_dir: str) -> list:
    """
    Demo-only protection:
    Make files read-only inside lab protected folder.
    This does not touch real user directories.
    """
    protected_path = Path(protected_dir)
    locked_files = []

    if protected_path.exists():
        for item in protected_path.glob("*"):
            if item.is_file():
                item.chmod(0o444)
                locked_files.append(str(item))

    return locked_files


def store_unknown_case(case: dict, unknown_case_dir: str) -> str:
    out_dir = Path(unknown_case_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_file = out_dir / f"unknown_case_{stamp}.json"
    out_file.write_text(json.dumps(case, indent=2), encoding="utf-8")

    return str(out_file)


def run_protective_lockdown(case: dict) -> dict:
    protected_dir = "data/protected_docs"
    backup_root = "data/emergency_backup"
    unknown_case_dir = "data/unknown_cases"

    backup_path = emergency_backup(protected_dir, backup_root)
    locked_files = lock_protected_files_demo(protected_dir)
    unknown_case_path = store_unknown_case(case, unknown_case_dir)

    return {
        "lockdown_mode": True,
        "backup_path": backup_path,
        "locked_files_demo": locked_files,
        "unknown_case_path": unknown_case_path,
        "note": "Demo-only lockdown applied inside lab folders only."
    }
