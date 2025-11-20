import flet as ft
import database

class AppLayout(ft.Row):
    def __init__(self, app, page: ft.Page, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.app = app
        self.page = page
        self.expand = True
        
        self.level_text = ft.Text("Seviye 1", size=12, weight="bold", color=ft.Colors.CYAN_200)
        self.xp_bar = ft.ProgressBar(width=80, value=0, color=ft.Colors.CYAN_400, bgcolor=ft.Colors.GREY_800, height=5)
        self.streak_text = ft.Text("0 Gün", size=12, weight="bold", color=ft.Colors.ORANGE_400)
        self.update_level_display()

        self.rail = ft.NavigationRail(
            selected_index=0,
            label_type=ft.NavigationRailLabelType.ALL,
            min_width=100,
            min_extended_width=200,
            group_alignment=-0.9,
            bgcolor=ft.Colors.ON_INVERSE_SURFACE,
            leading=ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.LOCAL_LIBRARY_ROUNDED, size=40, color=ft.Colors.PRIMARY),
                    ft.Text("Kütüphanem", weight="bold", size=16, color=ft.Colors.ON_SURFACE),
                    ft.Container(height=5),
                    self.level_text,
                    self.xp_bar,
                    ft.Container(height=5),
                    ft.Row([
                        ft.Icon(ft.Icons.LOCAL_FIRE_DEPARTMENT, color=ft.Colors.ORANGE_400, size=16),
                        self.streak_text
                    ], alignment=ft.MainAxisAlignment.CENTER, spacing=2)
                ], spacing=5, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                padding=ft.padding.symmetric(vertical=30),
                alignment=ft.alignment.center
            ),
            destinations=[
                ft.NavigationRailDestination(
                    icon=ft.Icons.DASHBOARD_OUTLINED, 
                    selected_icon=ft.Icons.DASHBOARD_ROUNDED, 
                    label="Ana Sayfa"
                ),
                ft.NavigationRailDestination(
                    icon=ft.Icons.ADD_CIRCLE_OUTLINE_ROUNDED, 
                    selected_icon=ft.Icons.ADD_CIRCLE_ROUNDED, 
                    label="Kitap Ekle"
                ),
                ft.NavigationRailDestination(
                    icon=ft.Icons.SHELVES, 
                    selected_icon=ft.Icons.SHELVES, 
                    label="Raflar"
                ),
                ft.NavigationRailDestination(
                    icon=ft.Icons.TABLET_MAC, 
                    selected_icon=ft.Icons.TABLET_ANDROID, 
                    label="E-Kitaplar"
                ),
                ft.NavigationRailDestination(
                    icon=ft.Icons.INSERT_CHART_OUTLINED, 
                    selected_icon=ft.Icons.INSERT_CHART_ROUNDED, 
                    label="İstatistikler"
                ),
            ],
            on_change=self.nav_change,
            trailing=ft.Container(
                content=ft.Column([
                    ft.IconButton(
                        icon=ft.Icons.DARK_MODE_ROUNDED if self.page.theme_mode == ft.ThemeMode.DARK else ft.Icons.LIGHT_MODE_ROUNDED,
                        icon_color=ft.Colors.ORANGE_300 if self.page.theme_mode == ft.ThemeMode.DARK else ft.Colors.BLUE_500,
                        tooltip="Tema Değiştir",
                        on_click=self.toggle_theme
                    ),
                    ft.Container(height=10),
                    ft.Text(self.app.username, size=12, color=ft.Colors.GREY_400)
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                padding=ft.padding.only(bottom=20),
                alignment=ft.alignment.bottom_center,
                expand=True
            )
        )

        self.content_area = ft.Container(expand=True, padding=30)
        self.controls = [self.rail, self.content_area]

    def toggle_theme(self, e):
        self.page.theme_mode = ft.ThemeMode.LIGHT if self.page.theme_mode == ft.ThemeMode.DARK else ft.ThemeMode.DARK
        e.control.icon = ft.Icons.DARK_MODE_ROUNDED if self.page.theme_mode == ft.ThemeMode.DARK else ft.Icons.LIGHT_MODE_ROUNDED
        e.control.icon_color = ft.Colors.ORANGE_300 if self.page.theme_mode == ft.ThemeMode.DARK else ft.Colors.BLUE_500
        self.page.update()

    def nav_change(self, e):
        self.app.set_page(e.control.selected_index)

    def update_level_display(self):
        try:
            xp = database.get_user_xp(self.app.user_id)
            level = int(xp / 500) + 1
            progress = (xp % 500) / 500
            
            self.level_text.value = f"Seviye {level}"
            self.xp_bar.value = progress
            self.xp_bar.tooltip = f"{xp % 500} / 500 XP"
            
            streak = database.get_current_streak(self.app.user_id)
            self.streak_text.value = f"{streak} Gün"
        except:
            pass
