"""
Unit tests for _derive_checkin_checkout and _compute_onscreen_time.
Each test case mirrors a mock_timesheet_log_*.json scenario.
"""
import pytest
from app.schemas.log import TimesheetEvent
from app.services.log_service import _derive_checkin_checkout, _compute_onscreen_time


def make_events(*pairs: tuple[str, str]) -> list[TimesheetEvent]:
    return [TimesheetEvent(type=t, timestamp=ts) for t, ts in pairs]


# ── Case 7: Multiple startups (crash / BSOD then reboot) ────────────────────
# startup(08:00) → lock(10:00) → startup(10:30) → lock(17:00)
# check_in  = min(first_startup=08:00, first_lock=10:00) = 08:00
# check_out = max lock = 17:00
# onscreen  = [08:00→10:00] + [10:30→17:00] = 2h + 6h30m = 8h30m

def test_multiple_startups_checkin_checkout():
    events = make_events(
        ("startup", "2026-05-13T08:00:00.000+07:00"),
        ("lock",    "2026-05-13T10:00:00.000+07:00"),
        ("startup", "2026-05-13T10:30:00.000+07:00"),
        ("lock",    "2026-05-13T17:00:00.000+07:00"),
    )
    check_in, check_out = _derive_checkin_checkout(events)
    assert check_in  == "08:00"
    assert check_out == "17:00"

def test_multiple_startups_onscreen_time():
    events = make_events(
        ("startup", "2026-05-13T08:00:00.000+07:00"),
        ("lock",    "2026-05-13T10:00:00.000+07:00"),
        ("startup", "2026-05-13T10:30:00.000+07:00"),
        ("lock",    "2026-05-13T17:00:00.000+07:00"),
    )
    # 2h + 6h30m = 8h30m → "8:30"
    assert _compute_onscreen_time(events) == "8:30"


# ── Case 8: Startup → immediate lock (auto-lock policy) ─────────────────────
# startup(08:05) → lock(08:06) → unlock(09:00) → lock(17:00)
# check_in  = min(startup=08:05, first_lock=08:06) = 08:05
# check_out = 17:00
# onscreen  = [08:05→08:06]=1min + [09:00→17:00]=8h = 8h01m

def test_immediate_autolock_checkin_checkout():
    events = make_events(
        ("startup", "2026-05-13T08:05:00.000+07:00"),
        ("lock",    "2026-05-13T08:06:00.000+07:00"),
        ("unlock",  "2026-05-13T09:00:00.000+07:00"),
        ("lock",    "2026-05-13T17:00:00.000+07:00"),
    )
    check_in, check_out = _derive_checkin_checkout(events)
    assert check_in  == "08:05"
    assert check_out == "17:00"

def test_immediate_autolock_onscreen_time():
    events = make_events(
        ("startup", "2026-05-13T08:05:00.000+07:00"),
        ("lock",    "2026-05-13T08:06:00.000+07:00"),
        ("unlock",  "2026-05-13T09:00:00.000+07:00"),
        ("lock",    "2026-05-13T17:00:00.000+07:00"),
    )
    # 1min + 8h = 8h01m → "8:01"
    assert _compute_onscreen_time(events) == "8:01"


# ── Case 9: Consecutive unlocks (agent missed a lock event) ──────────────────
# startup(08:00) → unlock(09:00) → unlock(10:00) → lock(17:00)
# check_in  = 08:00 (startup)
# check_out = 17:00
# onscreen  = on_since set at startup(08:00), second unlock ignored,
#             lock(17:00) closes → 9h → "9:00"

def test_consecutive_unlocks_checkin_checkout():
    events = make_events(
        ("startup", "2026-05-13T08:00:00.000+07:00"),
        ("unlock",  "2026-05-13T09:00:00.000+07:00"),
        ("unlock",  "2026-05-13T10:00:00.000+07:00"),
        ("lock",    "2026-05-13T17:00:00.000+07:00"),
    )
    check_in, check_out = _derive_checkin_checkout(events)
    assert check_in  == "08:00"
    assert check_out == "17:00"

def test_consecutive_unlocks_onscreen_time():
    events = make_events(
        ("startup", "2026-05-13T08:00:00.000+07:00"),
        ("unlock",  "2026-05-13T09:00:00.000+07:00"),
        ("unlock",  "2026-05-13T10:00:00.000+07:00"),
        ("lock",    "2026-05-13T17:00:00.000+07:00"),
    )
    # on_since=08:00 (startup), second unlock ignored, closed at 17:00 → 9h
    assert _compute_onscreen_time(events) == "9:00"


# ── Case 10: Empty events ────────────────────────────────────────────────────
# Agent ran but captured nothing.
# check_in  = None
# check_out = None
# onscreen  = None

def test_empty_events_checkin_checkout():
    events = make_events()
    check_in, check_out = _derive_checkin_checkout(events)
    assert check_in  is None
    assert check_out is None

def test_empty_events_onscreen_time():
    assert _compute_onscreen_time(make_events()) is None


# ── Case 11: Very late startup only (no lock) ────────────────────────────────
# startup(17:30) — user turned on PC briefly, never locked
# check_in  = 17:30 (from startup candidate)
# check_out = None  (no lock events)
# onscreen  = None  (on_since set but never closed by a lock)

def test_late_startup_only_checkin_checkout():
    events = make_events(
        ("startup", "2026-05-13T17:30:00.000+07:00"),
    )
    check_in, check_out = _derive_checkin_checkout(events)
    assert check_in  == "17:30"
    assert check_out is None

def test_late_startup_only_onscreen_time():
    events = make_events(
        ("startup", "2026-05-13T17:30:00.000+07:00"),
    )
    assert _compute_onscreen_time(events) is None
