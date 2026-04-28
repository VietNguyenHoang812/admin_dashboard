import asyncio
import os
import random
from datetime import datetime, timezone, date, timedelta

import httpx

BACKEND_URL = os.getenv("BACKEND_URL", "http://0.0.0.0:8000")
INTERVAL_SECONDS = 5

HEALTH_RESULTS = ["OK", "OK", "OK", "WARNING", "ERROR"]  # weighted toward OK
TS_STATUSES    = ["present", "late", "absent"]
WORK_CONTENTS  = [
    "Họp cả ngày, không làm được gì cả.",
    "Fix bug hệ thống giám sát.",
    "Review code và deploy lên staging.",
    "Viết tài liệu API cho module báo cáo.",
    "Hỗ trợ team khác xử lý sự cố mạng.",
]

FALLBACK_MACHINES = [
    {"hostname": "WS-TECH-042", "ip": "10.123.221.45", "username": "devuser01"},
    {"hostname": "WS-TECH-055", "ip": "10.123.221.60", "username": "devuser02"},
    {"hostname": "WS-DEV-011",  "ip": "10.123.222.11", "username": "vietnh41"},
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
            {
                "hostname": e["hostname"] or f"WS-{e['usercode']}",
                "ip": e["ip"] or "10.0.0.1",
                "username": e["username"],
            }
            for e in employees if e.get("ip")
        ]
        usernames = [e["username"] for e in employees if e.get("username")]

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
    return date.today().isoformat()


def random_time(hour_start: int, hour_end: int) -> str:
    total_minutes = (hour_end - hour_start) * 60
    offset = random.randint(0, total_minutes)
    h = hour_start + offset // 60
    m = offset % 60
    return f"{h:02d}:{m:02d}"


def make_health_check(machine: dict) -> dict:
    return {
        "pc_name": machine["hostname"],
        "health_result": random.choice(HEALTH_RESULTS),
    }


def make_token_usage(machine: dict) -> dict:
    input_tokens  = random.randint(100, 2000)
    output_tokens = random.randint(50, 1000)
    return {
        "pc_name":       machine["hostname"],
        "input_tokens":  input_tokens,
        "output_tokens": output_tokens,
        "total_tokens":  input_tokens + output_tokens,
    }


def make_last_active(machine: dict) -> dict:
    return {"pc_name": machine["hostname"]}


def _random_events(checkin_hour_start: int, checkin_hour_end: int) -> list[dict]:
    """Generate plausible startup/lock/unlock events for a workday."""
    today = date.today()
    tz_offset = "+07:00"

    def ts(h: int, m: int, s: int = 0) -> str:
        return f"{today.isoformat()}T{h:02d}:{m:02d}:{s:02d}.000{tz_offset}"

    # startup ~ checkin time
    start_h = random.randint(checkin_hour_start, checkin_hour_end)
    start_m = random.randint(0, 59)

    events = [{"type": "startup", "timestamp": ts(start_h, start_m)}]

    # a few lock/unlock pairs mid-day (lunch, short breaks)
    num_breaks = random.randint(1, 3)
    current_h, current_m = start_h + 1, random.randint(0, 59)
    for _ in range(num_breaks):
        if current_h >= 17:
            break
        lock_m = current_m + random.randint(5, 30)
        lock_h = current_h + lock_m // 60
        lock_m = lock_m % 60
        if lock_h >= 17:
            break
        events.append({"type": "lock", "timestamp": ts(lock_h, lock_m)})
        unlock_m = lock_m + random.randint(5, 60)
        unlock_h = lock_h + unlock_m // 60
        unlock_m = unlock_m % 60
        if unlock_h >= 17:
            break
        events.append({"type": "unlock", "timestamp": ts(unlock_h, unlock_m)})
        current_h, current_m = unlock_h, unlock_m + random.randint(30, 90)
        current_h += current_m // 60
        current_m = current_m % 60

    # final lock at checkout time (last event = lock → checkout derived from it)
    checkout_h = random.randint(17, 19)
    checkout_m = random.randint(0, 59)
    events.append({"type": "lock", "timestamp": ts(checkout_h, checkout_m)})

    return events


def make_timesheet_auto(machine: dict) -> dict:
    return {
        "date":     today_str(),
        "hostname": machine["hostname"],
        "username": machine["username"],
        "platform": "win32",
        "events":   _random_events(7, 9),
    }


def make_timesheet_manual(username: str) -> dict:
    return {
        "username":     username,
        "check_in":     random_time(7, 9),
        "check_out":    random_time(17, 20),
        "logged_date":  today_str(),
        "status":       random.choice(TS_STATUSES),
        "work_content": random.choice(WORK_CONTENTS),
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
        for _ in range(10):
            try:
                await client.get(f"{BACKEND_URL}/health")
                break
            except Exception:
                print("[INFO] Waiting for backend…")
                await asyncio.sleep(3)

        machines, usernames = await load_staff(client)

        current_day  = today_str()
        ts_done:     set[str] = set()   # pc_names with auto timesheet today
        manual_done: set[str] = set()   # usernames with manual timesheet today
        tick = 0

        while True:
            day = today_str()

            if day != current_day:
                print(f"[INFO] New day {day} — resetting daily logs")
                current_day = day
                ts_done.clear()
                manual_done.clear()

            print(f"\n--- {datetime.now(timezone.utc).strftime('%H:%M:%S')} ---")

            # Netclaw health + last-active every tick
            for machine in machines:
                await post(client, "/api/v1/netclaw/health-check",
                           make_health_check(machine), f"health-check {machine['pc_name']}")
                await post(client, "/api/v1/netclaw/last-active",
                           make_last_active(machine),  f"last-active  {machine['pc_name']}")

            # Token usage: once per machine per day
            for machine in machines:
                if machine["pc_name"] not in ts_done:
                    await post(client, "/api/v1/netclaw/token-usage",
                               make_token_usage(machine), f"token-usage  {machine['pc_name']}")

            # Auto timesheet: once per machine per day
            for machine in machines:
                if machine["pc_name"] not in ts_done:
                    await post(client, "/api/v1/logs/timesheet/auto",
                               make_timesheet_auto(machine), f"ts-auto      {machine['pc_name']}")
                    ts_done.add(machine["pc_name"])

            # Manual timesheet: once per user per day
            for user in usernames:
                if user not in manual_done:
                    await post(client, "/api/v1/logs/timesheet/manual",
                               make_timesheet_manual(user), f"ts-manual    {user}")
                    manual_done.add(user)

            tick += 1
            if tick % 60 == 0:
                machines, usernames = await load_staff(client)

            await asyncio.sleep(INTERVAL_SECONDS)


if __name__ == "__main__":
    asyncio.run(main())
