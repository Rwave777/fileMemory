import os
import flet as ft
from database.file_manager import FileManager


class MainApp:
    def __init__(self):
        self.file_manager = FileManager()
        self.success_message = ft.Text("", color=ft.colors.GREEN)
        self.picked_files = []

    def main(self, page: ft.Page):
        page.title = "ファイル管理アプリ"
        page.padding = 0
        page.window_width = 800
        page.window_height = 600

        # ナビゲーションレールの追加
        self.rail = ft.NavigationRail(
            selected_index=0,
            label_type=ft.NavigationRailLabelType.ALL,
            min_width=100,
            min_extended_width=400,
            group_alignment=-0.9,
            destinations=[
                ft.NavigationRailDestination(
                    icon=ft.icons.UPLOAD_FILE,
                    selected_icon=ft.icons.UPLOAD_FILE,
                    label="ファイル登録",
                ),
                ft.NavigationRailDestination(
                    icon=ft.icons.FILE_COPY,
                    selected_icon=ft.icons.FILE_COPY,
                    label="ファイル一覧",
                ),
                ft.NavigationRailDestination(icon=ft.icons.STORAGE, label="DB情報"),
            ],
            on_change=lambda e: self.change_page(e),
        )

        # ファイルピッカーの設定を変更
        self.file_picker = ft.FilePicker(on_result=self.on_file_picker_result)
        self.folder_picker = ft.FilePicker(on_result=self.on_folder_picker_result)
        page.overlay.extend([self.file_picker, self.folder_picker])

        # ドラッグ&ドロップエリアの修正
        drop_content = ft.Container(
            content=ft.Column(
                [
                    ft.Text("ファイルまたはフォルダをドロップ", size=20),
                    ft.Row(
                        [
                            ft.ElevatedButton(
                                "ファイルを選択",
                                on_click=lambda _: self.file_picker.pick_files(),
                                icon=ft.icons.FILE_UPLOAD,
                            ),
                            ft.ElevatedButton(
                                "フォルダを選択",
                                on_click=lambda _: self.folder_picker.get_directory_path(),
                                icon=ft.icons.FOLDER_OPEN,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=20,
            ),
            width=400,
            height=200,
            bgcolor=ft.colors.BLUE_GREY_100,
            border_radius=10,
            padding=20,
            alignment=ft.alignment.center,
        )

        self.drop_area = ft.DragTarget(
            group="files",
            content=drop_content,
            on_accept=self.on_drop,
            on_will_accept=lambda e: e.data.startswith("files://") if e.data else False,
        )

        # タグ入力フィールド
        self.tag_input = ft.TextField(label="タグを入力（カンマ区切り）", width=400)

        # 登録ボタンの追加
        self.submit_button = ft.ElevatedButton(
            text="登録", on_click=self.on_submit, width=400
        )

        # ファイル一覧表示用
        self.files_list = ft.ListView(expand=True)
        self.search_field = ft.TextField(
            label="検索", width=400, on_change=self.search_files
        )
        self.tag_filter = ft.TextField(
            label="タグで検索", width=400, on_change=self.search_files
        )

        # メインコンテンツエリア
        self.content_area = ft.Container(
            content=ft.Column(
                [
                    self.drop_area,
                    self.tag_input,
                    self.submit_button,
                    self.success_message,
                ]
            ),
            padding=20,
        )

        # レイアウト
        page.add(
            ft.Row(
                [self.rail, ft.VerticalDivider(width=1), self.content_area], expand=True
            )
        )

    def change_page(self, e):
        if e.control.selected_index == 0:
            self.content_area.content = ft.Column(
                [
                    self.drop_area,
                    self.tag_input,
                    self.submit_button,
                    self.success_message,
                ]
            )
            self.content_area.update()
        elif e.control.selected_index == 1:
            # まずコンテンツを更新
            self.content_area.content = ft.Column(
                [self.search_field, self.tag_filter, self.files_list]
            )
            self.content_area.update()
            # その後でファイル一覧を読み込む
            self.load_files()
        else:  # DB情報ページ
            self.show_database_info()

    def on_drag_over(self, e):
        """ドラッグオーバー時のイベントハンドラ"""
        e.accept()

    def on_drop(self, e: ft.DragEndEvent):
        """ドロップ時のイベントハンドラ"""
        if e.data and e.data.startswith("files://"):
            path = e.data.replace("files://", "")
            self.process_dropped_item(path)

    def process_dropped_item(self, path: str):
        """ドロップされたアイテム（ファイル/フォルダ）の処理"""
        if os.path.exists(path):
            self.current_file_path = path
            name = os.path.basename(path)
            type_text = "フォルダ" if os.path.isdir(path) else "ファイル"
            self.success_message.value = f"{type_text}準備完了: {name}\nパス: {path}"
            self.success_message.update()

    def on_file_picker_result(self, e: ft.FilePickerResultEvent):
        """ファイル選択ダイアログの結果処理"""
        if e.files:
            file_path = e.files[0].path
            self.process_dropped_item(file_path)

    def on_folder_picker_result(self, e: ft.FilePickerResultEvent):
        """フォルダ選択ダイアログの結果処理"""
        if e.path:
            self.process_dropped_item(e.path)

    def on_submit(self, e):
        """登録ボタン押下時の処理"""
        if hasattr(self, "current_file_path"):
            path = self.current_file_path
            name = os.path.basename(path)
            tags = [
                tag.strip() for tag in self.tag_input.value.split(",") if tag.strip()
            ]

            # 新しい接続を作成
            conn = self.file_manager.create_connection()
            with conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO files (filename, filepath) VALUES (?, ?)",
                    (name, path),
                )
                file_id = cursor.lastrowid

                for tag in tags:
                    cursor.execute(
                        "INSERT INTO tags (file_id, tag_name) VALUES (?, ?)",
                        (file_id, tag),
                    )
            conn.close()

            self.tag_input.value = ""
            self.success_message.value = "正常に登録されました！"
            self.tag_input.update()
            self.success_message.update()

    def load_files(self):
        self.files_list.controls.clear()
        # 新しい接続を作成
        conn = self.file_manager.create_connection()
        with conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT f.id, f.filename, f.filepath, GROUP_CONCAT(t.tag_name) as tags
                FROM files f
                LEFT JOIN tags t ON f.id = t.file_id
                GROUP BY f.id
            """
            )
            files = cursor.fetchall()

            for file in files:
                self.files_list.controls.append(
                    ft.ListTile(
                        title=ft.Text(file[1]),
                        subtitle=ft.Text(f"タグ: {file[3] if file[3] else ''}"),
                        on_click=lambda x, path=file[2]: self.open_file_location(path),
                    )
                )
        conn.close()
        self.files_list.update()

    def search_files(self, e):
        search_text = self.search_field.value.lower()
        tag_text = self.tag_filter.value.lower()

        self.files_list.controls.clear()
        # 新しい接続を作成
        conn = self.file_manager.create_connection()
        with conn:
            cursor = conn.cursor()
            query = """
                SELECT f.id, f.filename, f.filepath, GROUP_CONCAT(t.tag_name) as tags
                FROM files f
                LEFT JOIN tags t ON f.id = t.file_id
                GROUP BY f.id
                HAVING (? = '' OR LOWER(f.filename) LIKE ?)
                AND (? = '' OR LOWER(tags) LIKE ?)
            """
            cursor.execute(
                query, (search_text, f"%{search_text}%", tag_text, f"%{tag_text}%")
            )
            files = cursor.fetchall()

            for file in files:
                self.files_list.controls.append(
                    ft.ListTile(
                        title=ft.Text(file[1]),
                        subtitle=ft.Text(f"タグ: {file[3] if file[3] else ''}"),
                        on_click=lambda x, path=file[2]: self.open_file_location(path),
                    )
                )
        conn.close()
        self.files_list.update()

    def open_file_location(self, filepath):
        if os.path.exists(filepath):
            os.startfile(os.path.dirname(filepath))

    def show_database_info(self):
        conn = self.file_manager.create_connection()
        with conn:
            cursor = conn.cursor()

            # テーブル一覧を取得
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()

            # テーブルごとのレコード件数を取得
            table_data = []
            for table in tables:
                table_name = table[0]
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                table_data.append((table_name, count))

        conn.close()

        # データテーブルの作成
        data_rows = []
        for table_name, count in table_data:
            data_rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(
                            ft.TextButton(
                                text=table_name,
                                on_click=lambda e, t=table_name: self.show_table_structure(
                                    t
                                ),
                            )
                        ),
                        ft.DataCell(
                            ft.TextButton(
                                text=str(count),
                                on_click=lambda e, t=table_name: self.show_table_data(
                                    t
                                ),
                            )
                        ),
                    ]
                )
            )

        data_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("テーブル名")),
                ft.DataColumn(ft.Text("レコード件数")),
            ],
            rows=data_rows,
        )

        # データベース情報を表示
        self.content_area.content = ft.Column(
            [
                ft.Text("データベース構造", size=24, weight=ft.FontWeight.BOLD),
                ft.Container(
                    content=data_table,
                    padding=10,
                    bgcolor=ft.colors.BLUE_GREY_50,
                    border_radius=5,
                ),
            ],
            scroll=ft.ScrollMode.AUTO,
        )
        self.content_area.update()

    def show_table_structure(self, table_name: str):
        conn = self.file_manager.create_connection()
        with conn:
            cursor = conn.cursor()
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()

        conn.close()

        # カラム情報をデータテーブルで表示
        data_rows = []
        for col in columns:
            data_rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(str(col[0]))),  # cid
                        ft.DataCell(ft.Text(col[1])),  # name
                        ft.DataCell(ft.Text(col[2])),  # type
                        ft.DataCell(ft.Text("Yes" if col[3] else "No")),  # notnull
                        ft.DataCell(ft.Text(str(col[4]))),  # dflt_value
                        ft.DataCell(ft.Text("Yes" if col[5] else "No")),  # pk
                    ]
                )
            )

        data_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("ID")),
                ft.DataColumn(ft.Text("カラム名")),
                ft.DataColumn(ft.Text("型")),
                ft.DataColumn(ft.Text("NOT NULL")),
                ft.DataColumn(ft.Text("デフォルト値")),
                ft.DataColumn(ft.Text("主キー")),
            ],
            rows=data_rows,
        )

        self.content_area.content = ft.Column(
            [
                ft.Row(
                    [
                        ft.IconButton(
                            icon=ft.icons.ARROW_BACK,
                            on_click=lambda _: self.show_database_info(),
                        ),
                        ft.Text(
                            f"テーブル構造: {table_name}",
                            size=24,
                            weight=ft.FontWeight.BOLD,
                        ),
                    ]
                ),
                ft.Container(
                    content=data_table,
                    padding=10,
                    bgcolor=ft.colors.BLUE_GREY_50,
                    border_radius=5,
                ),
            ],
            scroll=ft.ScrollMode.AUTO,
        )
        self.content_area.update()

    def show_table_data(self, table_name: str):
        conn = self.file_manager.create_connection()
        with conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM {table_name}")
            records = cursor.fetchall()

            # カラム名を取得
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [col[1] for col in cursor.fetchall()]

        conn.close()

        # データをDataTableで表示
        data_rows = []
        for record in records:
            cells = [ft.DataCell(ft.Text(str(value))) for value in record]
            data_rows.append(ft.DataRow(cells=cells))

        data_table = ft.DataTable(
            columns=[ft.DataColumn(ft.Text(col)) for col in columns],
            rows=data_rows,
        )

        # テーブルデータを表示
        self.content_area.content = ft.Column(
            [
                ft.Row(
                    [
                        ft.IconButton(
                            icon=ft.icons.ARROW_BACK,
                            on_click=lambda _: self.show_database_info(),
                        ),
                        ft.Text(
                            f"テーブル: {table_name}",
                            size=24,
                            weight=ft.FontWeight.BOLD,
                        ),
                    ]
                ),
                ft.Container(
                    content=data_table,
                    padding=10,
                    bgcolor=ft.colors.BLUE_GREY_50,
                    border_radius=5,
                ),
            ],
            scroll=ft.ScrollMode.AUTO,
        )
        self.content_area.update()
