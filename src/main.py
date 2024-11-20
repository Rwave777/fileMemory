import flet as ft

from ui.main_app import MainApp


def main():
    app = MainApp()
    ft.app(target=app.main)


if __name__ == "__main__":
    main()
