#!/usr/bin/env python3

import csv
import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT_DIR / "web" / "data"
STATUS_PATH = DATA_DIR / "refresh-meta.json"

TASKS = [
    {
        "id": "market-price",
        "label": "美股价格数据",
        "command": [str(ROOT_DIR / "backend" / "scripts" / "localize_market_data.sh")],
        "series_ids": ["sp500_price", "nasdaq100_price"],
    },
    {
        "id": "us-total-return",
        "label": "标普500 / 纳指100 全收益",
        "command": [sys.executable, str(ROOT_DIR / "backend" / "scripts" / "localize_total_return_data.py")],
        "series_ids": ["sp500_total_return", "nasdaq100_total_return"],
    },
    {
        "id": "scheme-b-localized",
        "label": "沪深300 / 日经225 / 汇率 / 方案B本地化",
        "command": [sys.executable, str(ROOT_DIR / "backend" / "scripts" / "localize_scheme_b_data.py")],
        "series_ids": [
            "hs300_price",
            "hs300_total_return",
            "nikkei225_price",
            "nikkei225_total_return",
            "usdcny",
            "usdjpy",
        ],
    },
]

SERIES_FILES = {
    "sp500_price": DATA_DIR / "sp500.csv",
    "sp500_total_return": DATA_DIR / "sp500-total-return.csv",
    "nasdaq100_price": DATA_DIR / "nasdaq100.csv",
    "nasdaq100_total_return": DATA_DIR / "nasdaq100-total-return.csv",
    "hs300_price": DATA_DIR / "hs300.csv",
    "hs300_total_return": DATA_DIR / "hs300-total-return.csv",
    "nikkei225_price": DATA_DIR / "nikkei225.csv",
    "nikkei225_total_return": DATA_DIR / "nikkei225-total-return.csv",
    "usdcny": DATA_DIR / "usdcny.csv",
    "usdjpy": DATA_DIR / "usdjpy.csv",
}

SERIES_MAX_STALENESS_DAYS = {
    "sp500_price": 7,
    "sp500_total_return": 7,
    "nasdaq100_price": 7,
    "nasdaq100_total_return": 7,
    "hs300_price": 7,
    "hs300_total_return": 7,
    "nikkei225_price": 7,
    "nikkei225_total_return": 7,
    "usdcny": 10,
    "usdjpy": 10,
}

MAX_TASK_ATTEMPTS = 3
RETRY_BACKOFF_SECONDS = 5


def relativize_path(value: str) -> str:
    text = str(value)
    root_text = str(ROOT_DIR)
    home_text = str(Path.home())
    if text == root_text:
        return "."
    if root_text in text:
        return text.replace(root_text, ".")
    if text.startswith(f"{root_text}/"):
        return text.replace(f"{root_text}/", "", 1)
    if home_text in text:
        return text.replace(home_text, "$HOME")
    return text


def sanitize_log_lines(lines: list[str]) -> list[str]:
    sanitized = []
    for line in lines:
        sanitized.append(relativize_path(line))
    return sanitized


def command_for_status(command: list[str]) -> list[str]:
    return [relativize_path(part) for part in command]


def read_csv_coverage(path: Path) -> dict:
    if not path.exists():
        return {"exists": False}

    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.reader(handle))

    if len(rows) < 2:
        return {"exists": True, "rows": 0}

    return {
        "exists": True,
        "rows": len(rows) - 1,
        "start": rows[1][0],
        "end": rows[-1][0],
        "file": relativize_path(path),
    }


def collect_series_coverage() -> dict:
    return {series_id: read_csv_coverage(path) for series_id, path in SERIES_FILES.items()}


def assess_series_health(series_id: str, coverage: dict, reference_date) -> dict:
    if not coverage.get("exists"):
        return {
            "seriesId": series_id,
            "ok": False,
            "reason": "missing",
            "maxStalenessDays": SERIES_MAX_STALENESS_DAYS.get(series_id, 7),
        }

    rows = int(coverage.get("rows") or 0)
    end = coverage.get("end")
    max_staleness_days = SERIES_MAX_STALENESS_DAYS.get(series_id, 7)
    if rows <= 0 or not end:
        return {
            "seriesId": series_id,
            "ok": False,
            "reason": "empty",
            "rows": rows,
            "file": coverage.get("file"),
            "maxStalenessDays": max_staleness_days,
        }

    end_date = datetime.strptime(end, "%Y-%m-%d").date()
    staleness_days = max(0, (reference_date - end_date).days)
    ok = staleness_days <= max_staleness_days
    return {
        "seriesId": series_id,
        "ok": ok,
        "reason": "fresh" if ok else "stale",
        "rows": rows,
        "end": end,
        "stalenessDays": staleness_days,
        "file": coverage.get("file"),
        "maxStalenessDays": max_staleness_days,
    }


