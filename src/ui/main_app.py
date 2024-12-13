import flet as ft
from .pages.file_register import FileRegisterPage
from .pages.file_list import FileListPage
from database.file_manager import FileManager
from .pages.database_info import DatabaseInfoPage
from .pages.maintenance import MaintenancePage


class MainApp:
    def __init__(self):
        self.file_manager = FileManager()
        self.select_index_page = 0

    def main(self, page: ft.Page):
        page.title = "パス管理"
        page.padding = 0
        page.window_width = 1200
        page.window_height = 600

        self.file_register_page = FileRegisterPage(page, self.file_manager)
        self.file_list_page = FileListPage(page, self.file_manager)
        self.database_info_page = DatabaseInfoPage(page, self.file_manager)
        self.maintenance_page = MaintenancePage(page, self.file_manager)

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
                ft.NavigationRailDestination(
                    icon=ft.icons.SETTINGS,
                    label_content=ft.Text("メンテナンス"),
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
        if self.select_index_page == e.control.selected_index:
            return
        self.select_index_page = e.control.selected_index
        if self.select_index_page == 0:
            self.content_area.content = self.file_register_page.build(self.content_area)
        elif self.select_index_page == 1:
            self.content_area.content = self.file_list_page.build(self.content_area)
        elif self.select_index_page == 2:
            self.content_area.content = self.database_info_page.build(self.content_area)
        else:
            self.content_area.content = self.maintenance_page.build(self.content_area)
        self.content_area.update()

    @property
    def open_file_checkbox(self):
        return self.maintenance_page.open_file_checkbox
