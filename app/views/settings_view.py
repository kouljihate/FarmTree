import flet as ft
from flet import (
    Container, Text, Row, Column, Card, ListTile, Switch, AlertDialog,
    TextButton, Divider, Icon, Icons, Colors, Padding, FontWeight,
    ScrollMode, alignment, IconButton, Clipboard,
)


class SettingsView:
    def __init__(self, app):
        self.app = app

    def t(self, key: str) -> str:
        return self.app.t(key)

    def _font(self) -> str:
        return self.app._font()

    def setup(self):
        self.lang_switch = ft.Switch(
            value=(self.app.lang == "ar"),
            on_change=self._on_lang_change,
            active_color=Colors.GREEN_700,
        )
        self.container = Container(
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
                        ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
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
                        subtitle=Text(self.t("about_subtitle") + self.app.version, font_family=self._font()),
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

    def show(self):
        self.app._switch_view(self.container)
        self.app.nav_bar.selected_index = 2
        self.app.nav_bar.update()
        self.app.page.bottom_appbar = None
        self.app.page.update()

    def _on_lang_change(self, e):
        self.app.lang = "ar" if e.control.value else "en"
        self.app.apply_language()

    def show_help(self, e):
        def close(e):
            self.app.page.pop_dialog()

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
        self.app.page.show_dialog(dlg)

    def show_about(self, e):
        def close(e):
            self.app.page.pop_dialog()

        dlg = AlertDialog(
            title=Text(self.t("about_title"), font_family=self._font(), weight=FontWeight.BOLD),
            content=Column([
                Text(self.t("app_title"), size=18, weight=FontWeight.BOLD, font_family=self._font()),
                Text(self.t("about_subtitle") + self.app.version, font_family=self._font()),
                Divider(),
                Text(self.t("about_desc"), font_family=self._font()),
            ], spacing=8, tight=True),
            actions=[TextButton(self.t("close"), on_click=close)],
        )
        self.app.page.show_dialog(dlg)

    def show_logs(self, e):
        from app.logger import read_logs, clear_logs, export_logs

        def close(e):
            self.app.page.pop_dialog()

        def refresh(e):
            lines = read_logs(200)
            content.controls = [Text(l.rstrip(), size=11, font_family="Consolas", selectable=True) for l in lines]
            self.app.page.update()

        def clear(e):
            clear_logs()
            content.controls = [Text("[Logs cleared]", size=11, font_family="Consolas")]
            self.app.page.update()
            self.app.show_snack("Logs cleared", Colors.GREEN)

        def export(e):
            path = export_logs()
            if path:
                self.app.show_snack(f"Exported: {path}", Colors.GREEN)
            else:
                self.app.show_snack("Export failed", Colors.RED)

        def copy_clipboard(e):
            lines = read_logs(200)
            text = "".join(lines)
            self.app.page.set_clipboard(text)
            self.app.page.update()
            self.app.show_snack("Logs copied to clipboard", Colors.GREEN)

        lines = read_logs(200)
        content = Column(
            [Text(l.rstrip(), size=11, font_family="Consolas", selectable=True) for l in lines],
            scroll=ScrollMode.AUTO, spacing=2,
        )
        dlg = AlertDialog(
            title=Text(self.t("logs_title"), font_family=self._font(), weight=FontWeight.BOLD),
            content=Column([Text("App Logs", size=16, weight=FontWeight.BOLD), Divider(), content], width=360, height=500),
            actions=[
                TextButton("Clear", on_click=clear),
                TextButton("Export", on_click=export),
                TextButton("CC", on_click=copy_clipboard),
                TextButton("Refresh", on_click=refresh),
                TextButton("Close", on_click=close),
            ],
        )
        self.app.page.show_dialog(dlg)
