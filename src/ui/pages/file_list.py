import flet as ft
import os
from util.util_query import insert_file_joined


class FileRow(ft.DataRow):
    ACTION_EDIT = 1
    ACTION_DELETE = 2

    def __init__(
        self,
        file_id,
        filename,
        filepath,
        tags,
        created_at,
        page,
        file_manager,
        action_callback,
    ):
        self.file_id = file_id
        self.filename = filename
        self.filepath = filepath
        self.tags = tags
        self.created_at = created_at
        self.file_manager = file_manager
        self.page = page
        self.action_callback: function = action_callback

        # ファイルかフォルダかでアイコンを変更
        icon = (
            ft.icons.FOLDER if os.path.isdir(filepath) else ft.icons.INSERT_DRIVE_FILE
        )

        cells = [
            ft.DataCell(
                ft.IconButton(
                    icon=icon,
                    tooltip=(
                        "フォルダを開く"
                        if os.path.isdir(filepath)
                        else "ファイルの場所を開く"
                    ),
                    on_click=lambda e: self.open_location(filepath),
                )
            ),
            ft.DataCell(ft.Text(filename), on_double_tap=self.show_edit_dialog),
            ft.DataCell(
                ft.TextButton(
                    text=filepath,
                    tooltip="パスをコピー",
                    on_click=lambda e: self.copy_path(filepath),
                ),
                on_double_tap=self.show_edit_dialog,
            ),
            ft.DataCell(
                ft.Text(tags if tags else ""), on_double_tap=self.show_edit_dialog
            ),
            ft.DataCell(
                ft.IconButton(
                    icon=ft.icons.DELETE,
                    tooltip="削除",
                    on_click=self.delete_row,
                    icon_color=ft.colors.RED_400,
                )
            ),
        ]
        super().__init__(cells=cells)

    def open_location(self, path):
        """ファイルの場所を開く"""
        if os.path.exists(path):
            if os.path.isdir(path):
                os.startfile(path)  # フォルダを直接開く
            else:
                os.startfile(os.path.dirname(path))  # ファイルの場所を開く

    def copy_path(self, path):
        """パスをクリップボードにコピー"""
        self.page.set_clipboard(path)
        self.page.show_snack_bar(ft.SnackBar(content=ft.Text("パスをコピーしました")))

    def delete_row(self, e):
        """行を削除"""

        def confirm_delete(e):
            if e.control.result:
                conn = self.file_manager.create_connection()
                with conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "DELETE FROM file_tags WHERE file_id = ?", (self.file_id,)
                    )
                    cursor.execute("DELETE FROM files WHERE id = ?", (self.file_id,))
                conn.close()
                # ダイアログを閉じる
                self.page.dialog.open = False
                self.page.update()
                self.action_callback(self.ACTION_DELETE)

        # 削除確認ダイアログを表示
        self.page.dialog = ft.AlertDialog(
            title=ft.Text("確認"),
            content=ft.Text("このファイル情報を削除してもよろしいですか？"),
            actions=[
                ft.TextButton("キャンセル", on_click=lambda e: self.close_dialog(e)),
                ft.TextButton(
                    "削除", on_click=lambda e: self.handle_delete(e, confirm_delete)
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.dialog.open = True
        self.page.update()

    def close_dialog(self, e):
        """ダイアログを閉じる"""
        self.page.dialog.open = False
        self.page.update()

    def handle_delete(self, e, callback):
        """削除処理を実行"""
        e.control.result = True
        callback(e)

    def show_edit_dialog(self, e):
        """編集ダイアログを表示"""
        filename_field = ft.TextField(
            label="ファイル名",
            value=self.filename,
            width=400,
        )
        filepath_field = ft.TextField(
            label="パス",
            value=self.filepath,
            width=400,
        )
        tags_field = ft.TextField(
            label="タグ（カンマ区切り）",
            value=self.tags if self.tags else "",
            width=400,
        )
        created_at_text = ft.Text(f"作成日時: {self.created_at}")

        def save_changes(e):
            if e.control.result:
                conn = self.file_manager.create_connection()
                with conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        """
                        UPDATE files 
                        SET filename = ?, filepath = ?
                        WHERE id = ?
                        """,
                        (filename_field.value, filepath_field.value, self.file_id),
                    )
                    cursor.execute(
                        "DELETE FROM file_tags WHERE file_id = ?", (self.file_id,)
                    )
                    new_tags = [
                        tag.strip()
                        for tag in tags_field.value.split(",")
                        if tag.strip()
                    ]
                    for index, tag in enumerate(new_tags):
                        insert_file_joined(cursor, self.file_id, tag, index)

                conn.close()
                # ダイアログを閉じる
                self.page.dialog.open = False
                self.page.update()
                self.action_callback(self.ACTION_EDIT)

        self.page.dialog = ft.AlertDialog(
            title=ft.Text("ファイル情報の編集"),
            content=ft.Column(
                [
                    created_at_text,
                    ft.Divider(),
                    filename_field,
                    filepath_field,
                    tags_field,
                ],
                spacing=10,
                width=400,
            ),
            actions=[
                ft.TextButton("キャンセル", on_click=lambda e: self.close_dialog(e)),
                ft.TextButton(
                    "保存", on_click=lambda e: self.handle_save(e, save_changes)
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.dialog.open = True
        self.page.update()

    def handle_save(self, e, callback):
        """保存処理を実行"""
        e.control.result = True
        callback(e)


class FileListPage:
    def __init__(self, file_manager):
        self.file_manager = file_manager
        self.init_components()
        self.files = []
        self.sort_ascending = True

    def init_components(self):
        self.search_field = ft.TextField(
            label="ファイル名で検索", width=300, on_change=self.search_files
        )

        self.tag_filter = ft.TextField(
            label="タグで検索", width=300, on_change=self.search_files
        )

        # DataTableの設定を調整
        self.files_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Container(ft.Text("種類"), width=30)),
                ft.DataColumn(
                    ft.Container(ft.Text("ファイル名"), width=80),
                    on_sort=self.sort_function,
                ),
                ft.DataColumn(
                    ft.Container(ft.Text("パス"), width=200),
                    on_sort=self.sort_function,
                ),
                ft.DataColumn(
                    ft.Container(ft.Text("タグ"), width=100),
                    on_sort=self.sort_function,
                ),
                ft.DataColumn(ft.Container(ft.Text("操作"), width=50)),
            ],
            rows=[],
            horizontal_margin=10,
            horizontal_lines=ft.BorderSide(1, ft.colors.GREY_300),
            # ソート関連のパラメータ
            sort_column_index=1,  # デフォルトでソートする列のインデックス
            sort_ascending=True,  # デフォルトの昇順/降順
        )

    def build(self, page: ft.Page):
        self.search_files()
        return ft.Container(  # Containerでラップ
            content=ft.Column(
                [
                    ft.Row(
                        [self.search_field, self.tag_filter],
                        alignment=ft.MainAxisAlignment.START,  # 左寄せ
                    ),
                    ft.Row(
                        [
                            ft.Container(
                                content=self.files_table,
                                border=ft.border.all(1, ft.colors.GREY_300),
                                expand=True,
                            )
                        ],
                        scroll="auto",
                    ),
                ],
                spacing=20,  # 要素間の間隔を設定
                expand=True,
                alignment=ft.MainAxisAlignment.START,  # 上寄せ
            ),
            expand=True,
        )

    def search_files(self, page=None):
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
                LEFT JOIN file_tags j ON f.id = j.file_id
                LEFT JOIN tag_mng t ON j.tag_id = t.id
                GROUP BY f.id
                HAVING (? = '' OR LOWER(f.filename) LIKE ?)
                AND (? = '' OR LOWER(tags) LIKE ?)
                ORDER BY f.filename, j.number_of
            """
            cursor.execute(
                query, (search_text, f"%{search_text}%", tag_text, f"%{tag_text}%")
            )
            self.files = cursor.fetchall()

        conn.close()
        # 検索結果でテーブルを更新
        self.set_files_table()

    def sort_function(self, e):
        if e.control.parent.sort_column_index != e.column_index:
            e.control.parent.__setattr__("sort_ascending", False)
            e.control.parent.update()

        self.files.sort(
            key=lambda x: x[e.column_index] if x[e.column_index] else "",
            reverse=e.control.parent.sort_ascending,
        )
        # 検索結果でテーブルを更新
        self.set_files_table()
        # インデックス更新
        e.control.parent.__setattr__("sort_column_index", e.column_index)

        # フラグ更新
        (
            e.control.parent.__setattr__("sort_ascending", False)
            if e.control.parent.sort_ascending
            else e.control.parent.__setattr__("sort_ascending", True)
        )
        e.control.parent.update()

    def set_files_table(self):
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
                action_callback=self.wrap_action,
            )
            for file in self.files
        ]
        if self.files_table.page:
            self.files_table.update()

    def wrap_action(self, action):
        # FileRowクラスのaction_callbackのラッパー
        if action == FileRow.ACTION_EDIT:
            pass
        elif action == FileRow.ACTION_DELETE:
            pass
        self.search_files()
