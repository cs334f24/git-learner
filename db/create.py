import datetime
import sqlite3


class DBManager:
    def __init__(self, uri: str):
        self.uri = uri
        self.conn = sqlite3.connect(uri)
        self.conn.row_factory = sqlite3.Row
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
            name TEXT UNIQUE NOT NULL,
            base_repo TEXT,
            total_steps INTEGER NOT NULL,
            CHECK (total_steps >-1)
        );
        CREATE TABLE IF NOT EXISTS sessions(
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

    def _github_to_id(self, github_user: str) -> int | None:
        cur = self.conn.cursor()
        cur.execute(
            """SELECT id
                    FROM users
                    WHERE github = ?""",
            (github_user,),
        )
        result = cur.fetchone()
        if result:
            return result["id"]

    def _module_name_to_id(self, module_name: str) -> int | None:
        cur = self.conn.cursor()
        cur.execute(
            """SELECT id
                    FROM modules
                    WHERE name = ?""",
            (module_name,),
        )
        result = cur.fetchone()
        if result:
            return result["id"]


    def add_user(self, name: str, email: str, github: str):
        with self.conn:
            cur = self.conn.cursor()
            cur.execute(
                "INSERT INTO users(name, email, github) VALUES(?,?,?)",
                (name, email, github),
            )
            cur.close()

    def update_progress(self, user_id: int):
        cur = self.conn.cursor()

    def delete_session(self, github_user: str, module_name: str):
        user_id = self._github_to_id(github_user)
        module_id = self._module_name_to_id(module_name)
        if user_id is not None and module_id is not None:
            cur = self.conn.cursor()
            cur.execute(
                """DELETE FROM sessions
                    WHERE user_id = ? AND module_id = ?""",
                (user_id, module_id),
            )
            self.conn.commit()

    def get_session(self, github_user: str, module_name: str):
        cur = self.conn.cursor()
        cur.execute(
            """SELECT repo, created, current_step
            FROM sessions
            JOIN users on sessions.user_id = users.id
            JOIN modules on sessions.module_id = modules.id
            WHERE users.github = ? AND modules.name = ?""",
            (github_user, module_name),
        )
        return cur.fetchone()

    def get_modules(self):
        cur = self.conn.cursor()
        cur.execute("SELECT id, name, total_steps FROM modules")
        return [{"id": r[0], "name": r[1], "total_steps": r[2]} for r in cur.fetchall()]

    def update_session(self, repo: str, github_user: str, current_step: int):
        user_id = self._github_to_id(github_user)
        if user_id is None:
            return
        cur = self.conn.cursor()
        cur.execute(
            "UPDATE sessions SET repo = ?, current_step = ? WHERE user_id = ?",
            (repo, current_step, user_id),
        )
        self.conn.commit()

    def get_module(self, module_name: str):
        cur = self.conn.cursor()
        cur.execute(
            "SELECT id, name, base_repo, total_steps FROM modules WHERE name = ?",
            (module_name,),
        )
        return cur.fetchone()

    def create_session(self, github_user: str, module_name: str) -> bool:
        user_id = self._github_to_id(github_user)
        module_id = self._module_name_to_id(module_name)
        if user_id is None or module_id is None:
            return False
        cur = self.conn.cursor()
        try:
            timestamp = datetime.datetime.now(datetime.UTC).isoformat()
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
            return False
        finally:
            cur.close()
        return True

