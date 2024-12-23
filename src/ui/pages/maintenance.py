import flet as ft
import util.config_manager as conf
import common.define as define
from database.file_manager import FileManager
from util.util_query import delete_tag


class MaintenancePage:
    def __init__(self, page: ft.Page, file_manager: FileManager):
        self.page = page
        self.file_manager = file_manager

        def on_change(e):
            conf.set_config(
                define.SECTION_FILE_LIST, define.KEY_FILE_OPEN, e.control.value
            )

        self.open_file_radio = ft.RadioGroup(
            value=conf.get_config(
                define.SECTION_FILE_LIST,
                define.KEY_FILE_OPEN,
                define.FILE_OPEN["NONE"]["type"],
            ),
            content=ft.Row(
                [
                    ft.Radio(
                        value=define.FILE_OPEN["NONE"]["type"],
                        label=define.FILE_OPEN["NONE"]["text"],
                    ),
                    ft.Radio(
                        value=define.FILE_OPEN["ONLY"]["type"],
                        label=define.FILE_OPEN["ONLY"]["text"],
                    ),
                    ft.Radio(
                        value=define.FILE_OPEN["BOTH"]["type"],
                        label=define.FILE_OPEN["BOTH"]["text"],
                    ),
                ]
            ),
            on_change=lambda e: on_change(e),
        )
        # self.tags = self.get_dropdown_optin_tags()

    def build(self, con: ft.Container):
        # タグ削除用のドロップダウン
        self.tag_dropdown = ft.Dropdown(
            label="削除するタグを選択",
            options=self.get_dropdown_optin_tags(),
            width=300,
        )

        # タグ削除ボタン
        delete_tag_button = ft.ElevatedButton(
            text="タグを削除", on_click=self.delete_tag
        )

        content = ft.Column(
            [
                ft.Text("メンテナンス", size=24, weight=ft.FontWeight.BOLD),
                ft.Text("タグの削除", size=18, weight=ft.FontWeight.BOLD),
                self.tag_dropdown,
                delete_tag_button,
                ft.Divider(),
                ft.Text("ファイルオープン制御", size=18, weight=ft.FontWeight.BOLD),
                self.open_file_radio,
            ]
        )
        return content

    def get_all_tags(self) -> list:
        tags = []
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
                ORDER BY mng.tag_name
            """
            cursor.execute(query)
            tags = cursor.fetchall()

        return tags

    def get_dropdown_optin_tags(self) -> list:
        tags = self.get_all_tags()
        return [
            ft.dropdown.Option(
                key=tag[1], content=ft.Row([ft.Text(value=f"{tag[1]}({str(tag[2])})")])
            )
            for tag in tags
        ]

    def update_tag_list(self):
        self.tag_dropdown.options = self.get_dropdown_optin_tags()
        self.tag_dropdown.update()

    def delete_tag(self, e):
        selected_tag = self.tag_dropdown.value
        res = None
        if selected_tag:
            conn = self.file_manager.create_connection()
            with conn:
                cursor = conn.cursor()
                res = delete_tag(cursor, selected_tag)
            if res:
                self.update_tag_list()
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text(f"タグ '{selected_tag}' を削除しました")
                )

            else:
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text(f"タグを削除できませんでした('{selected_tag}')")
                )
            self.page.snack_bar.open = True
            self.page.update()
