# Admin Dashboard API Reference

Base URL: `http://localhost:8000/api/v1`  
Interactive docs (Swagger UI): `http://localhost:8000/docs`  
Alternative docs (ReDoc): `http://localhost:8000/redoc`

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
| `search` | string | no | Case-insensitive match against `name`, `username`, `usercode`, `department`, `ip`, `pc_name` |

**Response `200`** — `list[EmployeeRead]`
```json
[{
  "username": "duonglt18",
  "name": "Lê Tùng Dương",
  "usercode": "NV001",
  "department": "P. TTNT",
  "ip": "10.221.2.82",
  "pc_name": "WS-DUONGLT18",
  "created_at": "2024-01-01T00:00:00"
}]
```

---

### POST `/employees/import`
Bulk-import employees from a parsed Excel file. Matches the columns in `test_data/template_staff_info.xlsx`.

**Request body** — `list[EmployeeCreate]`
```json
[{
  "username": "duonglt18",
  "name": "Lê Tùng Dương",
  "usercode": "NV001",
  "department": "P. TTNT",
  "ip": "10.221.2.82",
  "pc_name": "WS-DUONGLT18"
}]
```

| Field | Type | Required | Notes |
|---|---|---|---|
| `username` | string | **yes** | Primary key — must be unique |
| `name` | string | **yes** | Full display name |
| `usercode` | string | **yes** | Employee ID code |
| `department` | string | no | Department name |
| `ip` | string | no | IP address |
| `pc_name` | string | no | PC hostname |

**Response `200`** — `list[EmployeeRead]` (the created records)  
**Response `409`** — Duplicate `username`.

---

### PUT `/employees/{username}`
Update a single employee. All fields are optional; only supplied fields are changed.

**Path param** — `username`: the employee's login name (primary key)

**Request body** — `EmployeeUpdate`
```json
{
  "name": "Lê Tùng Dương",
  "usercode": "NV001",
  "department": "P. TTNT",
  "ip": "10.221.2.82",
  "pc_name": "WS-DUONGLT18"
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
  "pc_name": "WS-DUONGLT18",
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
  "pc_name": "WS-DUONGLT18",
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
  "pc_name": "WS-DUONGLT18",
  "input_tokens": 500,
  "output_tokens": 200,
  "total_tokens": 700
}
```

**Response `201`** — `TokenUsageRead`
```json
{
  "id": 1,
  "pc_name": "WS-DUONGLT18",
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
{ "pc_name": "WS-DUONGLT18" }
```

**Response `201`** — `LastActiveRead`
```json
{
  "pc_name": "WS-DUONGLT18",
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
PC agent pushes an automatic check-in / check-out record.

**Request body** — `TimesheetAutoCreate`
```json
{
  "machine_id": "WS-DUONGLT18",
  "ip": "10.221.2.82",
  "check_in": "08:12",
  "check_out": "17:45",
  "logged_date": "2024-01-15",
  "status": "present"
}
```

| Field | Type | Required | Notes |
|---|---|---|---|
| `machine_id` | string | **yes** | PC hostname |
| `ip` | string | **yes** | PC IP address |
| `check_in` | string | no | Time string `HH:MM` |
| `check_out` | string | no | Time string `HH:MM` |
| `logged_date` | string | **yes** | Date string `YYYY-MM-DD` |
| `status` | string | no | `present` \| `late` \| `absent` |

**Response `200`** — `TimesheetAutoRead`

---

### GET `/logs/timesheet/auto`
List recent automatic timesheet records.

**Query params**

| Param | Type | Default | Max |
|---|---|---|---|
| `limit` | int | `50` | `500` |

**Response `200`** — `list[TimesheetAutoRead]`
```json
[{
  "id": 1,
  "machine_id": "WS-DUONGLT18",
  "ip": "10.221.2.82",
  "check_in": "08:12",
  "check_out": "17:45",
  "logged_date": "2024-01-15",
  "status": "present",
  "received_at": "2024-01-15T08:12:05"
}]
```

---

## Timesheet — Manual (user-submitted)

### POST `/logs/timesheet/manual`
User submits a manual timesheet entry with optional work content.

**Request body** — `TimesheetManualCreate`
```json
{
  "username": "duonglt18",
  "check_in": "08:05",
  "check_out": "17:30",
  "logged_date": "2024-01-15",
  "status": "present",
  "work_content": "Fix bug hệ thống giám sát."
}
```

| Field | Type | Required |
|---|---|---|
| `username` | string | **yes** |
| `check_in` | string | **yes** — `HH:MM` |
| `check_out` | string | **yes** — `HH:MM` |
| `logged_date` | string | **yes** — `YYYY-MM-DD` |
| `status` | string | **yes** — `present` \| `late` \| `absent` |
| `work_content` | string | no |

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
  "username": "duonglt18",
  "check_in": "08:05",
  "check_out": "17:30",
  "logged_date": "2024-01-15",
  "status": "present",
  "work_content": "Fix bug hệ thống giám sát.",
  "created_at": "2024-01-15T08:05:10"
}]
```

---

## Timesheet — Merged

### GET `/logs/timesheet/merged`
Joins `timesheet_auto_logs` with `employees` and the most recent `timesheet_manual_logs` entry for the same `username` + `logged_date`. Provides a single unified view per machine per day.

**Query params**

| Param | Type | Default | Max |
|---|---|---|---|
| `limit` | int | `100` | `500` |

**Response `200`** — `list[MergedTimesheetRead]`
```json
[{
  "id": 1,
  "machine_id": "WS-DUONGLT18",
  "ip": "10.221.2.82",
  "username": "duonglt18",
  "usercode": "NV001",
  "name": "Lê Tùng Dương",
  "department": "P. TTNT",
  "pc_name": "WS-DUONGLT18",
  "auto_check_in": "08:12",
  "auto_check_out": "17:45",
  "manual_check_in": "08:05",
  "manual_check_out": "17:30",
  "work_content": "Fix bug hệ thống giám sát.",
  "logged_date": "2024-01-15",
  "received_at": "2024-01-15T08:12:05"
}]
```

---

## Server Health

### GET `/health`
Root-level liveness check. No `/api/v1` prefix.

URL: `http://localhost:8000/health`

**Response `200`**
```json
{ "status": "ok", "environment": "development" }
```
