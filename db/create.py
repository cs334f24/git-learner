import datetime
import sqlite3


class DBMan:
    def __init__(self, uri: str):
        self.uri = uri
        self.conn = sqlite3.connect(uri)
        cur = self.conn.cursor()
        cur.executescript("""
        BEGIN;
        PRAGMA foreign_keys = ON;
        COMMIT;
        """)
        cur.executescript("""
        BEGIN;
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT,
            github TEXT
        );
        CREATE TABLE IF NOT EXISTS modules(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            base_repo TEXT,
            total_steps INTEGER NOT NULL,
            CHECK (total_steps >-1)
        );
        CREATE TABLE IF NOT EXISTS sessions(
            id ROWID,
            user_id INTEGER REFERENCES users(id),
            module_id INTEGER REFERENCES modules(id),
            repo TEXT,
            created TEXT,
            current_step INTEGER NOT NULL,
            CHECK (current_step > -1)
        );
        COMMIT;
        """)
        cur.close()

    def add_user(self, name: str, email: str, github: str):
        with self.conn:
            cur = self.conn.cursor()
            cur.execute(
                "INSERT INTO users(name, email, github) VALUES(?,?,?)",
                (name, email, github),
            )
            cur.close()

    def create_session(self, user_id: int, module_id: int):
        cur = self.conn.cursor()
        try:
            timestamp = datetime.datetime.now(datetime.UTC).isoformat()
            # TODO: generate repo
            cur.execute(
                """
                INSERT INTO sessions(user_id, module_id, created, current_step)
                VALUES(?,?,?,?)
                """,
                (user_id, module_id, timestamp, 0),
            )
            self.conn.commit()
        except Exception:
            self.conn.rollback()
        finally:
            cur.close()