def assess_task_outputs(series_ids: list[str], reference_date) -> dict:
    coverage = collect_series_coverage()
    checks = [assess_series_health(series_id, coverage.get(series_id, {}), reference_date) for series_id in series_ids]
    return {
        "ok": all(item["ok"] for item in checks),
        "series": checks,
    }


def write_status(payload: dict) -> None:
    STATUS_PATH.parent.mkdir(parents=True, exist_ok=True)
    temp_path = STATUS_PATH.with_suffix(STATUS_PATH.suffix + ".tmp")
    temp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    temp_path.replace(STATUS_PATH)


def main() -> int:
    started_at = datetime.now().astimezone()
    status = {
        "success": False,
        "startedAt": started_at.isoformat(),
        "refreshDate": started_at.date().isoformat(),
        "rootDir": ".",
        "tasks": [],
        "series": {},
        "warnings": [],
    }
    write_status(status)

    for task in TASKS:
        attempts = []
        task_succeeded = False
        task_started_at = time.time()

        for attempt_number in range(1, MAX_TASK_ATTEMPTS + 1):
            attempt_started_at = time.time()
            result = subprocess.run(
                task["command"],
                cwd=ROOT_DIR,
                capture_output=True,
                text=True,
            )
            attempt_finished_at = time.time()

            attempt_payload = {
                "attempt": attempt_number,
                "success": result.returncode == 0,
                "durationSeconds": round(attempt_finished_at - attempt_started_at, 2),
                "stdout": sanitize_log_lines(result.stdout.strip().splitlines()[-20:]),
                "stderr": sanitize_log_lines(result.stderr.strip().splitlines()[-20:]),
                "returnCode": result.returncode,
            }

            output_health = assess_task_outputs(task["series_ids"], started_at.date())
            if result.returncode == 0 and not output_health["ok"]:
                attempt_payload["success"] = False
                attempt_payload["stderr"] = [
                    *attempt_payload["stderr"],
                    "Command exited successfully, but one or more output datasets are missing or too stale.",
                ]
                attempt_payload["returnCode"] = 1

            attempts.append(attempt_payload)

            if attempt_payload["success"]:
                task_finished_at = time.time()
                status["tasks"].append(
                    {
                        "id": task["id"],
                        "label": task["label"],
                        "command": command_for_status(task["command"]),
                        "success": True,
                        "refreshSucceeded": True,
                        "usedCachedOutputs": False,
                        "durationSeconds": round(task_finished_at - task_started_at, 2),
                        "stdout": attempt_payload["stdout"],
                        "stderr": attempt_payload["stderr"],
                        "returnCode": 0,
                        "attemptCount": attempt_number,
                        "attempts": attempts,
                        "outputHealth": output_health["series"],
                    }
                )
                write_status(status)
                task_succeeded = True
                break

            if attempt_number < MAX_TASK_ATTEMPTS:
                time.sleep(RETRY_BACKOFF_SECONDS * attempt_number)

        if task_succeeded:
            continue

        output_health = assess_task_outputs(task["series_ids"], started_at.date())
        task_finished_at = time.time()
        fallback_allowed = output_health["ok"]
        task_payload = {
            "id": task["id"],
            "label": task["label"],
            "command": command_for_status(task["command"]),
            "success": fallback_allowed,
            "refreshSucceeded": False,
            "usedCachedOutputs": fallback_allowed,
            "durationSeconds": round(task_finished_at - task_started_at, 2),
            "stdout": attempts[-1]["stdout"] if attempts else [],
            "stderr": attempts[-1]["stderr"] if attempts else [],
            "returnCode": attempts[-1]["returnCode"] if attempts else 1,
            "attemptCount": len(attempts),
            "attempts": attempts,
            "outputHealth": output_health["series"],
        }

        if fallback_allowed:
            warning = (
                f"Task {task['id']} failed after {len(attempts)} attempts, "
                "but existing localized datasets are still fresh enough to keep using."
            )
            task_payload["warning"] = warning
            status["warnings"].append(warning)
            status["tasks"].append(task_payload)
            write_status(status)
            continue

        status["tasks"].append(task_payload)
        status["finishedAt"] = datetime.now().astimezone().isoformat()
        status["series"] = collect_series_coverage()
        write_status(status)
        return task_payload["returnCode"]

    finished_at = datetime.now().astimezone()
    status["success"] = True
    status["finishedAt"] = finished_at.isoformat()
    status["durationSeconds"] = round((finished_at - started_at).total_seconds(), 2)
    status["series"] = collect_series_coverage()
    write_status(status)
    print(json.dumps({"success": True, "finishedAt": status["finishedAt"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
