import os
import asyncio
import shutil
from datetime import datetime
import flet as ft
import logging
from flet import (
    Page, TextField, Dropdown, DropdownOption, IconButton, Icon, Icons,
    Text, Colors, Container, Row, Column, ListView, Card, ListTile,
    AlertDialog, TextButton, Button, OutlinedButton,
    AppBar, NavigationBar, NavigationBarDestination, SnackBar, Stack,
    Image, GridView, KeyboardType, InputBorder, TextStyle,
    Border, Divider, Padding, Margin, alignment,
    FontWeight, CrossAxisAlignment, MainAxisAlignment, ScrollMode,
    BorderRadius, Chip, ButtonStyle,
    PopupMenuItem, BottomSheet, ProgressRing,
    FilledButton, BoxFit, BottomAppBar,
)
from app.config import TREE_KINDS, TREE_VARIETIES, STATUS_LOOKUP
import version
from app.database import (
    init_db, get_all_trees, get_trees_page, get_trees_slice, search_trees, count_trees,
    insert_tree, add_visit, update_tree, update_tree_status,
    delete_tree, get_tree, get_gps_coordinates,
    invalidate_cache, PHOTOS_DIR,
)
from app.logger import get_logger, read_logs

STATUS_DROPDOWN_ITEMS = [DropdownOption(text=label, key=label) for label in STATUS_LOOKUP]
KIND_DROPDOWN_ITEMS = [DropdownOption(text=k, key=k) for k in TREE_KINDS]


