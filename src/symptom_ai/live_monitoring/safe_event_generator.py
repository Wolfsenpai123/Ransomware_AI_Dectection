from pathlib import Path
from datetime import datetime
import argparse
import json
import random
import time
import uuid


EVENT_DIR = Path("data/custom_sandbox/events")
EVENT_LOG = EVENT_DIR / "events.jsonl"
LAB_DIR = Path("data/custom_sandbox/lab_files")
CONTROL_DIR = Path("data/custom_sandbox/control")
STOP_SIGNAL = CONTROL_DIR / "STOP_SIGNAL.json"

HOSTS = ["host_hr", "host_finance", "host_accounting", "host_shared_drive"]
FOLDERS = ["documents", "spreadsheets", "contracts", "archives"]


def now_iso():
    return datetime.now().isoformat(timespec="seconds")


def ensure_lab_files(files_per_folder=8):
    LAB_DIR.mkdir(parents=True, exist_ok=True)

    for host in HOSTS:
        for folder in FOLDERS:
            d = LAB_DIR / host / folder
            d.mkdir(parents=True, exist_ok=True)

            for i in range(1, files_per_folder + 1):
                f = d / f"business_file_{i}.txt"
                if not f.exists():
                    f.write_text(
                        f"Safe business file {i} for {host}/{folder}\n",
                        encoding="utf-8"
                    )


def append_event(event):
    EVENT_DIR.mkdir(parents=True, exist_ok=True)
    with EVENT_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event) + "\n")


def should_stop():
    return STOP_SIGNAL.exists()


def clear_stop_signal():
    CONTROL_DIR.mkdir(parents=True, exist_ok=True)
    if STOP_SIGNAL.exists():
        STOP_SIGNAL.unlink()


def emit(event_type, scenario, host, path=None, extra=None):
    event = {
        "event_id": str(uuid.uuid4()),
        "timestamp": now_iso(),
        "scenario": scenario,
        "event_type": event_type,
        "host": host,
        "path": str(path) if path else None,
        "extra": extra or {},
        "safety_note": "Safe simulation only. No real ransomware is executed."
    }
    append_event(event)
    return event


def get_candidate_files(host_limit):
    files = []

    for host in HOSTS[:host_limit]:
        for p in (LAB_DIR / host).rglob("*.txt"):
            if p.name.endswith("ransom_note_demo.txt"):
                continue
            files.append(p)

    random.shuffle(files)
    return files


def simulate_known_ransomware(steps, delay):
    """
    Known scenario:
    gradually creates file write, rename, entropy-like write, and ransom-note demo events.
    """
    scenario = f"known_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    ensure_lab_files()

    print(f"[SANDBOX] Safe background activity started. Writing events to {EVENT_LOG}")
    print(f"[+] Scenario: {scenario}")

    for step in range(1, steps + 1):
        if should_stop():
            print("[SANDBOX] Stop signal detected. Safe event generation stopped.")
            break

        if step <= steps * 0.25:
            host_limit = 1
            event_count = 2
            event_types = ["file_read", "file_write"]
        elif step <= steps * 0.50:
            host_limit = 1
            event_count = 4
            event_types = ["file_read", "file_write", "process_spawn"]
        elif step <= steps * 0.75:
            host_limit = 2
            event_count = 7
            event_types = ["file_write", "file_rename", "high_entropy_write", "extension_change"]
        else:
            host_limit = min(4, len(HOSTS))
            event_count = 10
            event_types = ["file_write", "file_rename", "high_entropy_write", "extension_change", "ransom_note_created"]

        files = get_candidate_files(host_limit)

        for i in range(event_count):
            host = HOSTS[min(host_limit - 1, random.randrange(host_limit))]
            event_type = random.choice(event_types)
            path = files[i % len(files)] if files else LAB_DIR / host

            extra = {
                "step": step,
                "progress": round(step / steps, 3),
                "entropy_score": round(random.uniform(0.70, 0.98), 3) if event_type == "high_entropy_write" else 0.0,
                "new_extension": ".simlocked" if event_type in ["file_rename", "extension_change"] else "",
                "source": "safe_event_generator"
            }

            emit(event_type, scenario, host, path, extra)

        print(f"[SANDBOX] background activity observed: +{event_count} events")
        time.sleep(delay)


def simulate_unknown_ransomware(steps, delay):
    """
    Unknown scenario:
    starts with memory/process anomaly, then gradually reaches file impact.
    """
    scenario = f"unknown_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    ensure_lab_files()

    print(f"[SANDBOX] Safe background activity started. Writing events to {EVENT_LOG}")
    print(f"[+] Scenario: {scenario}")

    for step in range(1, steps + 1):
        if should_stop():
            print("[SANDBOX] Stop signal detected. Safe event generation stopped.")
            break

        progress = step / steps

        if progress <= 0.35:
            host_limit = 1
            event_count = 3
            event_types = ["memory_anomaly", "rare_process", "api_behavior"]
        elif progress <= 0.65:
            host_limit = 2
            event_count = 5
            event_types = ["memory_anomaly", "process_injection_suspected", "anti_vm", "api_behavior", "network_beacon"]
        elif progress <= 0.85:
            host_limit = 3
            event_count = 7
            event_types = ["file_write", "storage_write_spike", "high_entropy_write", "rare_process", "api_behavior"]
        else:
            host_limit = 4
            event_count = 10
            event_types = ["file_write", "file_rename", "high_entropy_write", "extension_change", "ransom_note_created"]

        files = get_candidate_files(host_limit)

        for i in range(event_count):
            host = HOSTS[min(host_limit - 1, random.randrange(host_limit))]
            event_type = random.choice(event_types)
            path = files[i % len(files)] if files else LAB_DIR / host

            extra = {
                "step": step,
                "progress": round(progress, 3),
                "memory_score": round(random.uniform(0.65, 0.98), 3) if event_type in ["memory_anomaly", "process_injection_suspected"] else 0.0,
                "entropy_score": round(random.uniform(0.70, 0.98), 3) if event_type == "high_entropy_write" else 0.0,
                "new_extension": ".unknownlock" if event_type in ["file_rename", "extension_change"] else "",
                "source": "safe_event_generator"
            }

            emit(event_type, scenario, host, path, extra)

        print(f"[SANDBOX] background activity observed: +{event_count} events")
        time.sleep(delay)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario", choices=["known", "unknown"], default="known")
    parser.add_argument("--steps", type=int, default=20)
    parser.add_argument("--delay", type=float, default=1.0)
    parser.add_argument("--reset-log", action="store_true")

    args = parser.parse_args()

    EVENT_DIR.mkdir(parents=True, exist_ok=True)

    if args.reset_log and EVENT_LOG.exists():
        EVENT_LOG.unlink()
        print(f"[+] Reset event log: {EVENT_LOG}")

    if args.reset_log:
        clear_stop_signal()
        print("[+] Cleared stop signal")

    if args.scenario == "known":
        simulate_known_ransomware(args.steps, args.delay)
    else:
        simulate_unknown_ransomware(args.steps, args.delay)


if __name__ == "__main__":
    main()
