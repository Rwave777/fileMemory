import flet as ft
import os


class TableInfoDialog(ft.AlertDialog):
    def __init__(self, table_name, file_manager):
        super().__init__()
        self.title = ft.Text(f"{table_name}テーブルの構成")
        self.file_manager = file_manager

        conn = file_manager.create_connection()
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        conn.close()

        # カラム情報を表形式で表示
        column_data = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("カラム名")),
                ft.DataColumn(ft.Text("型")),
                ft.DataColumn(ft.Text("NULL許可")),
                ft.DataColumn(ft.Text("主キー")),
            ],
            rows=[
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(col[1])),  # カラム名
                        ft.DataCell(ft.Text(col[2])),  # 型
                        ft.DataCell(ft.Text("○" if col[3] == 0 else "×")),  # NULL許可
                        ft.DataCell(ft.Text("○" if col[5] == 1 else "×")),  # 主キー
                    ]
                )
                for col in columns
            ],
        )

        self.content = column_data


class RecordsDialog(ft.AlertDialog):
    def __init__(self, table_name, file_manager):
        super().__init__()
        self.title = ft.Text(f"{table_name}テーブルのレコード")
        self.file_manager = file_manager

        conn = file_manager.create_connection()
        cursor = conn.cursor()

        # カラム名を取得
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [col[1] for col in cursor.fetchall()]

        # レコードを取得
        cursor.execute(f"SELECT * FROM {table_name}")
        records = cursor.fetchall()
        conn.close()

        # レコードを表形式で表示
        records_data = ft.DataTable(
            columns=[ft.DataColumn(ft.Text(col)) for col in columns],
            rows=[
                ft.DataRow(cells=[ft.DataCell(ft.Text(str(value))) for value in record])
                for record in records
            ],
        )
        self.content = ft.Row(
            [
                ft.Column(
                    controls=[records_data],
                    scroll=ft.ScrollMode.ALWAYS,
                    expand=True,
                    height=450,
                )
            ],
            scroll="auto",
        )


class TableInfoRow(ft.DataRow):
    def __init__(self, table_name, record_count, page, file_manager):
        # セルを作成
        cells = [
            ft.DataCell(
                ft.TextButton(
                    text=table_name,
                    on_click=lambda _: self.show_table_info(
                        page, table_name, file_manager
                    ),
                )
            ),
            ft.DataCell(
                ft.TextButton(
                    text=str(record_count),
                    on_click=lambda _: self.show_records(
                        page, table_name, file_manager
                    ),
                )
            ),
        ]
        # 親クラスの初期化時にcellsを渡す
        super().__init__(cells=cells)

    def show_table_info(self, page, table_name, file_manager):
        dialog = TableInfoDialog(table_name, file_manager)
        page.dialog = dialog
        dialog.open = True
        page.update()

    def show_records(self, page, table_name, file_manager):
        dialog = RecordsDialog(table_name, file_manager)
        page.dialog = dialog
        dialog.open = True
        page.update()


class DatabaseInfoPage:
    def __init__(self, file_manager):
        self.file_manager = file_manager
        self.init_components()

    def init_components(self):
        self.db_info = ft.Text("", size=16)
        self.file_count = ft.Text("", size=16)
        self.tag_count = ft.Text("", size=16)
        self.db_path = ft.Text("", size=16)

        # テーブル一覧用のDataTableを追加
        self.table_list = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("テーブル名")),
                ft.DataColumn(ft.Text("レコード数")),
            ],
            rows=[],
        )

    def build(self, page: ft.Page):
        self._update_table_list(page)  # テーブル一覧を更新
        return ft.Column(
            [
                ft.Card(
                    content=ft.Container(
                        content=ft.Column(
                            [
                                ft.Text(
                                    "テーブル一覧",
                                    size=24,
                                    weight=ft.FontWeight.BOLD,
                                ),
                                self.table_list,
                            ]
                        ),
                        padding=20,
                    )
                ),
            ],
            spacing=20,
        )

    def _update_table_list(self, page):
        """テーブル一覧を更新"""
        conn = self.file_manager.create_connection()
        with conn:
            cursor = conn.cursor()
            # テーブル一覧を取得
            cursor.execute(
                """
                SELECT name FROM sqlite_master 
                WHERE type='table' 
                AND name NOT LIKE 'sqlite_%'
            """
            )
            tables = cursor.fetchall()

            # 各テーブルのレコード数を取得してDataTableRowsを作成
            self.table_list.rows = []
            for table in tables:
                table_name = table[0]
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                self.table_list.rows.append(
                    TableInfoRow(table_name, count, page, self.file_manager)
                )
        conn.close()

    def open_db_location(self, e):
        db_path = os.path.abspath(self.file_manager.db_path)
        if os.path.exists(db_path):
            os.startfile(os.path.dirname(db_path))
