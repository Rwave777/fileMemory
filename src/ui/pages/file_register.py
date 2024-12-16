import flet as ft
import os
from util.util_query import insert_file_joined


class FileRegisterPage:
    def __init__(self, page, file_manager):
        self.page = page
        self.file_manager = file_manager
        self.success_message = ft.Text("", color=ft.colors.GREEN)
        self.file_picker = None
        self.folder_picker = None
        self.init_components()
        self.tags = []

    def init_components(self):
        # 名称入力
        self.file_name = ft.TextField(
            label="名称",
            width=500,
        )
        # パス
        self.file_path = ft.TextField(
            label="パス",
            width=500,
        )

        # タグ入力
        self.tag_input = ft.TextField(
            label="タグ（カンマ区切り）",
            width=460,
        )

        # メモ入力
        self.memo = ft.TextField(
            label="メモ", width=500, max_lines=3, min_lines=3, multiline=True
        )

        # 登録ボタン
        self.submit_button = ft.ElevatedButton(
            text="登録", on_click=self.on_submit, width=400
        )

        # クリアボタン
        self.clear_button = ft.ElevatedButton(
            text="クリア", on_click=self.on_clear, width=100
        )

        # ドロップエリアの作成
        drop_content = ft.Container(
            content=ft.Column(
                [
                    ft.Text("ファイルまたはフォルダをドロップ(機能未提供)", size=20),
                    ft.Row(
                        [
                            ft.ElevatedButton(
                                "ファイルを選択",
                                on_click=self.pick_files,
                                icon=ft.icons.FILE_UPLOAD,
                            ),
                            ft.ElevatedButton(
                                "フォルダを選択",
                                on_click=self.pick_folder,
                                icon=ft.icons.FOLDER_OPEN,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=20,
            ),
            width=500,
            height=140,
            bgcolor=ft.colors.BLUE_GREY_100,
            border_radius=10,
            padding=10,
            alignment=ft.alignment.center,
        )

        self.drop_area = ft.DragTarget(
            group="files",
            content=drop_content,
            on_accept=self.on_drop,
            on_will_accept=lambda e: e.data.startswith("files://") if e.data else False,
        )

    def search_tags(self, page=None):
        conn = self.file_manager.create_connection()
        with conn:
            cursor = conn.cursor()
            query = """
                SELECT 
                    mng.id, 
                    mng.tag_name
                FROM tag_mng mng
                ORDER BY mng.tag_name
            """
            cursor.execute(
                query,
            )
            self.tags = cursor.fetchall()
        conn.close()

    def get_tags_view_btn(self) -> ft.PopupMenuButton:
        # タグ一覧のPopupMenuButtonを更新
        def tag_select(text, e):
            tag_list = [tag for tag in self.tag_input.value.split(",") if not tag == ""]
            tag_list.append(text)
            self.tag_input.value = ",".join(tag_list)
            self.tag_input.update()

        return ft.PopupMenuButton(
            content=ft.Icon(name=ft.icons.FILTER_LIST_ALT),
            items=[
                ft.PopupMenuItem(
                    content=ft.Row(
                        [
                            ft.Icon(name=ft.icons.TAG, size=12),
                            ft.Text(value=tag[1], color=ft.colors.PRIMARY, size=12),
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.END,
                    ),
                    height=30,
                    on_click=lambda e: tag_select(
                        e.control.content.controls[1].value, e
                    ),
                )
                for tag in self.tags
            ],
            # on_open=lambda e: tag_open(),
        )

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

    def pick_files(self, _):
        """ファイル選択ダイアログを表示"""
        if self.file_picker:
            self.file_picker.pick_files()

    def pick_folder(self, _):
        """フォルダ選択ダイアログを表示"""
        if self.folder_picker:
            self.folder_picker.get_directory_path()

    def build(self, con: ft.Container):
        # ファイルピッカーの初期化
        self.file_picker = ft.FilePicker(on_result=self.on_file_picker_result)
        self.folder_picker = ft.FilePicker(on_result=self.on_folder_picker_result)
        self.search_tags()
        self.tag_view_btn = self.get_tags_view_btn()

        return ft.Column(
            [
                self.drop_area,
                self.file_picker,
                self.folder_picker,
                self.file_name,
                self.file_path,
                ft.Row([self.tag_input, self.tag_view_btn]),
                self.memo,
                ft.Row([self.submit_button, self.clear_button]),
                self.success_message,
            ],
            scroll="auto",
        )

    # イベントハンドラ
    def on_drop(self, e):
        if e.data and e.data.startswith("files://"):
            path = e.data.replace("files://", "")
            self.process_dropped_item(path)

    def process_dropped_item(self, path: str):
        if os.path.exists(path):
            name = os.path.basename(path)
            type_text = "フォルダ" if os.path.isdir(path) else "ファイル"
            self.file_name.value = name
            self.file_path.value = path
            self.file_name.update()
            self.file_path.update()

    def on_file_picker_result(self, e):
        if e.files:
            file_path = e.files[0].path
            self.process_dropped_item(file_path)

    def on_folder_picker_result(self, e):
        if e.path:
            self.process_dropped_item(e.path)

    def on_submit(self, e):
        if (
            self.file_name.value
            and self.file_path.value
            and os.path.exists(self.file_path.value)
        ):

            tags = [
                tag.strip() for tag in self.tag_input.value.split(",") if tag.strip()
            ]

            conn = self.file_manager.create_connection()
            with conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO files (filename, filepath, memo) VALUES (?, ?, ?)",
                    (self.file_name.value, self.file_path.value, self.memo.value),
                )
                file_id = cursor.lastrowid

                for index, tag in enumerate(tags):
                    insert_file_joined(cursor, file_id, tag, index)

            conn.close()

            self.file_name.value = ""
            self.file_path.value = ""
            self.tag_input.value = ""
            self.memo.value = ""
            self.file_name.update()
            self.file_path.update()
            self.tag_input.update()
            self.memo.update()
            self.page.show_snack_bar(
                ft.SnackBar(content=ft.Text("正常に登録されました！"))
            )

        else:
            msg_list = []
            if not self.file_name.value:
                msg_list.append("名称")
            if not self.file_path.value:
                msg_list.append("パス")
            elif not os.path.exists(self.file_path.value):
                self.page.show_snack_bar(
                    ft.SnackBar(content=ft.Text("存在しないパスです"))
                )
                return
            self.page.show_snack_bar(
                ft.SnackBar(content=ft.Text(f"{'・'.join(msg_list)}を入力してください"))
            )

    def on_clear(self, e):
        self.file_name.value = ""
        self.file_path.value = ""
        self.tag_input.value = ""
        self.memo.value = ""
        self.file_name.update()
        self.file_path.update()
        self.tag_input.update()
        self.memo.update()
