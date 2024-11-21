import flet as ft
import os


class FileRow(ft.DataRow):
    def __init__(
        self, file_id, filename, filepath, tags, created_at, page, file_manager
    ):
        self.file_id = file_id
        self.file_manager = file_manager
        self.page = page

        # ファイルかフォルダかでアイコンを変更
        icon = (
            ft.icons.FOLDER if os.path.isdir(filepath) else ft.icons.INSERT_DRIVE_FILE
        )

        # タグ編集用のテキストフィールド
        self.tag_field = ft.TextField(
            value=tags if tags else "",
            border=ft.InputBorder.NONE,
            on_blur=self.update_tags,
        )

        cells = [
            ft.DataCell(
                ft.IconButton(
                    icon=icon,
                    tooltip=filepath,
                    on_click=lambda e: self.copy_path(filepath),
                )
            ),
            ft.DataCell(ft.Text(filename)),
            ft.DataCell(ft.Text(filepath)),
            ft.DataCell(self.tag_field),
            ft.DataCell(ft.Text(created_at)),
        ]
        super().__init__(cells=cells)

    def copy_path(self, path):
        self.page.set_clipboard(path)
        self.page.show_snack_bar(ft.SnackBar(content=ft.Text("パスをコピーしました")))

    def update_tags(self, e):
        conn = self.file_manager.create_connection()
        with conn:
            cursor = conn.cursor()
            # 既存のタグを削除
            cursor.execute("DELETE FROM tags WHERE file_id = ?", (self.file_id,))

            # 新しいタグを追加
            new_tags = [
                tag.strip() for tag in self.tag_field.value.split(",") if tag.strip()
            ]
            for tag in new_tags:
                cursor.execute(
                    "INSERT INTO tags (file_id, tag_name) VALUES (?, ?)",
                    (self.file_id, tag),
                )
        conn.close()


class FileListPage:
    def __init__(self, file_manager):
        self.file_manager = file_manager
        self.init_components()

    def init_components(self):
        self.search_field = ft.TextField(
            label="ファイル名で検索", width=400, on_change=self.search_files
        )

        self.tag_filter = ft.TextField(
            label="タグで検索", width=400, on_change=self.search_files
        )

        # DataTableの列幅を固定
        self.files_table = ft.DataTable(
            columns=[
                ft.DataColumn(
                    ft.Container(
                        content=ft.Text("種類"), width=50, tooltip="ファイルの種類"
                    )
                ),
                ft.DataColumn(
                    ft.Container(
                        content=ft.Text("ファイル名"), width=200, tooltip="ファイル名"
                    )
                ),
                ft.DataColumn(
                    ft.Container(
                        content=ft.Text("パス"), width=300, tooltip="ファイルパス"
                    )
                ),
                ft.DataColumn(
                    ft.Container(
                        content=ft.Text("タグ"),
                        width=300,
                        tooltip="タグ（クリックで編集可能）",
                    )
                ),
                ft.DataColumn(
                    ft.Container(
                        content=ft.Text("作成日時"), width=150, tooltip="作成日時"
                    )
                ),
            ],
            rows=[],
            horizontal_margin=10,
            horizontal_lines=ft.BorderSide(1, ft.colors.GREY_300),
        )

    def build(self, page: ft.Page):
        self._load_files_data(page)
        return ft.Column(
            [
                ft.Row([self.search_field, self.tag_filter]),
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Container(
                                content=self.files_table,
                                border=ft.border.all(1, ft.colors.GREY_300),
                                border_radius=10,
                                padding=10,
                            )
                        ],
                        scroll=ft.ScrollMode.AUTO,
                        expand=True,
                    ),
                    height=400,
                    expand=True,
                ),
            ]
        )

    def _load_files_data(self, page):
        """ファイルデータを読み込んでテーブルを更新"""
        conn = self.file_manager.create_connection()
        with conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT 
                    f.id, 
                    f.filename, 
                    f.filepath, 
                    GROUP_CONCAT(t.tag_name) as tags,
                    f.created_at
                FROM files f
                LEFT JOIN tags t ON f.id = t.file_id
                GROUP BY f.id
                ORDER BY f.created_at DESC
                """
            )
            files = cursor.fetchall()

            # テーブルの行を更新
            self.files_table.rows = [
                FileRow(
                    file_id=file[0],
                    filename=file[1],
                    filepath=file[2],
                    tags=file[3],
                    created_at=file[4],
                    page=page,
                    file_manager=self.file_manager,
                )
                for file in files
            ]
        conn.close()
        if self.files_table.page:
            self.files_table.update()

    def search_files(self, e):
        """検索条件でファイル一覧を絞り込み"""
        search_text = self.search_field.value.lower()
        tag_text = self.tag_filter.value.lower()

        conn = self.file_manager.create_connection()
        with conn:
            cursor = conn.cursor()
            query = """
                SELECT 
                    f.id, 
                    f.filename, 
                    f.filepath, 
                    GROUP_CONCAT(t.tag_name) as tags,
                    f.created_at
                FROM files f
                LEFT JOIN tags t ON f.id = t.file_id
                GROUP BY f.id
                HAVING (? = '' OR LOWER(f.filename) LIKE ?)
                AND (? = '' OR LOWER(tags) LIKE ?)
                ORDER BY f.created_at DESC
            """
            cursor.execute(
                query, (search_text, f"%{search_text}%", tag_text, f"%{tag_text}%")
            )
            files = cursor.fetchall()

            # 検索結果でテーブルを更新
            self.files_table.rows = [
                FileRow(
                    file_id=file[0],
                    filename=file[1],
                    filepath=file[2],
                    tags=file[3],
                    created_at=file[4],
                    page=self.files_table.page,
                    file_manager=self.file_manager,
                )
                for file in files
            ]
        conn.close()
        if self.files_table.page:
            self.files_table.update()
