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
        memo,
        reg_tags,
        created_at,
        page,
        file_manager,
        action_callback,
    ):
        self.file_id = file_id
        self.filename = filename
        self.filepath = filepath
        self.memo = memo
        self.tags = tags
        self.reg_tags = reg_tags
        self.created_at = created_at
        self.file_manager = file_manager
        self.page = page
        self.action_callback: function = action_callback

        self.filename_clone = filename
        self.filepath_clone = filepath
        self.memo_clone = memo
        self.tags_clone = self.tags if self.tags else ""

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
            ft.DataCell(
                ft.Text(
                    filename,
                    no_wrap=True,
                    overflow=ft.TextOverflow.ELLIPSIS,
                    text_align=ft.TextAlign.LEFT,
                    size=12,
                    tooltip=filename,
                ),
                on_double_tap=self.show_edit_dialog,
            ),
            ft.DataCell(
                ft.Text(
                    tags if tags else "",
                    no_wrap=True,
                    overflow=ft.TextOverflow.ELLIPSIS,
                    text_align=ft.TextAlign.LEFT,
                    width=100,
                    size=12,
                ),
                on_double_tap=self.show_edit_dialog,
            ),
            ft.DataCell(
                ft.TextButton(
                    content=ft.Text(
                        filepath,
                        no_wrap=True,
                        overflow=ft.TextOverflow.ELLIPSIS,
                        text_align=ft.TextAlign.LEFT,
                        size=12,
                    ),
                    tooltip=f"'{filepath}'をコピー",
                    on_click=lambda e: self.copy_path(filepath),
                    width=250,
                    style=ft.ButtonStyle(alignment=ft.alignment.center_left),
                ),
                on_double_tap=self.show_edit_dialog,
            ),
            ft.DataCell(
                ft.Text(
                    memo,
                    no_wrap=True,
                    overflow=ft.TextOverflow.ELLIPSIS,
                    text_align=ft.TextAlign.LEFT,
                    size=12,
                    tooltip=memo,
                ),
                on_double_tap=self.show_edit_dialog,
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
        def file_update(e):
            self.filename_clone = e.control.value

        def path_update(e):
            self.filepath_clone = e.control.value

        def memo_update(e):
            self.memo_clone = e.control.value

        """編集ダイアログを表示"""
        filename_field = ft.TextField(
            label="名称", value=self.filename_clone, width=400, on_change=file_update
        )
        filepath_field = ft.TextField(
            label="パス", value=self.filepath_clone, width=400, on_change=path_update
        )
        memo_field = ft.TextField(
            label="メモ",
            value=self.memo_clone,
            width=400,
            max_lines=3,
            on_change=memo_update,
        )
        # タグを表示するためのコンテナ
        tags_container = ft.Container(
            content=ft.Row(controls=[], spacing=5, wrap=True),
            border=ft.border.all(1, ft.colors.GREY_400),
            border_radius=5,
            padding=10,
            width=400,
        )

        self.update_tags_container(tags_container)

        created_at_text = ft.Text(f"作成日時: {self.created_at}")

        def save_changes(e):
            if e.control.result:
                conn = self.file_manager.create_connection()
                with conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        """
                        UPDATE files 
                        SET filename = ?, filepath = ?, memo = ?
                        WHERE id = ?
                        """,
                        (
                            filename_field.value,
                            filepath_field.value,
                            memo_field.value,
                            self.file_id,
                        ),
                    )
                    cursor.execute(
                        "DELETE FROM file_tags WHERE file_id = ?", (self.file_id,)
                    )
                    new_tags = [
                        tag.strip() for tag in self.tags_clone.split(",") if tag.strip()
                    ]
                    for index, tag in enumerate(new_tags):
                        insert_file_joined(cursor, self.file_id, tag, index)

                conn.close()
                # ダイアログを閉じる
                self.page.dialog.open = False
                self.page.update()
                self.action_callback(self.ACTION_EDIT)
                self.filename = self.filename_clone
                self.filepath = self.filepath_clone
                self.memo = self.memo_clone

        def cancel():
            self.filename_clone = self.filename
            self.filepath_clone = self.filepath
            self.memo_clone = self.memo
            self.tags_clone = self.tags
            self.close_dialog(None)

        self.page.dialog = ft.AlertDialog(
            title=ft.Text("ファイル情報の編集"),
            content=ft.Column(
                [
                    created_at_text,
                    ft.Divider(),
                    filename_field,
                    filepath_field,
                    memo_field,
                    tags_container,
                ],
                spacing=10,
                width=400,
            ),
            actions=[
                ft.TextButton(
                    "保存", on_click=lambda e: self.handle_save(e, save_changes)
                ),
                ft.TextButton("キャンセル", on_click=lambda e: cancel()),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            modal=True,
        )
        self.page.dialog.open = True
        self.page.update()

    def handle_save(self, e, callback):
        """保存処理を実行"""
        e.control.result = True
        callback(e)

    def update_tags_container(self, container: ft.Container):
        """タグコンテナを更新"""
        container.content.controls = [
            ft.Chip(
                label=ft.Text(tag.strip()),
                on_delete=lambda _: self.remove_tag(tag.strip(), container),
            )
            for tag in (self.tags_clone.split(",") if self.tags_clone else [])
        ]
        container.content.controls.append(
            ft.IconButton(
                icon=ft.icons.ADD, on_click=lambda _: self.show_tag_dialog(container)
            )
        )

    def remove_tag(self, tag: str, container: ft.Container):
        """タグを削除"""
        self.tags_clone = ",".join(
            [t for t in self.tags_clone.split(",") if t.strip() != tag]
        )
        self.update_tags_container(container)
        self.page.update()

    def show_tag_dialog(self, container):
        def handle_tap(e):
            search_bar.open_view()

        def select_tag(e):
            text = e.control.data
            # search_bar.value = text
            search_bar.close_view(text)

        # def submit_tag(e):
        #     e.control.close_view(e.control.value)
        #     # self.add_tag(e.control.value, container)

        """タグ追加ダイアログを表示"""
        search_bar = ft.SearchBar(
            bar_hint_text="新しいタグを入力",
            # on_submit=lambda e: submit_tag(e),
            controls=[
                ft.ListTile(
                    title=ft.Text(item[1] if item[1] else ""),
                    on_click=select_tag,
                    data=item[1] if item[1] else "",
                )
                for item in self.reg_tags
            ],
            on_tap=handle_tap,
        )

        self.page.dialog = ft.AlertDialog(
            title=ft.Text("タグの追加"),
            content=ft.Column([search_bar]),
            actions=[
                ft.TextButton(
                    "追加", on_click=lambda e: self.add_tag(search_bar.value, container)
                ),
                ft.TextButton(
                    "閉じる", on_click=lambda e: self.close_tag_dialog(e, container)
                ),
            ],
        )
        self.page.dialog.open = True
        self.page.update()

    def add_tag(self, new_tag, container: ft.Container):
        """新しいタグを追加"""
        if new_tag and new_tag not in self.tags_clone:
            self.tags_clone = (
                f"{self.tags_clone},{new_tag}" if self.tags_clone else new_tag
            )
            self.update_tags_container(container)
        self.show_edit_dialog(None)

    def close_tag_dialog(self, e, container: ft.Container):
        """タグダイアログを閉じる"""
        self.update_tags_container(container)
        self.show_edit_dialog(e)


class FileListPage:
    def __init__(self, file_manager):
        self.file_manager = file_manager
        self.files = []
        self.tags = []
        self.sort_ascending = True
        self.init_components()

    def clear_text(self, text_field: ft.TextField):
        text_field.value = ""
        text_field.update()
        self.search_files()

    def init_components(self):
        self.search_tags()
        self.search_field = ft.TextField(
            label="名称で検索",
            width=300,
            on_change=self.search_files,
            suffix=ft.IconButton(
                icon=ft.icons.CLEAR,
                padding=ft.padding.all(0),
                visual_density=ft.VisualDensity.COMPACT,
                on_click=lambda e: self.clear_text(self.search_field),
            ),
            dense=True,
        )

        self.tag_filter = ft.TextField(
            label="タグで検索",
            width=300,
            on_change=self.search_files,
            suffix=ft.IconButton(
                icon=ft.icons.CLEAR,
                padding=ft.padding.all(0),
                visual_density=ft.VisualDensity.COMPACT,
                on_click=lambda e: self.clear_text(self.tag_filter),
            ),
            dense=True,
        )

        def tag_select(text):
            self.tag_filter.value = text
            self.tag_filter.update()
            self.search_files()

        self.tag_view_btn = ft.PopupMenuButton(
            content=ft.Icon(name=ft.icons.FILTER_LIST_ALT),
            items=[
                ft.PopupMenuItem(
                    content=ft.Row(
                        [
                            ft.Icon(name=ft.icons.TAG),
                            ft.Text(
                                value=tag[1],
                                color=ft.colors.PRIMARY,
                            ),
                        ]
                    ),
                    on_click=lambda e: tag_select(e.control.content.controls[1].value),
                )
                for tag in self.tags
            ],
            on_open=lambda e: e.control.parent.update(),
        )

        # DataTableの設定を調整
        self.files_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Container(ft.Text("種類"), width=30)),
                ft.DataColumn(
                    ft.Container(ft.Text("名称"), width=120),
                    on_sort=self.sort_function,
                ),
                ft.DataColumn(
                    ft.Container(ft.Text("タグ"), width=100),
                    on_sort=self.sort_function,
                ),
                ft.DataColumn(
                    ft.Container(ft.Text("パス"), width=250),
                    on_sort=self.sort_function,
                ),
                ft.DataColumn(
                    ft.Container(ft.Text("メモ"), width=250),
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
            border=ft.border.all(1, ft.colors.GREY_200),
            column_spacing=10,
        )

    def build(self, page: ft.Page):
        self.search_tags()
        self.search_files()
        return ft.Container(  # Containerでラップ
            content=ft.Column(
                [
                    ft.Row(
                        [self.search_field, self.tag_filter, self.tag_view_btn],
                        alignment=ft.MainAxisAlignment.START,  # 左寄せ
                    ),
                    ft.Row(
                        [
                            ft.Column(
                                controls=[self.files_table],
                                scroll=ft.ScrollMode.ALWAYS,
                                expand=True,
                                height=450,
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
                    f.memo,
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

    def search_tags(self, page=None):
        conn = self.file_manager.create_connection()
        with conn:
            cursor = conn.cursor()
            query = """
                SELECT 
                    mng.id, 
                    mng.tag_name,
                    count(j.file_id) AS count
                FROM tag_mng mng
                LEFT JOIN file_tags j ON mng.id = j.tag_id
                GROUP BY mng.id, mng.tag_name    
                ORDER BY count desc, mng.tag_name
            """
            cursor.execute(
                query,
            )
            self.tags = cursor.fetchall()
        conn.close()

    def set_files_table(self):
        # 検索結果でテーブルを更新
        self.files_table.rows = [
            FileRow(
                file_id=file[0],
                filename=file[1],
                filepath=file[2],
                tags=file[3],
                memo=file[4],
                reg_tags=self.tags,
                created_at=file[5],
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
