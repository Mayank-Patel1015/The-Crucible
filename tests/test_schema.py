import sqlite3
import os

SCHEMA_PATH = os.path.join(os.path.dirname(__file__), '..', 'schema.sql')


def _load_schema():
    conn = sqlite3.connect(':memory:')
    with open(SCHEMA_PATH) as f:
        conn.executescript(f.read())
    return conn


def test_table_exists():
    conn = _load_schema()
    tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")]
    assert 'socratic_sessions' in tables
    conn.close()


def test_required_columns_exist():
    conn = _load_schema()
    cols = {r[1] for r in conn.execute("PRAGMA table_info(socratic_sessions)")}
    required = {'id', 'timestamp', 'mission_day', 'topic', 'human_attempt',
                'ai_response', 'human_word_count', 'ai_word_count', 'cqr',
                'energy_joules', 'duration_seconds'}
    assert required <= cols
    conn.close()


def test_generated_columns_computed_correctly():
    # Validate generated columns via query rather than PRAGMA (PRAGMA omits them on some SQLite builds)
    conn = _load_schema()
    conn.execute(
        """INSERT INTO socratic_sessions
           (mission_day, topic, human_attempt, ai_response,
            human_word_count, ai_word_count, cqr, energy_joules, duration_seconds)
           VALUES (1, 'Gen', 'h', 'a', 20, 4, 0.5, 6.0, 60.0)"""
    )
    row = conn.execute("SELECT autonomy_ratio, watts_average FROM socratic_sessions").fetchone()
    assert abs(row[0] - 5.0) < 1e-9    # 20/4
    assert abs(row[1] - 0.1) < 1e-9    # 6.0/60.0
    conn.close()


def test_insert_and_query():
    conn = _load_schema()
    conn.execute(
        """INSERT INTO socratic_sessions
           (mission_day, topic, human_attempt, ai_response,
            human_word_count, ai_word_count, cqr, energy_joules, duration_seconds)
           VALUES (1, 'Test', 'human text', 'ai text', 10, 5, 0.75, 2.5, 30.0)"""
    )
    row = conn.execute("SELECT cqr, autonomy_ratio, watts_average FROM socratic_sessions").fetchone()
    assert row[0] == 0.75
    assert abs(row[1] - 2.0) < 1e-9   # 10/5
    assert abs(row[2] - 2.5 / 30.0) < 1e-9
    conn.close()
