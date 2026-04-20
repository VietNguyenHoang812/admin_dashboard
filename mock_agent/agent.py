import asyncio
import os
import random
from datetime import datetime, timezone, timedelta

import httpx

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
INTERVAL_SECONDS = 5

HC_STATUSES = ["Running", "Degraded", "Stopped"]
WORK_CONTENTS = [
    "Họp cả ngày, không làm được gì cả.",
    "Fix bug hệ thống giám sát.",
    "Review code và deploy lên staging.",
    "Viết tài liệu API cho module báo cáo.",
    "Hỗ trợ team khác xử lý sự cố mạng.",
]

FALLBACK_MACHINES = [
    {"machine_id": "WS-TECH-042", "IP": "10.123.221.45"},
    {"machine_id": "WS-TECH-055", "IP": "10.123.221.60"},
    {"machine_id": "WS-DEV-011",  "IP": "10.123.222.11"},
]
FALLBACK_USERS = ["vietnh41", "admin", "devuser01", "devuser02"]


async def load_staff(client: httpx.AsyncClient) -> tuple[list[dict], list[str]]:
    try:
        r = await client.get(f"{BACKEND_URL}/api/v1/employees")
        r.raise_for_status()
        employees = r.json()
        if not employees:
            raise ValueError("empty list")

        machines = [
            {"machine_id": f"WS-{e['usercode']}", "IP": e["ip"] or "10.0.0.1"}
            for e in employees if e.get("ip")
        ]
        usernames = [e["username"] for e in employees]

        if not machines:
            machines = FALLBACK_MACHINES
        if not usernames:
            usernames = FALLBACK_USERS

        print(f"[INFO] Loaded {len(employees)} employees → {len(machines)} machines, {len(usernames)} users")
        return machines, usernames
    except Exception as e:
        print(f"[WARN] Could not load staff ({e}), using fallback data")
        return FALLBACK_MACHINES, FALLBACK_USERS


def today_str() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def random_datetime_today(hour_start=8, hour_end=19) -> str:
    base = datetime.now(timezone.utc).replace(hour=hour_start, minute=0, second=0, microsecond=0)
    offset = random.randint(0, (hour_end - hour_start) * 3600)
    return (base + timedelta(seconds=offset)).isoformat()


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def make_healthcheck(machine: dict) -> dict:
    return {
        "machine_id": machine["machine_id"],
        "IP": machine["IP"],
        "timestamp": now_iso(),
        "netmind_healthcheck": {
            "version": "v2.1.0",
            "status": random.choice(HC_STATUSES),
            "active_services": random.randint(1, 6),
            "last_ping": now_iso(),
        },
    }


def make_timesheet(machine: dict) -> dict:
    return {
        "machine_id": machine["machine_id"],
        "IP": machine["IP"],
        "timestamp": now_iso(),
        "timesheet_log": {
            "check_in": random_datetime_today(7, 9),
            "check_out": random_datetime_today(17, 20),
        },
    }


def make_timesheet_manual(username: str) -> dict:
    return {
        "username": username,
        "timestamp": now_iso(),
        "timesheet_log": {
            "check_in": random_datetime_today(7, 9),
            "check_out": random_datetime_today(17, 20),
            "work_content": random.choice(WORK_CONTENTS),
        },
    }


async def post(client: httpx.AsyncClient, path: str, payload: dict, label: str):
    try:
        r = await client.post(f"{BACKEND_URL}{path}", json=payload)
        r.raise_for_status()
        print(f"[OK]  {label}")
    except Exception as e:
        print(f"[ERR] {label} — {e}")


async def main():
    print(f"Mock agent started — pushing every {INTERVAL_SECONDS}s to {BACKEND_URL}")
    async with httpx.AsyncClient(timeout=10) as client:
        # wait for backend to be ready
        for _ in range(10):
            try:
                await client.get(f"{BACKEND_URL}/health")
                break
            except Exception:
                print("[INFO] Waiting for backend…")
                await asyncio.sleep(3)

        machines, usernames = await load_staff(client)

        current_day = today_str()
        ts_done: set[str] = set()      # machine_ids that logged timesheet today
        manual_done: set[str] = set()  # usernames that logged manual today
        tick = 0

        while True:
            day = today_str()

            # Reset daily sets at midnight
            if day != current_day:
                print(f"[INFO] New day {day} — resetting daily logs")
                current_day = day
                ts_done.clear()
                manual_done.clear()

            print(f"\n--- {datetime.now(timezone.utc).strftime('%H:%M:%S')} ---")

            # Healthcheck every tick
            for machine in machines:
                await post(client, "/api/v1/logs/healthcheck", make_healthcheck(machine),
                           f"healthcheck {machine['machine_id']}")

            # Timesheet: once per machine per day
            for machine in machines:
                if machine["machine_id"] not in ts_done:
                    await post(client, "/api/v1/logs/timesheet", make_timesheet(machine),
                               f"timesheet   {machine['machine_id']}")
                    ts_done.add(machine["machine_id"])

            # Manual timesheet: once per user per day
            for user in usernames:
                if user not in manual_done:
                    await post(client, "/api/v1/logs/timesheet/manual", make_timesheet_manual(user),
                               f"manual      {user}")
                    manual_done.add(user)

            tick += 1
            # Reload staff every 60 ticks (~5 min)
            if tick % 60 == 0:
                machines, usernames = await load_staff(client)

            await asyncio.sleep(INTERVAL_SECONDS)


if __name__ == "__main__":
    asyncio.run(main())
