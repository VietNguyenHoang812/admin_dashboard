# Backend API Reference

Base URL: `http://localhost:8000/api/v1`

All timestamps are ISO 8601 (UTC). All request/response bodies are JSON unless noted.

---

## Auth

### POST `/auth/login`

Authenticate and receive a JWT token (TTL: 8 hours).

**Request body**
```json
{
  "username": "admin",
  "password": "secret"
}
```

**Response `200`**
```json
{
  "access_token": "<jwt>",
  "token_type": "bearer",
  "username": "admin"
}
```

**Errors**
- `401` — invalid credentials

---

## Employees

### GET `/employees`

List all employees. Supports optional name/usercode/username search.

**Query params**
| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `search` | string | no | Filter by name, usercode, or username (case-insensitive) |

**Response `200`** — array of employee objects
```json
[
  {
    "id": 1,
    "name": "Nguyen Van A",
    "usercode": "NV001",
    "username": "nguyenvana",
    "department": "IT",
    "ip": "192.168.1.20",
    "created_at": "2026-01-01T00:00:00Z"
  }
]
```

---

### POST `/employees/import`

Bulk-create employees from an array.

**Request body** — array of employee objects
```json
[
  {
    "name": "Nguyen Van A",
    "usercode": "NV001",
    "username": "nguyenvana",
    "department": "IT",
    "ip": "192.168.1.20"
  }
]
```

`department` and `ip` are optional.

**Response `200`** — array of created employee objects

**Errors**
- `409` — duplicate `usercode` or `username`

---

### PUT `/employees/{employee_id}`

Update an employee record. All fields are optional (partial update).

**Request body**
```json
{
  "name": "Nguyen Van B",
  "department": "Network"
}
```

**Response `200`** — updated employee object

**Errors**
- `404` — employee not found
- `409` — duplicate `usercode` or `username`

---

### DELETE `/employees/{employee_id}`

Delete an employee record.

**Response `204`** — no content

**Errors**
- `404` — employee not found

---

## Healthcheck

### POST `/health-check`

Ingest a healthcheck event from a background agent.

**Request body**
```json
{
  "username": "string",
  "health_result": "string"
}
```
**Successful Response (201):**
  ```json
  {
    "id": 1,
    "username": "string",
    "health_result": "string",
    "created_at": "2024-01-01T00:00:00"
  }
  ```

`netmind_healthcheck` and all its fields are optional.

**Response `200`**
```json
{
  "id": 1,
  "machine_id": "DESKTOP-ABC123",
  "ip": "192.168.1.10",
  "version": "1.2.3",
  "status": "running",****
  "active_services": 5,
  "last_ping": "2026-04-21T07:59:00Z",
  "timestamp": "2026-04-21T08:00:00Z",
  "received_at": "2026-04-21T08:00:01Z"
}
```

---

### GET `/logs/healthcheck`

List recent healthcheck logs.

**Query params**
| Param | Type | Default | Max |
|-------|------|---------|-----|
| `limit` | int | 50 | 500 |

**Response `200`** — array of healthcheck log objects

---

### GET `/logs/healthcheck/stats`

Aggregate healthcheck statistics.

**Response `200`**
```json
{
  "total": 120,
  "running": 90,
  "degraded": 20,
  "stopped": 10,
  "by_day": [
    { "day": "2026-04-21", "count": 30 }
  ]
}
```

---

## Timesheet

### POST `/admin_dashboard/api/automachinelog'`

Ingest a timesheet event from a background agent.

**Request body**
```json
{
  "machine_id": "DESKTOP-ABC123",
  "IP": "192.168.1.10",
  "timestamp": "2026-04-21T08:00:00Z",
  "timesheet_log": {
    "check_in": "2026-04-21T08:00:00Z",
    "check_out": null
  }
}
```

`timesheet_log` and its fields are optional.

**Response `200`**
```json
{
  "id": 1,
  "machine_id": "DESKTOP-ABC123",
  "ip": "192.168.1.10",
  "check_in": "2026-04-21T08:00:00Z",
  "check_out": null,
  "timestamp": "2026-04-21T08:00:00Z",
  "received_at": "2026-04-21T08:00:01Z"
}
```

---

### GET `/api/logs/timesheet`

List recent timesheet logs.

**Query params**
| Param | Type | Default | Max |
|-------|------|---------|-----|
| `limit` | int | 50 | 500 |

**Response `200`** — array of timesheet log objects

---

### POST `/api/logs/timesheet/manual`

Ingest a manual timesheet entry (submitted by a user, not an agent).

**Request body**
```json
{
  "username": "nguyenvana",
  "timestamp": "2026-04-21T08:00:00Z",
  "timesheet_log": {
    "check_in": "2026-04-21T08:00:00Z",
    "check_out": "2026-04-21T17:00:00Z",
    "work_content": "Deployed network update"
  }
}
```

`timesheet_log` and its fields are optional.

**Response `200`**
```json
{
  "id": 1,
  "username": "nguyenvana",
  "check_in": "2026-04-21T08:00:00Z",
  "check_out": "2026-04-21T17:00:00Z",
  "work_content": "Deployed network update",
  "timestamp": "2026-04-21T08:00:00Z",
  "received_at": "2026-04-21T08:00:01Z"
}
```

---

### GET `/api/logs/timesheet/manual`

List recent manual timesheet entries.

**Query params**
| Param | Type | Default | Max |
|-------|------|---------|-----|
| `limit` | int | 50 | 500 |

**Response `200`** — array of manual timesheet log objects

---

### GET `/logs/timesheet/merged`

List merged timesheet view — joins agent timesheet logs with manual entries and employee data.

**Query params**
| Param | Type | Default | Max |
|-------|------|---------|-----|
| `limit` | int | 100 | 500 |

**Response `200`**
```json
[
  {
    "id": 1,
    "machine_id": "DESKTOP-ABC123",
    "ip": "192.168.1.10",
    "username": "nguyenvana",
    "usercode": "NV001",
    "name": "Nguyen Van A",
    "department": "IT",
    "ts_check_in": "2026-04-21T08:00:00Z",
    "ts_check_out": "2026-04-21T17:00:00Z",
    "manual_check_in": "2026-04-21T08:05:00Z",
    "manual_check_out": "2026-04-21T17:10:00Z",
    "work_content": "Deployed network update",
    "received_at": "2026-04-21T08:00:01Z"
  }
]
```

---

## Server Health

### GET `/health`

Simple liveness check (no auth required).

**Response `200`**
```json
{ "status": "ok" }
```
