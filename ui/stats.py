import flet as ft
import database
import datetime
from collections import defaultdict

class Statistics(ft.Column):
    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id
        self.expand = True
        self.scroll = ft.ScrollMode.AUTO
        
        self.total_time_card = self.create_stat_card("Toplam Okuma Süresi", "0 dk", ft.Icons.TIMER, ft.Colors.BLUE_400)
        self.total_pages_card = self.create_stat_card("Oturumlarda Okunan", "0 sayfa", ft.Icons.AUTO_STORIES, ft.Colors.GREEN_400)
        self.total_books_card = self.create_stat_card("Toplam Kitap", "0", ft.Icons.LIBRARY_BOOKS, ft.Colors.ORANGE_400)
        
        self.chart_container = ft.Container(
            content=ft.Text("Veri yükleniyor..."),
            height=300,
            bgcolor=ft.Colors.ON_INVERSE_SURFACE,
            border_radius=15,
            padding=20
        )
        
        self.pie_chart_container = ft.Container(
            content=ft.Text("Veri yükleniyor..."),
            height=300,
            bgcolor=ft.Colors.ON_INVERSE_SURFACE,
            border_radius=15,
            padding=20
        )

        self.controls = [
            ft.Text("İstatistikler", size=24, weight="bold"),
            ft.Container(height=10),
            ft.Row([self.total_time_card, self.total_pages_card, self.total_books_card], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Container(height=20),
            ft.Text("Son 7 Günlük Okuma Aktivitesi (Sayfa)", size=16, weight="bold"),
            self.chart_container,
            ft.Container(height=20),
            ft.Text("Raf Dağılımı", size=16, weight="bold"),
            self.pie_chart_container
        ]

    def create_stat_card(self, title, value, icon, color):
        return ft.Container(
            content=ft.Column([
                ft.Icon(icon, color=color, size=30),
                ft.Text(value, size=20, weight="bold"),
                ft.Text(title, size=12, color=ft.Colors.GREY_400)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor=ft.Colors.ON_INVERSE_SURFACE,
            padding=20,
            border_radius=15,
            expand=True
        )

    def load_stats(self):
        # 1. Basic Stats
        total_minutes = database.get_total_reading_time(self.user_id)
        total_pages_session = database.get_total_pages_read_in_sessions(self.user_id)
        all_books = database.get_books(self.user_id)
        
        hours, mins = divmod(total_minutes, 60)
        time_str = f"{hours}s {mins}dk" if hours > 0 else f"{mins}dk"
        
        self.total_time_card.content.controls[1].value = time_str
        self.total_pages_card.content.controls[1].value = f"{total_pages_session} sayfa"
        self.total_books_card.content.controls[1].value = str(len(all_books))
        
        # 2. Bar Chart (Last 7 Days)
        sessions = database.get_user_reading_sessions(self.user_id)
        # sessions: (id, book_id, start_time, end_time, duration, pages, title)
        
        daily_pages = defaultdict(int)
        today = datetime.date.today()
        dates = [(today - datetime.timedelta(days=i)) for i in range(6, -1, -1)]
        
        for s in sessions:
            try:
                # s[2] is start_time string "YYYY-MM-DD HH:MM"
                s_date = datetime.datetime.strptime(s[2], "%Y-%m-%d %H:%M").date()
                if s_date in dates:
                    daily_pages[s_date] += s[5] # s[5] is pages_read
            except: pass
            
        chart_groups = []
        for d in dates:
            val = daily_pages[d]
            chart_groups.append(
                ft.BarChartGroup(
                    x=dates.index(d),
                    bar_rods=[
                        ft.BarChartRod(
                            from_y=0,
                            to_y=val,
                            width=20,
                            color=ft.Colors.BLUE_400 if val > 0 else ft.Colors.GREY_800,
                            tooltip=f"{d.strftime('%d.%m')}: {val} sayfa",
                            border_radius=5
                        )
                    ]
                )
            )
            
        self.chart_container.content = ft.BarChart(
            bar_groups=chart_groups,
            border=ft.border.all(1, ft.Colors.TRANSPARENT),
            left_axis=ft.ChartAxis(
                labels_size=40, title=ft.Text("Sayfa"), title_size=20
            ),
            bottom_axis=ft.ChartAxis(
                labels=[
                    ft.ChartAxisLabel(
                        value=i,
                        label=ft.Container(ft.Text(d.strftime("%d.%m"), size=10), padding=5)
                    ) for i, d in enumerate(dates)
                ],
                labels_size=30,
            ),
            horizontal_grid_lines=ft.ChartGridLines(
                color=ft.Colors.GREY_800, width=1, dash_pattern=[3, 3]
            ),
            tooltip_bgcolor=ft.Colors.with_opacity(0.8, ft.Colors.BLUE_GREY_900),
            max_y=max(daily_pages.values()) + 10 if daily_pages else 50,
            interactive=True,
            expand=True
        )

        # 3. Pie Chart (Shelves)
        shelves = database.get_shelves(self.user_id)
        shelf_map = {s[0]: s[1] for s in shelves} # id -> name
        shelf_counts = defaultdict(int)
        
        for b in all_books:
            s_id = b[5]
            s_name = shelf_map.get(s_id, "Bilinmiyor")
            shelf_counts[s_name] += 1
            
        pie_sections = []
        colors = [ft.Colors.BLUE, ft.Colors.RED, ft.Colors.GREEN, ft.Colors.ORANGE, ft.Colors.PURPLE, ft.Colors.TEAL, ft.Colors.PINK]
        
        for i, (name, count) in enumerate(shelf_counts.items()):
            pie_sections.append(
                ft.PieChartSection(
                    count,
                    title=f"{name}\n({count})",
                    color=colors[i % len(colors)],
                    radius=100,
                    title_style=ft.TextStyle(size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)
                )
            )
            
        if not pie_sections:
            self.pie_chart_container.content = ft.Text("Veri yok", color=ft.Colors.GREY)
        else:
            self.pie_chart_container.content = ft.PieChart(
                sections=pie_sections,
                sections_space=2,
                center_space_radius=40,
                expand=True
            )

        self.update()
