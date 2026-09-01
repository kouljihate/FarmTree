import flet as ft
from flet import (
    Container, Text, Row, Column, ListView, Card, ListTile, IconButton,
    Icon, Icons, Colors, Padding, Margin, BorderRadius, FontWeight,
    CrossAxisAlignment, MainAxisAlignment, ProgressRing, BottomAppBar,
    Stack, alignment,
)
from app.config import STATUS_LOOKUP
from app.database import get_trees_slice, search_trees, count_trees, invalidate_cache


class TreeListView:
    def __init__(self, app):
        self.app = app
        self.per_page = 20
        self.PAGE_CHUNK = 1000
        self.current_page = 0
        self._is_loading = False

    def t(self, key: str) -> str:
        return self.app.t(key)

    def _font(self) -> str:
        return self.app._font()

    def setup(self):
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

        self.container = Container(
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

    def show(self):
        self.app.app_bar.leading = None
        self.app._switch_view(self.container)
        self.app.page.bottom_appbar = self.pagination_bar
        self.app.page.update()
        invalidate_cache()
        self.current_page = 0
        self.load_trees()

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
            if self.app.search_query or self.app.filter_kind or self.app.filter_status:
                trees = search_trees(self.app.search_query, self.app.filter_kind, self.app.filter_status)
                total = len(trees)
            else:
                batch_end = (self.current_page + 1) * self.per_page
                batch_end = ((batch_end - 1) // self.PAGE_CHUNK + 1) * self.PAGE_CHUNK
                trees = get_trees_slice(0, batch_end)
                total = count_trees()
        except Exception as ex:
            self.app.logger.error("Failed to load trees: %s", ex, exc_info=True)
            self.app.show_snack("Error loading trees", Colors.RED)
            self.hide_loading_overlay()
            self._is_loading = False
            return

        self.app.tree_count_badge.content = Text(str(total), size=11, weight=FontWeight.BOLD, font_family="Comfortaa", color=Colors.WHITE)
        self.app.tree_count_badge.visible = total > 0

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
                self.tree_list.controls.append(self._create_tree_card(tree))

        self._update_pagination(total)
        self.app.tree_count_badge.update()
        self.tree_list.update()
        self.empty_state.update()
        self.pagination_controls.update()
        self.hide_loading_overlay()
        self._is_loading = False

    def _update_pagination(self, total):
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

    def _create_tree_card(self, tree: dict):
        tree_code = tree.get("tree_code", "Unknown")
        kind = tree.get("kind", "")
        variety = tree.get("variety", "")
        last_status = tree.get("last_status", "No visits")
        last_photo = tree.get("last_photo", "")
        lat = tree.get("latitude", "")
        lon = tree.get("longitude", "")

        status_color = STATUS_LOOKUP.get(last_status, "#455A64")
        status_badge = Container(
            content=Text(last_status, size=13, weight=FontWeight.BOLD, font_family="Comfortaa", color=Colors.WHITE),
            bgcolor=status_color,
            padding=Padding(12, 4, 12, 4),
            border_radius=BorderRadius(20, 20, 20, 20),
        )

        if last_photo:
            photo_src = last_photo if last_photo.startswith("data:") else f"data:image/jpeg;base64,{last_photo}"
            leading = Container(
                width=60, height=60,
                border_radius=BorderRadius(8, 8, 8, 8),
                clip_behavior=ft.ClipBehavior.HARD_EDGE,
                content=ft.Image(src=photo_src, fit=ft.BoxFit.COVER, width=60, height=60),
            )
        else:
            leading = Container(
                width=60, height=60,
                border_radius=BorderRadius(8, 8, 8, 8),
                content=Icon(Icons.PARK, size=30, color=Colors.GREEN_700),
                bgcolor=Colors.GREEN_50,
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
            self.app.detail_view.show_tree_detail(tree)

        def on_long_press(e):
            self.app.show_tree_context_menu(tree)

        card = Card(
            content=ListTile(
                leading=leading,
                title=Text(tree_code, weight=FontWeight.BOLD, size=16, font_family="Comfortaa"),
                subtitle=subtitle,
                trailing=IconButton(icon=Icons.CHEVRON_RIGHT, on_click=lambda _, t=tree: self.app.detail_view.show_tree_detail(t)),
                on_click=on_tap,
                on_long_press=on_long_press,
                content_padding=Padding(10, 8, 10, 8),
            ),
            elevation=2,
            margin=Margin(0, 0, 0, 0),
        )
        return card
