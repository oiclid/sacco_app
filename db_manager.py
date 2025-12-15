# db_manager.py
import sqlite3
import shutil
import os
from typing import List, Dict, Any, Tuple
from contextlib import contextmanager


class DBManager:
    def __init__(self, db_path: str):
        """
        Initialize the database manager.
        :param db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        self.ensure_tables_exist()

    def ensure_tables_exist(self):
        """Ensure all core tables exist."""
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS LoginTbl (
                Username TEXT PRIMARY KEY,
                Password TEXT NOT NULL,
                Status TEXT,
                Maintain CHAR,
                Operations CHAR,
                EditPriv CHAR,
                Reports CHAR
            )
        """)
        self.conn.commit()

    def get_tables(self) -> List[str]:
        """Return a list of all table names."""
        self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        return [row["name"] for row in self.cursor.fetchall()]

    def get_columns(self, table_name: str) -> List[Dict[str, Any]]:
        """Return column info for a given table."""
        self.cursor.execute(f"PRAGMA table_info({table_name})")
        columns = []
        for col in self.cursor.fetchall():
            columns.append({
                "id": col[0],
                "name": col[1],
                "type": col[2],
                "not_null": bool(col[3]),
                "default_value": col[4],
                "primary_key": bool(col[5])
            })
        return columns

    def fetch_all(self, table_name: str, where: str = "", params: Tuple = ()) -> List[Dict[str, Any]]:
        """Fetch all rows from a table optionally filtered."""
        query = f"SELECT * FROM {table_name}"
        if where:
            query += f" WHERE {where}"
        self.cursor.execute(query, params)
        return [dict(row) for row in self.cursor.fetchall()]

    def fetch_one(self, table_name: str, where: str = "", params: Tuple = ()) -> Dict[str, Any]:
        """Fetch a single row."""
        query = f"SELECT * FROM {table_name}"
        if where:
            query += f" WHERE {where}"
        self.cursor.execute(query, params)
        row = self.cursor.fetchone()
        return dict(row) if row else None

    def fetch_value(self, table_name: str, column: str, where: str = "", params: Tuple = ()) -> Any:
        """Fetch a single value."""
        query = f"SELECT {column} FROM {table_name}"
        if where:
            query += f" WHERE {where}"
        self.cursor.execute(query, params)
        row = self.cursor.fetchone()
        return row[0] if row else None

    def insert(self, table_name: str, data: Dict[str, Any]):
        """Insert a row into a table."""
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['?'] * len(data))
        values = tuple(data.values())
        query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
        self.cursor.execute(query, values)
        self.conn.commit()

    def update(self, table_name: str, data: Dict[str, Any], where: str, params: Tuple):
        """Update rows in a table."""
        set_clause = ', '.join([f"{k}=?" for k in data.keys()])
        values = tuple(data.values()) + params
        query = f"UPDATE {table_name} SET {set_clause} WHERE {where}"
        self.cursor.execute(query, values)
        self.conn.commit()

    def delete(self, table_name: str, where: str, params: Tuple):
        """Delete rows from a table."""
        query = f"DELETE FROM {table_name} WHERE {where}"
        self.cursor.execute(query, params)
        self.conn.commit()

    def backup_database(self, backup_path: str):
        """Backup the database file to a given path."""
        self.conn.commit()
        shutil.copy(self.db_path, backup_path)

    def close(self):
        """Close the database connection."""
        self.conn.close()

    @staticmethod
    def import_existing_database(existing_path: str, new_path: str):
        """Copy an existing SQLite database file."""
        if not os.path.exists(existing_path):
            raise FileNotFoundError(f"Source database not found: {existing_path}")
        shutil.copy(existing_path, new_path)

    def add_column_if_not_exists(self, table_name: str, column_name: str, column_type: str, default_value: Any = None):
        """Add a new column if it doesn't exist."""
        existing_cols = [col['name'] for col in self.get_columns(table_name)]
        if column_name not in existing_cols:
            default = f"DEFAULT '{default_value}'" if default_value is not None else ""
            query = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type} {default}"
            self.cursor.execute(query)
            self.conn.commit()

    def create_table_if_not_exists(self, table_name: str, columns: Dict[str, str], primary_key: str = None):
        """Create a table dynamically if it doesn't exist."""
        cols_def = []
        for col, col_type in columns.items():
            col_def = f"{col} {col_type}"
            if primary_key == col:
                col_def += " PRIMARY KEY"
            cols_def.append(col_def)
        query = f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(cols_def)})"
        self.cursor.execute(query)
        self.conn.commit()

    def ensure_columns(self, table_name: str, required_columns: Dict[str, str]):
        """Ensure a table has all required columns."""
        existing = {col['name'] for col in self.get_columns(table_name)}
        for col_name, col_type in required_columns.items():
            if col_name not in existing:
                self.add_column_if_not_exists(table_name, col_name, col_type)

    def execute_query(self, query: str, params: Tuple = ()) -> List[Dict[str, Any]]:
        """Execute a custom query safely and return results."""
        self.cursor.execute(query, params)
        self.conn.commit()
        return [dict(row) for row in self.cursor.fetchall()]

    @contextmanager
    def transaction(self):
        """Context manager for safe transaction handling."""
        try:
            yield
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            raise e

    def get_table_info(self) -> List[Dict[str, Any]]:
        """Return all tables with row counts."""
        tables = self.get_tables()
        info = []
        for tbl in tables:
            self.cursor.execute(f"SELECT COUNT(*) FROM {tbl}")
            count = self.cursor.fetchone()[0]
            info.append({"table": tbl, "rows": count})
        return info
