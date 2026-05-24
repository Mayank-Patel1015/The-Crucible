CREATE TABLE IF NOT EXISTS socratic_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    mission_day INTEGER NOT NULL,
    topic TEXT NOT NULL,
    human_attempt TEXT NOT NULL,
    ai_response TEXT NOT NULL,
    human_word_count INTEGER NOT NULL,
    ai_word_count INTEGER NOT NULL,
    autonomy_ratio REAL GENERATED ALWAYS AS (
        CAST(human_word_count AS REAL) / NULLIF(ai_word_count, 0)
    ) STORED,
    cqr REAL NOT NULL,
    energy_joules REAL NOT NULL,
    duration_seconds REAL NOT NULL,
    watts_average REAL GENERATED ALWAYS AS (
        energy_joules / NULLIF(duration_seconds, 0)
    ) STORED
);
