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

    def main(self, page: ft.Page):
        page.title = "ファイル管理アプリ"
        page.padding = 0
        page.window_width = 800
        page.window_height = 600

        # ナビゲーションレール
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
                ft.NavigationRailDestination(
                    icon=ft.icons.STORAGE,
                    selected_icon=ft.icons.STORAGE,
                    label="DB情報",
                ),
            ],
            on_change=lambda e: self.change_page(e),
        )

        # コンテンツエリア
        self.content_area = ft.Container(
            content=self.file_register_page.build(page), padding=20
        )

        # レイアウト
        page.add(
            ft.Row(
                [self.rail, ft.VerticalDivider(width=1), self.content_area], expand=True
            )
        )

    def change_page(self, e):
        if e.control.selected_index == 0:
            self.content_area.content = self.file_register_page.build(e.page)
        elif e.control.selected_index == 1:
            self.content_area.content = self.file_list_page.build(e.page)
        else:
            self.content_area.content = self.database_info_page.build(e.page)
        self.content_area.update()
