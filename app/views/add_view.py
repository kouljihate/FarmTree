import os
import shutil
import asyncio
import tempfile
from datetime import datetime

import flet as ft
from flet import (
    Container, Text, Row, Column, ListView, Card, TextField, Dropdown,
    DropdownOption, Button, FilledButton, IconButton, Icon, Icons, Image,
    Colors, Padding, Margin, BorderRadius, FontWeight, KeyboardType,
    InputBorder, TextStyle, Border, Divider, alignment, BoxFit,
    CrossAxisAlignment, MainAxisAlignment,
)
from app.config import TREE_KINDS, TREE_VARIETIES, STATUS_LOOKUP
from app.database import insert_tree, copy_photo_to_storage, PHOTOS_DIR

STATUS_DROPDOWN_ITEMS = [DropdownOption(text=label, key=label) for label in STATUS_LOOKUP]
KIND_DROPDOWN_ITEMS = [DropdownOption(text=k, key=k) for k in TREE_KINDS]


class TreeAddView:
    def __init__(self, app):
        self.app = app

    def t(self, key: str) -> str:
        return self.app.t(key)

    def _font(self) -> str:
        return self.app._font()

    def setup(self):
        self.add_sector = TextField(
            label=self.t("sector"),
            label_style=TextStyle(font_family=self._font(), size=10),
            border=InputBorder.OUTLINE,
            text_style=TextStyle(font_family=self._font()),
            keyboard_type=KeyboardType.NUMBER,
            on_change=lambda e: self.update_tree_code(),
        )
        self.add_zone = TextField(
            label=self.t("zone"),
            label_style=TextStyle(font_family=self._font(), size=10),
            border=InputBorder.OUTLINE,
            text_style=TextStyle(font_family=self._font()),
            keyboard_type=KeyboardType.NUMBER,
            on_change=lambda e: self.update_tree_code(),
        )
        self.add_row = TextField(
            label=self.t("row"),
            label_style=TextStyle(font_family=self._font(), size=10),
            border=InputBorder.OUTLINE,
            text_style=TextStyle(font_family=self._font()),
            keyboard_type=KeyboardType.NUMBER,
            on_change=lambda e: self.update_tree_code(),
        )
        self.add_tree_number = TextField(
            label=self.t("tree"),
            label_style=TextStyle(font_family=self._font(), size=10),
            border=InputBorder.OUTLINE,
            text_style=TextStyle(font_family=self._font()),
            keyboard_type=KeyboardType.NUMBER,
            on_change=lambda e: self.update_tree_code(),
        )
        self.add_tree_code = TextField(
            label=self.t("tree_code"),
            hint_text=self.t("tree_code_hint"),
            border=InputBorder.OUTLINE,
            text_style=TextStyle(font_family=self._font()),
            read_only=True,
        )
        self.location_tree_code = Text("", size=14, font_family=self._font(), color=Colors.GREEN_700)
        self.location_coords_badge = Container(
            content=Text("", size=10, font_family=self._font(), color=Colors.GREY_800),
            padding=Padding(8, 4, 8, 4),
            border=Border.all(1, Colors.GREY_300),
            border_radius=BorderRadius(12, 12, 12, 12),
            visible=False,
        )
        self.location_gps_btn = IconButton(
            icon=Icons.MY_LOCATION,
            icon_size=18,
            icon_color=Colors.GREEN_700,
            tooltip=self.t("get_gps"),
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
            label=self.t("kind_required"),
            options=KIND_DROPDOWN_ITEMS,
            border=InputBorder.OUTLINE,
            text_style=TextStyle(font_family=self._font()),
            on_select=self.on_kind_change,
        )
        self.add_variety = Dropdown(
            label=self.t("variety"),
            hint_text=self.t("variety_hint"),
            options=[],
            border=InputBorder.OUTLINE,
            text_style=TextStyle(font_family=self._font()),
            expand=True,
        )
        self.add_status = Dropdown(
            label=self.t("status_required"),
            options=STATUS_DROPDOWN_ITEMS,
            border=InputBorder.OUTLINE,
            text_style=TextStyle(font_family=self._font()),
            expand=True,
        )
        self.add_notes = TextField(
            label=self.t("notes"),
            border=InputBorder.OUTLINE,
            multiline=True,
            min_lines=2,
            max_lines=4,
            text_style=TextStyle(font_family=self._font()),
            expand=True,
        )

        self.add_photo_img = Image(
            src="",
            width=320,
            height=240,
            fit=BoxFit.COVER,
            border_radius=BorderRadius(8, 8, 8, 8),
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
            border_radius=BorderRadius(8, 8, 8, 8),
            alignment=alignment.Alignment(0, 0),
        )
        self.add_take_photo_btn = FilledButton(
            content=Row([Icon(Icons.CAMERA_ALT), Text(self.t("take_photo"))], spacing=8, alignment=MainAxisAlignment.CENTER),
            on_click=lambda e: self.app.page.run_task(self._take_photo),
            style=ft.ButtonStyle(color=Colors.WHITE, bgcolor=Colors.GREEN_700, padding=Padding(16, 12, 16, 12)),
        )

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

        self.tree_details_card = Card(
            content=Container(
                content=Column([
                    Row([
                        Text(self.t("tree_details"), size=16, weight=FontWeight.BOLD, font_family=self._font(), color=Colors.GREEN_700),
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
        self.add_save_btn = FilledButton(
            content=Row([Icon(Icons.SAVE), Text(self.t("save_tree"))], spacing=8, alignment=MainAxisAlignment.CENTER),
            on_click=self.save_new_tree,
            style=ft.ButtonStyle(
                bgcolor=Colors.GREEN_700,
                color=Colors.WHITE,
                padding=Padding(20, 12, 20, 12),
            ),
        )
        self.add_save_next_btn = FilledButton(
            content=Row([Icon(Icons.SKIP_NEXT), Text(self.t("save_next"))], spacing=8, alignment=MainAxisAlignment.CENTER),
            on_click=self.save_new_tree_next,
            style=ft.ButtonStyle(
                bgcolor=Colors.GREEN_500,
                color=Colors.WHITE,
                padding=Padding(20, 12, 20, 12),
            ),
        )

        self.container = Container(
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

    def show(self):
        self.app.back_btn.on_click = lambda _: self.app.list_view.show()
        self.app.app_bar.leading = self.app.back_btn
        self.reset_form()
        self.app._switch_view(self.container)
        self.app.nav_bar.selected_index = 1
        self.app.nav_bar.update()
        self.app.page.bottom_appbar = None
        self.app.page.update()

    def reset_form(self):
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
            self.app.captured_photo_path = None
            self.app.captured_gps_lat = ""
            self.app.captured_gps_lon = ""
            self.add_photo_img.visible = False
            self.add_photo_placeholder.visible = True
            self.add_take_photo_btn.visible = True
            self.update_tree_code()

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
            self.app.logger.warning("update_tree_code: %s", ex)

    def on_kind_change(self, e):
        kind = e.data if e.data else (e.control.value if e.control.value else "")
        if kind and kind in TREE_VARIETIES:
            self.add_variety.options = [DropdownOption(text=v, key=v) for v in TREE_VARIETIES[kind]]
        else:
            self.add_variety.options = []
        self.add_variety.value = None
        self.add_variety.update()

    def _save_tree(self, e, next_mode: bool = False):
        tree_code = (self.add_tree_code.value or "").strip()
        kind = self.add_kind.value
        variety = (self.add_variety.value or "").strip()
        latitude = self.app.captured_gps_lat
        longitude = self.app.captured_gps_lon
        status = self.add_status.value
        notes = (self.add_notes.value or "").strip()

        if not tree_code:
            self.app.show_snack(self.t("tree_code_required"), Colors.RED)
            return
        if not kind:
            self.app.show_snack(self.t("kind_required_msg"), Colors.RED)
            return
        if not status:
            self.app.show_snack(self.t("status_required_msg"), Colors.RED)
            return

        sector = self.add_sector.value.strip() if self.add_sector.value else ""
        zone = self.add_zone.value.strip() if self.add_zone.value else ""
        row = self.add_row.value.strip() if self.add_row.value else ""
        tree_number = self.add_tree_number.value.strip() if self.add_tree_number.value else ""

        if not sector or not sector.isdigit() or int(sector) <= 0:
            self.app.show_snack(self.t("sector_positive"), Colors.RED)
            return
        if not zone or not zone.isdigit() or int(zone) <= 0:
            self.app.show_snack(self.t("zone_positive"), Colors.RED)
            return
        if not row or not row.isdigit() or int(row) <= 0:
            self.app.show_snack(self.t("row_positive"), Colors.RED)
            return
        if not tree_number or not tree_number.isdigit() or int(tree_number) <= 0:
            self.app.show_snack(self.t("tree_positive"), Colors.RED)
            return

        photo_path = None
        if self.app.captured_photo_path:
            try:
                ext = os.path.splitext(self.app.captured_photo_path)[1].lower()
                if ext not in (".jpg", ".jpeg", ".png"):
                    ext = ".jpg"
                ts = datetime.now().strftime('%y%m%d%H%M')
                dst = os.path.join(PHOTOS_DIR, f"{tree_code}_{ts}{ext}")
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copy2(self.app.captured_photo_path, dst)
                photo_path = dst
            except Exception as ex:
                self.app.logger.error("Failed to save photo: %s", ex, exc_info=True)
                self.app.show_snack(self.t("error_saving_photo"), Colors.RED)

        try:
            insert_tree(tree_code, kind, variety, latitude, longitude, status, notes, [photo_path] if photo_path else None)
            self.app.show_snack(self.t("tree_added_next") if next_mode else self.t("tree_added"), Colors.GREEN)
        except Exception as ex:
            self.app.logger.error("Failed to save tree: %s", ex, exc_info=True)
            self.app.show_snack(self.t("error_saving"), Colors.RED)
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
                self.app.logger.warning("save_new_tree_next auto-increment: %s", ex)

            self.add_variety.value = variety
            self.add_status.value = None
            self.add_notes.value = ""
            self.app.captured_photo_path = None
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
            self.reset_form()
            self.app.list_view.show()

    def save_new_tree(self, e):
        self._save_tree(e, next_mode=False)

    def save_new_tree_next(self, e):
        self._save_tree(e, next_mode=True)

    async def _take_photo(self):
        if not self.app.camera_available:
            self.app.show_snack(self.t("camera_not_available"), Colors.RED)
            return
        try:
            self.app.show_snack(self.t("taking_photo"), Colors.BLUE)
            from flet_camera import ResolutionPreset
            cameras = await self.app.camera.get_available_cameras()
            if not cameras:
                self.app.show_snack("No camera found", Colors.RED)
                return
            await self.app.camera.initialize(
                description=cameras[0],
                resolution_preset=ResolutionPreset.HIGH,
                enable_audio=False,
            )
            img_bytes = await self.app.camera.take_picture()
            tmp = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
            tmp.write(img_bytes)
            tmp.close()
            self.app.captured_photo_path = tmp.name
            self.add_photo_img.src = self.app.captured_photo_path
            self.add_photo_img.visible = True
            self.add_photo_placeholder.visible = False
            self.add_photo_img.update()
            self.add_photo_placeholder.update()
            self.app.show_snack(self.t("photo_captured"), Colors.GREEN)
        except Exception as ex:
            self.app.logger.error("Camera capture failed: %s", ex, exc_info=True)
            self.app.show_snack(f"Camera error: {ex}", Colors.RED)

    def get_gps(self):
        if not self.app.geolocator_available:
            self.app.show_snack(self.t("gps_unavailable"), Colors.RED)
            return

        async def _get_position():
            try:
                from flet_geolocator import GeolocatorConfiguration, GeolocatorPositionAccuracy, GeolocatorPermissionStatus
                perm = await self.app.geolocator.request_permission()
                if perm in (GeolocatorPermissionStatus.DENIED, GeolocatorPermissionStatus.DENIED_FOREVER):
                    self.app.show_snack(self.t("gps_unavailable"), Colors.RED)
                    return
                pos = await self.app.geolocator.get_current_position(
                    GeolocatorConfiguration(accuracy=GeolocatorPositionAccuracy.HIGH)
                )
                self.app.captured_gps_lat = str(pos.latitude)
                self.app.captured_gps_lon = str(pos.longitude)
                if hasattr(self, 'location_coords_badge'):
                    self.location_coords_badge.content = Text(
                        f"{pos.latitude:.6f}, {pos.longitude:.6f}",
                        size=10, font_family="Comfortaa", color=Colors.GREY_800,
                    )
                    self.location_coords_badge.visible = True
                    self.location_coords_badge.update()
                self.app.show_snack(self.t("gps_captured"), Colors.GREEN)
            except Exception as ex:
                self.app.logger.warning("Geolocator failed: %s", ex)
                self.app.show_snack(self.t("gps_unavailable"), Colors.RED)

        self.app._gps_task = asyncio.create_task(_get_position())
        self.app.show_snack(self.t("gps_getting"), Colors.BLUE)
