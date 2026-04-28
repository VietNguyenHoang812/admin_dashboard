ALTER TABLE timesheet_auto_logs RENAME COLUMN machine_id TO hostname;
ALTER TABLE timesheet_auto_logs ADD COLUMN IF NOT EXISTS username TEXT;
ALTER TABLE timesheet_auto_logs ALTER COLUMN ip DROP NOT NULL;
CREATE INDEX IF NOT EXISTS ix_timesheet_auto_logs_username ON timesheet_auto_logs (username);
