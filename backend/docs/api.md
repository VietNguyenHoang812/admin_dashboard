# Admin Dashboard API Reference

Base URL (Docker): `http://localhost:9122/api/v1`  
Interactive docs (Swagger UI): `http://localhost:9122/docs`  
Alternative docs (ReDoc): `http://localhost:9122/redoc`

---

## Authentication

### POST `/auth/login`
Authenticate with admin credentials and receive a JWT bearer token valid for **8 hours**.

**Request body**
```json
{ "username": "admin", "password": "admin123" }
```

**Response `200`**
```json
{ "access_token": "<jwt>", "token_type": "bearer", "username": "admin" }
```

**Response `401`** — Invalid credentials.

---

## Employees

### GET `/employees`
List all employees, optionally filtered by a search term.

**Query params**

| Param | Type | Required | Description |
|---|---|---|---|
| `search` | string | no | Case-insensitive match against `name`, `username`, `usercode`, `department`, `ip`, `hostname` |

**Response `200`** — `list[EmployeeRead]`
```json
[{
  "username": "vietnh41",
  "name": "Nguyễn Hoàng Việt",
  "usercode": "293048",
  "department": "P. TTNT",
  "ip": "10.221.2.91",
  "hostname": "VTN-VIETNH41",
  "created_at": "2024-01-01T00:00:00"
}]
```

---

### POST `/employees/import`
Bulk-import employees from a parsed Excel file. Matches the columns in `test_data/template_staff_info.xlsx`.

**Request body** — `list[EmployeeCreate]`
```json
[{
  "username": "vietnh41",
  "name": "Nguyễn Hoàng Việt",
  "usercode": "293048",
  "department": "P. TTNT",
  "ip": "10.221.2.91",
  "hostname": "VTN-VIETNH41"
}]
```

| Field | Type | Required | Notes |
|---|---|---|---|
| `username` | string | **yes** | Primary key — must be unique |
| `name` | string | **yes** | Full display name |
| `usercode` | string | **yes** | Employee ID code |
| `department` | string | no | Department name |
| `ip` | string | no | IP address |
| `hostname` | string | no | PC hostname |

**Response `200`** — `list[EmployeeRead]` (the created/updated records)  
**Response `409`** — Duplicate `username`.

---

### PUT `/employees/{username}`
Update a single employee. All fields are optional; only supplied fields are changed.

**Path param** — `username`: the employee's login name (primary key)

**Request body** — `EmployeeUpdate`
```json
{
  "name": "Nguyễn Hoàng Việt",
  "usercode": "293048",
  "department": "P. TTNT",
  "ip": "10.221.2.91",
  "hostname": "VTN-VIETNH41"
}
```

**Response `200`** — `EmployeeRead` (the updated record)  
**Response `404`** — Employee not found.

---

### DELETE `/employees/{username}`
Delete an employee record.

**Path param** — `username`: the employee's login name (primary key)

**Response `204`** — Deleted.  
**Response `404`** — Employee not found.

---

## Netclaw

All Netclaw endpoints are under `/api/v1/netclaw/`.

### POST `/netclaw/health-check`
PC agent pushes a health check result.

**Request body** — `HealthCheckCreate`
```json
{
  "pc_name": "WS-DEV-011",
  "health_result": "OK"
}
```

| Field | Type | Required | Notes |
|---|---|---|---|
| `pc_name` | string | **yes** | PC hostname |
| `health_result` | string | **yes** | Free-form string, e.g. `OK` \| `WARNING` \| `ERROR` |

**Response `201`** — `HealthCheckRead`
```json
{
  "id": 1,
  "pc_name": "WS-DEV-011",
  "health_result": "OK",
  "created_at": "2024-01-15T08:30:00"
}
```

---

### GET `/netclaw/health-check`
List recent health check records ordered by most recent first.

**Query params** — `limit` (int, default `50`, max `500`)

**Response `200`** — `list[HealthCheckRead]`

---

### POST `/netclaw/token-usage`
PC agent reports token consumption for the current session.

