import os
import re
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
    BorderRadius, ButtonStyle,
    PopupMenuItem, BottomSheet, ProgressRing,
    FilledButton, BoxFit, BottomAppBar, SafeArea,
)
from flet_camera import Camera
from flet_charts import BarChart, BarChartGroup, BarChartRod, BarChartTooltip, ChartAxis, ChartAxisLabel
from flet_geolocator import Geolocator, GeolocatorConfiguration, GeolocatorPositionAccuracy
from app.config import TREE_KINDS, TREE_VARIETIES, STATUS_LOOKUP
import version
from app.database import (
    init_db, get_all_trees, get_trees_slice, search_trees, count_trees,
    insert_tree, add_visit, update_tree, update_tree_status,
    delete_tree, get_tree, copy_photo_to_storage,
    invalidate_cache, PHOTOS_DIR,
)
from app.logger import get_logger, read_logs

STATUS_DROPDOWN_ITEMS = [DropdownOption(text=label, key=label) for label in STATUS_LOOKUP]
KIND_DROPDOWN_ITEMS = [DropdownOption(text=k, key=k) for k in TREE_KINDS]

TRANSLATIONS = {
    "en": {
        "app_title": "Farm Tree Manager",
        "nav_trees": "Trees",
        "nav_add": "Add",
        "nav_settings": "Settings",
        "search_hint": "Search trees... (use | for AND)",
        "search": "Search",
        "refresh": "Refresh",
        "statistics": "Statistics",
        "add_new_tree": "Add New Tree",
        "tree_details": "Tree Details",
        "photo": "Photo",
        "location": "Location",
        "take_photo": "Take Photo",
        "no_photo": "No photo captured",
        "sector": "Sector",
        "zone": "Zone",
        "row": "Row",
        "tree": "Tree",
        "tree_code": "Tree Code",
        "tree_code_hint": "Auto-generated from Sector/Zone/Row/Tree#",
        "kind": "Kind",
        "kind_required": "Kind *",
        "variety": "Variety",
        "variety_hint": "Select variety",
        "status": "Status",
        "status_required": "Status *",
        "notes": "Notes",
        "save_tree": "Save Tree",
        "save_next": "Save & Next",
        "edit_tree": "Edit Tree",
        "visit_history": "Visit History",
        "add_new_visit": "Add New Visit",
        "visit_status": "Visit Status *",
        "visit_notes": "Visit Notes",
        "visit_photos": "Visit Photos",
        "add_photos": "Add Photos",
        "save_changes": "Save Changes",
        "delete_tree": "Delete Tree",
        "edit": "Edit",
        "new_visit": "New Visit",
        "delete": "Delete",
        "cancel": "Cancel",
        "close": "Close",
        "yes": "Yes",
        "no": "No",
        "settings": "Settings",
        "help": "Help",
        "help_subtitle": "Learn how to use the app",
        "about": "About",
        "about_subtitle": "Farm Tree Manager v",
        "view_logs": "View Logs",
        "view_logs_subtitle": "Check app logs for troubleshooting",
        "language": "Language",
        "language_subtitle": "Change app language",
        "total_trees": "Total Trees: ",
        "searched_trees": "Searched Trees: ",
        "heatmap_title": "Tree Density Heatmap",
        "barchart_title": "Trees per Sector",
        "no_tree_available": "No Tree Available",
        "no_trees_found": "No trees found",
        "tap_to_add": "Tap + to add your first tree",
        "loading": "Loading trees...",
        "loading_sub": "Please wait while we gather your data",
        "page": "Page ",
        "back": "Back",
        "help_title": "Help",
        "help_text_1": "Tap + to add a new tree.",
        "help_text_2": "Tap a tree card to view its details.",
        "help_text_3": "Long-press a tree for quick actions.",
        "help_text_4": "Use the search bar to find trees.",
        "help_text_5": "Track visits and update tree status.",
        "help_text_6": "Photos and notes can be added per visit.",
        "about_title": "About",
        "about_desc": "A farm tree management app for tracking tree health, visits, and maintenance.",
        "logs_title": "Logs",
        "confirm_delete": "Are you sure you want to delete this tree and all its visits?",
        "delete_title": "Delete Tree",
        "actions": "Actions",
        "edit_action": "Edit Tree",
        "quick_status": "Quick Status Change",
        "view_history": "View History",
        "delete_action": "Delete Tree",
        "change_status": "Change Status",
        "gps_getting": "Getting GPS location...",
        "gps_captured": "GPS coordinates captured",
        "gps_unavailable": "GPS location unavailable",
        "camera_not_available": "Camera not available on this platform",
        "photo_captured": "Photo captured!",
        "camera_error": "Camera error: ",
        "tree_added": "Tree added successfully!",
        "tree_added_next": "Tree added! Ready for next.",
        "tree_updated": "Tree updated successfully!",
        "tree_deleted": "Tree deleted",
        "error_saving": "Error saving tree",
        "error_updating": "Error updating tree",
        "error_deleting": "Error deleting tree",
        "error_loading": "Error loading trees",
        "error_stats": "Error loading statistics",
        "tree_code_required": "Tree code is required",
        "kind_required_msg": "Kind is required",
        "status_required_msg": "Status is required",
        "sector_positive": "Sector must be a positive number",
        "zone_positive": "Zone must be a positive number",
        "row_positive": "Row must be a positive number",
        "tree_positive": "Tree must be a positive number",
        "error_saving_photo": "Error saving photo",
    },
    "ar": {
        "app_title": "مدير أشجار المزرعة",
        "nav_trees": "الأشجار",
        "nav_add": "إضافة",
        "nav_settings": "الإعدادات",
        "search_hint": "بحث في الأشجار... (استخدم | لـ و)",
        "search": "بحث",
        "refresh": "تحديث",
        "statistics": "الإحصائيات",
        "add_new_tree": "إضافة شجرة جديدة",
        "tree_details": "تفاصيل الشجرة",
        "photo": "الصورة",
        "location": "الموقع",
        "take_photo": "التقاط صورة",
        "no_photo": "لم يتم التقاط صورة",
        "sector": "القطاع",
        "zone": "المنطقة",
        "row": "الصف",
        "tree": "الشجرة",
        "tree_code": "رمز الشجرة",
        "tree_code_hint": "يُولّد تلقائياً من القطاع/المنطقة/الصف/رقم الشجرة",
        "kind": "النوع",
        "kind_required": "النوع *",
        "variety": "الصنف",
        "variety_hint": "اختر الصنف",
        "status": "الحالة",
        "status_required": "الحالة *",
        "notes": "ملاحظات",
        "save_tree": "حفظ الشجرة",
        "save_next": "حفظ والتالي",
        "edit_tree": "تعديل الشجرة",
        "visit_history": "سجل الزيارات",
        "add_new_visit": "إضافة زيارة جديدة",
        "visit_status": "حالة الزيارة *",
        "visit_notes": "ملاحظات الزيارة",
        "visit_photos": "صور الزيارة",
        "add_photos": "إضافة صور",
        "save_changes": "حفظ التغييرات",
        "delete_tree": "حذف الشجرة",
        "edit": "تعديل",
        "new_visit": "زيارة جديدة",
        "delete": "حذف",
        "cancel": "إلغاء",
        "close": "إغلاق",
        "yes": "نعم",
        "no": "لا",
        "settings": "الإعدادات",
        "help": "المساعدة",
        "help_subtitle": "تعرف على كيفية استخدام التطبيق",
        "about": "حول",
        "about_subtitle": "مدير أشجار المزرعة v",
        "view_logs": "عرض السجلات",
        "view_logs_subtitle": "تحقق من سجلات التطبيق لحل المشكلات",
        "language": "اللغة",
        "language_subtitle": "تغيير لغة التطبيق",
        "total_trees": "إجمالي الأشجار: ",
        "searched_trees": "الأشجار المُبحث عنها: ",
        "heatmap_title": "خريطة كثافة الأشجار",
        "barchart_title": "الأشجار حسب القطاع",
        "no_tree_available": "لا توجد أشجار متاحة",
        "no_trees_found": "لم يتم العثور على أشجار",
        "tap_to_add": "اضغط + لإضافة أول شجرة",
        "loading": "جاري تحميل الأشجار...",
        "loading_sub": "يرجى الانتظار حتى نجمع بياناتك",
        "page": "صفحة ",
        "back": "رجوع",
        "help_title": "المساعدة",
        "help_text_1": "اضغط + لإضافة شجرة جديدة.",
        "help_text_2": "اضغط على بطاقة الشجرة لعرض تفاصيلها.",
        "help_text_3": "اضغط مطولاً على شجرة للإجراءات السريعة.",
        "help_text_4": "استخدم شريط البحث للعثور على الأشجار.",
        "help_text_5": "تتبع الزيارات وحدّث حالة الشجرة.",
        "help_text_6": "يمكن إضافة صور وملاحظات لكل زيارة.",
        "about_title": "حول",
        "about_desc": "تطبيق إدارة أشجار المزرعة لتتبع صحة الأشجار والزيارات والصيانة.",
        "logs_title": "السجلات",
        "confirm_delete": "هل أنت متأكد أنك تريد حذف هذه الشجرة وجميع زياراتها؟",
        "delete_title": "حذف الشجرة",
        "actions": "الإجراءات",
        "edit_action": "تعديل الشجرة",
        "quick_status": "تغيير سريع للحالة",
        "view_history": "عرض السجل",
        "delete_action": "حذف الشجرة",
        "change_status": "تغيير الحالة",
        "gps_getting": "جاري الحصول على الموقع...",
        "gps_captured": "تم التقاط إحداثيات GPS",
        "gps_unavailable": "موقع GPS غير متاح",
        "camera_not_available": "الكاميرا غير متاحة على هذه المنصة",
        "photo_captured": "تم التقاط الصورة!",
        "camera_error": "خطأ في الكاميرا: ",
        "tree_added": "تمت إضافة الشجرة بنجاح!",
        "tree_added_next": "تمت الإضافة! جاهز للتالي.",
        "tree_updated": "تم تحديث الشجرة بنجاح!",
        "tree_deleted": "تم حذف الشجرة",
        "error_saving": "خطأ في حفظ الشجرة",
        "error_updating": "خطأ في تحديث الشجرة",
        "error_deleting": "خطأ في حذف الشجرة",
        "error_loading": "خطأ في تحميل الأشجار",
        "error_stats": "خطأ في تحميل الإحصائيات",
        "tree_code_required": "رمز الشجرة مطلوب",
        "kind_required_msg": "النوع مطلوب",
        "status_required_msg": "الحالة مطلوبة",
        "sector_positive": "يجب أن يكون القطاع رقماً موجباً",
        "zone_positive": "يجب أن تكون المنطقة رقماً موجباً",
        "row_positive": "يجب أن يكون الصف رقماً موجباً",
        "tree_positive": "يجب أن يكون رقم الشجرة رقماً موجباً",
        "error_saving_photo": "خطأ في حفظ الصورة",
    },
}


