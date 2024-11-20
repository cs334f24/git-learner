import datetime
import sqlite3
from typing import TypedDict


class SessionInfo(TypedDict):
    repo: str
    created: datetime.datetime
    current_step: int


class ModuleInfo(TypedDict):
    name: str
    base_repo: str | None
    total_steps: int


class SessionsDB:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def _github_to_id(self, github_user: str) -> int | None:
        cur = self.conn.cursor()
        cur.execute(
            "SELECT id FROM users WHERE github = ?",
            (github_user,),
        )
        result = cur.fetchone()
        if result:
            return result["id"]

    def _module_name_to_id(self, module_name: str) -> int | None:
        cur = self.conn.cursor()
        cur.execute(
            "SELECT id FROM modules WHERE name = ?",
            (module_name,),
        )
        result = cur.fetchone()
        if result:
            return result["id"]

    def delete(self, github_user: str, module_name: str):
        user_id = self._github_to_id(github_user)
        module_id = self._module_name_to_id(module_name)
        if user_id is not None and module_id is not None:
            cur = self.conn.cursor()
            cur.execute(
                "DELETE FROM sessions WHERE user_id = ? AND module_id = ?",
                (user_id, module_id),
            )
            self.conn.commit()

    def get(self, github_user: str, module_name: str) -> SessionInfo:
        cur = self.conn.cursor()
        cur.execute(
            """SELECT repo, created, current_step
            FROM sessions
            JOIN users on sessions.user_id = users.id
            JOIN modules on sessions.module_id = modules.id
            WHERE users.github = ? AND modules.name = ?""",
            (github_user, module_name),
        )
        result = cur.fetchone()
        return {
            "repo": result["repo"],
            "created": datetime.datetime.fromisoformat(result["created"]),
            "current_step": result["current_step"],
        }

    def create(self, github_user: str, module_name: str, repo_name: str):
        user_id = self._github_to_id(github_user)
        module_id = self._module_name_to_id(module_name)
        if user_id is None or module_id is None:
            return False
        cur = self.conn.cursor()
        try:
            timestamp = datetime.datetime.now(datetime.UTC).isoformat()
            cur.execute(
                """
                INSERT INTO sessions(user_id, module_id, repo, created, current_step)
                VALUES(?,?,?,?,?)
                """,
                (user_id, module_id, repo_name, timestamp, 0),
            )
            self.conn.commit()
        except Exception:
            self.conn.rollback()
            return False
        finally:
            cur.close()
        return True

    def update(self, github_user: str, module_name: str, step: int):
        user_id = self._github_to_id(github_user)
        module_id = self._module_name_to_id(module_name)
        if user_id is None or module_id is None:
            return
        cur = self.conn.cursor()
        cur.execute(
            "UPDATE sessions SET current_step = ? WHERE user_id = ? AND module_id = ?",
            (step, user_id, module_id),
        )
        self.conn.commit()


class ModulesDB:
    """Helper class to interact with modules in the database"""
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def _name_to_id(self, name: str) -> int | None:
        cur = self.conn.cursor()
        cur.execute(
            "SELECT id FROM modules WHERE name = ?",
            (name,),
        )
        result = cur.fetchone()
        if result:
            return result["id"]

    def get(self, name: str | None = None) -> list[ModuleInfo]:
        """Get info for a module or all modules if no name is provided"""
        cur = self.conn.cursor()
        if name:
            cur.execute(
                "SELECT name, base_repo, total_steps FROM modules WHERE name = ?",
                (name,),
            )
        else:
            cur.execute("SELECT name, base_repo, total_steps FROM modules")

        return cur.fetchall()


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
        self._sessions = SessionsDB(self.conn)
        self._modules = ModulesDB(self.conn)

    def add_user(self, name: str, email: str, github: str):
        with self.conn:
            cur = self.conn.cursor()
            cur.execute(
                "INSERT INTO users(name, email, github) VALUES(?,?,?)",
                (name, email, github),
            )
            cur.close()

    @property
    def sessions(self):
        """Helper class to interact with sessions"""
        return self.sessions

    @property
    def modules(self):
        """Helper class to ineract with modules"""
        return self._modules
