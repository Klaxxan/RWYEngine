import sqlite3
from pathlib import Path

DB_FILE = "writer_memory.db"


class Database:
    def __init__(self):
        self.db_path = Path(DB_FILE)
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.create_tables()

    def create_tables(self):
        cursor = self.conn.cursor()

        # Entries table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            category TEXT,
            tags TEXT,
            synonyms TEXT
        )
        """)

        # Relationships table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS relationships (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entry_a INTEGER NOT NULL,
            entry_b INTEGER NOT NULL,
            type TEXT,
            FOREIGN KEY(entry_a) REFERENCES entries(id),
            FOREIGN KEY(entry_b) REFERENCES entries(id)
        )
        """)

        self.conn.commit()

    # --------------------------
    # ENTRY OPERATIONS
    # --------------------------

    def add_entry(self, title, description="", category="", tags="", synonyms=""):
        cursor = self.conn.cursor()
        cursor.execute("""
        INSERT INTO entries (title, description, category, tags, synonyms)
        VALUES (?, ?, ?, ?, ?)
        """, (title, description, category, tags, synonyms))
        self.conn.commit()
        return cursor.lastrowid

    def get_entry(self, entry_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM entries WHERE id = ?", (entry_id,))
        return cursor.fetchone()

    def get_all_entries(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM entries")
        return cursor.fetchall()

    def update_entry(self, entry_id, title, description, category, tags, synonyms):
        cursor = self.conn.cursor()
        cursor.execute("""
        UPDATE entries
        SET title = ?, description = ?, category = ?, tags = ?, synonyms = ?
        WHERE id = ?
        """, (title, description, category, tags, synonyms, entry_id))
        self.conn.commit()

    def delete_entry(self, entry_id):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM entries WHERE id = ?", (entry_id,))
        self.conn.commit()

    def delete_entry_and_relationships(self, entry_id):
        """
        Delete an entry and any relationships that reference it.
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            DELETE FROM relationships
            WHERE entry_a = ? OR entry_b = ?
        """, (entry_id, entry_id))

        cursor.execute("DELETE FROM entries WHERE id = ?", (entry_id,))
        self.conn.commit()

    # --------------------------
    # RELATIONSHIP OPERATIONS
    # --------------------------

    def add_relationship(self, entry_a, entry_b, rel_type=""):
        cursor = self.conn.cursor()
        cursor.execute("""
        INSERT INTO relationships (entry_a, entry_b, type)
        VALUES (?, ?, ?)
        """, (entry_a, entry_b, rel_type))
        self.conn.commit()
        return cursor.lastrowid

    def get_relationships_for_entry(self, entry_id):
        cursor = self.conn.cursor()
        cursor.execute("""
        SELECT * FROM relationships
        WHERE entry_a = ? OR entry_b = ?
        """, (entry_id, entry_id))
        return cursor.fetchall()

    def get_all_relationships(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM relationships")
        return cursor.fetchall()

    def delete_relationship(self, rel_id):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM relationships WHERE id = ?", (rel_id,))
        self.conn.commit()

    # --------------------------
    # CLEANUP
    # --------------------------

    def close(self):
        self.conn.close()

