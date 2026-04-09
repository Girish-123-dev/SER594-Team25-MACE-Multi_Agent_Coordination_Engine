import sqlite3
from pathlib import Path

from app.config import settings


class Database:
    def __init__(self, db_path: str | None = None):
        self.db_path = db_path or settings.db_path
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_tables()

    def _init_tables(self):
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                intent TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                assigned_agent TEXT,
                result TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS conflicts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id_a INTEGER NOT NULL,
                task_id_b INTEGER NOT NULL,
                conflict_type TEXT NOT NULL,
                resolution TEXT,
                resolved_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (task_id_a) REFERENCES tasks(id),
                FOREIGN KEY (task_id_b) REFERENCES tasks(id)
            );
        """)
        self.conn.commit()

    # ---- User operations ----

    def create_user(self, username: str, email: str, password_hash: str) -> int:
        cur = self.conn.execute(
            "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
            (username, email, password_hash),
        )
        self.conn.commit()
        return cur.lastrowid

    def get_user_by_username(self, username: str):
        return self.conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()

    def get_user_by_email(self, email: str):
        return self.conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()

    def get_user_by_id(self, user_id: int):
        return self.conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()

    # ---- Task operations ----

    def create_task(self, user_id: int, intent: str, assigned_agent: str | None = None) -> int:
        cur = self.conn.execute(
            "INSERT INTO tasks (user_id, intent, assigned_agent) VALUES (?, ?, ?)",
            (user_id, intent, assigned_agent),
        )
        self.conn.commit()
        return cur.lastrowid

    def get_tasks_by_user(self, user_id: int):
        return self.conn.execute(
            "SELECT * FROM tasks WHERE user_id = ? ORDER BY created_at DESC", (user_id,)
        ).fetchall()

    def close(self):
        self.conn.close()


# ---- FastAPI dependency ----

_db: Database | None = None


def get_db() -> Database:
    global _db
    if _db is None:
        _db = Database()
    return _db
