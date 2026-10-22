BEGIN IMMEDIATE;
CREATE TABLE IF NOT EXISTS practice_runs (
    owner INTEGER PRIMARY KEY,
    version INTEGER NOT NULL,
    payload TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
PRAGMA user_version = 1;
COMMIT;