def _build_visit_card(visit: dict, photo_size: int = 50) -> Card:
    status = visit.get("status", "")
    color = STATUS_LOOKUP.get(status, Colors.GREY)
    photos = visit.get("photos", [])
    photo_chips = [
        Container(
            content=Image(src=p, fit=BoxFit.COVER, width=photo_size, height=photo_size, border_radius=BorderRadius(6, 6, 6, 6)),
            width=photo_size, height=photo_size, border_radius=BorderRadius(6, 6, 6, 6), clip_behavior=ft.ClipBehavior.HARD_EDGE,
        ) for p in photos
    ]
    return Card(
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
                Row(photo_chips, spacing=4) if photo_chips else Container(),
            ], spacing=4, tight=True),
            padding=Padding(12, 10, 12, 10),
        ),
        elevation=1,
    )


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
        self.new_photos = []
        self.captured_photo_path = None
        self.captured_gps_lat = ""
        self.captured_gps_lon = ""
        self.lang = "en"

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

    def _apply_language(self):
        self.page.rtl = self.lang == "ar"
        font = self._font()
        self.page.update()
        self._rebuild_all_views()

    def _rebuild_all_views(self):
        self.setup_app_bar()
        self.setup_navigation()
        self.setup_list_view()
        self.setup_add_form()
        self.setup_edit_form()
        self.setup_detail_view()
        self.setup_settings_view()
        self.setup_stats_view()
        self.main_container.controls = [
            self.list_container,
            self.add_container,
            self.edit_container,
            self.detail_container,
            self.settings_container,
            self.stats_container,
        ]
        self.main_container.update()
        self.show_list_view()

    def setup_ui(self):
        font_path = os.path.join(os.path.dirname(__file__), "assets", "fonts", "Comfortaa-Regular.ttf")
        if os.path.exists(font_path):
            self.page.fonts = {"Comfortaa": font_path}
        ar_font_path = os.path.join(os.path.dirname(__file__), "assets", "fonts", "AlMaghrebi-Modern-Wahib.ttf")
        if os.path.exists(ar_font_path):
            self.page.fonts["AlMaghrebi"] = ar_font_path

        self.setup_app_bar()
        self.setup_navigation()
        self.setup_list_view()
        self.setup_add_form()
        self.setup_edit_form()
        self.setup_detail_view()
        self.setup_settings_view()
        self.setup_stats_view()

        self.geolocator = None
        self.camera = None
        self.camera_available = False
        self.geolocator_available = False

        _is_desktop = self.page.platform in (ft.PagePlatform.WINDOWS, ft.PagePlatform.MACOS, ft.PagePlatform.LINUX)
        if not _is_desktop:
            try:
                self.geolocator = Geolocator(
                    configuration=GeolocatorConfiguration(
                        accuracy=GeolocatorPositionAccuracy.HIGH,
                    ),
                )
                self.page.overlay.append(self.geolocator)
                self.geolocator_available = True
            except Exception as ex:
                self.logger.warning("Geolocator not available: %s", ex)

            try:
                self.camera = Camera(visible=False)
                self.page.overlay.append(self.camera)
                self.camera_available = True
            except Exception as ex:
                self.logger.warning("Camera init failed: %s", ex)
        else:
            self.logger.info("Camera and Geolocator skipped on desktop platform: %s", self.page.platform)

        self.main_container = Stack([
            self.list_container,
            self.add_container,
            self.edit_container,
            self.detail_container,
            self.settings_container,
            self.stats_container,
        ], expand=True)
        safe_main = SafeArea(
            content=self.main_container,
            expand=True,
            avoid_intrusions_top=True,
            avoid_intrusions_bottom=True,
            maintain_bottom_view_padding=True,
        )
        self.page.add(safe_main)
        self.show_list_view()

    def update_tree_code(self):
        try:
            s = self.add_sector.value.strip() if self.add_sector.value else ""
            z = self.add_zone.value.strip() if self.add_zone.value else ""
            r = self.add_row.value.strip() if self.add_row.value else ""
            t = self.add_tree_number.value.strip() if self.add_tree_number.value else ""
            code = f"S{s}Z{z}R{r}T{t}" if (s or z or r or t) else ""
            self.add_tree_code.value = code
            if hasattr(self, 'location_tree_code'):
                self.location_tree_code.value = code
                self.location_tree_code.update()
        except Exception as ex:
            self.logger.warning("update_tree_code: %s", ex)

    def on_kind_change(self, e):
        kind = e.control.value or e.data
        if kind and kind in TREE_VARIETIES:
            self.add_variety.options = [DropdownOption(text=v, key=v) for v in TREE_VARIETIES[kind]]
        else:
            self.add_variety.options = []
        self.add_variety.value = None
        self.add_variety.update()

    def on_edit_kind_change(self, e):
        kind = e.control.value or e.data
        if kind and kind in TREE_VARIETIES:
            self.edit_variety.options = [DropdownOption(text=v, key=v) for v in TREE_VARIETIES[kind]]
        else:
            self.edit_variety.options = []
        self.edit_variety.value = None
        self.edit_variety.update()

    def setup_app_bar(self):
        self.search_field = TextField(
            hint_text=self.t("search_hint"),
            hint_style=TextStyle(color=Colors.GREY_500, font_family=self._font()),
            border=InputBorder.NONE,
            content_padding=Padding(10, 0, 10, 0),
            on_change=self.on_search_change,
            expand=True,
            text_size=16,
            text_style=TextStyle(font_family=self._font()),
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
            border_radius=BorderRadius(10, 10, 10, 10),
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
            margin=Margin(0, 0, 4, 0),
            border_radius=BorderRadius(20, 20, 20, 20),
            padding=Padding(8, 0, 8, 0),
        )

        self.back_btn = IconButton(icon=Icons.ARROW_BACK, icon_color=Colors.WHITE, icon_size=32, tooltip="Back")
        self.stats_btn = IconButton(icon=Icons.ANALYTICS_OUTLINED, icon_color=Colors.WHITE, icon_size=32, on_click=lambda _: self.show_stats_view(), tooltip="Statistics")
        self.app_bar = AppBar(
            leading=None,
            title=None,
            bgcolor=Colors.GREEN_700,
            actions=[
                self.search_input_container,
                self.search_button,
                self.stats_btn,
                IconButton(icon=Icons.REFRESH, icon_color=Colors.WHITE, icon_size=32, on_click=lambda _: self.load_trees(), tooltip="Refresh"),
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

    def setup_list_view(self):
        self.tree_list = ListView(expand=True, spacing=8, padding=Padding(10, 10, 10, 90))
        self.loading_indicator = ProgressRing(visible=False, color=Colors.GREEN_700)
        self.empty_state = Container(
            content=Column([
                Icon(Icons.PARK, size=80, color=Colors.GREY_300),
                Text(self.t("no_trees_found"), size=18, color=Colors.GREY_500, font_family=self._font()),
                Text(self.t("tap_to_add"), size=14, color=Colors.GREY_400, font_family=self._font()),
            ], horizontal_alignment=CrossAxisAlignment.CENTER, spacing=10),
            alignment=alignment.Alignment(0, 0),
            expand=True,
            visible=False,
        )
        self.pagination_controls = Row([
            IconButton(icon=Icons.CHEVRON_LEFT, on_click=lambda _: self.prev_page(), disabled=True),
            Text(self.t("page") + "1 / 1", size=14, font_family=self._font()),
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
                Text(self.t("loading"), size=18, font_family=self._font(), color=Colors.GREEN_700, weight=FontWeight.BOLD),
                Text(self.t("loading_sub"), size=13, font_family=self._font(), color=Colors.GREY_500),
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
            keyboard_type=KeyboardType.NUMBER,
            on_change=lambda e: self.update_tree_code(),
        )
        self.add_zone = TextField(
            label="Zone",
            label_style=TextStyle(font_family="Comfortaa", size=10),
            border=InputBorder.OUTLINE,
            text_style=TextStyle(font_family="Comfortaa"),
            keyboard_type=KeyboardType.NUMBER,
            on_change=lambda e: self.update_tree_code(),
        )
        self.add_row = TextField(
            label="Row",
            label_style=TextStyle(font_family="Comfortaa", size=10),
            border=InputBorder.OUTLINE,
            text_style=TextStyle(font_family="Comfortaa"),
            keyboard_type=KeyboardType.NUMBER,
            on_change=lambda e: self.update_tree_code(),
        )
        self.add_tree_number = TextField(
            label="Tree",
            label_style=TextStyle(font_family="Comfortaa", size=10),
            border=InputBorder.OUTLINE,
            text_style=TextStyle(font_family="Comfortaa"),
            keyboard_type=KeyboardType.NUMBER,
            on_change=lambda e: self.update_tree_code(),
        )
        self.add_tree_code = TextField(
            label="Tree Code",
            hint_text="Auto-generated from Sector/Zone/Row/Tree#",
            border=InputBorder.OUTLINE,
            text_style=TextStyle(font_family="Comfortaa"),
            read_only=True,
        )
        self.location_tree_code = Text("", size=14, font_family="Comfortaa", color=Colors.GREEN_700)
        self.location_coords_badge = Container(
            content=Text("", size=10, font_family="Comfortaa", color=Colors.GREY_800),
            padding=Padding(8, 4, 8, 4),
            border=Border.all(1, Colors.GREY_300),
            border_radius=BorderRadius(12, 12, 12, 12),
            visible=False,
        )
        self.location_gps_btn = IconButton(
            icon=Icons.MY_LOCATION,
            icon_size=18,
            icon_color=Colors.GREEN_700,
            tooltip="Get GPS location",
            on_click=lambda e: self.get_gps(),
        )
        self.location_card = Card(
            content=Container(
                content=Column([
                    Row([
                        Text(self.t("location"), size=16, weight=FontWeight.BOLD, font_family=self._font(), color=Colors.GREEN_700),
                        self.location_coords_badge,
                        self.location_gps_btn,
                        self.location_tree_code,
                    ], alignment=MainAxisAlignment.SPACE_BETWEEN),
                    Row([
                        Container(content=self.add_sector, expand=1),
                        Container(content=self.add_zone, expand=1),
                        Container(content=self.add_row, expand=1),
                        Container(content=self.add_tree_number, expand=1),
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
        self.add_kind.on_select = self.on_kind_change
        self.add_variety = Dropdown(
            label="Variety",
            hint_text="Select variety",
            options=[],
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
                Text(self.t("no_photo"), size=14, color=Colors.GREY_500, font_family=self._font()),
            ], horizontal_alignment=CrossAxisAlignment.CENTER, spacing=10),
            width=320,
            height=240,
            border=Border.all(2, Colors.GREY_300),
            border_radius=BorderRadius(8,8,8,8),
            alignment=alignment.Alignment(0, 0),
        )
        self.add_take_photo_btn = FilledButton(
            content=Row([Icon(Icons.CAMERA_ALT), Text(self.t("take_photo"))], spacing=8, alignment=MainAxisAlignment.CENTER),
            on_click=self._take_photo,
            style=ButtonStyle(color=Colors.WHITE, bgcolor=Colors.GREEN_700, padding=Padding(16, 12, 16, 12)),
        )

        # Photos Card
        self.photos_card = Card(
            content=Container(
                content=Column([
                    Row([
                        Text(self.t("photo"), size=16, weight=FontWeight.BOLD, font_family=self._font(), color=Colors.GREEN_700),
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
            content=Text(self.t("save_tree")),
            icon=Icons.SAVE,
            on_click=self.save_new_tree,
            style=ButtonStyle(
                bgcolor=Colors.GREEN_700,
                color=Colors.WHITE,
                padding=Padding(20, 12, 20, 12),
            ),
        )
        self.add_save_next_btn = Button(
            content=Text(self.t("save_next")),
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
                        Row([Text(self.t("add_new_tree"), size=24, weight=FontWeight.BOLD, font_family=self._font(), color=Colors.GREEN_700)], spacing=8, vertical_alignment=CrossAxisAlignment.CENTER),
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
        self.edit_kind.on_select = self.on_edit_kind_change
        self.edit_variety = Dropdown(
            label="Variety",
            hint_text="Select variety",
            options=[],
            border=InputBorder.OUTLINE,
            text_style=TextStyle(font_family="Comfortaa"),
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
            on_click=self._take_visit_photo,
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
                        Text(self.t("edit_tree"), size=24, weight=FontWeight.BOLD, font_family=self._font(), color=Colors.GREEN_700),
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
                            Text(self.t("tree_details"), size=24, weight=FontWeight.BOLD, font_family=self._font(), color=Colors.GREEN_700, expand=True),
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

    def _switch_view(self, container):
        for c in (self.list_container, self.add_container, self.edit_container,
                  self.detail_container, self.settings_container, self.stats_container):
            c.visible = (c is container)
        self.main_container.update()

    def show_list_view(self):
        self.logger.debug("Navigating to list view")
        self.app_bar.leading = None
        self._switch_view(self.list_container)
        self.page.bottom_appbar = self.pagination_bar
        self.page.update()
        invalidate_cache()
        self.current_page = 0
        self.load_trees()

    def show_add_form(self):
        self.logger.debug("Navigating to add form")
        self.back_btn.on_click = lambda _: self.show_list_view()
        self.app_bar.leading = self.back_btn
        self.reset_add_form()
        self._switch_view(self.add_container)
        self.nav_bar.selected_index = 1
        self.nav_bar.update()
        self.page.bottom_appbar = None
        self.page.update()

    def show_search_view(self):
        self._switch_view(self.list_container)
        self.nav_bar.selected_index = 0
        self.nav_bar.update()
        self.page.bottom_appbar = None
        self.page.update()
        asyncio.create_task(self.search_field.focus())
        if self.search_query:
            self.load_trees()
        else:
            self.current_page = 0
            self.load_trees()

    def setup_settings_view(self):
        self.lang_switch = ft.Switch(
            value=(self.lang == "ar"),
            on_change=self._on_lang_change,
            active_color=Colors.GREEN_700,
        )
        self.settings_container = Container(
            content=Column([
                Text(self.t("settings"), size=24, weight=FontWeight.BOLD, font_family=self._font(), color=Colors.GREEN_700),
                Divider(height=2, color=Colors.GREEN_200),
                Container(height=10),
                Card(
                    content=Container(
                        content=Row([
                            Icon(Icons.LANGUAGE, color=Colors.GREEN_700),
                            Column([
                                Text(self.t("language"), font_family=self._font(), weight=FontWeight.BOLD),
                                Text(self.t("language_subtitle"), font_family=self._font(), size=12, color=Colors.GREY_600),
                            ], spacing=2, expand=True),
                            Text("EN", size=12, font_family="Comfortaa", weight=FontWeight.BOLD, color=Colors.GREY_600),
                            self.lang_switch,
                            Text("ع", size=14, font_family="AlMaghrebi", weight=FontWeight.BOLD, color=Colors.GREY_600),
                        ], spacing=8, vertical_alignment=CrossAxisAlignment.CENTER),
                        padding=Padding(16, 8, 16, 8),
                    ),
                    elevation=2,
                ),
                Container(height=5),
                Card(
                    content=ListTile(
                        leading=Icon(Icons.HELP, color=Colors.GREEN_700),
                        title=Text(self.t("help"), font_family=self._font(), weight=FontWeight.BOLD),
                        subtitle=Text(self.t("help_subtitle"), font_family=self._font()),
                        on_click=self.show_help,
                    ),
                    elevation=2,
                ),
                Container(height=5),
                Card(
                    content=ListTile(
                        leading=Icon(Icons.INFO, color=Colors.GREEN_700),
                        title=Text(self.t("about"), font_family=self._font(), weight=FontWeight.BOLD),
                        subtitle=Text(self.t("about_subtitle") + version.version, font_family=self._font()),
                        on_click=self.show_about,
                    ),
                    elevation=2,
                ),
                Container(height=5),
                Card(
                    content=ListTile(
                        leading=Icon(Icons.BUG_REPORT, color=Colors.GREEN_700),
                        title=Text(self.t("view_logs"), font_family=self._font(), weight=FontWeight.BOLD),
                        subtitle=Text(self.t("view_logs_subtitle"), font_family=self._font()),
                        on_click=self.show_logs,
                    ),
                    elevation=2,
                ),
            ], spacing=0, scroll=ScrollMode.AUTO),
            padding=Padding(20, 20, 20, 20),
            expand=True,
            visible=False,
        )

    def _on_lang_change(self, e):
        self.lang = "ar" if e.control.value else "en"
        self._apply_language()

    def setup_stats_view(self):
        self.stats_total_label = Text(self.t("total_trees") + "0", size=18, weight=FontWeight.BOLD, font_family=self._font(), color=Colors.GREEN_700)
        self.stats_searched_label = Text(self.t("searched_trees") + "0", size=18, weight=FontWeight.BOLD, font_family=self._font(), color=Colors.BLUE_700)
        self.stats_heatmap_grid = Column(spacing=2)
        self.stats_heatmap_legend = Row(spacing=0)
        self.stats_heatmap_empty = Container(
            content=Text(self.t("no_tree_available"), size=16, color=Colors.GREY_500, font_family=self._font()),
            height=120, alignment=alignment.Alignment(0, 0), visible=False,
        )
        self.stats_bar_chart = BarChart(
            expand=True,
            height=300,
            group_spacing=8,
            tooltip=BarChartTooltip(bgcolor=Colors.with_opacity(0.8, Colors.BLACK)),
            left_axis=ChartAxis(
                label_size=40,
            ),
            bottom_axis=ChartAxis(
                label_size=40,
            ),
        )
        self.stats_bar_legend = Row(spacing=0, wrap=True)
        self.stats_bar_empty = Container(
            content=Text(self.t("no_tree_available"), size=16, color=Colors.GREY_500, font_family=self._font()),
            height=120, alignment=alignment.Alignment(0, 0), visible=False,
        )

        self.stats_container = Container(
            content=ListView([
                Container(
                    content=Column([
                        Row([
                            Text(self.t("statistics"), size=24, weight=FontWeight.BOLD, font_family=self._font(), color=Colors.GREEN_700, expand=True),
                        ]),
                        Divider(height=2, color=Colors.GREEN_200),
                        Container(height=20),
                        self.stats_total_label,
                        Container(height=10),
                        self.stats_searched_label,
                        Container(height=20),
                        Text(self.t("heatmap_title"), size=16, weight=FontWeight.BOLD, font_family=self._font(), color=Colors.GREEN_700),
                        Divider(height=2),
                        Container(
                            content=self.stats_heatmap_grid,
                            border=Border.all(2, Colors.GREEN_700),
                            border_radius=BorderRadius(10, 10, 10, 10),
                            padding=Padding(8, 8, 8, 8),
                            bgcolor=Colors.WHITE,
                        ),
                        self.stats_heatmap_empty,
                        Container(height=10),
                        self.stats_heatmap_legend,
                        Container(height=30),
                        Text(self.t("barchart_title"), size=16, weight=FontWeight.BOLD, font_family=self._font(), color=Colors.GREEN_700),
                        Divider(height=2),
                        self.stats_bar_chart,
                        self.stats_bar_empty,
                        Container(height=10),
                        self.stats_bar_legend,
                    ], spacing=8, horizontal_alignment=CrossAxisAlignment.STRETCH),
                    padding=Padding(0, 20, 0, 20),
                ),
            ], expand=True, padding=Padding(0, 0, 0, 0)),
            visible=False,
        )

    def show_stats_view(self):
        self._switch_view(self.stats_container)
        self.nav_bar.selected_index = 0
        self.nav_bar.update()
        self.page.bottom_appbar = None
        self.back_btn.on_click = lambda _: self.show_list_view()
        self.app_bar.leading = self.back_btn
        self.page.update()
        self.load_stats()

    def load_stats(self):
        try:
            if self.search_query or self.filter_kind or self.filter_status:
                trees = search_trees(self.search_query, self.filter_kind, self.filter_status)
            else:
                trees = get_all_trees()
        except Exception as ex:
            self.logger.error("Failed to load stats: %s", ex)
            self.show_snack("Error loading statistics", Colors.RED)
            return

        total = len(trees)
        searched = sum(1 for t in trees if t.get("visits"))
        self.stats_total_label.value = f"Total Trees: {total}"
        self.stats_searched_label.value = f"Searched Trees: {searched}"

        # --- Heatmap data ---
        matrix = {}
        all_sectors = set()
        all_zones = set()
        for t in trees:
            code = t.get("tree_code", "")
            m = re.match(r"S(\d+)Z(\d+)", code)
            if m:
                s, z = m.groups()
                all_sectors.add(s)
                all_zones.add(z)
                matrix.setdefault(s, {}).setdefault(z, 0)
                matrix[s][z] += 1

        self.stats_heatmap_grid.controls.clear()
        if matrix:
            self.stats_heatmap_empty.visible = False
            sectors = sorted(all_sectors, key=int)
            zones = sorted(all_zones, key=int)
            counts = [matrix[s].get(z, 0) for s in sectors for z in zones]
            max_count = max(counts) if counts else 1

            header = Row([
                Container(width=40, height=24),
                *[Container(
                    content=Text(f"Z{z}", size=11, weight=FontWeight.BOLD, font_family="Comfortaa", color=Colors.GREEN_800, text_align=ft.TextAlign.CENTER),
                    expand=True, alignment=alignment.Alignment(0, 0),
                ) for z in zones],
            ], spacing=2, vertical_alignment=CrossAxisAlignment.CENTER)
            self.stats_heatmap_grid.controls.append(header)

            for s in sectors:
                row = [Container(
                    content=Text(f"S{s}", size=11, weight=FontWeight.BOLD, font_family="Comfortaa", color=Colors.GREEN_800),
                    width=40, height=40, alignment=alignment.Alignment(0, 0),
                )]
                for z in zones:
                    cnt = matrix[s].get(z, 0)
                    intensity = cnt / max_count if max_count else 0
                    r = int(220 - 180 * intensity)
                    g = int(245 - 175 * intensity)
                    b = int(220 - 150 * intensity)
                    hex_color = f"#{r:02x}{g:02x}{b:02x}"
                    row.append(Container(
                        content=Text(str(cnt) if cnt else "", size=12, font_family="Comfortaa", color=Colors.WHITE if intensity > 0.5 else Colors.GREY_800, text_align=ft.TextAlign.CENTER),
                        expand=True, height=40, bgcolor=hex_color, alignment=alignment.Alignment(0, 0),
                        border_radius=BorderRadius(3, 3, 3, 3),
                    ))
                self.stats_heatmap_grid.controls.append(Row(row, spacing=2))
        else:
            self.stats_heatmap_empty.visible = True

        self.stats_heatmap_legend.controls.clear()
        if matrix:
            steps = 6
            for i in range(steps):
                p = i / (steps - 1)
                r = int(220 - 180 * p)
                g = int(245 - 175 * p)
                b = int(220 - 150 * p)
                hex_color = f"#{r:02x}{g:02x}{b:02x}"
                self.stats_heatmap_legend.controls.append(
                    Container(
                        content=Text(str(int(p * 100)) + "%", size=9, font_family="Comfortaa", color=Colors.WHITE if p > 0.5 else Colors.GREY_800, text_align=ft.TextAlign.CENTER),
                        width=50, height=24, bgcolor=hex_color, alignment=alignment.Alignment(0, 0),
                    )
                )

        # --- Bar chart data ---
        sector_counts = {}
        for t in trees:
            code = t.get("tree_code", "")
            m = re.match(r"S(\d+)", code)
            if m:
                s = m.group(1)
                sector_counts[s] = sector_counts.get(s, 0) + 1

        self.stats_bar_empty.visible = not sector_counts
        self.stats_bar_chart.visible = bool(sector_counts)

        if sector_counts:
            chart_groups = []
            sector_colors = [
                Colors.GREEN_700, Colors.GREEN_500, Colors.GREEN_300,
                Colors.TEAL_700, Colors.TEAL_500, Colors.TEAL_300,
                Colors.CYAN_700, Colors.CYAN_500, Colors.CYAN_300,
                Colors.BLUE_700, Colors.BLUE_500, Colors.BLUE_300,
            ]
            sorted_sectors = sorted(sector_counts.keys(), key=int)
            bar_max = max(sector_counts.values()) if sector_counts else 1

            for i, s in enumerate(sorted_sectors):
                cnt = sector_counts[s]
                color = sector_colors[i % len(sector_colors)]
                chart_groups.append(
                    BarChartGroup(
                        x=i,
                        rods=[
                            BarChartRod(
                                to_y=cnt,
                                color=color,
                                width=20,
                                tooltip=f"S{s}: {cnt} trees",
                                border_radius=BorderRadius(4, 4, 0, 0),
                            )
                        ],
                    )
                )

            self.stats_bar_chart.groups = chart_groups
            self.stats_bar_chart.max_y = bar_max + 1
            self.stats_bar_chart.bottom_axis = ChartAxis(
                labels=[
                    ChartAxisLabel(value=i, label=Text(f"S{s}", size=11, font_family="Comfortaa"))
                    for i, s in enumerate(sorted_sectors)
                ],
                label_size=40,
            )

            self.stats_bar_legend.controls.clear()
            for i, s in enumerate(sorted_sectors):
                color = sector_colors[i % len(sector_colors)]
                cnt = sector_counts[s]
                self.stats_bar_legend.controls.append(
                    Row([
                        Container(width=12, height=12, bgcolor=color, border_radius=BorderRadius(3, 3, 3, 3)),
                        Text(f"S{s}: {cnt}", size=11, font_family="Comfortaa"),
                    ], spacing=4)
                )

        self.stats_heatmap_grid.update()
        self.stats_heatmap_legend.update()
        self.stats_bar_chart.update()
        self.stats_bar_legend.update()
        self.stats_total_label.update()
        self.stats_searched_label.update()

    def show_settings_view(self):
        self._switch_view(self.settings_container)
        self.nav_bar.selected_index = 2
        self.nav_bar.update()
        self.page.bottom_appbar = None
        self.page.update()

    def show_help(self, e):
        def close(e):
            dlg.open = False
            self.page.update()

        dlg = AlertDialog(
            title=Text(self.t("help_title"), font_family=self._font(), weight=FontWeight.BOLD),
            content=Column([
                Text(self.t("help_text_1"), font_family=self._font()),
                Text(self.t("help_text_2"), font_family=self._font()),
                Text(self.t("help_text_3"), font_family=self._font()),
                Text(self.t("help_text_4"), font_family=self._font()),
                Text(self.t("help_text_5"), font_family=self._font()),
                Text(self.t("help_text_6"), font_family=self._font()),
            ], spacing=8, tight=True),
            actions=[TextButton(self.t("close"), on_click=close)],
        )
        self.page.dialog = dlg
        dlg.open = True
        self.page.update()

    def show_about(self, e):
        def close(e):
            dlg.open = False
            self.page.update()

        dlg = AlertDialog(
            title=Text(self.t("about_title"), font_family=self._font(), weight=FontWeight.BOLD),
            content=Column([
                Text(self.t("app_title"), size=18, weight=FontWeight.BOLD, font_family=self._font()),
                Text(self.t("about_subtitle") + version.version, font_family=self._font()),
                Divider(),
                Text(self.t("about_desc"), font_family=self._font()),
            ], spacing=8, tight=True),
            actions=[TextButton(self.t("close"), on_click=close)],
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
            title=Text(self.t("logs_title"), font_family=self._font(), weight=FontWeight.BOLD),
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
            self.add_status.value = None
            self.add_notes.value = ""
            self.captured_photo_path = None
            self.captured_gps_lat = ""
            self.captured_gps_lon = ""
            self.add_photo_img.visible = False
            self.add_photo_placeholder.visible = True
            self.add_take_photo_btn.visible = True

            self.update_tree_code()

            # Note: Controls will be updated when they are added to the page
            # to avoid "Control must be added to the page first" error

    async def _take_photo(self):
        if not self.camera_available:
            self.show_snack("Camera not available on this platform", Colors.RED)
            return
        try:
            self.show_snack("Taking photo...", Colors.BLUE)
            await self.camera.initialize()
            img_bytes = await self.camera.take_picture()
            import tempfile
            tmp = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
            tmp.write(img_bytes)
            tmp.close()
            self.captured_photo_path = tmp.name
            self.add_photo_img.src = self.captured_photo_path
            self.add_photo_img.visible = True
            self.add_photo_placeholder.visible = False
            self.add_photo_img.update()
            self.add_photo_placeholder.update()
            self.show_snack("Photo captured!", Colors.GREEN)
        except Exception as ex:
            self.logger.error("Camera capture failed: %s", ex, exc_info=True)
            self.show_snack(f"Camera error: {ex}", Colors.RED)

    async def _take_visit_photo(self):
        if not self.camera_available:
            self.show_snack("Camera not available on this platform", Colors.RED)
            return
        try:
            self.show_snack("Taking photo...", Colors.BLUE)
            await self.camera.initialize()
            img_bytes = await self.camera.take_picture()
            import tempfile
            tmp = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
            tmp.write(img_bytes)
            tmp.close()
            photo_path = copy_photo_to_storage(tmp.name)
            self.new_photos.append(photo_path)
            self.add_visit_photos_grid.controls.append(
                Container(
                    content=Image(src=photo_path, fit=BoxFit.COVER, border_radius=BorderRadius(8, 8, 8, 8)),
                    width=80, height=80, border_radius=BorderRadius(8, 8, 8, 8), clip_behavior=ft.ClipBehavior.HARD_EDGE,
                )
            )
            self.add_visit_photos_grid.update()
            self.show_snack("Photo captured!", Colors.GREEN)
        except Exception as ex:
            self.logger.error("Camera capture failed: %s", ex, exc_info=True)
            self.show_snack(f"Camera error: {ex}", Colors.RED)

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

        self.tree_count_badge.content = Text(str(total), size=11, weight=FontWeight.BOLD, font_family="Comfortaa", color=Colors.WHITE)
        self.tree_count_badge.visible = total > 0

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
        self.tree_count_badge.update()
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
            self._switch_view(self.edit_container)

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
                    Text(self.t("change_status"), size=18, weight=FontWeight.BOLD, font_family=self._font()),
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
        items = [_build_visit_card(v) for v in reversed(visits)]

        bs = BottomSheet(
            content=Container(
                content=Column([
                    Text(self.t("visit_history"), size=18, weight=FontWeight.BOLD, font_family=self._font()),
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
        self.populate_detail_view(tree)
        self._switch_view(self.detail_container)
        self.nav_bar.selected_index = 0
        self.nav_bar.update()
        self.page.bottom_appbar = None
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
        self.detail_visits_list.controls.extend(_build_visit_card(v) for v in reversed(visits))

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
        self.populate_edit_form(self.current_tree_data)
        self._switch_view(self.edit_container)
        self.page.bottom_appbar = None
        self.page.update()

    def populate_edit_form(self, tree: dict):
        self.edit_tree_code.value = tree.get("tree_code", "")
        self.edit_kind.value = tree.get("kind", "")
        self.edit_variety.value = tree.get("variety", "")

        self.edit_visits_list.controls.clear()
        visits = tree.get("visits", [])
        self.edit_visits_list.controls.extend(_build_visit_card(v, photo_size=40) for v in reversed(visits))

        self.add_visit_status.value = None
        self.add_visit_notes.value = ""
        self.add_visit_photos_grid.controls.clear()
        self.new_photos = []

        self.edit_tree_code.update()
        self.edit_kind.update()
        self.edit_variety.update()
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
            title=Text(self.t("delete_title"), font_family=self._font()),
            content=Text(self.t("confirm_delete"), font_family=self._font()),
            actions=[
                TextButton(self.t("cancel"), on_click=cancel),
                TextButton(self.t("delete"), on_click=confirm, style=ButtonStyle(color=Colors.RED)),
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
        
        latitude = self.captured_gps_lat
        longitude = self.captured_gps_lon
        
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

        sector = self.add_sector.value.strip()
        zone = self.add_zone.value.strip()
        row = self.add_row.value.strip()
        tree_number = self.add_tree_number.value.strip()

        if not sector or not sector.isdigit() or int(sector) <= 0:
            self.show_snack("Sector must be a positive number", Colors.RED)
            return
        if not zone or not zone.isdigit() or int(zone) <= 0:
            self.show_snack("Zone must be a positive number", Colors.RED)
            return
        if not row or not row.isdigit() or int(row) <= 0:
            self.show_snack("Row must be a positive number", Colors.RED)
            return
        if not tree_number or not tree_number.isdigit() or int(tree_number) <= 0:
            self.show_snack("Tree must be a positive number", Colors.RED)
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
            try:
                self.add_photo_img.update()
                self.add_photo_placeholder.update()
                self.add_take_photo_btn.update()
            except RuntimeError:
                pass
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
        
        latitude = self.current_tree_data.get("latitude", "") if self.current_tree_data else ""
        longitude = self.current_tree_data.get("longitude", "") if self.current_tree_data else ""

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

    def get_gps(self):
        if not self.geolocator_available:
            self.show_snack("GPS not available on this platform", Colors.RED)
            return
        async def _get_position():
            try:
                pos = await self.geolocator.get_current_position(
                    GeolocatorConfiguration(
                        accuracy=GeolocatorPositionAccuracy.HIGH,
                    )
                )
                self.captured_gps_lat = str(pos.latitude)
                self.captured_gps_lon = str(pos.longitude)
                if hasattr(self, 'location_coords_badge'):
                    self.location_coords_badge.content = Text(
                        f"{pos.latitude:.6f}, {pos.longitude:.6f}",
                        size=10, font_family="Comfortaa", color=Colors.GREY_800,
                    )
                    self.location_coords_badge.visible = True
                    self.location_coords_badge.update()
                self.show_snack("GPS coordinates captured", Colors.GREEN)
            except Exception as ex:
                self.logger.warning("Geolocator failed: %s", ex)
                self.show_snack("GPS location unavailable", Colors.RED)
        import asyncio
        asyncio.create_task(_get_position())
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
