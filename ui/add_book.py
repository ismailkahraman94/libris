import flet as ft
import api
import database

class AddBook(ft.Column):
    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id
        self.expand = True
        self.scroll = ft.ScrollMode.AUTO # Enable scrolling for long lists
        
        self.search_query = ft.TextField(
            label="ISBN veya Başlık ile Ara", 
            text_size=16,
            border_radius=12,
            bgcolor=ft.Colors.ON_INVERSE_SURFACE,
            border_color=ft.Colors.TRANSPARENT,
            focused_border_color=ft.Colors.TEAL_400,
            prefix_icon=ft.Icons.SEARCH,
            expand=True,
            on_submit=self.search_book
        )
        
        self.search_btn = ft.ElevatedButton(
            "Ara", 
            icon=ft.Icons.SEARCH_ROUNDED,
            style=ft.ButtonStyle(
                padding=20,
                shape=ft.RoundedRectangleBorder(radius=12),
            ),
            on_click=self.search_book
        )
        
        self.results_area = ft.Column(spacing=20)
        self.shelf_dropdown = ft.Dropdown(
            label="Raf Seç", 
            options=[],
            border_radius=12,
            bgcolor=ft.Colors.ON_INVERSE_SURFACE,
            border_color=ft.Colors.TRANSPARENT,
        )
        self.current_book_data = None
        
        self.help_box = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.INFO_OUTLINE, color=ft.Colors.TEAL_200),
                ft.Text(
                    "Kitap eklemek için ISBN numarasını veya kitap adını girip 'Ara' butonuna basın. Gelen sonuçlardan doğru kitabı seçip, eklemek istediğiniz rafı belirleyerek kütüphanenize kaydedin.",
                    size=12, color=ft.Colors.GREY_300, expand=True
                )
            ]),
            padding=10,
            bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.TEAL),
            border_radius=10,
            margin=ft.margin.only(bottom=10)
        )
        
        self.controls = [
            ft.Container(
                content=ft.Column([
                    ft.Text("Yeni Kitap Ekle", size=32, weight=ft.FontWeight.BOLD),
                    self.help_box,
                ]),
                margin=ft.margin.only(bottom=30)
            ),
            ft.Container(
                content=ft.Column([
                    ft.Row([self.search_query, self.search_btn], alignment=ft.MainAxisAlignment.CENTER),
                    ft.Container(height=10),
                    self.shelf_dropdown
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                padding=30,
                bgcolor=ft.Colors.ON_INVERSE_SURFACE,
                border_radius=20,
            ),
            ft.Divider(height=40, color=ft.Colors.TRANSPARENT),
            self.results_area
        ]

    def did_mount(self):
        self.load_shelves()

    def load_shelves(self):
        shelves = database.get_shelves(self.user_id)
        if not shelves:
            # Create default shelf if none exists
            database.add_shelf("Okunacaklar", "Varsayılan okuma listesi", self.user_id)
            shelves = database.get_shelves(self.user_id)
            
        self.shelf_dropdown.options = [ft.dropdown.Option(key=str(s[0]), text=s[1]) for s in shelves]
        if shelves:
            self.shelf_dropdown.value = str(shelves[0][0])
        self.update()

    def search_book(self, e):
        if not self.search_query.value:
            return
        
        self.results_area.controls.clear()
        self.results_area.controls.append(ft.ProgressBar(color=ft.Colors.TEAL_400))
        self.update()

        books = api.get_book_metadata(self.search_query.value)
        self.results_area.controls.clear()

        if books:
            for book_data in books:
                self.results_area.controls.append(
                    ft.Container(
                        content=ft.Row(
                            [
                                ft.Container(
                                    content=ft.Image(
                                        src=book_data["cover_url"] if book_data["cover_url"] else "https://via.placeholder.com/150", 
                                        height=150, 
                                        border_radius=10,
                                        fit=ft.ImageFit.CONTAIN,
                                    ),
                                    shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.with_opacity(0.3, ft.Colors.BLACK)),
                                    border_radius=10,
                                ),
                                ft.Container(width=20),
                                ft.Column(
                                    [
                                    ft.Text(book_data['title'], size=18, weight="bold", max_lines=2, overflow=ft.TextOverflow.ELLIPSIS),
                                    ft.Text(f"Yazar: {book_data['author']}", size=14, color=ft.Colors.TEAL_200),
                                    ft.Text(f"Yayınevi: {book_data['publisher']}", size=12, color=ft.Colors.GREY_400),
                                    ft.Text(f"Sayfa: {book_data['page_count']}", size=12, color=ft.Colors.GREY_500),
                                    ft.Container(height=10),
                                    ft.Row([
                                        ft.ElevatedButton(
                                            "Hızlı Ekle", 
                                            icon=ft.Icons.ADD_TASK_ROUNDED, 
                                            on_click=lambda e, b=book_data: self.save_book(b),
                                            style=ft.ButtonStyle(
                                                bgcolor=ft.Colors.TEAL_600,
                                                color=ft.Colors.WHITE
                                            )
                                        ),
                                        ft.OutlinedButton(
                                            "Düzenle & Ekle",
                                            icon=ft.Icons.EDIT_NOTE,
                                            on_click=lambda e, b=book_data: self.open_edit_dialog(b)
                                        ),
                                        ft.IconButton(
                                            icon=ft.Icons.OPEN_IN_NEW,
                                            tooltip="Kitabı İncele",
                                            icon_color=ft.Colors.TEAL_200,
                                            on_click=lambda e, url=book_data.get("link"): e.page.launch_url(url) if url else None,
                                            visible=bool(book_data.get("link"))
                                        )
                                    ])
                                    ],
                                    expand=True,
                                    alignment=ft.MainAxisAlignment.START
                                )
                            ],
                            alignment=ft.MainAxisAlignment.START,
                            vertical_alignment=ft.CrossAxisAlignment.START
                        ),
                        padding=20,
                        bgcolor=ft.Colors.ON_INVERSE_SURFACE,
                        border_radius=15,
                        animate_opacity=300,
                    )
                )
        else:
            self.results_area.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.Icons.ERROR_OUTLINE_ROUNDED, size=50, color=ft.Colors.RED_400),
                        ft.Text("Kitap bulunamadı", size=18, weight="bold"),
                        ft.Text("Lütfen ISBN veya Başlığı kontrol edip tekrar deneyin.", color=ft.Colors.GREY_400)
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    padding=40,
                    alignment=ft.alignment.center,
                    bgcolor=ft.Colors.ON_INVERSE_SURFACE,
                    border_radius=20
                )
            )
        
        self.update()

    def save_book(self, book_data):
        shelf_id = self.shelf_dropdown.value
        if not shelf_id:
            self.page.snack_bar = ft.SnackBar(ft.Text("Lütfen önce yukarıdan bir raf seçin!"))
            self.page.snack_bar.open = True
            self.page.update()
            return

        # Check for duplicate book
        if database.check_book_exists(book_data["isbn"], self.user_id):
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"'{book_data['title']}' zaten kütüphanenizde mevcut!"),
                action="Yine de Ekle",
                on_action=lambda e: self.force_add_book(book_data, shelf_id)
            )
            self.page.snack_bar.open = True
            self.page.update()
            return

        self.force_add_book(book_data, shelf_id)

    def force_add_book(self, book_data, shelf_id):
        # Sanitize summary
        summary = book_data.get("summary", "Özet yok.")
        if summary and ("Kitapyurdu'ndan bulundu" in summary or ("bulundu" in summary.lower() and len(summary) < 50)):
            summary = "Özet yok."

        database.add_book(
            book_data["title"],
            book_data["author"],
            book_data["isbn"],
            book_data["cover_url"],
            int(shelf_id),
            self.user_id,
            summary,
            book_data.get("page_count"),
            book_data.get("publisher"),
            book_data.get("status", "Okunacak"),
            book_data.get("current_page", 0),
            book_data.get("start_date"),
            book_data.get("finish_date"),
            book_data.get("link")
        )
        
        self.page.snack_bar = ft.SnackBar(ft.Text(f"'{book_data['title']}' kütüphanenize eklendi!"))
        self.page.snack_bar.open = True
        self.page.update()

    def open_edit_dialog(self, book_data):
        title_field = ft.TextField(label="Kitap Adı", value=book_data["title"])
        author_field = ft.TextField(label="Yazar", value=book_data["author"])
        publisher_field = ft.TextField(label="Yayınevi", value=book_data["publisher"])
        page_count_field = ft.TextField(label="Sayfa Sayısı", value=str(book_data["page_count"]), keyboard_type=ft.KeyboardType.NUMBER)
        summary_field = ft.TextField(label="Özet", value=book_data["summary"], multiline=True, min_lines=3)
        
        status_dropdown = ft.Dropdown(
            label="Durum",
            options=[
                ft.dropdown.Option("Okunacak"),
                ft.dropdown.Option("Okunuyor"),
                ft.dropdown.Option("Okundu"),
            ],
            value="Okunacak"
        )
        
        current_page_field = ft.TextField(label="Okunan Sayfa", value="0", keyboard_type=ft.KeyboardType.NUMBER, visible=False)
        
        def on_status_change(e):
            current_page_field.visible = (status_dropdown.value == "Okunuyor")
            self.page.update()
            
        status_dropdown.on_change = on_status_change

        start_date_field = ft.TextField(label="Başlangıç Tarihi (GG.AA.YYYY)", hint_text="Örn: 20.11.2023")
        finish_date_field = ft.TextField(label="Bitiş Tarihi (GG.AA.YYYY)", hint_text="Örn: 25.11.2023")

        def save_edited_book(e):
            # Update book data with new values
            book_data["title"] = title_field.value
            book_data["author"] = author_field.value
            book_data["publisher"] = publisher_field.value
            book_data["summary"] = summary_field.value
            book_data["status"] = status_dropdown.value
            book_data["start_date"] = start_date_field.value
            book_data["finish_date"] = finish_date_field.value
            
            try:
                book_data["page_count"] = int(page_count_field.value)
            except:
                book_data["page_count"] = 0
                
            try:
                book_data["current_page"] = int(current_page_field.value)
            except:
                book_data["current_page"] = 0
            
            self.save_book(book_data)
            self.page.dialog.open = False
            self.page.update()

        self.page.dialog = ft.AlertDialog(
            title=ft.Text("Kitap Bilgilerini Düzenle"),
            content=ft.Column([
                title_field,
                author_field,
                publisher_field,
                ft.Row([page_count_field, status_dropdown]),
                current_page_field,
                ft.Row([start_date_field, finish_date_field]),
                summary_field
            ], tight=True, width=500, scroll=ft.ScrollMode.AUTO),
            actions=[
                ft.TextButton("İptal", on_click=lambda e: setattr(self.page.dialog, 'open', False) or self.page.update()),
                ft.ElevatedButton("Kaydet ve Ekle", on_click=save_edited_book)
            ],
        )
        self.page.dialog.open = True
        self.page.update()

