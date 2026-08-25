import re
import flet as ft
from flet import (
    Container, Text, Row, Column, ListView, Card,
    Colors, Padding, BorderRadius, FontWeight, Divider, alignment,
    CrossAxisAlignment, MainAxisAlignment,
)
from flet_charts import BarChart, BarChartGroup, BarChartRod, BarChartTooltip, ChartAxis, ChartAxisLabel
from app.config import STATUS_LOOKUP
from app.database import get_all_trees, search_trees


class StatsView:
    def __init__(self, app):
        self.app = app

    def t(self, key: str) -> str:
        return self.app.t(key)

    def _font(self) -> str:
        return self.app._font()

    def setup(self):
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
            left_axis=ChartAxis(label_size=40),
            bottom_axis=ChartAxis(label_size=40),
        )
        self.stats_bar_legend = Row(spacing=0, wrap=True)
        self.stats_bar_empty = Container(
            content=Text(self.t("no_tree_available"), size=16, color=Colors.GREY_500, font_family=self._font()),
            height=120, alignment=alignment.Alignment(0, 0), visible=False,
        )

        self.container = Container(
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
                            border=ft.Border.all(2, Colors.GREEN_700),
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

    def show(self):
        self.app._switch_view(self.container)
        self.app.nav_bar.selected_index = 0
        self.app.nav_bar.update()
        self.app.page.bottom_appbar = None
        self.app.back_btn.on_click = lambda _: self.app.list_view.show()
        self.app.app_bar.leading = self.app.back_btn
        self.app.page.update()
        self.load_stats()

    def load_stats(self):
        try:
            if self.app.search_query or self.app.filter_kind or self.app.filter_status:
                trees = search_trees(self.app.search_query, self.app.filter_kind, self.app.filter_status)
            else:
                trees = get_all_trees()
        except Exception as ex:
            self.app.logger.error("Failed to load stats: %s", ex)
            self.app.show_snack("Error loading statistics", Colors.RED)
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
