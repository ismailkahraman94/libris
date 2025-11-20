import flet as ft
import database
import os

class EBooks(ft.Column):
    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id
        self.expand = True
        self.scroll = ft.ScrollMode.AUTO
        
        # Online Search Section
        self.search_query = ft.TextField(
            label="Kitap Adı / Yazar", 
            hint_text="Aradığınız kitabın adını yazın...",
            expand=True, 
            on_submit=self.search_online,
            border_radius=10
        )
        self.file_type = ft.Dropdown(
            width=100,
            options=[
                ft.dropdown.Option("pdf"),
                ft.dropdown.Option("epub"),
                ft.dropdown.Option("mobi"),
                ft.dropdown.Option("tümü"),
            ],
            value="pdf",
            label="Format",
            border_radius=10
        )
        
        self.online_search_card = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.PUBLIC, color=ft.Colors.BLUE_400),
                    ft.Text("İnternette E-Kitap Ara", size=16, weight="bold")
                ]),
                ft.Container(height=10),
                ft.Row([
                    self.search_query,
                    self.file_type,
                    ft.IconButton(
                        ft.Icons.SEARCH, 
                        on_click=self.search_online, 
                        icon_color=ft.Colors.WHITE,
                        bgcolor=ft.Colors.BLUE_600,
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10))
                    )
                ]),
                ft.Text("Google üzerinde dosya türüne göre arama yapar (örn: 'Sefiller filetype:pdf').", size=12, color=ft.Colors.GREY_500)
            ]),
            padding=20,
            bgcolor=ft.Colors.ON_INVERSE_SURFACE,
            border_radius=15
        )

        # Local E-Books List
        self.ebooks_grid = ft.GridView(
            expand=1,
            runs_count=5,
            max_extent=250,
            child_aspect_ratio=1.0,
            spacing=15,
            run_spacing=15,
        )

        self.controls = [
            ft.Container(height=10),
            ft.Text("E-Kitap Merkezi", size=24, weight="bold"),
            ft.Container(height=10),
            self.online_search_card,
            ft.Divider(height=40, color=ft.Colors.GREY_800),
            ft.Row([
                ft.Icon(ft.Icons.FOLDER_SPECIAL, color=ft.Colors.ORANGE_300),
                ft.Text("Kitaplığınızdaki Dosyalar", size=18, weight="bold"),
            ]),
            ft.Container(height=10),
            self.ebooks_grid
        ]

    def load_ebooks(self):
        self.ebooks_grid.controls.clear()
        books = database.get_books(self.user_id)
        # Filter books with file_path
        ebooks = [b for b in books if len(b) > 20 and b[20]]
        
        if not ebooks:
            self.ebooks_grid.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.Icons.FOLDER_OFF, size=50, color=ft.Colors.GREY_500),
                        ft.Text("Henüz dosya eklenmiş kitabınız yok.", color=ft.Colors.GREY_500)
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    alignment=ft.alignment.center,
                    padding=40
                )
            )
        else:
            for book in ebooks:
                self.ebooks_grid.controls.append(self.create_book_card(book))
        self.update()

    def create_book_card(self, book):
        # book[20] is file_path
        file_path = book[20]
        file_name = os.path.basename(file_path)
        cover_url = book[4]
        
        icon = ft.Icons.INSERT_DRIVE_FILE
        color = ft.Colors.BLUE_400
        if file_path.lower().endswith('.pdf'):
            icon = ft.Icons.PICTURE_AS_PDF
            color = ft.Colors.RED_400
        elif file_path.lower().endswith('.epub'):
            icon = ft.Icons.BOOK
            color = ft.Colors.GREEN_400
            
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(icon, size=30, color=color),
                    ft.Container(expand=True),
                    ft.IconButton(ft.Icons.FOLDER_OPEN, tooltip="Klasörü Aç", icon_size=18, on_click=lambda _: self.open_folder(file_path))
                ]),
                ft.Text(book[1], weight="bold", size=14, max_lines=2, overflow=ft.TextOverflow.ELLIPSIS, text_align=ft.TextAlign.CENTER),
                ft.Text(file_name, size=10, color=ft.Colors.GREY, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS, text_align=ft.TextAlign.CENTER),
                ft.Container(expand=True),
                ft.ElevatedButton(
                    "Aç", 
                    icon=ft.Icons.PLAY_ARROW, 
                    on_click=lambda _: self.open_file(file_path),
                    style=ft.ButtonStyle(
                        bgcolor=ft.Colors.with_opacity(0.1, color),
                        color=color,
                        shape=ft.RoundedRectangleBorder(radius=8)
                    ),
                    width=1000 # Full width
                )
            ], alignment=ft.MainAxisAlignment.START, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor=ft.Colors.ON_INVERSE_SURFACE,
            padding=15,
            border_radius=15,
            on_click=lambda _: self.open_file(file_path)
        )

    def search_online(self, e):
        if not self.search_query.value: return
        
        query = self.search_query.value
        fmt = self.file_type.value
        
        if fmt == "tümü":
            search_term = f"{query} e-book download"
        else:
            search_term = f"{query} filetype:{fmt}"
            
        url = f"https://www.google.com/search?q={search_term}"
        self.page.launch_url(url)

    def open_file(self, path):
        if os.path.exists(path):
            try:
                os.startfile(path)
            except Exception as ex:
                self.page.snack_bar = ft.SnackBar(ft.Text(f"Hata: {ex}"))
                self.page.snack_bar.open = True
                self.page.update()
        else:
            self.page.snack_bar = ft.SnackBar(ft.Text("Dosya bulunamadı!"))
            self.page.snack_bar.open = True
            self.page.update()

    def open_folder(self, path):
        if os.path.exists(path):
            try:
                folder = os.path.dirname(path)
                os.startfile(folder)
            except Exception as ex:
                self.page.snack_bar = ft.SnackBar(ft.Text(f"Hata: {ex}"))
                self.page.snack_bar.open = True
                self.page.update()