**Request body** — `TokenUsageCreate`
```json
{
  "pc_name": "WS-DEV-011",
  "input_tokens": 500,
  "output_tokens": 200,
  "total_tokens": 700
}
```

**Response `201`** — `TokenUsageRead`
```json
{
  "id": 1,
  "pc_name": "WS-DEV-011",
  "input_tokens": 500,
  "output_tokens": 200,
  "total_tokens": 700,
  "usage_date": "2024-01-15"
}
```

---

### GET `/netclaw/token-usage`
List recent token usage records ordered by date descending.

**Query params** — `limit` (int, default `50`, max `500`)

**Response `200`** — `list[TokenUsageRead]`

---

### POST `/netclaw/last-active`
Upsert the last-seen timestamp for a PC. Creates on first call, updates `last_active_at` on subsequent calls for the same `pc_name`.

**Request body** — `LastActiveCreate`
```json
{ "pc_name": "WS-DEV-011" }
```

**Response `201`** — `LastActiveRead`
```json
{
  "pc_name": "WS-DEV-011",
  "last_active_at": "2024-01-15T08:30:00"
}
```

---

### GET `/netclaw/last-active`
List all machines with their last-seen timestamp, ordered by most recent first.

**Response `200`** — `list[LastActiveRead]`

---

### GET `/netclaw/stats`
Aggregate stats used by the dashboard.

- `running` = machines with `last_active_at` within the last **5 minutes**
- `stopped` = total machines − running
- `by_day` = health check counts per day for the last 7 days

**Response `200`** — `NetclawStats`
```json
{
  "total": 20,
  "running": 15,
  "degraded": 0,
  "stopped": 5,
  "by_day": [
    { "day": "Mon", "count": 42 },
    { "day": "Tue", "count": 38 }
  ]
}
```

---

## Timesheet — Auto (PC agent)

### POST `/logs/timesheet/auto`
PC agent pushes an event-based timesheet record. The server derives `check_in` and `check_out` from the events array.

**Check-in / check-out derivation rules:**
- `check_in` = earliest timestamp among the first `startup` event and the first `lock` event (whichever comes first)
- `check_out` = latest `lock` event timestamp; if the last event in the array is `unlock`, `check_out` is set to `"00:00"` (midnight)

**Request body** — `TimesheetAutoCreate`
```json
{
  "date": "2024-01-15",
  "hostname": "VTN-VIETNH41",
  "username": "vietnh41",
  "platform": "win32",
  "events": [
    { "type": "startup",  "timestamp": "2024-01-15T08:06:12+07:00" },
    { "type": "unlock",   "timestamp": "2024-01-15T08:10:00+07:00" },
    { "type": "lock",     "timestamp": "2024-01-15T12:00:00+07:00" },
    { "type": "unlock",   "timestamp": "2024-01-15T13:00:00+07:00" },
    { "type": "lock",     "timestamp": "2024-01-15T17:45:30+07:00" }
  ]
}
```

| Field | Type | Required | Notes |
|---|---|---|---|
| `date` | string | **yes** | Work date `YYYY-MM-DD` |
| `hostname` | string | **yes** | PC hostname |
| `username` | string | **yes** | Windows login username |
| `platform` | string | no | OS platform string, e.g. `win32` |
| `events` | array | **yes** | Ordered list of session events |
| `events[].type` | string | **yes** | `startup` \| `lock` \| `unlock` |
| `events[].timestamp` | string | **yes** | ISO 8601 with timezone offset, e.g. `2024-01-15T08:06:12+07:00` |

**Response `200`** — `TimesheetAutoRead`
```json
{
  "id": 1,
  "hostname": "VTN-VIETNH41",
  "username": "vietnh41",
  "ip": null,
  "check_in": "08:06",
  "check_out": "17:45",
  "logged_date": "2024-01-15",
  "status": null,
  "received_at": "2024-01-15T08:06:20"
}
```

---

### GET `/logs/timesheet/auto`
List recent automatic timesheet records.

**Query params**

| Param | Type | Default | Max |
|---|---|---|---|
| `limit` | int | `50` | `500` |

**Response `200`** — `list[TimesheetAutoRead]`

