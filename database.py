"""
database.py — Local SQLite database.
All data saved permanently in 'fitai.db'.
"""

import sqlite3, os, json

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fitai.db')

def conn():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c

def create_tables():
    db = conn()
    db.executescript('''
        CREATE TABLE IF NOT EXISTS users (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            name          TEXT NOT NULL,
            age           INTEGER NOT NULL,
            weight_kg     REAL NOT NULL,
            height_cm     REAL NOT NULL,
            fitness_level TEXT NOT NULL,
            goal          TEXT NOT NULL,
            created_at    TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS workout_logs (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id       INTEGER NOT NULL,
            date          TEXT DEFAULT CURRENT_TIMESTAMP,
            exercise_name TEXT NOT NULL,
            sets          INTEGER NOT NULL,
            reps          INTEGER NOT NULL,
            weight_kg     REAL DEFAULT 0.0,
            rpe           REAL,
            notes         TEXT
        );
        CREATE TABLE IF NOT EXISTS workout_plans (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    INTEGER NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            plan_json  TEXT NOT NULL,
            source     TEXT DEFAULT 'hybrid'
        );
    ''')
    db.commit()
    db.close()

# ── Users ─────────────────────────────────────────────────────────────────────
def create_user(name, age, weight_kg, height_cm, fitness_level, goal):
    db = conn()
    cur = db.execute(
        'INSERT INTO users (name,age,weight_kg,height_cm,fitness_level,goal) VALUES (?,?,?,?,?,?)',
        (name, int(age), float(weight_kg), float(height_cm), fitness_level, goal)
    )
    uid = cur.lastrowid
    db.commit(); db.close()
    return uid

def get_user(uid):
    db = conn()
    row = db.execute('SELECT * FROM users WHERE id=?', (uid,)).fetchone()
    db.close()
    return dict(row) if row else None

def get_all_users():
    db = conn()
    rows = db.execute('SELECT * FROM users ORDER BY created_at DESC').fetchall()
    db.close()
    return [dict(r) for r in rows]

def update_user(uid, **kwargs):
    fields = ', '.join(f'{k}=?' for k in kwargs)
    db = conn()
    db.execute(f'UPDATE users SET {fields} WHERE id=?', (*kwargs.values(), uid))
    db.commit(); db.close()

# ── Logs ──────────────────────────────────────────────────────────────────────
def log_workout(user_id, exercise_name, sets, reps,
                weight_kg=0.0, rpe=None, notes=None):
    db = conn()
    db.execute(
        'INSERT INTO workout_logs (user_id,exercise_name,sets,reps,weight_kg,rpe,notes) VALUES (?,?,?,?,?,?,?)',
        (user_id, exercise_name, int(sets), int(reps), float(weight_kg), rpe, notes)
    )
    db.commit(); db.close()

def get_logs(user_id, limit=100):
    db = conn()
    rows = db.execute(
        'SELECT * FROM workout_logs WHERE user_id=? ORDER BY date ASC LIMIT ?',
        (user_id, limit)
    ).fetchall()
    db.close()
    return [dict(r) for r in rows]

def get_recent_logs(user_id, limit=20):
    db = conn()
    rows = db.execute(
        'SELECT * FROM workout_logs WHERE user_id=? ORDER BY date DESC LIMIT ?',
        (user_id, limit)
    ).fetchall()
    db.close()
    return [dict(r) for r in rows]

def get_stats(user_id):
    db = conn()
    total = db.execute(
        'SELECT COUNT(*) as n FROM workout_logs WHERE user_id=?', (user_id,)
    ).fetchone()['n']
    if total == 0:
        db.close()
        return {'total_sessions': 0, 'total_volume_kg': 0,
                'avg_rpe': 0, 'unique_exercises': 0}
    row = dict(db.execute('''
        SELECT SUM(sets*reps*weight_kg) as vol, AVG(rpe) as rpe,
               COUNT(DISTINCT exercise_name) as uniq
        FROM workout_logs WHERE user_id=?
    ''', (user_id,)).fetchone())
    db.close()
    return {
        'total_sessions':   total,
        'total_volume_kg':  round(row['vol'] or 0, 1),
        'avg_rpe':          round(row['rpe'] or 0, 1),
        'unique_exercises': row['uniq'] or 0,
    }

# ── Plans ─────────────────────────────────────────────────────────────────────
def save_plan(user_id, plan):
    db = conn()
    db.execute(
        'INSERT INTO workout_plans (user_id,plan_json,source) VALUES (?,?,?)',
        (user_id, json.dumps(plan), plan.get('source', 'hybrid'))
    )
    db.commit(); db.close()

def get_latest_plan(user_id):
    db = conn()
    row = db.execute(
        'SELECT * FROM workout_plans WHERE user_id=? ORDER BY created_at DESC LIMIT 1',
        (user_id,)
    ).fetchone()
    db.close()
    return json.loads(row['plan_json']) if row else None

def get_plan_history(user_id, limit=10):
    db = conn()
    rows = db.execute(
        'SELECT id, created_at, source FROM workout_plans WHERE user_id=? ORDER BY created_at DESC LIMIT ?',
        (user_id, limit)
    ).fetchall()
    db.close()
    return [dict(r) for r in rows]
