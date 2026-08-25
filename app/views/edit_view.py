import tempfile

import flet as ft
from flet import (
    Container, Text, Row, Column, ListView, Card, TextField, Dropdown,
    DropdownOption, Button, OutlinedButton, IconButton, Icon, Icons,
    GridView, Image, Colors, Padding, Margin, BorderRadius, FontWeight,
    InputBorder, TextStyle, Divider, alignment, BoxFit,
    CrossAxisAlignment, MainAxisAlignment,
)
from app.config import TREE_KINDS, TREE_VARIETIES, STATUS_LOOKUP
from app.database import update_tree, add_visit, copy_photo_to_storage

STATUS_DROPDOWN_ITEMS = [DropdownOption(text=label, key=label) for label in STATUS_LOOKUP]
KIND_DROPDOWN_ITEMS = [DropdownOption(text=k, key=k) for k in TREE_KINDS]


class TreeEditView:
    def __init__(self, app):
        self.app = app
        self.new_photos = []

    def t(self, key: str) -> str:
        return self.app.t(key)

    def _font(self) -> str:
        return self.app._font()

    def setup(self):
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
            on_select=self.on_edit_kind_change,
        )
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
            style=ft.ButtonStyle(color=Colors.GREEN_700),
        )
        self.edit_save_btn = Button(
            content=Text("Save Changes"),
            icon=Icons.SAVE,
            on_click=self.save_edit_changes,
            style=ft.ButtonStyle(
                bgcolor=Colors.GREEN_700,
                color=Colors.WHITE,
                padding=Padding(20, 12, 20, 12),
            ),
        )
        self.edit_delete_btn = OutlinedButton(
            content=Text("Delete Tree"),
            icon=Icons.DELETE,
            icon_color=Colors.RED,
            style=ft.ButtonStyle(color=Colors.RED),
            on_click=lambda _: self.app.confirm_delete_current(),
        )

        self.container = Container(
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

    def show(self, tree: dict):
        self.app.current_tree_id = tree["id"]
        self.app.current_tree_data = tree
        self.populate_form(tree)
        self.app._switch_view(self.container)
        self.app.page.bottom_appbar = None
        self.app.page.update()

    def populate_form(self, tree: dict):
        from app.views.components import build_visit_card

        self.edit_tree_code.value = tree.get("tree_code", "")
        self.edit_kind.value = tree.get("kind", "")
        self.edit_variety.value = tree.get("variety", "")

        self.edit_visits_list.controls.clear()
        visits = tree.get("visits", [])
        self.edit_visits_list.controls.extend(build_visit_card(v, photo_size=40) for v in reversed(visits))

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

    def on_edit_kind_change(self, e):
        kind = e.data if e.data else (e.control.value if e.control.value else "")
        if kind and kind in TREE_VARIETIES:
            self.edit_variety.options = [DropdownOption(text=v, key=v) for v in TREE_VARIETIES[kind]]
        else:
            self.edit_variety.options = []
        self.edit_variety.value = None
        self.edit_variety.update()

    def save_edit_changes(self, e):
        if not self.app.current_tree_id:
            return
        tree_code = self.edit_tree_code.value.strip()
        kind = self.edit_kind.value
        variety = (self.edit_variety.value or "").strip()

        latitude = self.app.current_tree_data.get("latitude", "") if self.app.current_tree_data else ""
        longitude = self.app.current_tree_data.get("longitude", "") if self.app.current_tree_data else ""

        if not tree_code:
            self.app.show_snack("Tree code is required", Colors.RED)
            return
        if not kind:
            self.app.show_snack("Kind is required", Colors.RED)
            return

        try:
            update_tree(self.app.current_tree_id, tree_code, kind, variety, latitude, longitude)
            status = self.add_visit_status.value
            notes = (self.add_visit_notes.value or "").strip()
            if status:
                add_visit(self.app.current_tree_id, status, notes, None)
            self.app.show_snack("Tree updated successfully!", Colors.GREEN)
        except Exception as ex:
            self.app.logger.error("Failed to update tree %s: %s", self.app.current_tree_id, ex, exc_info=True)
            self.app.show_snack("Error updating tree", Colors.RED)
            return
        self.app.list_view.show()

    async def _take_visit_photo(self):
        if not self.app.camera_available:
            self.app.show_snack("Camera not available on this platform", Colors.RED)
            return
        try:
            self.app.show_snack("Taking photo...", Colors.BLUE)
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
            photo_path = copy_photo_to_storage(tmp.name)
            self.new_photos.append(photo_path)
            self.add_visit_photos_grid.controls.append(
                Container(
                    content=Image(src=photo_path, fit=BoxFit.COVER, border_radius=BorderRadius(8, 8, 8, 8)),
                    width=80, height=80, border_radius=BorderRadius(8, 8, 8, 8), clip_behavior=ft.ClipBehavior.HARD_EDGE,
                )
            )
            self.add_visit_photos_grid.update()
            self.app.show_snack("Photo captured!", Colors.GREEN)
        except Exception as ex:
            self.app.logger.error("Camera capture failed: %s", ex, exc_info=True)
            self.app.show_snack(f"Camera error: {ex}", Colors.RED)
