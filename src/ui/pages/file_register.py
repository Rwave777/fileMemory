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

    def init_components(self):
        # タグ入力
        self.tag_input = ft.TextField(
            label="タグ（カンマ区切り）",
            width=400,
        )

        # tags_container = ft.Container(
        #     content=ft.Row(controls=[], spacing=5, wrap=True),
        #     border=ft.border.all(1, ft.colors.GREY_400),
        #     border_radius=5,
        #     padding=10,
        #     width=400,
        # )
        # self.tag_input = tags_container
        # self.update_tags_container(tags_container)

        # 登録ボタン
        self.submit_button = ft.ElevatedButton(
            text="登録", on_click=self.on_submit, width=400
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

    def build(self, page: ft.Page):
        # ファイルピッカーの初期化
        self.file_picker = ft.FilePicker(on_result=self.on_file_picker_result)
        self.folder_picker = ft.FilePicker(on_result=self.on_folder_picker_result)

        return ft.Column(
            [
                self.drop_area,
                self.file_picker,
                self.folder_picker,
                self.tag_input,
                self.submit_button,
                self.success_message,
            ]
        )

    # イベントハンドラ
    def on_drop(self, e):
        if e.data and e.data.startswith("files://"):
            path = e.data.replace("files://", "")
            self.process_dropped_item(path)

    def process_dropped_item(self, path: str):
        if os.path.exists(path):
            self.current_file_path = path
            name = os.path.basename(path)
            type_text = "フォルダ" if os.path.isdir(path) else "ファイル"
            self.success_message.value = f"{type_text}準備完了: {name}\nパス: {path}"
            self.success_message.update()

    def on_file_picker_result(self, e):
        if e.files:
            file_path = e.files[0].path
            self.process_dropped_item(file_path)

    def on_folder_picker_result(self, e):
        if e.path:
            self.process_dropped_item(e.path)

    def on_submit(self, e):
        if hasattr(self, "current_file_path"):
            path = self.current_file_path
            name = os.path.basename(path)

            tags = [
                tag.strip() for tag in self.tag_input.value.split(",") if tag.strip()
            ]

            conn = self.file_manager.create_connection()
            with conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO files (filename, filepath) VALUES (?, ?)",
                    (name, path),
                )
                file_id = cursor.lastrowid

                for index, tag in enumerate(tags):
                    insert_file_joined(cursor, file_id, tag, index)

            conn.close()

            self.tag_input.value = ""
            self.success_message.value = "正常に登録されました！"
            self.tag_input.update()
            self.success_message.update()
