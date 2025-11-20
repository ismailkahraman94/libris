import flet as ft
import database

from ui.dashboard import BookDetailsDialog

class Shelves(ft.Column):
    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id
        self.expand = True
        self.scroll = ft.ScrollMode.HIDDEN
        
        self.shelf_name = ft.TextField(
            label="Yeni Raf Adı", 
            border_radius=10,
            bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.WHITE),
            border_color=ft.Colors.TRANSPARENT,
            text_size=14,
            expand=True
        )
        self.shelf_desc = ft.TextField(
            label="Açıklama (İsteğe bağlı)", 
            border_radius=10,
            bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.WHITE),
            border_color=ft.Colors.TRANSPARENT,
            text_size=14,
            expand=True
        )
        
        self.shelves_grid = ft.GridView(
            expand=1,
            runs_count=4,
            max_extent=300,
            child_aspect_ratio=1.2,
            spacing=20,
            run_spacing=20,
        )
        
        self.help_box = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.INFO_OUTLINE, color=ft.Colors.BLUE_200),
                ft.Text(
                    "Kitaplarınızı kategorize etmek için yeni raflar oluşturun. Raflarınızı düzenleyebilir ve silebilirsiniz.",
                    size=13, color=ft.Colors.GREY_400, expand=True
                )
            ]),
            padding=15,
            bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.BLUE),
            border_radius=10,
            margin=ft.margin.only(bottom=20)
        )
        
        # Define the main view controls
        self.shelves_view_controls = [
            ft.Container(
                content=ft.Column([
                    ft.Text("Raflar", size=28, weight=ft.FontWeight.BOLD),
                    self.help_box,
                ]),
                margin=ft.margin.only(bottom=10)
            ),
            ft.Container(
                content=ft.Row(
                    [
                        self.shelf_name,
                        self.shelf_desc,
                        ft.FloatingActionButton(
                            icon=ft.Icons.ADD,
                            text="Oluştur",
                            on_click=self.add_shelf,
                            bgcolor=ft.Colors.BLUE_GREY_700,
                        )
                    ],
                    alignment=ft.MainAxisAlignment.CENTER
                ),
                padding=20,
                bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.WHITE),
                border_radius=15,
                border=ft.border.all(1, ft.Colors.with_opacity(0.1, ft.Colors.WHITE))
            ),
            ft.Divider(height=40, color=ft.Colors.TRANSPARENT),
            self.shelves_grid
        ]
        
        self.controls = self.shelves_view_controls.copy()
        self.current_shelf_id = None

    def did_mount(self):
        self.load_shelves()

    def load_shelves(self):
        self.shelves_grid.controls.clear()
        shelves = database.get_shelves(self.user_id)
        # Get book counts for each shelf
        all_books = database.get_books(self.user_id)
        shelf_counts = {}
        for book in all_books:
            s_id = book[5]
            shelf_counts[s_id] = shelf_counts.get(s_id, 0) + 1

        for shelf in shelves:
            count = shelf_counts.get(shelf[0], 0)
            self.shelves_grid.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Icon(ft.Icons.FOLDER_SPECIAL_ROUNDED, color=ft.Colors.BLUE_GREY_200, size=32),
                            ft.PopupMenuButton(
                                items=[
                                    ft.PopupMenuItem(
                                        text="Sil", 
                                        icon=ft.Icons.DELETE_OUTLINE, 
                                        on_click=lambda e, shelf_id=shelf[0]: self.delete_shelf(shelf_id)
                                    )
                                ]
                            ),
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        ft.Container(height=10),
                        ft.Text(shelf[1], size=18, weight="bold", no_wrap=True, overflow=ft.TextOverflow.ELLIPSIS),
                        ft.Text(shelf[2] if shelf[2] else "Açıklama yok", size=12, color=ft.Colors.GREY_400, no_wrap=True, overflow=ft.TextOverflow.ELLIPSIS, max_lines=2),
                        ft.Container(expand=True),
                        ft.Divider(height=1, color=ft.Colors.with_opacity(0.1, ft.Colors.WHITE)),
                        ft.Row([
                            ft.Text(f"{count} Kitap", size=12, weight="bold", color=ft.Colors.BLUE_GREY_200),
                            ft.Icon(ft.Icons.ARROW_FORWARD, size=16, color=ft.Colors.BLUE_GREY_200)
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
                    ]),
                    padding=20,
                    bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.WHITE),
                    border_radius=15,
                    animate=ft.Animation(300, ft.AnimationCurve.EASE_OUT),
                    on_hover=self.on_card_hover,
                    on_click=lambda e, s_id=shelf[0], s_name=shelf[1]: self.open_shelf(s_id, s_name)
                )
            )
        self.update()

    def open_shelf(self, shelf_id, shelf_name):
        self.current_shelf_id = shelf_id
        self.controls = []
        
        self.books_grid = ft.GridView(
            expand=1,
            runs_count=5,
            max_extent=250,
            child_aspect_ratio=0.7,
            spacing=20,
            run_spacing=20,
        )
        
        header = ft.Row([
            ft.IconButton(
                icon=ft.Icons.ARROW_BACK_IOS_NEW_ROUNDED, 
                on_click=self.show_shelves_list,
                icon_color=ft.Colors.BLUE_200
            ),
            ft.Text(shelf_name, size=28, weight="bold"),
            ft.Container(expand=True),
            ft.Chip(
                label=ft.Text("Bu raftaki kitaplar"), 
                bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.BLUE),
                leading=ft.Icon(ft.Icons.FOLDER_OPEN, color=ft.Colors.BLUE_200)
            )
        ], alignment=ft.MainAxisAlignment.START)

        self.controls.append(ft.Container(content=header, margin=ft.margin.only(bottom=20)))
        self.controls.append(self.books_grid)
        
        self.load_shelf_books(shelf_id)
        self.update()

    def show_shelves_list(self, e=None):
        self.current_shelf_id = None
        self.controls = self.shelves_view_controls.copy()
        self.load_shelves()
        self.update()

    def load_shelf_books(self, shelf_id):
        books = database.get_books(self.user_id, shelf_id)
        self.render_books(books)

    def render_books(self, books):
        self.books_grid.controls.clear()
        
        if not books:
            self.books_grid.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.Icons.AUTO_STORIES_OFF_OUTLINED, size=60, color=ft.Colors.GREY_500),
                        ft.Text("Bu rafta henüz kitap yok.", color=ft.Colors.GREY_400)
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    alignment=ft.alignment.center,
                    padding=50
                )
            )
            self.update()
            return

        for book in books:
            # book: (id, title, author, isbn, cover_url, shelf_id, is_read, rating, notes, summary, page_count, publisher, borrower_name, borrow_date, status, current_page, ...)
            status = book[14] if len(book) > 14 else "Okunacak"
            rating = book[7] if len(book) > 7 else 0
            page_count = book[10] if len(book) > 10 else 0
            current_page = book[15] if len(book) > 15 else 0
            
            # Progress bar calculation
            progress_val = 0
            if page_count > 0 and status == "Okunuyor":
                progress_val = min(current_page / page_count, 1.0)
            elif status == "Okundu":
                progress_val = 1.0
            
            status_color = ft.Colors.GREY_400
            status_bg = ft.Colors.GREY_800
            if status == "Okundu":
                status_color = ft.Colors.GREEN_200
                status_bg = ft.Colors.GREEN_900
            elif status == "Okunuyor":
                status_color = ft.Colors.ORANGE_200
                status_bg = ft.Colors.ORANGE_900
            
            self.books_grid.controls.append(
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Container(
                                content=ft.Stack([
                                    ft.Image(
                                        src=book[4] if book[4] else "https://via.placeholder.com/150",
                                        fit=ft.ImageFit.COVER,
                                        border_radius=ft.border_radius.all(12),
                                        width=1000, # Fill container
                                        height=220,
                                    ),
                                    ft.Container(
                                        content=ft.Text(status, size=10, weight="bold", color=status_color),
                                        bgcolor=status_bg,
                                        padding=ft.padding.symmetric(horizontal=8, vertical=4),
                                        border_radius=ft.border_radius.only(top_left=12, bottom_right=12),
                                        alignment=ft.alignment.center,
                                        top=0, left=0
                                    )
                                ]),
                                clip_behavior=ft.ClipBehavior.HARD_EDGE,
                                border_radius=ft.border_radius.all(12),
                                shadow=ft.BoxShadow(
                                    spread_radius=1,
                                    blur_radius=10,
                                    color=ft.Colors.with_opacity(0.3, ft.Colors.BLACK),
                                    offset=ft.Offset(0, 5),
                                ),
                                on_click=lambda e, b=book: self.open_book_details(b)
                            ),
                            ft.Container(height=5),
                            ft.Text(book[1], weight="bold", size=15, no_wrap=True, overflow=ft.TextOverflow.ELLIPSIS, tooltip=book[1]),
                            ft.Text(book[2], size=12, color=ft.Colors.ON_SURFACE_VARIANT, no_wrap=True, overflow=ft.TextOverflow.ELLIPSIS),
                            
                            # Rating Stars
                            ft.Row([
                                ft.Icon(ft.Icons.STAR_ROUNDED, size=14, color=ft.Colors.AMBER if i < rating else ft.Colors.GREY_800) for i in range(5)
                            ], spacing=2),
                            
                            # Progress Bar (Only if reading or read)
                            ft.ProgressBar(value=progress_val, color=status_color, bgcolor=ft.Colors.GREY_800, height=4, border_radius=2) if status in ["Okunuyor", "Okundu"] else ft.Container(height=4),
                            
                            ft.Row(
                                [
                                    ft.Text(f"{current_page}/{page_count} sf." if status == "Okunuyor" and page_count > 0 else "", size=10, color=ft.Colors.GREY_500),
                                    ft.IconButton(
                                        icon=ft.Icons.DELETE_OUTLINE_ROUNDED,
                                        icon_size=18,
                                        icon_color=ft.Colors.RED_300,
                                        tooltip="Kitabı Sil",
                                        on_click=lambda e, book_id=book[0]: self.delete_book(book_id)
                                    )
                                ],
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                            )
                        ],
                        spacing=5,
                    ),
                    padding=15,
                    bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.WHITE),
                    border_radius=ft.border_radius.all(15),
                    animate=ft.Animation(300, ft.AnimationCurve.EASE_OUT),
                    on_hover=self.on_card_hover,
                    on_click=lambda e, b=book: self.open_book_details(b)
                )
            )
        self.update()

    def open_book_details(self, book):
        try:
            print(f"Opening details for book: {book[1]}")
            dialog = BookDetailsDialog(book, lambda: self.load_shelf_books(self.current_shelf_id), self.user_id)
            self.page.open(dialog)
        except Exception as e:
            print(f"Error opening book details: {e}")
            self.page.snack_bar = ft.SnackBar(content=ft.Text(f"Hata: {e}"))
            self.page.snack_bar.open = True
            self.page.update()
        
    def delete_book(self, book_id):
        database.delete_book(book_id)
        self.load_shelf_books(self.current_shelf_id)

    def on_card_hover(self, e):
        e.control.scale = 1.02 if e.data == "true" else 1.0
        e.control.update()

    def add_shelf(self, e):
        name = self.shelf_name.value
        desc = self.shelf_desc.value
        
        if not name:
            self.page.snack_bar = ft.SnackBar(ft.Text("Lütfen raf adı girin!"))
            self.page.snack_bar.open = True
            self.page.update()
            return

        database.add_shelf(name, desc, self.user_id)
        self.shelf_name.value = ""
        self.shelf_desc.value = ""
        self.load_shelves()
        self.update()

    def delete_shelf(self, shelf_id):
        book_count = database.get_shelf_book_count(shelf_id)
        if book_count > 0:
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Bu rafta {book_count} kitap var. Silmek için önce kitapları taşıyın veya silin."),
                bgcolor=ft.Colors.RED_400
            )
            self.page.snack_bar.open = True
            self.page.update()
            return

        database.delete_shelf(shelf_id)
        self.load_shelves()

