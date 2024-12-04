import sqlite3

NOW_VERSION = 1


class FileManager:
    def __init__(self):
        self.db_path = "files.db"
        self.create_tables()

    def create_tables(self):
        conn = self.create_connection()
        with conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS version (
                    version INTEGER,
                    PRIMARY KEY (version)
                )
            """
            )
            self.query_create_files(cursor)
            self.query_create_tag_mng(cursor)
            self.query_create_file_tags(cursor)
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_tags_join_file_id ON file_tags(file_id)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_tags_join_tag_id ON file_tags(tag_id)"
            )
            self.version()

    def create_connection(self):
        return sqlite3.connect(self.db_path)

    def version(self):
        conn = self.create_connection()
        version_no = 0
        with conn:
            cursor = conn.cursor()
            query = """
                SELECT * FROM version
            """
            cursor.execute(
                query,
            )
            version = cursor.fetchone()
            version_no = version[0] if version else 0
            # バージョン更新
            if version_no != NOW_VERSION:
                cursor.execute("DELETE FROM version ")
                cursor.execute(
                    "INSERT INTO version (version) VALUES (?)",
                    (NOW_VERSION,),
                )
            # バージョンごとの対応
            if version_no == 0:
                cursor.execute("CREATE TABLE files_BK AS SELECT * FROM files")
                cursor.execute("DROP TABLE files")
                self.query_create_files(cursor)
                cursor.execute(
                    """
                        INSERT INTO files 
                        SELECT id, filename, filepath ,"", created_at FROM files_BK
                    """
                )
                cursor.execute("DROP TABLE files_BK")

    # ============================================
    def query_create_files(self, conn: sqlite3.Cursor) -> str:
        conn.execute(
            """
                CREATE TABLE IF NOT EXISTS files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT NOT NULL,
                    filepath TEXT NOT NULL,
                    memo TEXT,
                    created_at TIMESTAMP DEFAULT (datetime('now', 'localtime'))
                )
            """
        )

    def query_create_tag_mng(self, conn: sqlite3.Cursor) -> str:
        conn.execute(
            """
                CREATE TABLE IF NOT EXISTS tag_mng (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tag_name TEXT,
                    created_at TIMESTAMP DEFAULT  (datetime('now', 'localtime')),
                    updated_at TIMESTAMP DEFAULT  (datetime('now', 'localtime'))
                )
            """
        )

    def query_create_file_tags(self, conn: sqlite3.Cursor) -> str:
        conn.execute(
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
