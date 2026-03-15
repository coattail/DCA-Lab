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
    },
    {
        "id": "us-total-return",
        "label": "标普500 / 纳指100 全收益",
        "command": [sys.executable, str(ROOT_DIR / "backend" / "scripts" / "localize_total_return_data.py")],
    },
    {
        "id": "scheme-b-localized",
        "label": "沪深300 / 日经225 / 汇率 / 方案B本地化",
        "command": [sys.executable, str(ROOT_DIR / "backend" / "scripts" / "localize_scheme_b_data.py")],
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
        "file": str(path),
    }


def collect_series_coverage() -> dict:
    return {series_id: read_csv_coverage(path) for series_id, path in SERIES_FILES.items()}


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
        "rootDir": str(ROOT_DIR),
        "tasks": [],
        "series": {},
    }
    write_status(status)

    for task in TASKS:
        task_started_at = time.time()
        result = subprocess.run(
            task["command"],
            cwd=ROOT_DIR,
            capture_output=True,
            text=True,
        )
        task_finished_at = time.time()

        task_payload = {
            "id": task["id"],
            "label": task["label"],
            "command": task["command"],
            "success": result.returncode == 0,
            "durationSeconds": round(task_finished_at - task_started_at, 2),
            "stdout": result.stdout.strip().splitlines()[-20:],
            "stderr": result.stderr.strip().splitlines()[-20:],
            "returnCode": result.returncode,
        }
        status["tasks"].append(task_payload)
        write_status(status)

        if result.returncode != 0:
            status["finishedAt"] = datetime.now().astimezone().isoformat()
            status["series"] = collect_series_coverage()
            write_status(status)
            return result.returncode

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
