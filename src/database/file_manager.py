import sqlite3


class FileManager:
    def __init__(self):
        self.db_path = "files.db"
        self.conn = sqlite3.connect("files.db")
        self.create_tables()

    def create_tables(self):
        with self.conn:
            self.conn.execute(
                """
                CREATE TABLE IF NOT EXISTS files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT NOT NULL,
                    filepath TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )
            self.conn.execute(
                """
                CREATE TABLE IF NOT EXISTS tags (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_id INTEGER,
                    tag_name TEXT NOT NULL,
                    FOREIGN KEY (file_id) REFERENCES files (id)
                )
            """
            )

    def create_connection(self):
        return sqlite3.connect(self.db_path)
