import flet as ft
from Share.libs.logger import log_error

def main(page: ft.Page):
    try:
        page.title = "Farm Tree Manager - Tree List"

        # Header
        header = ft.Text("🌳 Tree List", size=24, weight="bold")

        # Search bar
        search_bar = ft.TextField(label="Search by species or health")

        # Tree list (sample data)
        tree_list = ft.ListView(expand=True, spacing=10, controls=[
            ft.Text("Tree #1 - Olive - Healthy"),
            ft.Text("Tree #2 - Apple - Needs Water"),
            ft.Text("Tree #3 - Orange - Diseased"),
        ])

        # Add button
        add_button = ft.FloatingActionButton(icon=ft.icons.ADD, text="Add Tree")

        # Layout
        page.add(
            header,
            search_bar,
            tree_list,
            add_button
        )

    except Exception as e:
        log_error("FrontEnd.ui.tree_list", e)

ft.app(target=main)
