import os
import sys
import asyncio
import threading
import flet as ft
from flet import (
    Page, TextField, Dropdown, DropdownOption, IconButton, Icon,
    Text, Colors, Container, Row, Column, ListView, Card, ListTile,
    AlertDialog, TextButton, Button, OutlinedButton, FloatingActionButton,
    AppBar, NavigationBar, NavigationBarDestination, SnackBar, Stack, Image, GridView,
    KeyboardType, InputBorder, TextStyle,
    BorderSide, Border, Divider, VerticalDivider, Padding, Margin,
    alignment, border_radius, Animation, AnimationCurve, ControlEvent,
    FontWeight, CrossAxisAlignment, MainAxisAlignment,
    ScrollMode, TextAlign, BorderRadius, ControlState,
    ControlStateValue, VisualDensity, ListTileTitleAlignment,
    Tooltip, ProgressBar, Switch, Slider, Checkbox,
    Chip, RadioGroup, Radio, Tab,
    Tabs, SegmentedButton, Segment, ButtonStyle,
    Control, Ref, Markdown,
    Offset, Rotate, Scale,
    Transform, BoxShadow, Gradient, LinearGradient, RadialGradient,
    SweepGradient, Alignment, BlurTileMode, ImageRepeat,
    FilterQuality, Paint, PaintingStyle, StrokeCap, StrokeJoin,
    GestureDetector, DragStartEvent, DragUpdateEvent, DragEndEvent,
    HoverEvent, TapEvent, ScaleStartEvent, ScaleUpdateEvent, ScaleEndEvent,
    Badge, PopupMenuButton, PopupMenuItem, BottomSheet, CupertinoAlertDialog,
    CupertinoDialogAction, NavigationRail, NavigationRailDestination,
    ExpansionTile, DataTable, DataColumn, DataRow, DataCell,
    SearchBar, ProgressRing, DropdownOption,
)
from flet import FilePicker
Icons = ft.Icons
from app.config import TREE_KINDS, TREE_STATUSES, STATUS_LOOKUP
from app.database import (
    init_db, get_all_trees, get_trees_page, search_trees, count_trees,
    insert_tree, add_visit, update_tree, update_tree_status,
    delete_tree, get_tree, copy_photo_to_storage, get_gps_coordinates,
)

TREE_STATUSES = [
    ("Healthy", "#2E7D32"),
    ("Needs Water", "#1565C0"),
    ("Needs Fertilizer", "#E65100"),
    ("Diseased", "#C62828"),
    ("Pest Infestation", "#AD1457"),
    ("Pruned", "#6A1B9A"),
    ("Damaged", "#BF360C"),
    ("Dead", "#455A64"),
    ("Flowering", "#C2185B"),
    ("Fruiting", "#F57F17"),
    ("New Planting", "#558B2F"),
]

STATUS_COLOR_MAP = {label: color for label, color in TREE_STATUSES}
STATUS_DROPDOWN_ITEMS = [DropdownOption(text=label, key=label) for label, _ in TREE_STATUSES]
KIND_DROPDOWN_ITEMS = [DropdownOption(text=k, key=k) for k in TREE_KINDS]


