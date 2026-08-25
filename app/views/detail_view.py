import flet as ft
from flet import (
    Container, Text, Row, Column, ListView, Card, Button, OutlinedButton,
    GridView, Image, Icon, Icons, Colors, Padding, BorderRadius, FontWeight,
    Divider, alignment, BoxFit, ClipBehavior,
    CrossAxisAlignment, MainAxisAlignment,
)
from app.config import STATUS_LOOKUP
from app.database import get_tree
from app.views.components import build_visit_card


class TreeDetailView:
    def __init__(self, app):
        self.app = app

    def t(self, key: str) -> str:
        return self.app.t(key)

    def _font(self) -> str:
        return self.app._font()

    def setup(self):
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
            on_click=lambda _: self._edit_current_tree(),
            style=ft.ButtonStyle(
                bgcolor=Colors.GREEN_700,
                color=Colors.WHITE,
                padding=Padding(20, 12, 20, 12),
            ),
        )
        self.detail_delete_btn = OutlinedButton(
            content=Text("Delete"),
            icon=Icons.DELETE,
            icon_color=Colors.RED,
            style=ft.ButtonStyle(color=Colors.RED),
            on_click=lambda _: self.app.confirm_delete_current(),
        )

        self.detail_add_visit_btn = Button(
            content=Text("New Visit"),
            icon=Icons.ADD,
            on_click=lambda _: self._edit_current_tree(),
            style=ft.ButtonStyle(
                bgcolor=Colors.GREEN_500,
                color=Colors.WHITE,
                padding=Padding(16, 12, 16, 12),
            ),
        )

        self.container = Container(
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

    def show_tree_detail(self, tree: dict):
        self.app.current_tree_id = tree["id"]
        self.app.current_tree_data = tree
        self.app.back_btn.on_click = lambda _: self.app.list_view.show()
        self.app.app_bar.leading = self.app.back_btn
        self._populate(tree)
        self.app._switch_view(self.container)
        self.app.nav_bar.selected_index = 0
        self.app.nav_bar.update()
        self.app.page.bottom_appbar = None
        self.app.page.update()

    def _populate(self, tree: dict):
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
                    width=120, height=120, border_radius=BorderRadius(8, 8, 8, 8), clip_behavior=ClipBehavior.HARD_EDGE,
                )
            )

        self.detail_visits_list.controls.clear()
        self.detail_visits_list.controls.extend(build_visit_card(v) for v in reversed(visits))

        self.detail_tree_code.update()
        self.detail_kind.update()
        self.detail_variety.update()
        self.detail_location.update()
        self.detail_status_badge.update()
        self.detail_notes.update()
        self.detail_photos_grid.update()
        self.detail_visits_list.update()

    def _edit_current_tree(self):
        self.app.back_btn.on_click = lambda _: self.show_tree_detail(self.app.current_tree_data) if self.app.current_tree_data else self.app.list_view.show()
        self.app.app_bar.leading = self.app.back_btn
        self.app.edit_view.show(self.app.current_tree_data)
