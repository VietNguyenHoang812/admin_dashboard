# Timesheet Auto Log — Logic Test Cases

Tests for `_derive_checkin_checkout` and `_compute_onscreen_time` in `backend/app/services/log_service.py`.

Test file: `backend/tests/test_timesheet_logic.py`

---

## Event Types

| Type | Description |
|------|-------------|
| `startup` | PC booted up |
| `lock` | Screen locked |
| `unlock` | Screen unlocked |

## Derivation Rules

- **check_in** = earliest of: first `startup`, first `unlock`, or first `lock`
- **check_out** = timestamp of the last `lock` event
- **onscreen_time** = total duration between `startup`/`unlock` → `lock` pairs (unclosed sessions at end of day are excluded)

---

## Mock Files & Test Cases

### Case 7 — Multiple startups (crash / BSOD then reboot)
**File:** `mock_agent/mock_data/mock_timesheet_log_7.json`

| Event | Timestamp |
|-------|-----------|
| startup | 08:00 |
| lock | 10:00 |
| startup | 10:30 |
| lock | 17:00 |

| check_in | check_out | onscreen |
|----------|-----------|----------|
| `08:00` | `17:00` | `8:30` |

> First startup wins for check_in. Both sessions [08:00→10:00] + [10:30→17:00] contribute to onscreen time.

---

### Case 8 — Startup → immediate lock (auto-lock policy)
**File:** `mock_agent/mock_data/mock_timesheet_log_8.json`

| Event | Timestamp |
|-------|-----------|
| startup | 08:05 |
| lock | 08:06 |
| unlock | 09:00 |
| lock | 17:00 |

| check_in | check_out | onscreen |
|----------|-----------|----------|
| `08:05` | `17:00` | `8:01` |

> Auto-lock fires 1 minute after boot. Onscreen = 1min + 8h = 8h01m.

---

### Case 9 — Consecutive unlocks (agent missed a lock event)
**File:** `mock_agent/mock_data/mock_timesheet_log_9.json`

| Event | Timestamp |
|-------|-----------|
| startup | 08:00 |
| unlock | 09:00 |
| unlock | 10:00 |
| lock | 17:00 |

| check_in | check_out | onscreen |
|----------|-----------|----------|
| `08:00` | `17:00` | `9:00` |

> Second unlock is silently ignored (on_since already set from startup). No double-counting.

---

### Case 10 — Empty events
**File:** `mock_agent/mock_data/mock_timesheet_log_10.json`

| Event | Timestamp |
|-------|-----------|
| *(none)* | — |

| check_in | check_out | onscreen |
|----------|-----------|----------|
| `None` | `None` | `None` |

> Agent ran but captured nothing.

---

### Case 11 — Very late startup only (no lock)
**File:** `mock_agent/mock_data/mock_timesheet_log_11.json`

| Event | Timestamp |
|-------|-----------|
| startup | 17:30 |

| check_in | check_out | onscreen |
|----------|-----------|----------|
| `17:30` | `None` | `None` |

> check_in recorded from startup. No lock → check_out is None. Unclosed session excluded from onscreen_time.

---

## Bug Found & Fixed

**Cases 3 and 6** revealed that `_derive_checkin_checkout` originally only considered `startup` and `lock` for `check_in`, ignoring `unlock`. This caused wrong check_in when a session starts with an `unlock` (PC left on from previous day or user active before first lock).

**Fix:** Added `unlocks[:1]` to the candidate list.

### Case 3 — No startup, starts with unlock (PC left on from yesterday)
**File:** `mock_agent/mock_data/mock_timesheet_log_3.json`

| check_in | check_out | onscreen | Before fix |
|----------|-----------|----------|------------|
| `07:50` | `17:32` | `8:46` | check_in was `12:10` ❌ |

### Case 6 — Unlock → startup → normal (active then restarted)
**File:** `mock_agent/mock_data/mock_timesheet_log_6.json`

| check_in | check_out | onscreen | Before fix |
|----------|-----------|----------|------------|
| `08:03` | `17:30` | `8:28` | check_in was `09:20` ❌ |

---

## Running Tests

```bash
cd backend
python -m pytest tests/test_timesheet_logic.py -v
```

Results are saved to `backend/tests/results/test_timesheet_logic.txt`.
