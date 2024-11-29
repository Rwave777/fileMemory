import flet as ft
from .pages.file_register import FileRegisterPage
from .pages.file_list import FileListPage
from database.file_manager import FileManager
from .pages.database_info import DatabaseInfoPage


class MainApp:
    def __init__(self):
        self.file_manager = FileManager()
        self.file_register_page = FileRegisterPage(self.file_manager)
        self.file_list_page = FileListPage(self.file_manager)
        self.database_info_page = DatabaseInfoPage(self.file_manager)
        self.selec_index_page = 0

    def main(self, page: ft.Page):
        page.title = "ファイル管理アプリ"
        page.padding = 0
        page.window_width = 800
        page.window_height = 600

        # ナビゲーションレール
        self.rail = ft.NavigationRail(
            destinations=[
                ft.NavigationRailDestination(
                    icon=ft.icons.UPLOAD_FILE,
                    label_content=ft.Text("ファイル登録"),
                ),
                ft.NavigationRailDestination(
                    icon=ft.icons.FILE_COPY,
                    label_content=ft.Text("ファイル一覧"),
                ),
                ft.NavigationRailDestination(
                    icon=ft.icons.STORAGE,
                    label_content=ft.Text("DB情報"),
                ),
            ],
            selected_index=0,
            on_change=lambda e: self.change_page(e),
        )

        # コンテンツエリア
        self.content_area = ft.Container(
            content=self.file_register_page.build(page),
            padding=20,
            expand=True,
        )

        # レイアウト
        page.add(
            ft.Row(
                [
                    self.rail,
                    ft.VerticalDivider(width=1),
                    self.content_area,
                ],
                expand=True,
                spacing=0,
            )
        )

    def change_page(self, e):
        if self.selec_index_page == e.control.selected_index:
            return
        self.selec_index_page = e.control.selected_index
        if self.selec_index_page == 0:
            self.content_area.content = self.file_register_page.build(e.page)
        elif self.selec_index_page == 1:
            self.content_area.content = self.file_list_page.build(e.page)
        else:
            self.content_area.content = self.database_info_page.build(e.page)
        self.content_area.update()
