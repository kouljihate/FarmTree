import os
import logging
import flet as ft
from flet import (
    Page, AppBar, IconButton, Icon, Icons, TextField,
    Colors, Container, Stack, Row, Column, Text, SnackBar, SafeArea,
    NavigationBar, NavigationBarDestination, TextStyle,
    Padding, FontWeight, CrossAxisAlignment, MainAxisAlignment,
    PopupMenuItem, BottomSheet, ListView, AlertDialog, TextButton,
    ListTile, alignment, ProgressRing, LinearGradient, BorderRadius,
)
from app.config import STATUS_LOOKUP
from app.database import init_db, delete_tree, get_tree, update_tree_status, invalidate_cache
from app.logger import get_logger
from app.views.components import TRANSLATIONS, build_visit_card
from app.views.list_view import TreeListView
from app.views.add_view import TreeAddView
from app.views.edit_view import TreeEditView
from app.views.detail_view import TreeDetailView
from app.views.settings_view import SettingsView
from app.views.stats_view import StatsView
import version


class TreesApp:
    def __init__(self, page: Page):
        self.page = page
        self.page.title = "Farm Tree Manager"
        self.page.theme_mode = ft.ThemeMode.LIGHT
        self.page.theme = ft.Theme(
            color_scheme_seed=Colors.GREEN_700,
            font_family="Comfortaa",
        )

        _is_desktop = self.page.platform in (ft.PagePlatform.WINDOWS, ft.PagePlatform.MACOS, ft.PagePlatform.LINUX)
        if _is_desktop:
            self.page.window.width = 420
            self.page.window.height = 780
            self.page.window.min_width = 360
            self.page.window.min_height = 600

        self.search_query = ""
        self.filter_kind = None
        self.filter_status = None
        self.current_tree_id = None
        self.current_tree_data = None
        self.captured_photo_path = None
        self.captured_gps_lat = ""
        self.captured_gps_lon = ""
        self.lang = "en"
        self.version = version.version
        self._gps_task = None

        self.logger = get_logger()

        try:
            self.db = init_db()
        except Exception as ex:
            self.logger.error("Failed to init DB: %s", ex, exc_info=True)
            raise

    def t(self, key: str) -> str:
        return TRANSLATIONS.get(self.lang, TRANSLATIONS["en"]).get(key, key)

    def _font(self) -> str:
        return "AlMaghrebi" if self.lang == "ar" else "Comfortaa"

    def setup_ui(self):
        font_path = os.path.join(os.path.dirname(__file__), "assets", "fonts", "Comfortaa-Regular.ttf")
        if os.path.exists(font_path):
            self.page.fonts = {"Comfortaa": font_path}
        ar_font_path = os.path.join(os.path.dirname(__file__), "assets", "fonts", "AlMaghrebi-Modern-Wahib.ttf")
        if os.path.exists(ar_font_path):
            self.page.fonts["AlMaghrebi"] = ar_font_path

        self.setup_app_bar()
        self.setup_navigation()

        self.geolocator = None
        self.camera = None
        self.camera_available = False
        self.geolocator_available = False

        _is_desktop = self.page.platform in (ft.PagePlatform.WINDOWS, ft.PagePlatform.MACOS, ft.PagePlatform.LINUX)
        if not _is_desktop:
            try:
                from flet_geolocator import Geolocator, GeolocatorConfiguration, GeolocatorPositionAccuracy
                self.geolocator = Geolocator(
                    configuration=GeolocatorConfiguration(accuracy=GeolocatorPositionAccuracy.HIGH),
                )
                self.page.services.append(self.geolocator)
                self.geolocator_available = True
            except Exception as ex:
                self.logger.warning("Geolocator not available: %s", ex)

            try:
                from flet_camera import Camera
                self.camera = Camera(preview_enabled=False)
                self.page.overlay.append(self.camera)
                self.camera_available = True
            except Exception as ex:
                self.logger.warning("Camera init failed: %s", ex)
        else:
            self.logger.info("Camera and Geolocator skipped on desktop platform: %s", self.page.platform)

        self.list_view = TreeListView(self)
        self.add_view = TreeAddView(self)
        self.edit_view = TreeEditView(self)
        self.detail_view = TreeDetailView(self)
        self.settings_view = SettingsView(self)
        self.stats_view = StatsView(self)

        self.list_view.setup()
        self.add_view.setup()
        self.edit_view.setup()
        self.detail_view.setup()
        self.settings_view.setup()
        self.stats_view.setup()

        self.splash_container = Container(
            content=Column([
                Container(
                    content=Icon(Icons.PARK, size=80, color=Colors.WHITE),
                    bgcolor=Colors.GREEN_800,
                    width=120,
                    height=120,
                    border_radius=BorderRadius(60, 60, 60, 60),
                    alignment=alignment.Alignment(0, 0),
                ),
                Text(
                    "Farm Tree Manager",
                    size=26,
                    weight=FontWeight.BOLD,
                    color=Colors.WHITE,
                    font_family="Comfortaa",
                ),
                Text(
                    "Managing your orchards with care",
                    size=14,
                    color=Colors.GREEN_100,
                    font_family="Comfortaa",
                ),
                Container(height=20),
                ProgressRing(
                    width=36,
                    height=36,
                    stroke_width=4,
                    color=Colors.WHITE,
                ),
                Container(height=10),
                Text(
                    "Loading...",
                    size=12,
                    color=Colors.GREEN_200,
                    font_family="Comfortaa",
                ),
            ],
                horizontal_alignment=CrossAxisAlignment.CENTER,
                alignment=MainAxisAlignment.CENTER,
                spacing=12,
            ),
            gradient=LinearGradient(
                begin=alignment.Alignment(0, -1),
                end=alignment.Alignment(0, 1),
                colors=[Colors.GREEN_900, Colors.GREEN_700, Colors.GREEN_600],
            ),
            expand=True,
            alignment=alignment.Alignment(0, 0),
        )

        self.main_container = Stack([
            self.splash_container,
            self.list_view.container,
            self.add_view.container,
            self.edit_view.container,
            self.detail_view.container,
            self.settings_view.container,
            self.stats_view.container,
        ], expand=True)
        safe_main = SafeArea(
            content=self.main_container,
            expand=True,
            avoid_intrusions_top=True,
            avoid_intrusions_bottom=True,
            maintain_bottom_view_padding=True,
        )
        self.page.add(safe_main)
        self.splash_container.visible = True
        for c in (self.list_view.container, self.add_view.container, self.edit_view.container,
                  self.detail_view.container, self.settings_view.container, self.stats_view.container):
            c.visible = False
        self.page.update()

        import asyncio
        async def _hide_splash():
            await asyncio.sleep(2)
            self.splash_container.visible = False
            self.list_view.container.visible = True
            self.list_view.show()
            self.page.update()

        self.page.run_task(_hide_splash)

    def setup_app_bar(self):
        self.search_field = TextField(
            hint_text=self.t("search_hint"),
            hint_style=TextStyle(color=Colors.GREY_500, font_family="Comfortaa"),
            border=None,
            content_padding=Padding(10, 0, 10, 0),
            on_change=self.on_search_change,
            expand=True,
            text_size=16,
            text_style=TextStyle(font_family="Comfortaa"),
        )

        self.search_clear_btn = IconButton(
            icon=Icons.CLOSE,
            icon_color=Colors.GREY_500,
            visible=False,
            on_click=self.clear_search,
            tooltip="Clear search",
        )

        self.search_button = IconButton(
            icon=Icons.SEARCH,
            icon_color=Colors.WHITE,
            icon_size=32,
            on_click=self.trigger_search,
            tooltip="Search",
        )

        self.tree_count_badge = Container(
            visible=False,
            padding=Padding(6, 2, 6, 2),
            border_radius=ft.BorderRadius(10, 10, 10, 10),
            bgcolor=Colors.GREEN_700,
        )

        self.search_input_container = Container(
            content=Row([
                self.search_field,
                self.tree_count_badge,
                self.search_clear_btn,
            ], spacing=8, alignment=MainAxisAlignment.END, vertical_alignment=CrossAxisAlignment.CENTER),
            width=280,
            height=40,
            bgcolor=Colors.WHITE,
            margin=ft.Margin(0, 0, 4, 0),
            border_radius=ft.BorderRadius(20, 20, 20, 20),
            padding=Padding(8, 0, 8, 0),
        )

        self.back_btn = IconButton(icon=Icons.ARROW_BACK, icon_color=Colors.WHITE, icon_size=32, tooltip="Back")
        self.stats_btn = IconButton(icon=Icons.ANALYTICS_OUTLINED, icon_color=Colors.WHITE, icon_size=32, on_click=lambda _: self.stats_view.show(), tooltip="Statistics")
        self.app_bar = AppBar(
            leading=None,
            title=None,
            bgcolor=Colors.GREEN_700,
            actions=[
                self.search_input_container,
                self.search_button,
                self.stats_btn,
                IconButton(icon=Icons.REFRESH, icon_color=Colors.WHITE, icon_size=32, on_click=lambda _: self.list_view.load_trees(), tooltip="Refresh"),
            ],
            toolbar_height=48,
        )
        self.page.appbar = self.app_bar

    def setup_navigation(self):
        self.nav_bar = NavigationBar(
            destinations=[
                NavigationBarDestination(icon=Icons.LIST_ALT, label=self.t("nav_trees")),
                NavigationBarDestination(icon=Icons.ADD_CIRCLE, label=self.t("nav_add")),
                NavigationBarDestination(icon=Icons.SETTINGS, label=self.t("nav_settings")),
            ],
            selected_index=0,
            on_change=self.on_nav_change,
            bgcolor=Colors.WHITE,
            indicator_color=Colors.GREEN_100,
            label_behavior=ft.NavigationBarLabelBehavior.ALWAYS_SHOW,
        )
        self.page.navigation_bar = self.nav_bar

    def on_nav_change(self, e):
        idx = e.control.selected_index
        if idx == 0:
            self.list_view.show()
        elif idx == 1:
            self.add_view.show()
        elif idx == 2:
            self.settings_view.show()
        self.nav_bar.selected_index = idx
        self.nav_bar.update()

    def _switch_view(self, container):
        for c in (self.list_view.container, self.add_view.container, self.edit_view.container,
                  self.detail_view.container, self.settings_view.container, self.stats_view.container):
            c.visible = (c is container)
        self._remove_old_bottomsheets()
        self.main_container.update()

    def _remove_old_bottomsheets(self):
        if hasattr(self.page.overlay, 'controls'):
            self.page.overlay.controls = [
                c for c in self.page.overlay.controls
                if not isinstance(c, BottomSheet)
            ]
        else:
            self.page.overlay[:] = [
                c for c in self.page.overlay
                if not isinstance(c, BottomSheet)
            ]

    def apply_language(self):
        self.page.rtl = self.lang == "ar"
        self.page.update()
        self._rebuild_all_views()

    def _rebuild_all_views(self):
        self.setup_app_bar()
        self.setup_navigation()
        self.list_view.setup()
        self.add_view.setup()
        self.edit_view.setup()
        self.detail_view.setup()
        self.settings_view.setup()
        self.stats_view.setup()
        self.main_container.controls = [
            self.list_view.container,
            self.add_view.container,
            self.edit_view.container,
            self.detail_view.container,
            self.settings_view.container,
            self.stats_view.container,
        ]
        self.main_container.update()
        self.list_view.show()

    def trigger_search(self, e=None):
        if hasattr(self, 'search_field'):
            import asyncio
            asyncio.create_task(self.search_field.focus())
            self.list_view.current_page = 0
            self.list_view.load_trees()
        else:
            self.list_view.show()

    def on_search_change(self, e):
        self.search_query = e.control.value.strip()
        self.search_clear_btn.visible = bool(self.search_query)
        self.search_clear_btn.update()
        self.list_view.current_page = 0
        self.list_view.load_trees()

    def clear_search(self, e):
        self.search_field.value = ""
        self.search_query = ""
        self.search_clear_btn.visible = False
        self.search_clear_btn.update()
        self.search_field.update()
        invalidate_cache()
        self.list_view.current_page = 0
        self.list_view.load_trees()

    def show_snack(self, message: str, color: str):
        self.page.snack_bar = SnackBar(content=Text(message, color=Colors.WHITE, font_family="Comfortaa"), bgcolor=color, duration=2000)
        self.page.snack_bar.open = True
        self.page.update()

    def show_error_popup(self, error_id: str, description: str):
        import traceback as _tb
        self.logger.error("Error %s: %s", error_id, description)

        def close_dlg(e):
            dlg.open = False
            self.page.update()

        dlg = AlertDialog(
            title=Row([
                Icon(Icons.ERROR, color=Colors.RED, size=24),
                Text(f"Error {error_id}", font_family="Comfortaa", size=16, color=Colors.RED),
            ]),
            content=Container(
                content=Column([
                    Text(description, font_family="Comfortaa", size=13, color=Colors.GREY_800, selectable=True),
                ], spacing=8),
                width=350,
                padding=Padding(0, 8, 0, 0),
            ),
            actions=[
                TextButton("OK", on_click=close_dlg, style=ft.ButtonStyle(color=Colors.GREEN_700)),
            ],
        )
        self.page.dialog = dlg
        dlg.open = True
        self.page.update()

    def safe_handler(self, func):
        import uuid as _uuid
        def wrapper(e):
            try:
                return func(e)
            except Exception as ex:
                error_id = _uuid.uuid4().hex[:8].upper()
                self.show_error_popup(error_id, str(ex))
        return wrapper

    def confirm_delete_current(self):
        def confirm(e):
            self.delete_current_tree()
            dlg.open = False
            self.page.update()

        def cancel(e):
            dlg.open = False
            self.page.update()

        dlg = AlertDialog(
            title=Text(self.t("delete_title"), font_family=self._font()),
            content=Text(self.t("confirm_delete"), font_family=self._font()),
            actions=[
                TextButton(self.t("cancel"), on_click=cancel),
                TextButton(self.t("delete"), on_click=confirm, style=ft.ButtonStyle(color=Colors.RED)),
            ],
        )
        self.page.dialog = dlg
        dlg.open = True
        self.page.update()

    def delete_current_tree(self):
        if self.current_tree_id:
            try:
                photos = delete_tree(self.current_tree_id)
            except Exception as ex:
                import uuid as _uuid
                error_id = _uuid.uuid4().hex[:8].upper()
                self.show_error_popup(error_id, f"Failed to delete tree: {ex}")
                return
            for p in photos:
                try:
                    os.remove(p)
                except Exception as ex:
                    self.logger.warning("Failed to remove photo %s: %s", p, ex)
            self.logger.info("Tree %s deleted", self.current_tree_id)
            self.show_snack("Tree deleted", Colors.GREEN)
            self.list_view.show()

    def show_tree_context_menu(self, tree: dict):
        def make_handler(fn):
            def handler(e):
                bs.open = False
                self.page.update()
                fn()
            return handler

        def on_edit():
            self.current_tree_id = tree["id"]
            self.current_tree_data = tree
            self.edit_view.show(tree)

        def on_delete():
            self.current_tree_id = tree["id"]
            self.confirm_delete_current()

        def on_history():
            self.show_history_bottom_sheet(tree["id"])

        items = Column([
            ListTile(leading=Icon(Icons.EDIT), title=Text(self.t("edit_action"), font_family=self._font()), on_click=make_handler(on_edit)),
            ListTile(leading=Icon(Icons.FLAG), title=Text(self.t("quick_status"), font_family=self._font()), on_click=make_handler(lambda: self.show_status_picker(tree))),
            ListTile(leading=Icon(Icons.HISTORY), title=Text(self.t("view_history"), font_family=self._font()), on_click=make_handler(on_history)),
            ListTile(leading=Icon(Icons.DELETE), title=Text(self.t("delete_action"), font_family=self._font()), on_click=make_handler(on_delete)),
        ], spacing=0)

        bs = BottomSheet(
            content=Container(
                content=Column([
                    Text(self.t("actions"), size=18, weight=FontWeight.BOLD, font_family=self._font()),
                    ft.Divider(),
                    items,
                ], spacing=8, tight=True),
                padding=Padding(20, 20, 20, 20),
            ),
            open=True,
        )
        self._remove_old_bottomsheets()
        self.page.overlay.append(bs)
        self.page.update()

    def show_status_picker(self, tree: dict):
        def on_status_click(status):
            update_tree_status(tree["id"], status)
            self.show_snack(f"Status updated to {status}", Colors.GREEN)
            self.list_view.load_trees()
            bs.open = False
            self.page.update()

        items = []
        for status, color in STATUS_LOOKUP.items():
            items.append(
                PopupMenuItem(
                    content=Row([
                        Container(width=12, height=12, bgcolor=color, border_radius=ft.BorderRadius(6, 6, 6, 6)),
                        Text(status, font_family="Comfortaa"),
                    ], spacing=10),
                    on_click=lambda _, s=status: on_status_click(s),
                )
            )

        bs = BottomSheet(
            content=Container(
                content=Column([
                    Text(self.t("change_status"), size=18, weight=FontWeight.BOLD, font_family=self._font()),
                    ft.Divider(),
                    ListView(items, spacing=4, shrink_wrap=True),
                ], spacing=8, tight=True),
                padding=Padding(20, 20, 20, 20),
            ),
            open=True,
        )
        self._remove_old_bottomsheets()
        self.page.overlay.append(bs)
        self.page.update()

    def show_history_bottom_sheet(self, tree_id: int):
        tree = get_tree(tree_id)
        if not tree:
            return

        visits = tree.get("visits", [])
        items = [build_visit_card(v) for v in reversed(visits)]

        bs = BottomSheet(
            content=Container(
                content=Column([
                    Text(self.t("visit_history"), size=18, weight=FontWeight.BOLD, font_family=self._font()),
                    ft.Divider(),
                    ListView(items, spacing=8, shrink_wrap=True, expand=True),
                ], spacing=8, tight=True),
                padding=Padding(20, 20, 20, 20),
                height=400,
            ),
            open=True,
        )
        self._remove_old_bottomsheets()
        self.page.overlay.append(bs)
        self.page.update()


def main(page: Page):
    try:
        app = TreesApp(page)
        app.logger.info("App started")
        app.setup_ui()
    except Exception as ex:
        logging.basicConfig(level=logging.DEBUG)
        logging.getLogger("farmtree").error("Startup failed: %s", ex, exc_info=True)
        raise


if __name__ == "__main__":
    try:
        ft.run(main, assets_dir="assets")
    except Exception as ex:
        logging.basicConfig(level=logging.DEBUG)
        logging.getLogger("farmtree").critical("Unhandled exception: %s", ex, exc_info=True)
        raise
