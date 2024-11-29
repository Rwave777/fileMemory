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
                    created_at TIMESTAMP DEFAULT (datetime('now', 'localtime'))
                )
            """
            )
            self.conn.execute(
                """
                CREATE TABLE IF NOT EXISTS tag_mng (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tag_name TEXT,
                    created_at TIMESTAMP DEFAULT  (datetime('now', 'localtime')),
                    updated_at TIMESTAMP DEFAULT  (datetime('now', 'localtime'))
                )
            """
            )
            self.conn.execute(
                """
                CREATE TABLE IF NOT EXISTS file_tags (
                    file_id INTEGER,
                    tag_id INTEGER,
                    number_of INTEGER,
                    created_at TIMESTAMP DEFAULT  (datetime('now', 'localtime')),
                    PRIMARY KEY (file_id, tag_id),
                    FOREIGN KEY (file_id) REFERENCES files(id),
                    FOREIGN KEY (tag_id) REFERENCES tag_mng(id)
                )
            """
            )
            self.conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_tags_join_file_id ON file_tags(file_id)"
            )
            self.conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_tags_join_tag_id ON file_tags(tag_id)"
            )

    def create_connection(self):
        return sqlite3.connect(self.db_path)