---

## Timesheet — Manual (user-submitted)

### POST `/logs/timesheet/manual`
User submits a manual timesheet entry with optional work content. Unknown extra fields are silently ignored.

**Request body** — `TimesheetManualCreate`
```json
{
  "username": "vietnh41",
  "check_in": "08:05",
  "check_out": "17:30",
  "logged_date": "15-01-2024",
  "status": "present",
  "work_content": "Fix bug hệ thống giám sát.",
  "work_content_ot": "Deploy extra feature."
}
```

| Field | Type | Required | Notes |
|---|---|---|---|
| `username` | string | **yes** | |
| `check_in` | string | **yes** | `HH:MM` |
| `check_out` | string | **yes** | `HH:MM` |
| `logged_date` | string | **yes** | `DD-MM-YYYY` |
| `status` | string | **yes** | `present` \| `late` \| `absent` |
| `work_content` | string | no | Stored as `office_hour_work` |
| `work_content_ot` | string | no | Stored as `ot_work` |

**Response `200`** — `TimesheetManualRead`

---

### GET `/logs/timesheet/manual`
List recent manual timesheet entries.

**Query params**

| Param | Type | Default | Max |
|---|---|---|---|
| `limit` | int | `50` | `500` |

**Response `200`** — `list[TimesheetManualRead]`
```json
[{
  "id": 1,
  "username": "vietnh41",
  "check_in": "08:05",
  "check_out": "17:30",
  "logged_date": "15-01-2024",
  "status": "present",
  "office_hour_work": "Fix bug hệ thống giám sát.",
  "ot_work": "Deploy extra feature.",
  "created_at": "2024-01-15T08:05:10"
}]
```

---

## Timesheet — Merged

### GET `/logs/timesheet/merged`
Returns a unified view of timesheet data per employee per day, merging auto logs with the most recent manual submission. Includes employees who submitted a manual log even if no auto log exists for that day (full outer approach).

**Merge logic:**
- Primary rows: from `timesheet_auto_logs` grouped by `(username, logged_date)` — `check_in` = `MIN`, `check_out` = `MAX` — joined to `employees` and the latest `timesheet_manual_logs` entry for the same user+date
- Additional rows: manual-only entries where no auto log exists for that user+date, joined to `employees`
- Rows where `username` is not found in the `employees` table are excluded

**Query params**

| Param | Type | Default | Max |
|---|---|---|---|
| `limit` | int | `100` | `500` |

**Response `200`** — `list[MergedTimesheetRead]`
```json
[{
  "id": null,
  "machine_id": null,
  "ip": "10.221.2.91",
  "username": "vietnh41",
  "usercode": "293048",
  "name": "Nguyễn Hoàng Việt",
  "department": "P. TTNT",
  "hostname": "VTN-VIETNH41",
  "auto_check_in": "08:06",
  "auto_check_out": "17:45",
  "manual_check_in": "08:05",
  "manual_check_out": "17:30",
  "office_hour_work": "Fix bug hệ thống giám sát.",
  "ot_work": "Deploy extra feature.",
  "logged_date": "15-01-2024",
  "received_at": "2024-01-15T08:06:20"
}]
```

| Field | Notes |
|---|---|
| `id` | Always `null` (aggregated row, no single source ID) |
| `machine_id` | Always `null` (legacy field, kept for compatibility) |
| `ip` | From the `employees` table |
| `hostname` | From the `employees` table |
| `auto_check_in` / `auto_check_out` | Derived from agent events; `null` for manual-only rows |
| `manual_check_in` / `manual_check_out` | From the most recent manual submission; `null` if none |
| `office_hour_work` | Regular-hours work content from the manual log; `null` if none |
| `ot_work` | Overtime work content from the manual log; `null` if none |
| `logged_date` | The actual work date (`DD-MM-YYYY`) — use this for date filtering |

---

## Server Health

### GET `/health`
Root-level liveness check. No `/api/v1` prefix.

URL: `http://localhost:9122/health`

**Response `200`**
```json
{ "status": "ok", "environment": "development" }
```