class TreesApp:
    def __init__(self, page: Page):
        self.page = page
        self.page.title = "Farm Tree Manager"
        self.page.theme_mode = ft.ThemeMode.LIGHT
        self.page.theme = ft.Theme(
            color_scheme_seed=Colors.GREEN_700,
            font_family="Comfortaa",
        )
        self.page.window.width = 420
        self.page.window.height = 780
        self.page.window.min_width = 360
        self.page.window.min_height = 600

        self.current_page = 0
        self.per_page = 20
        self.PAGE_CHUNK = 1000
        self.search_query = ""
        self.filter_kind = None
        self.filter_status = None
        self.current_tree_id = None
        self.current_tree_data = None
        self.photos = []
        self.new_photos = []
        self.captured_photo_path = None

        self._is_loading = False
        self.logger = get_logger()

        try:
            self.db = init_db()
        except Exception as ex:
            self.logger.error("Failed to init DB: %s", ex, exc_info=True)
            raise

    def setup_ui(self):
        font_path = os.path.join(os.path.dirname(__file__), "assets", "fonts", "Comfortaa-Regular.ttf")
        if os.path.exists(font_path):
            self.page.fonts = {"Comfortaa": font_path}

        self.setup_app_bar()
        self.setup_navigation()
        self.setup_list_view()
        self.setup_add_form()
        self.setup_edit_form()
        self.setup_detail_view()
        self.setup_settings_view()

        self.main_container = Stack([
            self.list_container,
            self.add_container,
            self.edit_container,
            self.detail_container,
            self.settings_container,
        ], expand=True)
        self.page.add(self.main_container)
        self.show_list_view()

    def update_tree_code(self):
        try:
            s = self.add_sector.value.strip() if self.add_sector.value else ""
            z = self.add_zone.value.strip() if self.add_zone.value else ""
            r = self.add_row.value.strip() if self.add_row.value else ""
            t = self.add_tree_number.value.strip() if self.add_tree_number.value else ""
            code = f"S{s}Z{z}R{r}T{t}" if (s or z or r or t) else ""
            self.add_tree_code.value = code
            if hasattr(self, 'location_header'):
                lat = self.add_latitude.value.strip() if self.add_latitude.value else ""
                lon = self.add_longitude.value.strip() if self.add_longitude.value else ""
                latlon = f" - {lat},{lon}" if lat and lon else ""
                if code:
                    self.location_header.value = f"Location {code}{latlon}"
                elif latlon:
                    self.location_header.value = f"Location{latlon}"
                else:
                    self.location_header.value = "Location"
                self.location_header.update()
        except Exception as ex:
            self.logger.warning("update_tree_code: %s", ex)

    def on_kind_change(self, e):
        kind = e.control.value
        if kind and kind in TREE_VARIETIES:
            self.add_variety.options = [DropdownOption(text=v, key=v) for v in TREE_VARIETIES[kind]]
        else:
            self.add_variety.options = []
        self.add_variety.value = None
        self.add_variety.update()

    def on_edit_kind_change(self, e):
        kind = e.control.value
        if kind and kind in TREE_VARIETIES:
            self.edit_variety.options = [DropdownOption(text=v, key=v) for v in TREE_VARIETIES[kind]]
        else:
            self.edit_variety.options = []
        self.edit_variety.value = None
        self.edit_variety.update()

    def setup_app_bar(self):
        self.search_field = TextField(
            hint_text="Search trees...",
            hint_style=TextStyle(color=Colors.GREY_500, font_family="Comfortaa"),
            border=InputBorder.NONE,
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
            icon_size=28,
            on_click=self.trigger_search,
            tooltip="Search",
        )

        self.search_input_container = Container(
            content=Row([
                self.search_field,
                self.search_clear_btn,
            ], spacing=8, alignment=MainAxisAlignment.END, vertical_alignment=CrossAxisAlignment.CENTER),
            width=280,
            height=40,
            bgcolor=Colors.WHITE,
            margin=Margin(0, 8, 8, 0),
            border_radius=BorderRadius(8, 8, 8, 8),
            padding=Padding(8, 0, 8, 0),
        )

        self.back_btn = IconButton(icon=Icons.ARROW_BACK, icon_color=Colors.WHITE, tooltip="Back")
        self.app_bar = AppBar(
            leading=None,
            title=None,
            bgcolor=Colors.GREEN_700,
            actions=[
                self.search_button,
                self.search_input_container,
                IconButton(icon=Icons.REFRESH, icon_color=Colors.WHITE, icon_size=28, on_click=lambda _: self.load_trees(), tooltip="Refresh"),
            ],
        )
        self.page.appbar = self.app_bar

    def setup_navigation(self):
        self.nav_bar = NavigationBar(
            destinations=[
                NavigationBarDestination(icon=Icons.LIST_ALT, label="Trees"),
                NavigationBarDestination(icon=Icons.ADD_CIRCLE, label="Add"),
                NavigationBarDestination(icon=Icons.SETTINGS, label="Settings"),
            ],
            selected_index=0,
            on_change=self.on_nav_change,
            bgcolor=Colors.WHITE,
            indicator_color=Colors.GREEN_100,
            label_behavior=ft.NavigationBarLabelBehavior.ALWAYS_SHOW,
        )
        self.page.navigation_bar = self.nav_bar

    def setup_list_view(self):
        self.tree_list = ListView(expand=True, spacing=8, padding=Padding(10, 10, 10, 80))
        self.loading_indicator = ProgressRing(visible=False, color=Colors.GREEN_700)
        self.empty_state = Container(
            content=Column([
                Icon(Icons.PARK, size=80, color=Colors.GREY_300),
                Text("No trees found", size=18, color=Colors.GREY_500, font_family="Comfortaa"),
                Text("Tap + to add your first tree", size=14, color=Colors.GREY_400, font_family="Comfortaa"),
            ], horizontal_alignment=CrossAxisAlignment.CENTER, spacing=10),
            alignment=alignment.Alignment(0, 0),
            expand=True,
            visible=False,
        )
        self.pagination_controls = Row([
            IconButton(icon=Icons.CHEVRON_LEFT, on_click=lambda _: self.prev_page(), disabled=True),
            Text("Page 1 / 1", size=14, font_family="Comfortaa"),
            IconButton(icon=Icons.CHEVRON_RIGHT, on_click=lambda _: self.next_page(), disabled=True),
        ], alignment=MainAxisAlignment.CENTER)

        self.pagination_bar = BottomAppBar(
            content=Container(
                content=self.pagination_controls,
                bgcolor=Colors.WHITE,
                padding=Padding(0, 4, 0, 4),
            ),
            bgcolor=Colors.WHITE,
        )

        self.loading_overlay = Container(
            content=Column([
                Container(height=180),
                ProgressRing(width=56, height=56, color=Colors.GREEN_700),
                Container(height=20),
                Text("Loading trees...", size=18, font_family="Comfortaa", color=Colors.GREEN_700, weight=FontWeight.BOLD),
                Text("Please wait while we gather your data", size=13, font_family="Comfortaa", color=Colors.GREY_500),
            ], horizontal_alignment=CrossAxisAlignment.CENTER, spacing=4),
            alignment=alignment.Alignment(0, 0),
            bgcolor=Colors.with_opacity(0.92, Colors.WHITE),
            expand=True,
            visible=False,
        )

        self.list_container = Container(
            content=Stack([
                Column([
                    self.loading_indicator,
                    self.tree_list,
                    self.empty_state,
                ], expand=True),
                self.loading_overlay,
            ], expand=True),
            expand=True,
            visible=True,
        )

    def setup_add_form(self):
        self.add_sector = TextField(
            label="Sector",
            label_style=TextStyle(font_family="Comfortaa", size=10),
            border=InputBorder.OUTLINE,
            text_style=TextStyle(font_family="Comfortaa"),
            on_change=lambda e: self.update_tree_code(),
        )
        self.add_zone = TextField(
            label="Zone",
            label_style=TextStyle(font_family="Comfortaa", size=10),
            border=InputBorder.OUTLINE,
            text_style=TextStyle(font_family="Comfortaa"),
            on_change=lambda e: self.update_tree_code(),
        )
        self.add_row = TextField(
            label="Row",
            label_style=TextStyle(font_family="Comfortaa", size=10),
            border=InputBorder.OUTLINE,
            text_style=TextStyle(font_family="Comfortaa"),
            on_change=lambda e: self.update_tree_code(),
        )
        self.add_tree_number = TextField(
            label="Tree",
            label_style=TextStyle(font_family="Comfortaa", size=10),
            border=InputBorder.OUTLINE,
            text_style=TextStyle(font_family="Comfortaa"),
            on_change=lambda e: self.update_tree_code(),
        )
        self.add_tree_code = TextField(
            label="Tree Code",
            hint_text="Auto-generated from Sector/Zone/Row/Tree#",
            border=InputBorder.OUTLINE,
            text_style=TextStyle(font_family="Comfortaa"),
            read_only=True,
        )
        self.add_latitude = TextField(
            label="Latitude",
            hint_text="Auto-fill with GPS",
            border=InputBorder.OUTLINE,
            keyboard_type=KeyboardType.NUMBER,
            text_style=TextStyle(font_family="Comfortaa"),
        )
        self.add_longitude = TextField(
            label="Longitude",
            hint_text="Auto-fill with GPS",
            border=InputBorder.OUTLINE,
            keyboard_type=KeyboardType.NUMBER,
            text_style=TextStyle(font_family="Comfortaa"),
        )

        self.location_header = Text("Location", size=16, weight=FontWeight.BOLD, font_family="Comfortaa", color=Colors.GREEN_700)
        self.gps_btn = IconButton(
            icon=Icons.MY_LOCATION,
            icon_size=20,
            icon_color=Colors.GREEN_700,
            tooltip="Get GPS location",
            on_click=lambda e: self.get_gps(self.add_latitude, self.add_longitude),
        )

        self.location_card = Card(
            content=Container(
                content=Column([
                    Row([
                        self.location_header,
                        self.gps_btn,
                    ], alignment=MainAxisAlignment.SPACE_BETWEEN),
                    Divider(height=12),
                    Row([
                        Container(content=self.add_sector, expand=True),
                        Container(content=self.add_zone, expand=True),
                        Container(content=self.add_row, expand=True),
                        Container(content=self.add_tree_number, expand=True),
                    ], spacing=8),
                ], spacing=10),
                padding=Padding(16, 12, 16, 12),
            ),
            elevation=2,
            margin=Margin(0, 0, 0, 12),
        )

        self.add_kind = Dropdown(
            label="Kind *",
            options=KIND_DROPDOWN_ITEMS,
            border=InputBorder.OUTLINE,
            text_style=TextStyle(font_family="Comfortaa"),
        )
        self.add_kind.on_change = self.on_kind_change
        self.add_variety = Dropdown(
            label="Variety",
            hint_text="Select variety",
            border=InputBorder.OUTLINE,
            text_style=TextStyle(font_family="Comfortaa"),
            expand=True,
        )
        self.add_status = Dropdown(
            label="Status *",
            options=STATUS_DROPDOWN_ITEMS,
            border=InputBorder.OUTLINE,
            text_style=TextStyle(font_family="Comfortaa"),
            expand=True,
        )
        self.add_notes = TextField(
            label="Notes",
            border=InputBorder.OUTLINE,
            multiline=True,
            min_lines=2,
            max_lines=4,
            text_style=TextStyle(font_family="Comfortaa"),
            expand=True,
        )

        self.add_photo_img = Image(
            src="",
            width=320,
            height=240,
            fit=BoxFit.COVER,
            border_radius=BorderRadius(8,8,8,8),
            visible=False,
        )
        self.add_photo_placeholder = Container(
            content=Column([
                Icon(Icons.CAMERA_ALT, size=64, color=Colors.GREY_400),
                Text("No photo captured", size=14, color=Colors.GREY_500, font_family="Comfortaa"),
            ], horizontal_alignment=CrossAxisAlignment.CENTER, spacing=10),
            width=320,
            height=240,
            border=Border.all(2, Colors.GREY_300),
            border_radius=BorderRadius(8,8,8,8),
            alignment=alignment.Alignment(0, 0),
        )
        self.add_take_photo_btn = FilledButton(
            content=Row([Icon(Icons.CAMERA_ALT), Text("Take Photo")], spacing=8, alignment=MainAxisAlignment.CENTER),
            on_click=lambda _: self.show_snack("Camera not available", Colors.RED),
            style=ButtonStyle(color=Colors.WHITE, bgcolor=Colors.GREEN_700, padding=Padding(16, 12, 16, 12)),
        )

        # Photos Card
        self.photos_card = Card(
            content=Container(
                content=Column([
                    Row([
                        Text("Photo", size=16, weight=FontWeight.BOLD, font_family="Comfortaa", color=Colors.GREEN_700),
                    ], alignment=MainAxisAlignment.START),
                    Divider(height=12),
                    self.add_photo_placeholder,
                    self.add_photo_img,
                    self.add_take_photo_btn,
                ], spacing=10, horizontal_alignment=CrossAxisAlignment.CENTER),
                padding=Padding(16, 12, 16, 12),
            ),
            elevation=2,
            margin=Margin(0, 0, 0, 12),
        )

        # Tree Details Card
        self.tree_details_card = Card(
            content=Container(
                content=Column([
                    Row([
                        Text("Tree Details", size=16, weight=FontWeight.BOLD, font_family="Comfortaa", color=Colors.GREEN_700),
                    ], alignment=MainAxisAlignment.START),
                    Divider(height=12),
                    Row([
                        Container(content=self.add_kind, expand=True),
                        Container(content=self.add_variety, expand=True),
                    ], spacing=10),
                    Container(content=self.add_status, expand=True),
                    Container(content=self.add_notes, expand=True),
                ], spacing=12),
                padding=Padding(16, 12, 16, 12),
            ),
            elevation=2,
            margin=Margin(0, 0, 0, 12),
        )
        self.add_save_btn = Button(
            content=Text("Save Tree"),
            icon=Icons.SAVE,
            on_click=self.save_new_tree,
            style=ButtonStyle(
                bgcolor=Colors.GREEN_700,
                color=Colors.WHITE,
                padding=Padding(20, 12, 20, 12),
            ),
        )
        self.add_save_next_btn = Button(
            content=Text("Save & Next"),
            icon=Icons.SKIP_NEXT,
            on_click=self.save_new_tree_next,
            style=ButtonStyle(
                bgcolor=Colors.GREEN_500,
                color=Colors.WHITE,
                padding=Padding(20, 12, 20, 12),
            ),
        )

        self.add_container = Container(
            content=ListView([
                Container(
                    content=Column([
                        Row([Text("Add New Tree", size=24, weight=FontWeight.BOLD, font_family="Comfortaa", color=Colors.GREEN_700)], spacing=8, vertical_alignment=CrossAxisAlignment.CENTER),
                        Divider(height=12),
                        self.photos_card,
                        Divider(height=8),
                        self.location_card,
                        Divider(height=8),
                        self.tree_details_card,
                        Divider(height=12),
                        Row([self.add_save_btn, self.add_save_next_btn], spacing=10, alignment=MainAxisAlignment.CENTER),
                    ], spacing=12, horizontal_alignment=CrossAxisAlignment.START),
                    padding=Padding(20, 20, 20, 20),
                ),
            ], expand=True, padding=Padding(0, 0, 0, 20)),
            visible=False,
        )

    def setup_edit_form(self):
        self.edit_tree_code = TextField(
            label="Tree Code *",
            border=InputBorder.OUTLINE,
            text_style=TextStyle(font_family="Comfortaa"),
            read_only=True,
        )
        self.edit_kind = Dropdown(
            label="Kind *",
            options=KIND_DROPDOWN_ITEMS,
            border=InputBorder.OUTLINE,
            text_style=TextStyle(font_family="Comfortaa"),
            expand=True,
        )
        self.edit_kind.on_change = self.on_edit_kind_change
        self.edit_variety = Dropdown(
            label="Variety",
            hint_text="Select variety",
            border=InputBorder.OUTLINE,
            text_style=TextStyle(font_family="Comfortaa"),
            expand=True,
        )
        self.edit_latitude = TextField(
            label="Latitude",
            border=InputBorder.OUTLINE,
            keyboard_type=KeyboardType.NUMBER,
            text_style=TextStyle(font_family="Comfortaa"),
            read_only=True,
            expand=True,
        )
        self.edit_longitude = TextField(
            label="Longitude",
            border=InputBorder.OUTLINE,
            keyboard_type=KeyboardType.NUMBER,
            text_style=TextStyle(font_family="Comfortaa"),
            read_only=True,
            expand=True,
        )
        self.edit_visits_list = Column(spacing=8)
        self.add_visit_status = Dropdown(
            label="Visit Status *",
            options=STATUS_DROPDOWN_ITEMS,
            border=InputBorder.OUTLINE,
            text_style=TextStyle(font_family="Comfortaa"),
        )
        self.add_visit_notes = TextField(
            label="Visit Notes",
            border=InputBorder.OUTLINE,
            multiline=True,
            min_lines=2,
            max_lines=4,
            text_style=TextStyle(font_family="Comfortaa"),
        )
        self.add_visit_photos_grid = GridView(expand=False, max_extent=100, child_aspect_ratio=1, spacing=8, run_spacing=8)
        self.add_visit_photo_btn = OutlinedButton(
            content=Text("Add Photos"),
            icon=Icons.PHOTO_CAMERA,
            on_click=lambda _: self.show_snack("Photo capture coming soon", Colors.BLUE),
            style=ButtonStyle(color=Colors.GREEN_700),
        )
        self.edit_save_btn = Button(
            content=Text("Save Changes"),
            icon=Icons.SAVE,
            on_click=self.save_edit_changes,
            style=ButtonStyle(
                bgcolor=Colors.GREEN_700,
                color=Colors.WHITE,
                padding=Padding(20, 12, 20, 12),
            ),
        )
        self.edit_delete_btn = OutlinedButton(
            content=Text("Delete Tree"),
            icon=Icons.DELETE,
            icon_color=Colors.RED,
            style=ButtonStyle(color=Colors.RED),
            on_click=lambda _: self.confirm_delete_current(),
        )

        self.edit_container = Container(
            content=ListView([
                Container(
                    content=Column([
                        Text("Edit Tree", size=24, weight=FontWeight.BOLD, font_family="Comfortaa", color=Colors.GREEN_700),
                        Divider(height=12),
                        Card(
                            content=Container(
                                content=Column([
                                    Row([
                                        Text("Tree Details", size=16, weight=FontWeight.BOLD, font_family="Comfortaa", color=Colors.GREEN_700),
                                    ], alignment=MainAxisAlignment.START),
                                    Divider(height=12),
                                    self.edit_tree_code,
                                    Row([self.edit_kind, self.edit_variety], spacing=10),
                                    Row([
                                        self.edit_latitude,
                                        self.edit_longitude,
                                        IconButton(
                                            icon=Icons.MY_LOCATION,
                                            icon_size=18,
                                            icon_color=Colors.GREEN_700,
                                            tooltip="Get GPS location",
                                            on_click=lambda e: self.get_gps(self.edit_latitude, self.edit_longitude),
                                        ),
                                    ], spacing=10, vertical_alignment=CrossAxisAlignment.CENTER),
                                ], spacing=12),
                                padding=Padding(16, 12, 16, 12),
                            ),
                            elevation=2,
                            margin=Margin(0, 0, 0, 12),
                        ),
                        Divider(height=8),
                        Text("Visit History", size=18, weight=FontWeight.W_500, font_family="Comfortaa"),
                        self.edit_visits_list,
                        Divider(height=10),
                        Text("Add New Visit", size=18, weight=FontWeight.W_500, font_family="Comfortaa"),
                        self.add_visit_status,
                        self.add_visit_notes,
                        Text("Visit Photos", size=14, weight=FontWeight.W_500, font_family="Comfortaa"),
                        self.add_visit_photos_grid,
                        self.add_visit_photo_btn,
                        Divider(height=20),
                        Row([self.edit_save_btn, self.edit_delete_btn], spacing=10, alignment=MainAxisAlignment.CENTER),
                    ], spacing=12, horizontal_alignment=CrossAxisAlignment.START),
                    padding=Padding(20, 20, 20, 20),
                ),
            ], expand=True, padding=Padding(0, 0, 0, 20)),
            visible=False,
        )

    def setup_detail_view(self):
        self.detail_tree_code = Text("", size=16, font_family="Comfortaa")
        self.detail_kind = Text("", size=16, font_family="Comfortaa")
        self.detail_variety = Text("", size=16, font_family="Comfortaa")
        self.detail_location = Text("", size=16, font_family="Comfortaa")
        self.detail_status_badge = Container(
            bgcolor=Colors.GREEN_100,
            padding=Padding(12, 4, 12, 4),
            border_radius=BorderRadius(20, 20, 20, 20),
        )
        self.detail_notes = Text("", size=14, font_family="Comfortaa", color=Colors.GREY_700)
        self.detail_photos_grid = GridView(expand=False, max_extent=120, child_aspect_ratio=1, spacing=8, run_spacing=8)
        self.detail_visits_list = Column(spacing=8)

        self.detail_edit_btn = Button(
            content=Text("Edit"),
            icon=Icons.EDIT,
            on_click=lambda _: self.edit_current_tree(),
            style=ButtonStyle(
                bgcolor=Colors.GREEN_700,
                color=Colors.WHITE,
                padding=Padding(20, 12, 20, 12),
            ),
        )
        self.detail_delete_btn = OutlinedButton(
            content=Text("Delete"),
            icon=Icons.DELETE,
            icon_color=Colors.RED,
            style=ButtonStyle(color=Colors.RED),
            on_click=lambda _: self.confirm_delete_current(),
        )

        self.detail_add_visit_btn = Button(
            content=Text("New Visit"),
            icon=Icons.ADD,
            on_click=lambda _: self.edit_current_tree(),
            style=ButtonStyle(
                bgcolor=Colors.GREEN_500,
                color=Colors.WHITE,
                padding=Padding(16, 12, 16, 12),
            ),
        )

        self.detail_container = Container(
            content=ListView([
                Container(
                    content=Column([
                        Row([
                            Text("Tree Details", size=24, weight=FontWeight.BOLD, font_family="Comfortaa", color=Colors.GREEN_700, expand=True),
                        ]),
                        Divider(height=10),
                        Card(
                            content=Container(
                                content=Column([
                                    self.detail_tree_code,
                                    self.detail_kind,
                                    self.detail_variety,
                                    self.detail_location,
                                    Row([self.detail_status_badge], alignment=MainAxisAlignment.START),
                                    Text("Notes:", weight=FontWeight.W_500, font_family="Comfortaa"),
                                    self.detail_notes,
                                ], spacing=8, horizontal_alignment=CrossAxisAlignment.START),
                                padding=Padding(16, 16, 16, 16),
                            ),
                            elevation=2,
                        ),
                        Divider(height=10),
                        Text("Photos", size=18, weight=FontWeight.W_500, font_family="Comfortaa"),
                        self.detail_photos_grid,
                        Divider(height=10),
                        Text("Visit History", size=18, weight=FontWeight.W_500, font_family="Comfortaa"),
                        self.detail_visits_list,
                        Divider(height=20),
                        Row([self.detail_edit_btn, self.detail_add_visit_btn, self.detail_delete_btn], spacing=10, alignment=MainAxisAlignment.CENTER),
                    ], spacing=12, horizontal_alignment=CrossAxisAlignment.START),
                    padding=Padding(20, 20, 20, 20),
                ),
            ], expand=True, padding=Padding(0, 0, 0, 20)),
            visible=False,
        )

    def on_nav_change(self, e):
        idx = e.control.selected_index
        if idx == 0:
            self.show_list_view()
        elif idx == 1:
            self.show_add_form()
        elif idx == 2:
            self.show_settings_view()
        self.nav_bar.selected_index = idx
        self.nav_bar.update()

    def show_list_view(self):
        self.logger.debug("Navigating to list view")
        self.app_bar.leading = None
        self.app_bar.update()
        self.list_container.visible = True
        self.add_container.visible = False
        self.edit_container.visible = False
        self.detail_container.visible = False
        self.settings_container.visible = False
        self.nav_bar.selected_index = 0
        self.nav_bar.update()
        self.page.bottom_appbar = self.pagination_bar
        self.main_container.update()
        self.page.update()
        invalidate_cache()
        self.current_page = 0
        self.load_trees()

    def show_add_form(self):
        self.logger.debug("Navigating to add form")
        self.back_btn.on_click = lambda _: self.show_list_view()
        self.app_bar.leading = self.back_btn
        self.app_bar.update()
        self.reset_add_form()
        self.list_container.visible = False
        self.add_container.visible = True
        self.edit_container.visible = False
        self.detail_container.visible = False
        self.settings_container.visible = False
        self.nav_bar.selected_index = 1
        self.nav_bar.update()
        self.page.bottom_appbar = None
        self.main_container.update()
        self.page.update()
        self.get_gps(self.add_latitude, self.add_longitude)

    def show_search_view(self):
        self.list_container.visible = True
        self.add_container.visible = False
        self.edit_container.visible = False
        self.detail_container.visible = False
        self.settings_container.visible = False
        self.nav_bar.selected_index = 0
        self.nav_bar.update()
        self.page.bottom_appbar = None
        self.main_container.update()
        self.page.update()
        asyncio.create_task(self.search_field.focus())
        if self.search_query:
            self.load_trees()
        else:
            self.current_page = 0
            self.load_trees()

    def setup_settings_view(self):
        self.settings_container = Container(
            content=Column([
                Text("Settings", size=24, weight=FontWeight.BOLD, font_family="Comfortaa", color=Colors.GREEN_700),
                Divider(height=2, color=Colors.GREEN_200),
                Container(height=10),
                Card(
                    content=ListTile(
                        leading=Icon(Icons.HELP, color=Colors.GREEN_700),
                        title=Text("Help", font_family="Comfortaa", weight=FontWeight.BOLD),
                        subtitle=Text("Learn how to use the app", font_family="Comfortaa"),
                        on_click=self.show_help,
                    ),
                    elevation=2,
                ),
                Container(height=5),
                Card(
                    content=ListTile(
                        leading=Icon(Icons.INFO, color=Colors.GREEN_700),
                        title=Text("About", font_family="Comfortaa", weight=FontWeight.BOLD),
                        subtitle=Text("Farm Tree Manager v" + version.version, font_family="Comfortaa"),
                        on_click=self.show_about,
                    ),
                    elevation=2,
                ),
                Container(height=5),
                Card(
                    content=ListTile(
                        leading=Icon(Icons.BUG_REPORT, color=Colors.GREEN_700),
                        title=Text("View Logs", font_family="Comfortaa", weight=FontWeight.BOLD),
                        subtitle=Text("Check app logs for troubleshooting", font_family="Comfortaa"),
                        on_click=self.show_logs,
                    ),
                    elevation=2,
                ),
            ], spacing=0, scroll=ScrollMode.AUTO),
            padding=Padding(20, 20, 20, 20),
            expand=True,
            visible=False,
        )

    def show_settings_view(self):
        self.list_container.visible = False
        self.add_container.visible = False
        self.edit_container.visible = False
        self.detail_container.visible = False
        self.settings_container.visible = True
        self.nav_bar.selected_index = 2
        self.nav_bar.update()
        self.page.bottom_appbar = None
        self.main_container.update()
        self.page.update()

    def show_help(self, e):
        def close(e):
            dlg.open = False
            self.page.update()

        dlg = AlertDialog(
            title=Text("Help", font_family="Comfortaa", weight=FontWeight.BOLD),
            content=Column([
                Text("• Tap + to add a new tree.", font_family="Comfortaa"),
                Text("• Tap a tree card to view its details.", font_family="Comfortaa"),
                Text("• Long-press a tree for quick actions.", font_family="Comfortaa"),
                Text("• Use the search bar to find trees.", font_family="Comfortaa"),
                Text("• Track visits and update tree status.", font_family="Comfortaa"),
                Text("• Photos and notes can be added per visit.", font_family="Comfortaa"),
            ], spacing=8, tight=True),
            actions=[TextButton("Close", on_click=close)],
        )
        self.page.dialog = dlg
        dlg.open = True
        self.page.update()

    def show_about(self, e):
        def close(e):
            dlg.open = False
            self.page.update()

        dlg = AlertDialog(
            title=Text("About", font_family="Comfortaa", weight=FontWeight.BOLD),
            content=Column([
                Text("Farm Tree Manager", size=18, weight=FontWeight.BOLD, font_family="Comfortaa"),
                Text("Version " + version.version, font_family="Comfortaa"),
                Divider(),
                Text("A farm tree management app for tracking tree health, visits, and maintenance.", font_family="Comfortaa"),
            ], spacing=8, tight=True),
            actions=[TextButton("Close", on_click=close)],
        )
        self.page.dialog = dlg
        dlg.open = True
        self.page.update()

    def show_logs(self, e):
        def close(e):
            dlg.open = False
            self.page.update()

        def refresh(e):
            lines = read_logs(200)
            content.controls = [Text(l.rstrip(), size=11, font_family="Consolas", selectable=True) for l in lines]
            dlg.content = Column([Text("App Logs", size=16, weight=FontWeight.BOLD), Divider(), content], width=360, height=500)
            self.page.update()

        lines = read_logs(200)
        content = Column(
            [Text(l.rstrip(), size=11, font_family="Consolas", selectable=True) for l in lines],
            scroll=ScrollMode.AUTO, spacing=2,
        )
        dlg = AlertDialog(
            title=Text("Logs", font_family="Comfortaa", weight=FontWeight.BOLD),
            content=Column([Text("App Logs", size=16, weight=FontWeight.BOLD), Divider(), content], width=360, height=500),
            actions=[
                TextButton("Refresh", on_click=refresh),
                TextButton("Close", on_click=close),
            ],
        )
        self.page.dialog = dlg
        dlg.open = True
        self.page.update()

    def trigger_search(self, e=None):
        if hasattr(self, 'search_field'):
            asyncio.create_task(self.search_field.focus())
            self.current_page = 0
            self.load_trees()
        else:
            self.show_search_view()

    def reset_add_form(self):
        # Only reset form values - don't update controls
        if hasattr(self, 'add_sector'):
            self.add_sector.value = ""
            self.add_zone.value = ""
            self.add_row.value = ""
            self.add_tree_number.value = ""
            self.add_kind.value = None
            self.add_variety.value = None
            self.add_variety.options = []
            self.add_latitude.value = ""
            self.add_longitude.value = ""
            self.add_status.value = None
            self.add_notes.value = ""
            self.captured_photo_path = None
            self.add_photo_img.visible = False
            self.add_photo_placeholder.visible = True
            self.add_take_photo_btn.visible = True

            self.update_tree_code()

            # Note: Controls will be updated when they are added to the page
            # to avoid "Control must be added to the page first" error

    def show_loading_overlay(self):
        self.loading_overlay.visible = True
        self.loading_overlay.update()

    def hide_loading_overlay(self):
        self.loading_overlay.visible = False
        self.loading_overlay.update()

    def load_trees(self):
        self._is_loading = True
        self.show_loading_overlay()
        self.tree_list.controls.clear()

        try:
            if self.search_query or self.filter_kind or self.filter_status:
                trees = search_trees(self.search_query, self.filter_kind, self.filter_status)
                total = len(trees)
            else:
                batch_end = (self.current_page + 1) * self.per_page
                batch_end = ((batch_end - 1) // self.PAGE_CHUNK + 1) * self.PAGE_CHUNK
                trees = get_trees_slice(0, batch_end)
                total = count_trees()
        except Exception as ex:
            self.logger.error("Failed to load trees: %s", ex, exc_info=True)
            self.show_snack("Error loading trees", Colors.RED)
            self.hide_loading_overlay()
            self._is_loading = False
            return

        if not total:
            self.tree_list.visible = False
            self.empty_state.visible = True
            self.pagination_controls.visible = False
        else:
            self.tree_list.visible = True
            self.empty_state.visible = False
            self.pagination_controls.visible = True
            start = self.current_page * self.per_page
            end = min(start + self.per_page, total)
            page_trees = trees[start:end]
            for tree in page_trees:
                self.tree_list.controls.append(self.create_tree_card(tree))

        self.update_pagination(total)
        self.tree_list.update()
        self.empty_state.update()
        self.pagination_controls.update()
        self.hide_loading_overlay()
        self._is_loading = False

    def update_pagination(self, total):
        total_pages = max(1, (total + self.per_page - 1) // self.per_page)
        self.pagination_controls.controls[0].disabled = self.current_page == 0
        self.pagination_controls.controls[2].disabled = self.current_page >= total_pages - 1
        self.pagination_controls.controls[1].value = f"Page {self.current_page + 1} / {total_pages}"
        self.pagination_controls.update()

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.load_trees()

    def next_page(self):
        self.current_page += 1
        self.load_trees()

    def on_search_change(self, e):
        self.search_query = e.control.value.strip()
        self.search_clear_btn.visible = bool(self.search_query)
        self.search_clear_btn.update()
        self.current_page = 0
        self.load_trees()

    def clear_search(self, e):
        self.search_field.value = ""
        self.search_query = ""
        self.search_clear_btn.visible = False
        self.search_clear_btn.update()
        self.search_field.update()
        invalidate_cache()
        self.current_page = 0
        self.load_trees()

    def create_tree_card(self, tree: dict):
        tree_code = tree.get("tree_code", "Unknown")
        kind = tree.get("kind", "")
        variety = tree.get("variety", "")
        last_status = tree.get("last_status", "No visits")
        last_photo = tree.get("last_photo", "")
        last_notes = tree.get("last_notes", "")
        lat = tree.get("latitude", "")
        lon = tree.get("longitude", "")

        status_color = STATUS_LOOKUP.get(last_status, "#455A64")
        status_badge = Container(
            content=Text(last_status, size=13, weight=FontWeight.BOLD, font_family="Comfortaa", color=Colors.WHITE),
            bgcolor=status_color,
            padding=Padding(12, 4, 12, 4),
            border_radius=BorderRadius(20, 20, 20, 20),
        )

        leading = Container(
            width=60, height=60,
            border_radius=BorderRadius(8,8,8,8),
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
            content=Image(src=last_photo, fit=BoxFit.COVER) if last_photo else Icon(Icons.PARK, size=30, color=Colors.GREEN_700),
            bgcolor=Colors.GREEN_50 if not last_photo else None,
        )

        subtitle = Column([
            Row([
                Text(kind, size=13, color=Colors.GREY_700, font_family="Comfortaa"),
                Text(f" \u2022 {variety}" if variety else "", size=13, color=Colors.GREY_700, font_family="Comfortaa"),
            ], spacing=0),
            Row([
                Text(f"Lat: {lat}, Lon: {lon}" if lat or lon else "No location", size=12, color=Colors.GREY_500, font_family="Comfortaa"),
            ], spacing=0),
            Row([status_badge], spacing=8),
        ], spacing=4, tight=True)

        def on_tap(e):
            self.show_tree_detail(tree)

        def on_long_press(e):
            self.show_tree_context_menu(tree)

        card = Card(
            content=ListTile(
                leading=leading,
                title=Text(tree_code, weight=FontWeight.BOLD, size=16, font_family="Comfortaa"),
                subtitle=subtitle,
                trailing=IconButton(icon=Icons.CHEVRON_RIGHT, on_click=lambda _, t=tree: self.show_tree_detail(t)),
                on_click=on_tap,
                on_long_press=on_long_press,
                content_padding=Padding(10, 8, 10, 8),
            ),
            elevation=2,
            margin=Margin(0, 0, 0, 0),
        )
        return card

    def show_tree_context_menu(self, tree: dict):
        def make_handler(fn):
            def handler(e):
                bs.open = False
                self.page.update()
                fn()
            return handler

        def on_edit():
            self.current_tree_id = tree["id"]
            self.populate_edit_form(tree)
            self.list_container.visible = False
            self.edit_container.visible = True
            self.main_container.update()

        def on_delete():
            self.current_tree_id = tree["id"]
            self.confirm_delete_current()

        def on_history():
            self.show_history_bottom_sheet(tree["id"])

        items = Column([
            ListTile(leading=Icon(Icons.EDIT), title=Text("Edit Tree", font_family="Comfortaa"), on_click=make_handler(on_edit)),
            ListTile(leading=Icon(Icons.FLAG), title=Text("Quick Status Change", font_family="Comfortaa"), on_click=make_handler(lambda: self.show_status_picker(tree))),
            ListTile(leading=Icon(Icons.HISTORY), title=Text("View History", font_family="Comfortaa"), on_click=make_handler(on_history)),
            ListTile(leading=Icon(Icons.DELETE), title=Text("Delete Tree", font_family="Comfortaa"), on_click=make_handler(on_delete)),
        ], spacing=0)

        bs = BottomSheet(
            content=Container(
                content=Column([
                    Text("Actions", size=18, weight=FontWeight.BOLD, font_family="Comfortaa"),
                    Divider(),
                    items,
                ], spacing=8, tight=True),
                padding=Padding(20, 20, 20, 20),
            ),
            open=True,
        )
        self.page.overlay.append(bs)
        self.page.update()

    def show_status_picker(self, tree: dict):
        def on_status_click(status):
            update_tree_status(tree["id"], status)
            self.show_snack(f"Status updated to {status}", Colors.GREEN)
            self.load_trees()
            bs.open = False
            self.page.update()

        items = []
        for status, color in STATUS_LOOKUP.items():
            items.append(
                PopupMenuItem(
                    content=Row([
                        Container(width=12, height=12, bgcolor=color, border_radius=BorderRadius(6, 6, 6, 6)),
                        Text(status, font_family="Comfortaa"),
                    ], spacing=10),
                    on_click=lambda _, s=status: on_status_click(s),
                )
            )

        bs = BottomSheet(
            content=Container(
                content=Column([
                    Text("Change Status", size=18, weight=FontWeight.BOLD, font_family="Comfortaa"),
                    Divider(),
                    ListView(items, spacing=4, shrink_wrap=True),
                ], spacing=8, tight=True),
                padding=Padding(20, 20, 20, 20),
            ),
            open=True,
        )
        self.page.overlay.append(bs)
        self.page.update()

    def show_history_bottom_sheet(self, tree_id: int):
        tree = get_tree(tree_id)
        if not tree:
            return

        visits = tree.get("visits", [])
        items = []
        for visit in reversed(visits):
            status = visit.get("status", "")
            color = STATUS_LOOKUP.get(status, Colors.GREY)
            photos = visit.get("photos", [])
            photo_controls = []
            for p in photos:
                photo_controls.append(
                    Container(
                        content=Image(src=p, fit=BoxFit.COVER, width=50, height=50, border_radius=BorderRadius(6, 6, 6, 6)),
                        width=50, height=50, border_radius=BorderRadius(6, 6, 6, 6), clip_behavior=ft.ClipBehavior.HARD_EDGE,
                    )
                )

            items.append(
                Card(
                    content=Container(
                        content=Column([
                            Row([
                                Text(visit.get("visit_dt", ""), weight=FontWeight.BOLD, size=13, font_family="Comfortaa"),
                                Container(
                                    content=Text(status, size=11, weight=FontWeight.W_500, color=Colors.WHITE, font_family="Comfortaa"),
                                    bgcolor=color, padding=Padding(6, 2, 6, 2), border_radius=BorderRadius(10, 10, 10, 10),
                                ),
                            ], alignment=MainAxisAlignment.SPACE_BETWEEN),
                            Text(visit.get("notes", "No notes"), size=13, color=Colors.GREY_700, font_family="Comfortaa"),
                            Row(photo_controls, spacing=4) if photo_controls else Container(),
                        ], spacing=4, tight=True),
                        padding=Padding(12, 10, 12, 10),
                    ),
                    elevation=1,
                )
            )

        bs = BottomSheet(
            content=Container(
                content=Column([
                    Text("Visit History", size=18, weight=FontWeight.BOLD, font_family="Comfortaa"),
                    Divider(),
                    ListView(items, spacing=8, shrink_wrap=True, expand=True),
                ], spacing=8, tight=True),
                padding=Padding(20, 20, 20, 20),
                height=400,
            ),
            open=True,
        )
        self.page.overlay.append(bs)
        self.page.update()

    def show_tree_detail(self, tree: dict):
        self.current_tree_id = tree["id"]
        self.current_tree_data = tree
        self.back_btn.on_click = lambda _: self.show_list_view()
        self.app_bar.leading = self.back_btn
        self.app_bar.update()
        self.populate_detail_view(tree)
        self.list_container.visible = False
        self.add_container.visible = False
        self.edit_container.visible = False
        self.detail_container.visible = True
        self.settings_container.visible = False
        self.nav_bar.selected_index = 0
        self.nav_bar.update()
        self.page.bottom_appbar = None
        self.main_container.update()
        self.page.update()

    def populate_detail_view(self, tree: dict):
        self.detail_tree_code.value = f"Code: {tree.get('tree_code', 'N/A')}"
        self.detail_kind.value = f"Kind: {tree.get('kind', 'N/A')}"
        self.detail_variety.value = f"Variety: {tree.get('variety', 'N/A')}"
        lat = tree.get('latitude', '')
        lon = tree.get('longitude', '')
        self.detail_location.value = f"Location: {lat}, {lon}" if lat or lon else "Location: Not set"
        last_status = tree.get("last_status", "No visits")
        status_color = STATUS_LOOKUP.get(last_status, "#455A64")
        self.detail_status_badge.bgcolor = status_color
        self.detail_status_badge.content = Text(last_status, size=13, weight=FontWeight.BOLD, font_family="Comfortaa", color=Colors.WHITE)
        self.detail_notes.value = tree.get("last_notes", "No notes")

        self.detail_photos_grid.controls.clear()
        visits = tree.get("visits", [])
        all_photos = []
        for visit in visits:
            for photo in visit.get("photos", []):
                all_photos.append(photo)
        for photo in all_photos:
            self.detail_photos_grid.controls.append(
                Container(
                    content=Image(src=photo, fit=BoxFit.COVER, border_radius=BorderRadius(8, 8, 8, 8)),
                    width=120, height=120, border_radius=BorderRadius(8,8,8,8), clip_behavior=ft.ClipBehavior.HARD_EDGE,
                )
            )

        self.detail_visits_list.controls.clear()
        for visit in reversed(visits):
            status = visit.get("status", "")
            status_color = STATUS_LOOKUP.get(status, Colors.GREY)
            photos = visit.get("photos", [])
            photo_chips = []
            for p in photos:
                photo_chips.append(
                    Container(
                        content=Image(src=p, fit=BoxFit.COVER, width=50, height=50, border_radius=BorderRadius(6, 6, 6, 6)),
                        width=50, height=50, border_radius=BorderRadius(6, 6, 6, 6), clip_behavior=ft.ClipBehavior.HARD_EDGE,
                    )
                )
            self.detail_visits_list.controls.append(
                Card(
                    content=Container(
                        content=Column([
                            Row([
                                Text(visit.get("visit_dt", ""), weight=FontWeight.BOLD, size=13, font_family="Comfortaa"),
                                Container(
                                    content=Text(status, size=11, weight=FontWeight.W_500, color=Colors.WHITE, font_family="Comfortaa"),
                                    bgcolor=status_color, padding=Padding(6, 2, 6, 2), border_radius=BorderRadius(10, 10, 10, 10),
                                ),
                            ], alignment=MainAxisAlignment.SPACE_BETWEEN),
                            Text(visit.get("notes", "No notes"), size=13, color=Colors.GREY_700, font_family="Comfortaa"),
                            Row(photo_chips, spacing=4) if photo_chips else Container(),
                        ], spacing=4, tight=True),
                        padding=Padding(12, 10, 12, 10),
                    ),
                    elevation=1,
                )
            )

        self.detail_tree_code.update()
        self.detail_kind.update()
        self.detail_variety.update()
        self.detail_location.update()
        self.detail_status_badge.update()
        self.detail_notes.update()
        self.detail_photos_grid.update()
        self.detail_visits_list.update()

    def edit_current_tree(self):
        self.current_tree_id = self.current_tree_data["id"]
        self.back_btn.on_click = lambda _: self.show_tree_detail(self.current_tree_data) if self.current_tree_data else self.show_list_view()
        self.app_bar.leading = self.back_btn
        self.app_bar.update()
        self.populate_edit_form(self.current_tree_data)
        self.detail_container.visible = False
        self.edit_container.visible = True
        self.page.bottom_appbar = None
        self.page.update()
        self.main_container.update()

    def populate_edit_form(self, tree: dict):
        self.edit_tree_code.value = tree.get("tree_code", "")
        self.edit_kind.value = tree.get("kind", "")
        self.edit_variety.value = tree.get("variety", "")
        self.edit_latitude.value = tree.get("latitude", "")
        self.edit_longitude.value = tree.get("longitude", "")

        self.edit_visits_list.controls.clear()
        visits = tree.get("visits", [])
        for visit in reversed(visits):
            status = visit.get("status", "")
            status_color = STATUS_LOOKUP.get(status, Colors.GREY)
            photos = visit.get("photos", [])
            photo_controls = []
            for p in photos:
                photo_controls.append(
                    Container(
                        content=Image(src=p, fit=BoxFit.COVER, width=40, height=40, border_radius=BorderRadius(6, 6, 6, 6)),
                        width=40, height=40, border_radius=BorderRadius(6, 6, 6, 6), clip_behavior=ft.ClipBehavior.HARD_EDGE,
                    )
                )
            self.edit_visits_list.controls.append(
                Card(
                    content=Container(
                        content=Column([
                            Row([
                                Text(visit.get("visit_dt", ""), weight=FontWeight.BOLD, size=13, font_family="Comfortaa"),
                                Container(
                                    content=Text(status, size=11, weight=FontWeight.W_500, color=Colors.WHITE, font_family="Comfortaa"),
                                    bgcolor=status_color, padding=Padding(6, 2, 6, 2), border_radius=BorderRadius(10, 10, 10, 10),
                                ),
                            ], alignment=MainAxisAlignment.SPACE_BETWEEN),
                            Text(visit.get("notes", "No notes"), size=13, color=Colors.GREY_700, font_family="Comfortaa"),
                            Row(photo_controls, spacing=4) if photo_controls else Container(),
                        ], spacing=4, tight=True),
                        padding=Padding(12, 10, 12, 10),
                    ),
                    elevation=1,
                )
            )

        self.add_visit_status.value = None
        self.add_visit_notes.value = ""
        self.add_visit_photos_grid.controls.clear()
        self.new_photos = []

        self.edit_tree_code.update()
        self.edit_kind.update()
        self.edit_variety.update()
        self.edit_latitude.update()
        self.edit_longitude.update()
        self.edit_visits_list.update()
        self.add_visit_status.update()
        self.add_visit_notes.update()
        self.add_visit_photos_grid.update()

    def confirm_delete_current(self):
        def confirm(e):
            self.delete_current_tree()
            dlg.open = False
            self.page.update()

        def cancel(e):
            dlg.open = False
            self.page.update()

        dlg = AlertDialog(
            title=Text("Delete Tree", font_family="Comfortaa"),
            content=Text("Are you sure you want to delete this tree and all its visits?", font_family="Comfortaa"),
            actions=[
                TextButton("Cancel", on_click=cancel),
                TextButton("Delete", on_click=confirm, style=ButtonStyle(color=Colors.RED)),
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
                self.logger.error("Failed to delete tree %s: %s", self.current_tree_id, ex, exc_info=True)
                self.show_snack("Error deleting tree", Colors.RED)
                return
            for p in photos:
                try:
                    os.remove(p)
                except Exception as ex:
                    self.logger.warning("Failed to remove photo %s: %s", p, ex)
            self.logger.info("Tree %s deleted", self.current_tree_id)
            self.show_snack("Tree deleted", Colors.GREEN)
            self.show_list_view()



    def _save_tree(self, e, next_mode: bool = False):
        tree_code = self.add_tree_code.value.strip()
        kind = self.add_kind.value
        variety = (self.add_variety.value or "").strip()
        latitude = (self.add_latitude.value or "").strip()
        longitude = (self.add_longitude.value or "").strip()
        status = self.add_status.value
        notes = (self.add_notes.value or "").strip()

        if not tree_code:
            self.show_snack("Tree code is required", Colors.RED)
            return
        if not kind:
            self.show_snack("Kind is required", Colors.RED)
            return
        if not status:
            self.show_snack("Status is required", Colors.RED)
            return

        photo_path = None
        if self.captured_photo_path:
            try:
                ext = os.path.splitext(self.captured_photo_path)[1].lower()
                if ext not in (".jpg", ".jpeg", ".png"):
                    ext = ".jpg"
                ts = datetime.now().strftime('%y%m%d%H%M')
                dst = os.path.join(PHOTOS_DIR, f"{tree_code}_{ts}{ext}")
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copy2(self.captured_photo_path, dst)
                photo_path = dst
            except Exception as ex:
                self.logger.error("Failed to save photo: %s", ex, exc_info=True)
                self.show_snack("Error saving photo", Colors.RED)

        try:
            insert_tree(tree_code, kind, variety, latitude, longitude, status, notes, [photo_path] if photo_path else None)
            self.show_snack("Tree added! Ready for next." if next_mode else "Tree added successfully!", Colors.GREEN)
        except Exception as ex:
            self.logger.error("Failed to save tree: %s", ex, exc_info=True)
            self.show_snack("Error saving tree", Colors.RED)
            return

        if next_mode:
            try:
                parts = tree_code.replace("S", "").replace("Z", " ").replace("R", " ").replace("T", " ").split()
                if len(parts) == 4:
                    s, z, r, t = parts
                    next_t = int(t) + 1
                    next_code = f"S{s}Z{z}R{r}T{next_t}"
                    self.add_tree_code.value = next_code
            except Exception as ex:
                self.logger.warning("save_new_tree_next auto-increment: %s", ex)

            self.add_variety.value = variety
            self.add_status.value = None
            self.add_notes.value = ""
            self.captured_photo_path = None
            self.add_photo_img.visible = False
            self.add_photo_placeholder.visible = True
            self.add_take_photo_btn.visible = True
            self.add_tree_code.update()
            self.add_variety.update()
            self.add_status.update()
            self.add_notes.update()
            if self.add_photo_img.page:
                self.add_photo_img.update()
                self.add_photo_placeholder.update()
                self.add_take_photo_btn.update()
        else:
            self.reset_add_form()
            self.show_list_view()

    def save_new_tree(self, e):
        self._save_tree(e, next_mode=False)

    def save_new_tree_next(self, e):
        self._save_tree(e, next_mode=True)

    def save_edit_changes(self, e):
        if not self.current_tree_id:
            return
        tree_code = self.edit_tree_code.value.strip()
        kind = self.edit_kind.value
        variety = (self.edit_variety.value or "").strip()
        latitude = (self.edit_latitude.value or "").strip()
        longitude = (self.edit_longitude.value or "").strip()

        if not tree_code:
            self.show_snack("Tree code is required", Colors.RED)
            return
        if not kind:
            self.show_snack("Kind is required", Colors.RED)
            return

        try:
            update_tree(self.current_tree_id, tree_code, kind, variety, latitude, longitude)
            status = self.add_visit_status.value
            notes = (self.add_visit_notes.value or "").strip()
            if status:
                add_visit(self.current_tree_id, status, notes, None)
            self.show_snack("Tree updated successfully!", Colors.GREEN)
        except Exception as ex:
            self.logger.error("Failed to update tree %s: %s", self.current_tree_id, ex, exc_info=True)
            self.show_snack("Error updating tree", Colors.RED)
            return
        self.show_list_view()

    def show_snack(self, message: str, color: str):
        self.page.snack_bar = SnackBar(content=Text(message, color=Colors.WHITE, font_family="Comfortaa"), bgcolor=color, duration=2000)
        self.page.snack_bar.open = True
        self.page.update()

    def start_voice_recording(self, e=None):
        self.show_snack("Recording voice note...", Colors.BLUE)

    def get_gps(self, lat_field: TextField, lon_field: TextField):
        def callback(lat, lon):
            lat_field.value = lat
            lon_field.value = lon
            lat_field.update()
            lon_field.update()
            # Update location header with lat/lon
            if hasattr(self, 'location_header'):
                self.update_tree_code()
            self.show_snack("GPS coordinates captured", Colors.GREEN)

        get_gps_coordinates(callback)
        self.show_snack("Getting GPS location...", Colors.BLUE)


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
