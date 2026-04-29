-- Admin Dashboard — initial schema
-- PostgreSQL. Run once on a fresh database.
-- The application also creates these tables on startup via SQLAlchemy create_all.

CREATE TABLE IF NOT EXISTS employees (
    username    TEXT        PRIMARY KEY,
    name        TEXT        NOT NULL,
    usercode    TEXT        NOT NULL,
    department  TEXT,
    ip          TEXT,
    hostname    TEXT,
    created_at  TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_employees_usercode ON employees (usercode);
CREATE INDEX IF NOT EXISTS ix_employees_ip       ON employees (ip);


CREATE TABLE IF NOT EXISTS timesheet_manual_logs (
    id                SERIAL PRIMARY KEY,
    username          TEXT        NOT NULL,
    check_in          TEXT        NOT NULL,
    check_out         TEXT        NOT NULL,
    logged_date       TEXT        NOT NULL,
    status            TEXT        NOT NULL,
    office_hour_work  TEXT,
    ot_work           TEXT,
    created_at        TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_timesheet_manual_logs_username    ON timesheet_manual_logs (username);
CREATE INDEX IF NOT EXISTS ix_timesheet_manual_logs_logged_date ON timesheet_manual_logs (logged_date);


CREATE TABLE IF NOT EXISTS timesheet_auto_logs (
    id            SERIAL PRIMARY KEY,
    hostname      TEXT        NOT NULL,
    username      TEXT,
    ip            TEXT,
    check_in      TEXT,
    check_out     TEXT,
    onscreen_time TEXT,
    logged_date   TEXT        NOT NULL,
    status        TEXT,
    received_at   TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_auto_logs_username_date UNIQUE (username, logged_date)
);

CREATE INDEX IF NOT EXISTS ix_timesheet_auto_logs_hostname    ON timesheet_auto_logs (hostname);
CREATE INDEX IF NOT EXISTS ix_timesheet_auto_logs_username    ON timesheet_auto_logs (username);
CREATE INDEX IF NOT EXISTS ix_timesheet_auto_logs_logged_date ON timesheet_auto_logs (logged_date);


CREATE TABLE IF NOT EXISTS health_check (
    id            SERIAL PRIMARY KEY,
    pc_name       TEXT      NOT NULL,
    health_result TEXT      NOT NULL,
    created_at    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_health_check_pc_name    ON health_check (pc_name);
CREATE INDEX IF NOT EXISTS ix_health_check_created_at ON health_check (created_at);


CREATE TABLE IF NOT EXISTS token_usage (
    id            SERIAL  PRIMARY KEY,
    pc_name       TEXT    NOT NULL,
    input_tokens  INTEGER NOT NULL DEFAULT 0,
    output_tokens INTEGER NOT NULL DEFAULT 0,
    total_tokens  INTEGER NOT NULL DEFAULT 0,
    usage_date    DATE    NOT NULL DEFAULT CURRENT_DATE
);

CREATE INDEX IF NOT EXISTS ix_token_usage_pc_name    ON token_usage (pc_name);
CREATE INDEX IF NOT EXISTS ix_token_usage_usage_date ON token_usage (usage_date);


CREATE TABLE IF NOT EXISTS last_active (
    pc_name        TEXT      PRIMARY KEY,
    last_active_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