def copy_photo_to_storage(src_path: str) -> str:
    import uuid
    import shutil
    from datetime import datetime
    PHOTOS_DIR = os.path.join(os.path.dirname(__file__), "data", "photos")
    os.makedirs(PHOTOS_DIR, exist_ok=True)
    ext = os.path.splitext(src_path)[1].lower()
    if ext not in (".jpg", ".jpeg", ".png"):
        ext = ".jpg"
    filename = f"{uuid.uuid4().hex}_{datetime.now().strftime('%y%m%d%H%M')}{ext}"
    dst_path = os.path.join(PHOTOS_DIR, filename)
    try:
        shutil.copy2(src_path, dst_path)
    except Exception:
        pass
    return dst_path


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
        self.search_query = ""
        self.filter_kind = None
        self.filter_status = None
        self.current_tree_id = None
        self.current_tree_data = None
        self.photos = []
        self.new_photos = []
        self.file_picker = FilePicker()
        self.file_picker.on_result = self.on_file_picker_result
        self.page.overlay.append(self.file_picker)
        self.page.update()

        self.db = init_db()

        self.setup_ui()
        self.load_font()
        self.load_trees()

    def load_font(self):
        font_path = os.path.join(os.path.dirname(__file__), "assets", "fonts", "Comfortaa-Regular.woff2")
        if os.path.exists(font_path):
            self.page.fonts = {"Comfortaa": font_path}

    def setup_ui(self):
        self.setup_app_bar()
        self.setup_navigation()
        self.setup_list_view()
        self.setup_add_form()
        self.setup_edit_form()
        self.setup_detail_view()

        self.main_container = Stack([
            self.list_container,
            self.add_container,
            self.edit_container,
            self.detail_container,
        ], expand=True)
        self.page.add(self.main_container)
        self.show_list_view()

    def update_tree_code(self):
        try:
            s = self.add_sector.value.strip() if self.add_sector.value else "1"
            z = self.add_zone.value.strip() if self.add_zone.value else "1"
            r = self.add_row.value.strip() if self.add_row.value else "1"
            t = self.add_tree_number.value.strip() if self.add_tree_number.value else "1"
            code = f"S{s}Z{z}R{r}T{t}"
            self.add_tree_code.value = code
        except Exception:
            pass

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

        self.app_bar = AppBar(
            leading=IconButton(icon=Icons.MENU, icon_color=Colors.WHITE, on_click=lambda _: self.show_list_view(), tooltip="Menu"),
            title=Text("Scan Tree", font_family="Comfortaa", weight=FontWeight.BOLD, color=Colors.WHITE),
            bgcolor=Colors.GREEN_700,
            actions=[
                self.search_button,
                self.search_input_container,
                IconButton(icon=Icons.REFRESH, icon_color=Colors.WHITE, on_click=lambda _: self.load_trees(), tooltip="Refresh"),
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
            Text("Page 1", size=14, font_family="Comfortaa"),
            IconButton(icon=Icons.CHEVRON_RIGHT, on_click=lambda _: self.next_page(), disabled=True),
        ], alignment=MainAxisAlignment.CENTER)

        self.list_container = Container(
            content=Column([
                self.loading_indicator,
                self.tree_list,
                self.empty_state,
                self.pagination_controls,
            ], expand=True),
            visible=True,
        )

    def setup_add_form(self):
        self.add_sector = TextField(
            label="Sector",
            border=InputBorder.OUTLINE,
            text_style=TextStyle(font_family="Comfortaa"),
            on_change=lambda e: self.update_tree_code(),
        )
        self.add_zone = TextField(
            label="Zone",
            border=InputBorder.OUTLINE,
            text_style=TextStyle(font_family="Comfortaa"),
            on_change=lambda e: self.update_tree_code(),
        )
        self.add_row = TextField(
            label="Row",
            border=InputBorder.OUTLINE,
            text_style=TextStyle(font_family="Comfortaa"),
            on_change=lambda e: self.update_tree_code(),
        )
        self.add_tree_number = TextField(
            label="Tree Number",
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
        self.add_gps_btn = Row([OutlinedButton(
            content=Text("Get GPS"),
            icon=Icons.MY_LOCATION,
            on_click=lambda _: self.get_gps(self.add_latitude, self.add_longitude),
            style=ButtonStyle(color=Colors.BLUE_700),
        ), IconButton(icon=Icons.MIC, on_click=lambda _: self.start_voice_recording(), style=ButtonStyle(color=Colors.GREEN_700))], alignment=MainAxisAlignment.START)

        self.location_card = Card(
            content=Container(
                content=Column([
                    Row([
                        Text("Location", size=16, weight=FontWeight.BOLD, font_family="Comfortaa", color=Colors.GREEN_700),
                        self.add_gps_btn,
                    ], alignment=MainAxisAlignment.SPACE_BETWEEN),
                    Divider(height=12),
                    Row([
                        Container(content=self.add_sector, expand=True),
                        Container(content=self.add_zone, expand=True),
                        Container(content=self.add_row, expand=True),
                        Container(content=self.add_tree_number, expand=True),
                    ], spacing=8),
                    Row([
                        Text("Code: ", font_family="Comfortaa", size=12, color=Colors.GREEN_700),
                        Text("", font_family="Comfortaa", size=12, color=Colors.GREEN_700, key="add_code_display"),
                    ], alignment=MainAxisAlignment.START),
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
        self.add_variety = TextField(
            label="Variety",
            hint_text="e.g., Red Oak",
            border=InputBorder.OUTLINE,
            text_style=TextStyle(font_family="Comfortaa"),
        )
        self.add_status = Dropdown(
            label="Status *",
            options=STATUS_DROPDOWN_ITEMS,
            border=InputBorder.OUTLINE,
            text_style=TextStyle(font_family="Comfortaa"),
        )
        self.add_notes = TextField(
            label="Notes",
            border=InputBorder.OUTLINE,
            multiline=True,
            min_lines=2,
            max_lines=4,
            text_style=TextStyle(font_family="Comfortaa"),
        )

        self.add_photo_btn = Row([
            OutlinedButton(
                content=Row([Icon(Icons.CAMERA_ALT), Text("Camera")], spacing=8, alignment=MainAxisAlignment.CENTER),
                icon=Icons.CAMERA_ALT,
                on_click=lambda _: self.page.run_task(self.take_photo, "add"),
                style=ButtonStyle(color=Colors.GREEN_700),
            ),
            OutlinedButton(
                content=Row([Icon(Icons.PHOTO_LIBRARY), Text("Gallery")], spacing=8, alignment=MainAxisAlignment.CENTER),
                icon=Icons.PHOTO_LIBRARY,
                on_click=lambda _: self.page.run_task(self.pick_photos, "add"),
                style=ButtonStyle(color=Colors.GREEN_700),
            ),
        ], spacing=10)
        self.add_photos_grid = GridView(expand=False, max_extent=100, child_aspect_ratio=1, spacing=8, run_spacing=8)

        # Location Card
        self.location_card = Card(
            content=Container(
                content=Column([
                    Row([
                        Text("Tree Details", size=16, weight=FontWeight.BOLD, font_family="Comfortaa", color=Colors.GREEN_700),
                    ], alignment=MainAxisAlignment.START),
                    Divider(height=12),
                    Row([self.add_kind, self.add_variety], spacing=10),
                    self.add_status,
                    self.add_notes,
                ], spacing=12),
                padding=Padding(16, 12, 16, 12),
            ),
            elevation=2,
            margin=Margin(0, 0, 0, 12),
        )

        # Photos Card
        self.photos_card = Card(
            content=Container(
                content=Column([
                    Row([
                        Text("Photos", size=16, weight=FontWeight.BOLD, font_family="Comfortaa", color=Colors.GREEN_700),
                    ], alignment=MainAxisAlignment.START),
                    Divider(height=12),
                    self.add_photo_btn,
                    self.add_photos_grid,
                ], spacing=12),
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
                    Row([self.add_kind, self.add_variety], spacing=10),
                    self.add_status,
                    self.add_notes,
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
                        Text("Add New Tree", size=24, weight=FontWeight.BOLD, font_family="Comfortaa", color=Colors.GREEN_700),
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
        )
        self.edit_kind = Dropdown(
            label="Kind *",
            options=KIND_DROPDOWN_ITEMS,
            border=InputBorder.OUTLINE,
            text_style=TextStyle(font_family="Comfortaa"),
        )
        self.edit_variety = TextField(
            label="Variety",
            border=InputBorder.OUTLINE,
            text_style=TextStyle(font_family="Comfortaa"),
        )
        self.edit_latitude = TextField(
            label="Latitude",
            border=InputBorder.OUTLINE,
            keyboard_type=KeyboardType.NUMBER,
            text_style=TextStyle(font_family="Comfortaa"),
        )
        self.edit_longitude = TextField(
            label="Longitude",
            border=InputBorder.OUTLINE,
            keyboard_type=KeyboardType.NUMBER,
            text_style=TextStyle(font_family="Comfortaa"),
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
            on_click=lambda _: self.page.run_task(self.pick_photos, "visit"),
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
                        Divider(height=20),
                        self.edit_tree_code,
                        Row([self.edit_kind, self.edit_variety], spacing=10),
                        Row([self.edit_latitude, self.edit_longitude], spacing=10),
                        Divider(height=10),
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
        self.detail_status_chip = Chip(
            label=Text("", font_family="Comfortaa"),
            bgcolor=Colors.GREEN_100,
            color=Colors.GREEN_700,
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

        self.detail_container = Container(
            content=ListView([
                Container(
                    content=Column([
                        Row([
                            IconButton(icon=Icons.ARROW_BACK, on_click=lambda _: self.show_list_view()),
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
                                    Row([self.detail_status_chip], alignment=MainAxisAlignment.START),
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
                        Row([self.detail_edit_btn, self.detail_delete_btn], spacing=10, alignment=MainAxisAlignment.CENTER),
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
            self.show_search_view()
        self.nav_bar.selected_index = idx
        self.nav_bar.update()

    def show_list_view(self):
        self.list_container.visible = True
        self.add_container.visible = False
        self.edit_container.visible = False
        self.detail_container.visible = False
        self.nav_bar.selected_index = 0
        self.nav_bar.update()
        self.main_container.update()
        self.load_trees()

    def show_add_form(self):
        self.reset_add_form()
        self.list_container.visible = False
        self.add_container.visible = True
        self.edit_container.visible = False
        self.detail_container.visible = False
        self.nav_bar.selected_index = 1
        self.nav_bar.update()
        self.main_container.update()

    def show_search_view(self):
        self.list_container.visible = True
        self.add_container.visible = False
        self.edit_container.visible = False
        self.detail_container.visible = False
        self.nav_bar.selected_index = 2
        self.nav_bar.update()
        self.main_container.update()
        import asyncio
        asyncio.create_task(self.search_field.focus())
        if self.search_query:
            self.load_trees()
        else:
            self.current_page = 0
            self.load_trees()

    def trigger_search(self, e=None):
        if hasattr(self, 'search_field'):
            import asyncio
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
            self.add_variety.value = ""
            self.add_latitude.value = ""
            self.add_longitude.value = ""
            self.add_status.value = None
            self.add_notes.value = ""
            self.photos = []
            self.add_photos_grid.controls.clear()
            
            # Note: Controls will be updated when they are added to the page
            # to avoid "Control must be added to the page first" error

    def load_trees(self):
        self.loading_indicator.visible = True
        self.loading_indicator.update()
        self.tree_list.controls.clear()

        if self.search_query or self.filter_kind or self.filter_status:
            trees = search_trees(self.search_query, self.filter_kind, self.filter_status)
        else:
            trees = get_all_trees()

        if not trees:
            self.tree_list.visible = False
            self.empty_state.visible = True
            self.pagination_controls.visible = False
        else:
            self.tree_list.visible = True
            self.empty_state.visible = False
            self.pagination_controls.visible = True
            for tree in trees:
                self.tree_list.controls.append(self.create_tree_card(tree))

        self.update_pagination(len(trees))
        self.loading_indicator.visible = False
        self.loading_indicator.update()
        self.tree_list.update()
        self.empty_state.update()
        self.pagination_controls.update()

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

        status_color = STATUS_COLOR_MAP.get(last_status, Colors.GREY)
        status_chip = Chip(
            label=Text(last_status, size=11, weight=FontWeight.W_500, font_family="Comfortaa", color=Colors.WHITE),
            bgcolor=status_color,
            padding=Padding(8, 0, 8, 0),
        )

        leading = Container(
            width=60, height=60,
            border_radius=BorderRadius(8),
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
            content=Image(src=last_photo, fit=ImageFit.COVER) if last_photo else Icon(Icons.PARK, size=30, color=Colors.GREEN_700),
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
            Row([status_chip], spacing=8),
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
        def on_status_change(status):
            update_tree_status(tree["id"], status)
            self.show_snack(f"Status changed to {status}", Colors.GREEN)
            self.load_trees()

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

        items = [
            PopupMenuItem(text="Edit Tree", icon=Icons.EDIT, on_click=lambda _: on_edit()),
            PopupMenuItem(text="Quick Status Change", icon=Icons.FLAG, on_click=lambda _: self.show_status_picker(tree)),
            PopupMenuItem(text="View History", icon=Icons.HISTORY, on_click=lambda _: on_history()),
            PopupMenuItem(text="Delete Tree", icon=Icons.DELETE, on_click=lambda _: on_delete()),
        ]

        menu = PopupMenuButton(items=items, icon=Icons.MORE_VERT)
        self.page.open(menu)

    def show_status_picker(self, tree: dict):
        def on_status_click(status):
            update_tree_status(tree["id"], status)
            self.show_snack(f"Status updated to {status}", Colors.GREEN)
            self.load_trees()
            bs.open = False
            self.page.update()

        items = []
        for status, color in TREE_STATUSES:
            items.append(
                PopupMenuItem(
                    content=Row([
                        Container(width=12, height=12, bgcolor=color, border_radius=BorderRadius(6)),
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
        self.page.open(bs)

    def show_history_bottom_sheet(self, tree_id: int):
        tree = get_tree(tree_id)
        if not tree:
            return

        visits = tree.get("visits", [])
        items = []
        for visit in reversed(visits):
            status = visit.get("status", "")
            color = STATUS_COLOR_MAP.get(status, Colors.GREY)
            photos = visit.get("photos", [])
            photo_controls = []
            for p in photos:
                photo_controls.append(
                    Container(
                        content=Image(src=p, fit=ImageFit.COVER, width=50, height=50, border_radius=BorderRadius(6)),
                        width=50, height=50, border_radius=BorderRadius(6), clip_behavior=ft.ClipBehavior.HARD_EDGE,
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
                                    bgcolor=color, padding=Padding(6, 2, 6, 2), border_radius=BorderRadius(10),
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
        self.page.open(bs)

    def show_tree_detail(self, tree: dict):
        self.current_tree_id = tree["id"]
        self.current_tree_data = tree
        self.populate_detail_view(tree)
        self.list_container.visible = False
        self.add_container.visible = False
        self.edit_container.visible = False
        self.detail_container.visible = True
        self.nav_bar.selected_index = 0
        self.nav_bar.update()
        self.main_container.update()

    def populate_detail_view(self, tree: dict):
        self.detail_tree_code.value = f"Code: {tree.get('tree_code', 'N/A')}"
        self.detail_kind.value = f"Kind: {tree.get('kind', 'N/A')}"
        self.detail_variety.value = f"Variety: {tree.get('variety', 'N/A')}"
        lat = tree.get('latitude', '')
        lon = tree.get('longitude', '')
        self.detail_location.value = f"Location: {lat}, {lon}" if lat or lon else "Location: Not set"
        last_status = tree.get("last_status", "No visits")
        status_color = STATUS_COLOR_MAP.get(last_status, Colors.GREY)
        self.detail_status_chip.label.value = last_status
        self.detail_status_chip.bgcolor = status_color + "20"
        self.detail_status_chip.color = status_color
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
                    content=Image(src=photo, fit=ImageFit.COVER, border_radius=BorderRadius(8)),
                    width=120, height=120, border_radius=BorderRadius(8), clip_behavior=ft.ClipBehavior.HARD_EDGE,
                )
            )

        self.detail_visits_list.controls.clear()
        for visit in reversed(visits):
            status = visit.get("status", "")
            status_color = STATUS_COLOR_MAP.get(status, Colors.GREY)
            photos = visit.get("photos", [])
            photo_chips = []
            for p in photos:
                photo_chips.append(
                    Container(
                        content=Image(src=p, fit=ImageFit.COVER, width=50, height=50, border_radius=BorderRadius(6)),
                        width=50, height=50, border_radius=BorderRadius(6), clip_behavior=ft.ClipBehavior.HARD_EDGE,
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
                                    bgcolor=status_color, padding=Padding(6, 2, 6, 2), border_radius=BorderRadius(10),
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
        self.detail_status_chip.update()
        self.detail_notes.update()
        self.detail_photos_grid.update()
        self.detail_visits_list.update()

    def edit_current_tree(self):
        self.current_tree_id = self.current_tree_data["id"]
        self.populate_edit_form(self.current_tree_data)
        self.detail_container.visible = False
        self.edit_container.visible = True
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
            status_color = STATUS_COLOR_MAP.get(status, Colors.GREY)
            photos = visit.get("photos", [])
            photo_controls = []
            for p in photos:
                photo_controls.append(
                    Container(
                        content=Image(src=p, fit=ImageFit.COVER, width=40, height=40, border_radius=BorderRadius(6)),
                        width=40, height=40, border_radius=BorderRadius(6), clip_behavior=ft.ClipBehavior.HARD_EDGE,
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
                                    bgcolor=status_color, padding=Padding(6, 2, 6, 2), border_radius=BorderRadius(10),
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
        self.page.open(dlg)

    def delete_current_tree(self):
        if self.current_tree_id:
            photos = delete_tree(self.current_tree_id)
            for p in photos:
                try:
                    os.remove(p)
                except Exception:
                    pass
            self.show_snack("Tree deleted", Colors.GREEN)
            self.show_list_view()

    async def pick_photos(self, mode: str):
        files = await self.file_picker.pick_files(allow_multiple=True, allowed_extensions=["jpg", "jpeg", "png"])
        if files:
            for f in files:
                path = copy_photo_to_storage(f.path)
                if mode == "add":
                    self.photos.append(path)
                    self.add_photo_to_grid(path, "add")
                elif mode == "visit":
                    self.new_photos.append(path)
                    self.add_photo_to_grid(path, "visit")
        self.page.update()

    def on_file_picker_result(self, e):
        if e.files:
            for f in e.files:
                path = copy_photo_to_storage(f.path)
                # Determine mode based on current view
                if self.add_container.visible:
                    self.photos.append(path)
                    self.add_photo_to_grid(path, "add")
                else:
                    self.new_photos.append(path)
                    self.add_photo_to_grid(path, "visit")
            self.page.update()

    async def take_photo(self, mode: str):
        await self.file_picker.pick_files(
            allow_multiple=False,
            allowed_extensions=["jpg", "jpeg", "png"],
            dialog_title="Take Photo",
            file_type=ft.FilePickerFileType.IMAGE,
        )

    def add_photo_to_grid(self, path: str, mode: str):
        grid = self.add_photos_grid if mode == "add" else self.add_visit_photos_grid
        idx = len(grid.controls)
        container = Container(
            content=Stack([
                Image(src=path, fit=ImageFit.COVER, width=100, height=100, border_radius=BorderRadius(8)),
                Container(
                    content=IconButton(icon=Icons.CLOSE, icon_size=16, icon_color=Colors.WHITE, on_click=lambda _, i=idx, m=mode: self.remove_photo(i, m)),
                    alignment=alignment.Alignment(1, -1),
                    bgcolor=Colors.BLACK54,
                    border_radius=BorderRadius(0, 8, 0, 0),
                ),
            ]),
            width=100, height=100, border_radius=BorderRadius(8), clip_behavior=ft.ClipBehavior.HARD_EDGE,
        )
        grid.controls.append(container)
        grid.update()

    def save_new_tree(self, e):
        tree_code = self.add_tree_code.value.strip()
        kind = self.add_kind.value
        variety = self.add_variety.value.strip()
        latitude = self.add_latitude.value.strip()
        longitude = self.add_longitude.value.strip()
        status = self.add_status.value
        notes = self.add_notes.value.strip()

        if not tree_code:
            self.show_snack("Tree code is required", Colors.RED)
            return
        if not kind:
            self.show_snack("Kind is required", Colors.RED)
            return
        if not status:
            self.show_snack("Status is required", Colors.RED)
            return

        insert_tree(tree_code, kind, variety, latitude, longitude, status, notes, self.photos if self.photos else None)
        self.show_snack("Tree added successfully!", Colors.GREEN)
        self.reset_add_form()
        self.show_list_view()

    def save_new_tree_next(self, e):
        tree_code = self.add_tree_code.value.strip()
        kind = self.add_kind.value
        variety = self.add_variety.value.strip()
        latitude = self.add_latitude.value.strip()
        longitude = self.add_longitude.value.strip()
        status = self.add_status.value
        notes = self.add_notes.value.strip()

        if not tree_code:
            self.show_snack("Tree code is required", Colors.RED)
            return
        if not kind:
            self.show_snack("Kind is required", Colors.RED)
            return
        if not status:
            self.show_snack("Status is required", Colors.RED)
            return

        insert_tree(tree_code, kind, variety, latitude, longitude, status, notes, self.photos if self.photos else None)
        self.show_snack("Tree added! Ready for next.", Colors.GREEN)

        try:
            parts = tree_code.replace("S", "").replace("Z", " ").replace("R", " ").replace("T", " ").split()
            if len(parts) == 4:
                s, z, r, t = parts
                next_t = int(t) + 1
                next_code = f"S{s}Z{z}R{r}T{next_t}"
                self.add_tree_code.value = next_code
        except Exception:
            pass

        self.add_variety.value = variety
        self.add_status.value = None
        self.add_notes.value = ""
        self.photos = []
        self.add_photos_grid.controls.clear()
        self.add_tree_code.update()
        self.add_variety.update()
        self.add_status.update()
        self.add_notes.update()
        self.add_photos_grid.update()

    def save_edit_changes(self, e):
        if not self.current_tree_id:
            return
        tree_code = self.edit_tree_code.value.strip()
        kind = self.edit_kind.value
        variety = self.edit_variety.value.strip()
        latitude = self.edit_latitude.value.strip()
        longitude = self.edit_longitude.value.strip()

        if not tree_code:
            self.show_snack("Tree code is required", Colors.RED)
            return
        if not kind:
            self.show_snack("Kind is required", Colors.RED)
            return

        update_tree(self.current_tree_id, tree_code, kind, variety, latitude, longitude)

        status = self.add_visit_status.value
        notes = self.add_visit_notes.value.strip()
        if status:
            add_visit(self.current_tree_id, status, notes, self.new_photos if self.new_photos else None)

        self.show_snack("Tree updated successfully!", Colors.GREEN)
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
            self.show_snack("GPS coordinates captured", Colors.GREEN)

        get_gps_coordinates(callback)
        self.show_snack("Getting GPS location...", Colors.BLUE)


def main(page: Page):
    app = TreesApp(page)


if __name__ == "__main__":
    ft.run(main, assets_dir="assets")