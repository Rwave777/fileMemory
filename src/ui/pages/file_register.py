import flet as ft
import os


class FileRegisterPage:
    def __init__(self, file_manager):
        self.file_manager = file_manager
        self.success_message = ft.Text("", color=ft.colors.GREEN)
        self.init_components()

    def init_components(self):
        # ファイルピッカーの設定
        self.file_picker = None  # mainで初期化
        self.folder_picker = None  # mainで初期化

        # タグ入力
        self.tag_input = ft.TextField(
            label="タグ（カンマ区切り）",
            width=400,
        )

        # 登録ボタン
        self.submit_button = ft.ElevatedButton(
            text="登録", on_click=self.on_submit, width=400
        )

        # ドロップエリアの作成
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

    def build(self, page: ft.Page):
        # ファイルピッカーの初期化
        self.file_picker = ft.FilePicker(on_result=self.on_file_picker_result)
        self.folder_picker = ft.FilePicker(on_result=self.on_folder_picker_result)
        page.overlay.extend([self.file_picker, self.folder_picker])

        return ft.Column(
            [self.drop_area, self.tag_input, self.submit_button, self.success_message]
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
