import flet as ft
import database
import datetime
import random
import os
import utils
import csv
import codecs
import api

class BookDetailsDialog(ft.AlertDialog):
    def __init__(self, book, on_update, user_id):
        super().__init__()
        print("BookDetailsDialog initialized")
        self.book = book 
        self.on_update = on_update
        self.user_id = user_id
        self.modal = True
        self.title = ft.Text("Kitap Detayları", size=20, weight=ft.FontWeight.BOLD)
        
        # Unpack book data safely
        # (id, title, author, isbn, cover_url, shelf_id, is_read, rating, notes, summary, page_count, publisher, borrower_name, borrow_date, status, current_page, start_date, finish_date)
        self.book_id = book[0]
        self.title_val = book[1] or ""
        self.author_val = book[2] or ""
        self.shelf_id_val = book[5]
        self.rating_val = book[7] if len(book) > 7 and book[7] is not None else 0
        self.notes_val = book[8] if len(book) > 8 and book[8] is not None else ""
        self.summary_val = book[9] if len(book) > 9 and book[9] is not None else "Özet yok."
        self.page_count_val = book[10] if len(book) > 10 and book[10] is not None else 0
        self.publisher_val = book[11] if len(book) > 11 and book[11] is not None else "Bilinmiyor"
        self.borrower_val = book[12] if len(book) > 12 and book[12] is not None else ""
        self.borrow_date_val = book[13] if len(book) > 13 and book[13] is not None else ""
        self.status_val = book[14] if len(book) > 14 and book[14] is not None else "Okunacak"
        self.current_page_val = book[15] if len(book) > 15 and book[15] is not None else 0
        self.start_date_val = book[16] if len(book) > 16 and book[16] is not None else ""
        self.finish_date_val = book[17] if len(book) > 17 and book[17] is not None else ""
        self.link_val = book[18] if len(book) > 18 and book[18] is not None else ""
        # Index 19 is user_id, Index 20 is file_path
        self.file_path_val = book[20] if len(book) > 20 else None

        # Edit Fields
        self.edit_title = ft.TextField(label="Başlık", value=self.title_val, border_radius=10)
        self.edit_author = ft.TextField(label="Yazar", value=self.author_val, border_radius=10)
        self.edit_notes = ft.TextField(label="Kişisel Notlar", value=self.notes_val, multiline=True, min_lines=3, border_radius=10)
        self.edit_summary = ft.TextField(label="Özet", value=self.summary_val, multiline=True, min_lines=3, max_lines=8, border_radius=10)
        self.edit_borrower = ft.TextField(label="Ödünç Verilen Kişi", value=self.borrower_val, border_radius=10)
        
        # Author Card
        self.author_card = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.PERSON_ROUNDED, color=ft.Colors.BLUE_200, size=40),
                ft.Column([
                    ft.Text("Yazar", size=12, color=ft.Colors.GREY_400),
                    ft.Text(self.author_val, size=16, weight="bold")
                ], spacing=2)
            ]),
            padding=15,
            bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.BLUE),
            border_radius=12,
            margin=ft.margin.only(bottom=10)
        )

        # Status & Progress
        self.status_dropdown = ft.Dropdown(
            label="Durum",
            value=self.status_val,
            options=[
                ft.dropdown.Option("Okunacak"),
                ft.dropdown.Option("Okunuyor"),
                ft.dropdown.Option("Okundu"),
            ],
            border_radius=10,
            on_change=self.on_status_change
        )
        
        self.current_page_field = ft.TextField(
            label="Okunan Sayfa", 
            value=str(self.current_page_val), 
            keyboard_type=ft.KeyboardType.NUMBER,
            border_radius=10,
            visible=(self.status_val == "Okunuyor")
        )
        
        self.start_date_field = ft.TextField(label="Başlangıç", value=self.start_date_val, hint_text="GG.AA.YYYY", border_radius=10, expand=True)
        self.finish_date_field = ft.TextField(label="Bitiş", value=self.finish_date_val, hint_text="GG.AA.YYYY", border_radius=10, expand=True)

        # Rating
        self.rating_slider = ft.Slider(min=0, max=5, divisions=5, label="{value}", value=self.rating_val)
        
        # Shelf Dropdown
        shelves = database.get_shelves(self.user_id)
        self.shelf_dropdown = ft.Dropdown(
            label="Raf",
            value=str(self.shelf_id_val),
            options=[ft.dropdown.Option(key=str(s[0]), text=s[1]) for s in shelves],
            border_radius=10
        )

        # Tags Tab
        self.tag_input = ft.TextField(label="Etiket Ekle", expand=True, on_submit=self.add_tag_action)
        self.tags_row = ft.Row(wrap=True, spacing=5)
        self.load_tags(update=False)

        # Quotes Tab
        self.quote_text = ft.TextField(label="Alıntı Ekle", multiline=True, min_lines=2, expand=True)
        self.quote_page = ft.TextField(label="Sayfa", width=80, keyboard_type=ft.KeyboardType.NUMBER)
        self.quotes_list = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO)
        self.load_quotes(update=False)

        # Vocabulary Tab
        self.vocab_word = ft.TextField(label="Kelime", expand=True)
        self.vocab_def = ft.TextField(label="Anlamı", expand=True)
        self.vocab_sentence = ft.TextField(label="Örnek Cümle", multiline=True)
        self.vocab_list = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO)
        self.load_vocab(update=False)

        # History Tab
        self.history_list = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO)
        self.load_history(update=False)

        self.content = ft.Container(
            width=600,
            content=ft.Column([
                ft.Tabs(
                    selected_index=0,
                    animation_duration=300,
                    tabs=[
                        ft.Tab(
                            text="Genel Bilgiler",
                            icon=ft.Icons.INFO_OUTLINE,
                            content=ft.Column([
                                ft.Container(height=10),
                                self.author_card,
                                self.edit_title,
                                # self.edit_author, # Removed as we have author card now, but maybe keep for editing?
                                # Keeping edit_author but maybe less prominent or just below title
                                self.edit_author,
                                ft.Row([self.shelf_dropdown, self.status_dropdown]),
                                self.current_page_field,
                                ft.Row([
                                    self.start_date_field,
                                    ft.IconButton(ft.Icons.CALENDAR_MONTH, on_click=lambda _: self.pick_date(self.start_date_field)),
                                    self.finish_date_field,
                                    ft.IconButton(ft.Icons.CALENDAR_MONTH, on_click=lambda _: self.pick_date(self.finish_date_field))
                                ]),
                                ft.Text(f"Yayınevi: {self.publisher_val} | Sayfa: {self.page_count_val}", size=12, color=ft.Colors.GREY),
                                ft.Divider(),
                                ft.Text("Özet:", weight="bold", size=14),
                                self.edit_summary,
                                ft.Container(height=10),
                                ft.ElevatedButton(
                                    "Kitap Bağlantısına Git",
                                    icon=ft.Icons.OPEN_IN_NEW,
                                    url=self.link_val,
                                    visible=bool(self.link_val),
                                    style=ft.ButtonStyle(
                                        color=ft.Colors.BLUE_200,
                                    )
                                ),
                                ft.Divider(),
                                ft.Text("E-Kitap / Dosya:", weight="bold", size=14),
                                ft.Row([
                                    ft.ElevatedButton("Dosya Seç", icon=ft.Icons.UPLOAD_FILE, on_click=self.pick_file),
                                    ft.ElevatedButton("Web'de Ara", icon=ft.Icons.PUBLIC, on_click=self.search_web_for_book),
                                    ft.ElevatedButton("Aç", icon=ft.Icons.FILE_OPEN, on_click=self.open_file, visible=bool(self.file_path_val), bgcolor=ft.Colors.GREEN_600, color=ft.Colors.WHITE),
                                ]),
                                ft.Text(self.file_path_val if self.file_path_val else "Dosya yok", size=12, color=ft.Colors.GREY, no_wrap=True, overflow=ft.TextOverflow.ELLIPSIS),
                                ft.Container(height=10),
                                ft.ElevatedButton("Kapak Değiştir", icon=ft.Icons.IMAGE, on_click=self.pick_cover, bgcolor=ft.Colors.BLUE_GREY_700, color=ft.Colors.WHITE, width=300),
                                ft.Container(height=5),
                                ft.ElevatedButton("Okuma Modunu Başlat", icon=ft.Icons.TIMER, on_click=self.open_reading_mode, bgcolor=ft.Colors.PURPLE_600, color=ft.Colors.WHITE, width=300)
                            ], scroll=ft.ScrollMode.AUTO)
                        ),
                        ft.Tab(
                            text="Notlar & Puan",
                            icon=ft.Icons.STAR_BORDER,
                            content=ft.Column([
                                ft.Container(height=20),
                                ft.Text("Puanınız:", weight="bold"),
                                self.rating_slider,
                                ft.Container(height=10),
                                self.edit_notes,
                                ft.Container(height=10),
                                ft.Text("Etiketler:", weight="bold"),
                                ft.Row([self.tag_input, ft.IconButton(ft.Icons.ADD, on_click=self.add_tag_action)]),
                                self.tags_row,
                                ft.Container(height=10),
                                ft.ElevatedButton("PDF Karnesi Oluştur", icon=ft.Icons.PICTURE_AS_PDF, on_click=self.create_pdf_report, bgcolor=ft.Colors.RED_700, color=ft.Colors.WHITE)
                            ])
                        ),
                        ft.Tab(
                            text="Alıntılar",
                            icon=ft.Icons.FORMAT_QUOTE_ROUNDED,
                            content=ft.Column([
                                ft.Container(height=20),
                                ft.Row([self.quote_text, self.quote_page, ft.IconButton(ft.Icons.ADD_CIRCLE, icon_color=ft.Colors.TEAL_400, on_click=self.add_quote_action)]),
                                ft.Divider(),
                                ft.Container(content=self.quotes_list, height=300)
                            ])
                        ),
                        ft.Tab(
                            text="Kelimeler",
                            icon=ft.Icons.SCHOOL_OUTLINED,
                            content=ft.Column([
                                ft.Container(height=20),
                                ft.Row([self.vocab_word, self.vocab_def]),
                                self.vocab_sentence,
                                ft.ElevatedButton("Kelime Ekle", icon=ft.Icons.ADD, on_click=self.add_vocab_action),
                                ft.Divider(),
                                ft.Container(content=self.vocab_list, height=250)
                            ])
                        ),
                        ft.Tab(
                            text="Geçmiş",
                            icon=ft.Icons.HISTORY,
                            content=ft.Column([
                                ft.Container(height=20),
                                ft.Text("Okuma Geçmişi", weight="bold", size=16),
                                ft.Container(content=self.history_list, height=300)
                            ])
                        ),
                        ft.Tab(
                            text="Ödünç Takibi",
                            icon=ft.Icons.PEOPLE_OUTLINE,
                            content=ft.Column([
                                ft.Container(height=20),
                                ft.Text("Ödünç Durumu", weight="bold", size=16),
                                ft.Container(height=10),
                                self.edit_borrower,
                                ft.Text(f"Veriliş Tarihi: {self.borrow_date_val}" if self.borrow_date_val else "Ödünç verilmedi", italic=True, color=ft.Colors.GREY)
                            ])
                        )
                    ],
                    expand=1,
                )
            ], height=500)
        )
        
        self.actions = [
            ft.TextButton("Sil", icon=ft.Icons.DELETE_OUTLINE, icon_color=ft.Colors.RED_400, on_click=self.delete_book_action),
            ft.TextButton("İptal", on_click=self.close_dialog),
            ft.ElevatedButton("Değişiklikleri Kaydet", on_click=self.save_changes, bgcolor=ft.Colors.INDIGO_500, color=ft.Colors.WHITE)
        ]

    def pick_date(self, field):
        def on_change(e):
            if e.control.value:
                field.value = e.control.value.strftime("%d.%m.%Y")
                field.update()
        
        self.page.open(
            ft.DatePicker(
                on_change=on_change,
            )
        )

    def pick_file(self, e):
        try:
            def on_result(e: ft.FilePickerResultEvent):
                if e.files:
                    self.file_path_val = e.files[0].path
                    self.page.snack_bar = ft.SnackBar(ft.Text(f"Dosya seçildi: {self.file_path_val}"))
                    self.page.snack_bar.open = True
                    self.page.update()
            
            picker = ft.FilePicker(on_result=on_result)
            self.page.overlay.append(picker)
            self.page.update()
            picker.pick_files(allow_multiple=False)
        except Exception as ex:
            self.page.snack_bar = ft.SnackBar(ft.Text(f"Hata: {ex}"))
            self.page.snack_bar.open = True
            self.page.update()

    def pick_cover(self, e):
        try:
            def on_result(e: ft.FilePickerResultEvent):
                if e.files:
                    new_cover_path = e.files[0].path
                    # Update database directly
                    database.update_book_details(
                        self.book_id,
                        self.edit_title.value,
                        self.edit_author.value,
                        int(self.shelf_dropdown.value),
                        int(self.rating_slider.value),
                        self.edit_notes.value,
                        self.edit_summary.value,
                        self.edit_borrower.value,
                        self.borrow_date_val,
                        self.status_dropdown.value,
                        int(self.current_page_field.value) if self.current_page_field.value else 0,
                        self.start_date_field.value,
                        self.finish_date_field.value,
                        self.file_path_val
                    )
                    # We need a separate update for cover_url since update_book_details doesn't handle it yet?
                    # Wait, update_book_details doesn't have cover_url param.
                    # I need to add a specific function or update the existing one.
                    # Let's add a specific function to database.py first or just execute SQL here? 
                    # Better to add to database.py.
                    database.update_book_cover(self.book_id, new_cover_path)
                    
                    self.page.snack_bar = ft.SnackBar(ft.Text("Kapak resmi güncellendi!"))
                    self.page.snack_bar.open = True
                    self.page.update()
                    self.on_update() # Refresh dashboard to show new cover
            
            picker = ft.FilePicker(on_result=on_result)
            self.page.overlay.append(picker)
            self.page.update()
            picker.pick_files(allow_multiple=False, file_type=ft.FilePickerFileType.IMAGE)
        except Exception as ex:
            self.page.snack_bar = ft.SnackBar(ft.Text(f"Hata: {ex}"))
            self.page.snack_bar.open = True
            self.page.update()

    def open_file(self, e):
        if self.file_path_val and os.path.exists(self.file_path_val):
            try:
                os.startfile(self.file_path_val)
            except Exception as ex:
                self.page.snack_bar = ft.SnackBar(ft.Text(f"Hata: {ex}"))
                self.page.snack_bar.open = True
                self.page.update()
        else:
            self.page.snack_bar = ft.SnackBar(ft.Text("Dosya bulunamadı!"))
            self.page.snack_bar.open = True
            self.page.update()

    def search_web_for_book(self, e):
        try:
            query = f"{self.title_val} {self.author_val} e-kitap indir pdf epub"
            url = f"https://www.google.com/search?q={query}"
            self.page.launch_url(url)
        except Exception as ex:
            self.page.snack_bar = ft.SnackBar(ft.Text(f"Hata: {ex}"))
            self.page.snack_bar.open = True
            self.page.update()

    def open_reading_mode(self, e):
        try:
            dialog = ReadingSessionDialog(self.book, self.on_update)
            self.page.open(dialog)
        except Exception as ex:
            # Fallback for older Flet versions or other errors
            print(f"Error opening reading mode: {ex}")
            self.page.snack_bar = ft.SnackBar(ft.Text(f"Hata: {ex}"))
            self.page.snack_bar.open = True
            self.page.update()

    def load_quotes(self, update=True):
        self.quotes_list.controls.clear()
        quotes = database.get_quotes(self.book_id)
        for q in quotes:
            # q: (id, book_id, text, page_number)
            self.quotes_list.controls.append(
                ft.Container(
                    content=ft.Row([
                        ft.Column([
                            ft.Text(f'"{q[2]}"', italic=True, size=14),
                            ft.Text(f"Sayfa: {q[3]}", size=10, color=ft.Colors.GREY)
                        ], expand=True),
                        ft.Row([
                            ft.IconButton(ft.Icons.IMAGE, tooltip="Kart Oluştur", icon_size=20, icon_color=ft.Colors.BLUE_400, on_click=lambda e, txt=q[2]: self.create_quote_card(txt)),
                            ft.IconButton(ft.Icons.DELETE_OUTLINE, icon_size=16, icon_color=ft.Colors.RED_300, on_click=lambda e, qid=q[0]: self.delete_quote_action(qid))
                        ])
                    ]),
                    padding=10,
                    bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.WHITE),
                    border_radius=10
                )
            )
        if update: self.update()

    def create_quote_card(self, text):
        try:
            # Generate image
            img_path = utils.generate_quote_card(text, self.author_val, self.title_val)
            abs_path = os.path.abspath(img_path)
            
            # Show preview dialog
            def open_image(e):
                os.startfile(abs_path)
                
            preview_dialog = ft.AlertDialog(
                title=ft.Text("Alıntı Kartı Oluşturuldu"),
                content=ft.Column([
                    ft.Image(src=abs_path, width=300, height=300, fit=ft.ImageFit.CONTAIN),
                    ft.Text(f"Kaydedildi: {img_path}", size=12, color=ft.Colors.GREY)
                ], tight=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                actions=[
                    ft.TextButton("Kapat", on_click=lambda e: self.page.close(preview_dialog)),
                    ft.ElevatedButton("Aç", on_click=open_image)
                ]
            )
            self.page.open(preview_dialog)
            
        except Exception as ex:
            self.page.snack_bar = ft.SnackBar(ft.Text(f"Kart oluşturulamadı: {ex}"))
            self.page.snack_bar.open = True
            self.page.update()


    def add_quote_action(self, e):
        text = self.quote_text.value
        if not text: return
        
        try:
            page = int(self.quote_page.value)
        except:
            page = 0
            
        database.add_quote(self.book_id, text, page)
        self.quote_text.value = ""
        self.quote_page.value = ""
        self.load_quotes()

    def delete_quote_action(self, quote_id):
        database.delete_quote(quote_id)
        self.load_quotes()

    def delete_book_action(self, e):
        def confirm_delete(e):
            database.delete_book(self.book_id)
            self.open = False
            self.page.close(self.confirm_dialog)
            self.update()
            self.on_update()
            self.page.snack_bar = ft.SnackBar(ft.Text("Kitap silindi."))
            self.page.snack_bar.open = True
            self.page.update()

        self.confirm_dialog = ft.AlertDialog(
            title=ft.Text("Kitabı Sil"),
            content=ft.Text("Bu kitabı silmek istediğinize emin misiniz?"),
            actions=[
                ft.TextButton("Hayır", on_click=lambda e: self.page.close(self.confirm_dialog)),
                ft.TextButton("Evet", on_click=confirm_delete, style=ft.ButtonStyle(color=ft.Colors.RED)),
            ],
        )
        self.page.open(self.confirm_dialog)

    def on_status_change(self, e):
        self.current_page_field.visible = (self.status_dropdown.value == "Okunuyor")
        self.update()

    def close_dialog(self, e):
        self.open = False
        self.update()

    def save_changes(self, e):
        borrow_date = self.borrow_date_val
        if self.edit_borrower.value and not self.borrower_val:
            borrow_date = datetime.datetime.now().strftime("%Y-%m-%d")
        elif not self.edit_borrower.value:
            borrow_date = ""
            
        try:
            current_page = int(self.current_page_field.value)
        except:
            current_page = 0

        database.update_book_details(
            self.book_id,
            self.edit_title.value,
            self.edit_author.value,
            int(self.shelf_dropdown.value),
            int(self.rating_slider.value),
            self.edit_notes.value,
            self.edit_summary.value,
            self.edit_borrower.value,
            borrow_date,
            self.status_dropdown.value,
            current_page,
            self.start_date_field.value,
            self.finish_date_field.value,
            self.file_path_val
        )
        self.open = False
        self.update()
        self.on_update()

    def load_history(self, update=True):
        self.history_list.controls.clear()
        sessions = database.get_reading_sessions(self.book_id)
        if not sessions:
            self.history_list.controls.append(ft.Text("Henüz okuma kaydı yok.", italic=True, color=ft.Colors.GREY))
        else:
            for s in sessions:
                # s: (id, book_id, start_time, end_time, duration_minutes, pages_read)
                self.history_list.controls.append(
                    ft.Container(
                        content=ft.Row([
                            ft.Icon(ft.Icons.ACCESS_TIME, size=16, color=ft.Colors.BLUE_200),
                            ft.Column([
                                ft.Text(f"{s[2]}", size=12, weight="bold"),
                                ft.Text(f"{s[4]} dk okundu, {s[5]} sayfa ilerlendi.", size=12, color=ft.Colors.GREY_400)
                            ], spacing=2)
                        ]),
                        padding=10,
                        bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.WHITE),
                        border_radius=10
                    )
                )
        if update: self.update()

    def load_vocab(self, update=True):
        self.vocab_list.controls.clear()
        words = database.get_words(self.book_id)
        if not words:
            self.vocab_list.controls.append(ft.Text("Henüz kelime eklenmemiş.", italic=True, color=ft.Colors.GREY))
        else:
            for w in words:
                # w: (id, user_id, book_id, word, definition, sentence, date_added)
                self.vocab_list.controls.append(
                    ft.Container(
                        content=ft.Row([
                            ft.Column([
                                ft.Text(w[3], weight="bold", size=16, color=ft.Colors.CYAN_200),
                                ft.Text(w[4], size=14),
                                ft.Text(f'"{w[5]}"', italic=True, size=12, color=ft.Colors.GREY_400) if w[5] else ft.Container()
                            ], expand=True),
                            ft.IconButton(ft.Icons.DELETE_OUTLINE, icon_size=16, icon_color=ft.Colors.RED_300, on_click=lambda e, wid=w[0]: self.delete_vocab_action(wid))
                        ]),
                        padding=10,
                        bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.WHITE),
                        border_radius=10
                    )
                )
        if update: self.update()

    def add_vocab_action(self, e):
        word = self.vocab_word.value
        definition = self.vocab_def.value
        sentence = self.vocab_sentence.value
        
        if not word: return
        
        database.add_word(self.user_id, self.book_id, word, definition, sentence)
        
        # Award XP for learning new words!
        database.add_xp(self.user_id, 5)
        
        self.vocab_word.value = ""
        self.vocab_def.value = ""
        self.vocab_sentence.value = ""
        self.load_vocab()
        self.page.snack_bar = ft.SnackBar(ft.Text("Kelime eklendi! +5 XP"))
        self.page.snack_bar.open = True
        self.page.update()

    def delete_vocab_action(self, word_id):
        database.delete_word(word_id)
        self.load_vocab()

    def load_tags(self, update=True):
        self.tags_row.controls.clear()
        book_tags = database.get_book_tags(self.book_id)
        for t in book_tags:
            # t: (id, name, color)
            self.tags_row.controls.append(
                ft.Container(
                    content=ft.Row([
                        ft.Text(t[1], color=ft.Colors.WHITE, size=12),
                        ft.GestureDetector(
                            content=ft.Icon(ft.Icons.CLOSE, size=14, color=ft.Colors.WHITE),
                            on_tap=lambda e, tid=t[0]: self.remove_tag_action(tid)
                        )
                    ], spacing=5),
                    bgcolor=t[2] if t[2] else ft.Colors.BLUE,
                    padding=ft.padding.symmetric(horizontal=8, vertical=4),
                    border_radius=10
                )
            )
        if update: self.update()

    def add_tag_action(self, e):
        tag_name = self.tag_input.value.strip()
        if not tag_name: return
        
        # Check if tag exists, if not create it
        # For simplicity, we'll just try to create it and ignore error if exists, then get ID
        # But we need ID.
        # Let's assume create_tag returns ID or None.
        # If None, we need to fetch ID
        
        # First, try to find tag ID
        all_tags = database.get_all_tags()
        tag_id = None
        for t in all_tags:
            if t[1].lower() == tag_name.lower():
                tag_id = t[0]
                break
        
        if not tag_id:
            # Create new tag with random color
            colors = [ft.Colors.RED, ft.Colors.BLUE, ft.Colors.GREEN, ft.Colors.ORANGE, ft.Colors.PURPLE, ft.Colors.TEAL]
            color = random.choice(colors)
            tag_id = database.create_tag(tag_name, color)
            
        if tag_id:
            database.add_tag_to_book(self.book_id, tag_id)
            self.tag_input.value = ""
            self.load_tags()
        else:
            self.page.snack_bar = ft.SnackBar(ft.Text("Etiket eklenemedi."))
            self.page.snack_bar.open = True
            self.page.update()

    def remove_tag_action(self, tag_id):
        database.remove_tag_from_book(self.book_id, tag_id)
        self.load_tags()

    def create_pdf_report(self, e):
        try:
            quotes = database.get_quotes(self.book_id)
            vocab = database.get_words(self.book_id)
            
            # Re-fetch book data to get latest notes/summary
            # Actually self.book might be stale, but we have edit fields values
            # Let's construct a temporary book tuple or just pass values
            # book_data tuple structure:
            # (id, title, author, isbn, cover_url, shelf_id, is_read, rating, notes, summary, ...)
            # We only need title, author, rating, summary, notes for PDF
            
            # Let's update self.book with current values from UI for the PDF
            current_book = list(self.book)
            current_book[1] = self.edit_title.value
            current_book[2] = self.edit_author.value
            current_book[7] = int(self.rating_slider.value)
            current_book[8] = self.edit_notes.value
            current_book[9] = self.edit_summary.value
            
            filename = f"Kitap_Karnesi_{self.book_id}.pdf"
            desktop = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop')
            output_path = os.path.join(desktop, filename)
            
            utils.generate_book_report_pdf(current_book, quotes, vocab, self.edit_notes.value, output_path)
            
            self.page.snack_bar = ft.SnackBar(ft.Text(f"PDF oluşturuldu: {output_path}"), bgcolor=ft.Colors.GREEN_600)
            self.page.snack_bar.open = True
            self.page.update()
            
            # Open PDF
            os.startfile(output_path)
            
        except Exception as ex:
            self.page.snack_bar = ft.SnackBar(ft.Text(f"PDF hatası: {ex}"), bgcolor=ft.Colors.RED_400)
            self.page.snack_bar.open = True
            self.page.update()

class ReadingSessionDialog(ft.AlertDialog):
    def __init__(self, book, on_update):
        super().__init__()
        self.book = book
        self.on_update = on_update
        self.modal = True
        self.title = ft.Text("Okuma Modu", size=20, weight="bold")
        
        self.seconds = 0
        self.is_running = False
        self.is_pomodoro = False
        self.timer_text = ft.Text("00:00:00", size=40, weight="bold", font_family="monospace")
        
        self.pomodoro_btn = ft.ElevatedButton(
            "Pomodoro Modu (25dk)", 
            icon=ft.Icons.TIMER, 
            on_click=self.toggle_pomodoro,
            style=ft.ButtonStyle(bgcolor=ft.Colors.ORANGE_700, color=ft.Colors.WHITE)
        )

        self.current_page = book[15] if len(book) > 15 else 0
        self.page_count = book[10] if len(book) > 10 else 0
        
        self.page_slider = ft.Slider(
            min=0, max=self.page_count if self.page_count > 0 else 1000,
            value=self.current_page,
            label="{value}",
            on_change=self.slider_change
        )
        
        self.page_input = ft.TextField(
            value=str(self.current_page),
            width=80,
            text_align=ft.TextAlign.CENTER,
            on_change=self.input_change
        )
        
        self.content = ft.Container(
            width=400,
            content=ft.Column([
                ft.Text(book[1], size=16, color=ft.Colors.GREY_400),
                ft.Container(height=10),
                self.pomodoro_btn,
                ft.Container(height=10),
                ft.Container(
                    content=self.timer_text,
                    alignment=ft.alignment.center,
                    padding=20,
                    bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.BLUE),
                    border_radius=20
                ),
                ft.Row([
                    ft.IconButton(ft.Icons.PLAY_ARROW_ROUNDED, icon_size=40, on_click=self.toggle_timer, icon_color=ft.Colors.GREEN_400),
                    ft.IconButton(ft.Icons.STOP_ROUNDED, icon_size=40, on_click=self.stop_timer, icon_color=ft.Colors.RED_400),
                ], alignment=ft.MainAxisAlignment.CENTER),
                ft.Divider(),
                ft.Text("İlerleme Durumu", weight="bold"),
                ft.Row([
                    ft.Text("Sayfa:"),
                    self.page_input,
                    ft.Text(f"/ {self.page_count}")
                ], alignment=ft.MainAxisAlignment.CENTER),
                self.page_slider
            ], tight=True)
        )
        
        self.actions = [
            ft.TextButton("Kapat", on_click=self.close_dialog),
            ft.ElevatedButton("Kaydet ve Bitir", on_click=self.save_session)
        ]

    def did_mount(self):
        self.toggle_timer(None) # Auto start

    def toggle_timer(self, e):
        self.is_running = not self.is_running
        if self.is_running:
            self.run_timer()
        self.update()

    def stop_timer(self, e):
        self.is_running = False
        self.update()

    def run_timer(self):
        import time
        import threading
        def timer_loop():
            while self.is_running:
                time.sleep(1)
                if self.is_pomodoro:
                    self.seconds -= 1
                    if self.seconds <= 0:
                        self.is_running = False
                        self.timer_text.value = "00:00:00"
                        self.timer_text.update()
                        # Ideally play sound here
                        break
                else:
                    self.seconds += 1
                    
                mins, secs = divmod(self.seconds, 60)
                hours, mins = divmod(mins, 60)
                self.timer_text.value = f"{hours:02d}:{mins:02d}:{secs:02d}"
                self.timer_text.update()
        threading.Thread(target=timer_loop, daemon=True).start()

    def slider_change(self, e):
        self.page_input.value = str(int(e.control.value))
        self.page_input.update()

    def input_change(self, e):
        try:
            val = int(e.control.value)
            self.page_slider.value = val
            self.page_slider.update()
        except: pass

    def save_session(self, e):
        self.is_running = False
        try:
            new_page = int(self.page_input.value)
            
            # Calculate stats
            pages_read = new_page - self.current_page
            if pages_read < 0: pages_read = 0
            
            duration_minutes = int(self.seconds / 60)
            
            start_time = (datetime.datetime.now() - datetime.timedelta(seconds=self.seconds)).strftime("%Y-%m-%d %H:%M")
            end_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            
            database.update_book_progress(self.book[0], new_page)
            database.add_reading_session(self.book[0], start_time, end_time, duration_minutes, pages_read)
            
            # Award XP
            xp_earned = (pages_read * 2) + duration_minutes
            user_id = self.book[19] if len(self.book) > 19 else 1
            database.add_xp(user_id, xp_earned)
            
            self.page.snack_bar = ft.SnackBar(ft.Text(f"Oturum kaydedildi: {duration_minutes} dk, {pages_read} sayfa. +{xp_earned} XP!"))
            self.page.snack_bar.open = True
            self.page.update()

        except Exception as ex:
            print(ex)
            
        self.on_update() # Refresh dashboard
        self.page.close(self)

    def close_dialog(self, e):
        self.is_running = False
        self.page.close(self)

    def toggle_pomodoro(self, e):
        if self.is_running: return # Don't toggle while running
        
        self.is_pomodoro = not self.is_pomodoro
        if self.is_pomodoro:
            self.pomodoro_btn.text = "Serbest Mod"
            self.pomodoro_btn.style.bgcolor = ft.Colors.BLUE_GREY_700
            self.seconds = 25 * 60
            self.timer_text.value = "00:25:00"
        else:
            self.pomodoro_btn.text = "Pomodoro Modu (25dk)"
            self.pomodoro_btn.style.bgcolor = ft.Colors.ORANGE_700
            self.seconds = 0
            self.timer_text.value = "00:00:00"
        self.pomodoro_btn.update()
        self.timer_text.update()

class Dashboard(ft.Column):
    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id
        self.expand = True
        self.scroll = ft.ScrollMode.HIDDEN
        
        self.stats_row = ft.Row(spacing=20)
        
        # Search and Filter
        self.search_field = ft.TextField(
            label="Kütüphanede ara...", 
            prefix_icon=ft.Icons.SEARCH,
            border_radius=12,
            bgcolor=ft.Colors.ON_INVERSE_SURFACE,
            border_color=ft.Colors.TRANSPARENT,
            expand=True,
            on_change=self.filter_books
        )
        
        self.filter_dropdown = ft.Dropdown(
            width=150,
            label="Filtre",
            border_radius=12,
            bgcolor=ft.Colors.ON_INVERSE_SURFACE,
            border_color=ft.Colors.TRANSPARENT,
            options=[
                ft.dropdown.Option("Tümü"),
                ft.dropdown.Option("Okunacak"),
                ft.dropdown.Option("Okunuyor"),
                ft.dropdown.Option("Okundu"),
                ft.dropdown.Option("Ödünç Verilen"),
            ],
            value="Tümü",
            on_change=self.filter_books
        )

        self.sort_dropdown = ft.Dropdown(
            width=180,
            label="Sıralama",
            border_radius=12,
            bgcolor=ft.Colors.ON_INVERSE_SURFACE,
            border_color=ft.Colors.TRANSPARENT,
            options=[
                ft.dropdown.Option("Eklenme (Yeni-Eski)"),
                ft.dropdown.Option("Eklenme (Eski-Yeni)"),
                ft.dropdown.Option("Başlık (A-Z)"),
                ft.dropdown.Option("Başlık (Z-A)"),
                ft.dropdown.Option("Puan (Yüksek-Düşük)"),
            ],
            value="Eklenme (Yeni-Eski)",
            on_change=self.filter_books
        )

        self.export_btn = ft.IconButton(
            icon=ft.Icons.DOWNLOAD_ROUNDED,
            tooltip="Kütüphaneyi Excel/CSV Olarak İndir",
            on_click=self.export_library
        )

        self.import_btn = ft.IconButton(
            icon=ft.Icons.UPLOAD_FILE,
            tooltip="Kitapları İçe Aktar (CSV)",
            on_click=self.import_library_dialog
        )

        self.random_btn = ft.IconButton(
            icon=ft.Icons.SHUFFLE_ROUNDED,
            tooltip="Rastgele Kitap Seç",
            icon_color=ft.Colors.PURPLE_300,
            on_click=self.pick_random_book
        )

        self.recommend_btn = ft.IconButton(
            icon=ft.Icons.AUTO_AWESOME,
            tooltip="Yapay Zeka Önerisi Al",
            icon_color=ft.Colors.AMBER_400,
            on_click=self.show_recommendations
        )

        self.help_box = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.INFO_OUTLINE, color=ft.Colors.BLUE_200),
                ft.Text(
                    "Burada kütüphanenizdeki tüm kitapları görebilirsiniz. Kitapları arayabilir, okuma durumuna göre filtreleyebilir ve detaylarını düzenlemek için kitap kapaklarına tıklayabilirsiniz.",
                    size=12, color=ft.Colors.GREY_400, expand=True
                )
            ]),
            padding=10,
            bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.BLUE),
            border_radius=10,
            margin=ft.margin.only(bottom=10)
        )

        self.books_grid = ft.GridView(
            expand=1,
            runs_count=5,
            max_extent=250,
            child_aspect_ratio=0.7,
            spacing=20,
            run_spacing=20,
        )
        
        self.controls = [
            ft.Container(
                content=ft.Column([
                    ft.Text("Panel", size=32, weight=ft.FontWeight.BOLD),
                    self.help_box,
                    ft.Row([self.search_field, self.filter_dropdown, self.sort_dropdown, self.random_btn, self.recommend_btn, self.import_btn, self.export_btn]),
                ]),
                margin=ft.margin.only(bottom=20)
            ),
            self.stats_row,
            ft.Divider(height=30, color=ft.Colors.TRANSPARENT),
            ft.Text("Koleksiyonunuz", size=20, weight=ft.FontWeight.W_600),
            ft.Container(height=10),
            self.books_grid
        ]
        
        self.all_books = []
        self.reading_goal = database.get_user_goal(self.user_id)

    def did_mount(self):
        self.load_books()

    def pick_random_book(self, e):
        unread_books = [b for b in self.all_books if len(b) > 14 and b[14] == "Okunacak"]
        if not unread_books:
            self.page.snack_bar = ft.SnackBar(ft.Text("Okunacak kitap bulunamadı!"))
            self.page.snack_bar.open = True
            self.page.update()
            return
            
        book = random.choice(unread_books)
        self.open_book_details(book)
        self.page.snack_bar = ft.SnackBar(ft.Text(f"Öneri: {book[1]}"))
        self.page.snack_bar.open = True
        self.page.update()

    def edit_goal(self, e):
        def save_goal(e):
            try:
                new_goal = int(goal_field.value)
                database.update_user_goal(self.user_id, new_goal)
                self.reading_goal = new_goal
                self.page.close(dialog)
                self.load_books() # Refresh stats
            except ValueError:
                pass

        goal_field = ft.TextField(label="Yıllık Hedef", value=str(self.reading_goal), keyboard_type=ft.KeyboardType.NUMBER)
        dialog = ft.AlertDialog(
            title=ft.Text("Okuma Hedefi Belirle"),
            content=goal_field,
            actions=[
                ft.TextButton("İptal", on_click=lambda e: self.page.close(dialog)),
                ft.ElevatedButton("Kaydet", on_click=save_goal)
            ]
        )
        self.page.open(dialog)

    def load_books(self):
        self.all_books = database.get_books(self.user_id)
        self.filter_books(None) # Apply sort and filter

    def filter_books(self, e):
        search_term = self.search_field.value.lower() if self.search_field.value else ""
        filter_type = self.filter_dropdown.value
        sort_type = self.sort_dropdown.value
        
        filtered_books = []
        for book in self.all_books:
            # book: (id, title, author, isbn, cover_url, shelf_id, is_read, rating, notes, summary, page_count, publisher, borrower_name, borrow_date, status, current_page, ...)
            title = book[1].lower() if book[1] else ""
            author = book[2].lower() if book[2] else ""
            status = book[14] if len(book) > 14 else "Okunacak"
            borrower = book[12] if len(book) > 12 else ""
            
            matches_search = search_term in title or search_term in author
            matches_filter = True
            
            if filter_type == "Okunacak":
                matches_filter = (status == "Okunacak")
            elif filter_type == "Okunuyor":
                matches_filter = (status == "Okunuyor")
            elif filter_type == "Okundu":
                matches_filter = (status == "Okundu")
            elif filter_type == "Ödünç Verilen":
                matches_filter = (borrower != "")
                
            if matches_search and matches_filter:
                filtered_books.append(book)
        
        # Sorting
        if sort_type == "Eklenme (Yeni-Eski)":
            filtered_books.sort(key=lambda x: x[0], reverse=True)
        elif sort_type == "Eklenme (Eski-Yeni)":
            filtered_books.sort(key=lambda x: x[0])
        elif sort_type == "Başlık (A-Z)":
            filtered_books.sort(key=lambda x: x[1].lower() if x[1] else "")
        elif sort_type == "Başlık (Z-A)":
            filtered_books.sort(key=lambda x: x[1].lower() if x[1] else "", reverse=True)
        elif sort_type == "Puan (Yüksek-Düşük)":
            filtered_books.sort(key=lambda x: x[7] if len(x) > 7 and x[7] is not None else 0, reverse=True)

        self.render_books(filtered_books)

    def render_books(self, books):
        self.books_grid.controls.clear()
        for book in books:
            # book: (id, title, author, isbn, cover_url, shelf_id, is_read, rating, notes, summary, page_count, publisher, borrower_name, borrow_date, status, current_page, ...)
            
            # Calculate progress
            page_count = book[10] if len(book) > 10 and book[10] else 0
            current_page = book[15] if len(book) > 15 and book[15] else 0
            progress = 0
            if page_count > 0:
                progress = min(current_page / page_count, 1.0)
                
            status = book[14] if len(book) > 14 else "Okunacak"
            status_color = ft.Colors.GREY
            if status == "Okunuyor": status_color = ft.Colors.ORANGE
            elif status == "Okundu": status_color = ft.Colors.GREEN
            
            card = ft.Container(
                content=ft.Column([
                    ft.Container(
                        content=ft.Image(
                            src=book[4] if book[4] else "https://via.placeholder.com/150",
                            fit=ft.ImageFit.COVER,
                            border_radius=10,
                        ),
                        expand=True,
                        clip_behavior=ft.ClipBehavior.HARD_EDGE,
                        border_radius=10,
                        shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.with_opacity(0.3, ft.Colors.BLACK))
                    ),
                    ft.Container(height=5),
                    ft.Text(book[1], weight="bold", size=14, no_wrap=True, overflow=ft.TextOverflow.ELLIPSIS),
                    ft.Text(book[2], size=12, color=ft.Colors.GREY_400, no_wrap=True, overflow=ft.TextOverflow.ELLIPSIS),
                    ft.ProgressBar(value=progress, color=status_color, bgcolor=ft.Colors.GREY_800, height=4),
                    ft.Row([
                        ft.Icon(ft.Icons.CIRCLE, size=10, color=status_color),
                        ft.Text(status, size=10, color=status_color)
                    ], spacing=5)
                ], spacing=2),
                padding=10,
                bgcolor=ft.Colors.ON_INVERSE_SURFACE,
                border_radius=15,
                on_click=lambda e, b=book: self.open_book_details(b)
            )
            self.books_grid.controls.append(card)
        self.update()

    def open_book_details(self, book):
        print(f"Opening details for book: {book[1]}")
        try:
            dialog = BookDetailsDialog(book, self.load_books, self.user_id)
            self.page.open(dialog)
        except Exception as e:
            print(f"Error opening book details: {e}")
            self.page.snack_bar = ft.SnackBar(ft.Text(f"Hata: {e}"))
            self.page.snack_bar.open = True
            self.page.update()

    def export_library(self, e):
        import csv
        import os
        
        try:
            desktop = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop')
            filename = os.path.join(desktop, f"kutuphane_yedek_{self.user_id}.csv")
            
            with open(filename, 'w', newline='', encoding='utf-8-sig') as file:
                writer = csv.writer(file)
                writer.writerow(["ID", "Başlık", "Yazar", "ISBN", "Raf ID", "Puan", "Notlar", "Özet", "Sayfa Sayısı", "Yayınevi", "Durum", "Başlangıç", "Bitiş", "Dosya Yolu"])
                
                for book in self.all_books:
                    # Map indices carefully
                    writer.writerow([
                        book[0], book[1], book[2], book[3], book[5], 
                        book[7], book[8], book[9], book[10], book[11], 
                        book[14], book[16], book[17],
                        book[20] if len(book) > 20 else ""
                    ])
            
            self.page.snack_bar = ft.SnackBar(ft.Text(f"Kütüphane dışa aktarıldı: {filename}"), bgcolor=ft.Colors.GREEN_600)
            self.page.snack_bar.open = True
            self.page.update()
            
        except Exception as ex:
            self.page.snack_bar = ft.SnackBar(ft.Text(f"Hata: {ex}"), bgcolor=ft.Colors.RED_400)
            self.page.snack_bar.open = True
            self.page.update()

    def import_library_dialog(self, e):
        def on_result(e: ft.FilePickerResultEvent):
            if e.files:
                self.import_csv(e.files[0].path)
        
        picker = ft.FilePicker(on_result=on_result)
        self.page.overlay.append(picker)
        self.page.update()
        picker.pick_files(allow_multiple=False, allowed_extensions=["csv"])

    def import_csv(self, file_path):
        try:
            count = 0
            skipped = 0
            
            # Detect encoding
            encoding = 'utf-8'
            try:
                with open(file_path, 'r', encoding='utf-8') as f: f.read()
            except UnicodeDecodeError:
                encoding = 'cp1254' # Turkish Windows encoding
            
            with open(file_path, mode='r', encoding=encoding) as csv_file:
                # Check if it has header
                sample = csv_file.read(1024)
                csv_file.seek(0)
                has_header = csv.Sniffer().has_header(sample)
                
                reader = csv.reader(csv_file)
                if has_header:
                    header = next(reader)
                    # Try to map columns if possible, otherwise assume order: Title, Author, ISBN...
                    # Simple mapping: 0=Title, 1=Author
                
                for row in reader:
                    if len(row) < 2: continue
                    
                    title = row[0].strip()
                    author = row[1].strip()
                    isbn = row[2].strip() if len(row) > 2 else ""
                    publisher = row[3].strip() if len(row) > 3 else ""
                    page_count = int(row[4]) if len(row) > 4 and row[4].isdigit() else 0
                    status = row[5].strip() if len(row) > 5 else "Okunacak"
                    
                    if not title: continue
                    
                    if not database.book_exists(self.user_id, title, author):
                        # Get default shelf
                        shelves = database.get_shelves(self.user_id)
                        shelf_id = shelves[0][0] if shelves else 1
                        
                        database.add_book(
                            title, author, isbn, "", shelf_id, self.user_id, 
                            page_count=page_count, publisher=publisher, status=status
                        )
                        count += 1
                    else:
                        skipped += 1
                        
            self.page.snack_bar = ft.SnackBar(ft.Text(f"İçe aktarma tamamlandı: {count} eklendi, {skipped} atlandı."), bgcolor=ft.Colors.GREEN_600)
            self.page.snack_bar.open = True
            self.load_books()
            self.page.update()
            
        except Exception as ex:
            self.page.snack_bar = ft.SnackBar(ft.Text(f"Hata: {ex}"), bgcolor=ft.Colors.RED_400)
            self.page.snack_bar.open = True
            self.page.update()

    def show_recommendations(self, e):
        # 1. Get user's top rated books
        all_books = database.get_books(self.user_id)
        # Filter books with rating >= 4
        favorites = [b for b in all_books if len(b) > 7 and b[7] is not None and b[7] >= 4]
        
        if not favorites:
            # Fallback to any read book
            favorites = [b for b in all_books if len(b) > 14 and b[14] == "Okundu"]
            
        query = ""
        reason = ""
        
        if favorites:
            fav_book = random.choice(favorites)
            # Search for author
            author = fav_book[2]
            title = fav_book[1]
            query = f"inauthor:{author}"
            reason = f"Çünkü '{title}' kitabını beğendin."
        else:
            # Generic recommendation
            genres = ["Bilim Kurgu", "Roman", "Tarih", "Kişisel Gelişim", "Felsefe"]
            genre = random.choice(genres)
            query = f"subject:{genre}"
            reason = f"Popüler {genre} kitaplarından bir öneri."
            
        # Show loading
        self.page.snack_bar = ft.SnackBar(ft.Text("Yapay zeka kitap arıyor..."))
        self.page.snack_bar.open = True
        self.page.update()
        
        # Fetch from API
        # We use search_books but we need to filter out books user already has
        results = api.search_books(query)
        
        # Filter
        my_titles = [b[1].lower() for b in all_books]
        recommendations = []
        for r in results:
            if r['title'].lower() not in my_titles:
                recommendations.append(r)
                if len(recommendations) >= 3: break
        
        if not recommendations:
            self.page.snack_bar = ft.SnackBar(ft.Text("Öneri bulunamadı, tekrar deneyin."))
            self.page.snack_bar.open = True
            self.page.update()
            return
            
        # Show Dialog
        content = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO, height=400)
        content.controls.append(ft.Text(reason, italic=True, color=ft.Colors.AMBER_400))
        
        for book in recommendations:
            content.controls.append(
                ft.Container(
                    content=ft.Row([
                        ft.Image(src=book['cover_url'] if book['cover_url'] else "https://via.placeholder.com/100", width=60, height=90, fit=ft.ImageFit.COVER),
                        ft.Column([
                            ft.Text(book['title'], weight="bold", width=200, no_wrap=True, overflow=ft.TextOverflow.ELLIPSIS),
                            ft.Text(book['author'], size=12, color=ft.Colors.GREY_400),
                            ft.ElevatedButton("İncele", on_click=lambda e, b=book: self.open_recommendation_details(b), height=30)
                        ], spacing=2)
                    ]),
                    padding=10,
                    bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.WHITE),
                    border_radius=10
                )
            )
            
        dialog = ft.AlertDialog(
            title=ft.Text("Sizin İçin Öneriler"),
            content=content,
            actions=[ft.TextButton("Kapat", on_click=lambda e: self.page.close(dialog))]
        )
        self.page.open(dialog)

    def open_recommendation_details(self, book_data):
        # Reuse AddBook logic or show simple details
        # Let's show a simple dialog with "Add to Library" button
        
        def add_rec(e):
            # Add to library
            shelves = database.get_shelves(self.user_id)
            shelf_id = shelves[0][0] if shelves else 1
            
            database.add_book(
                book_data["title"],
                book_data["author"],
                book_data["isbn"],
                book_data["cover_url"],
                shelf_id,
                self.user_id,
                book_data.get("summary"),
                book_data.get("page_count"),
                book_data.get("publisher"),
                "Okunacak"
            )
            self.page.snack_bar = ft.SnackBar(ft.Text("Kitap eklendi!"))
            self.page.snack_bar.open = True
            self.load_books()
            self.page.close(rec_dialog)
            self.page.update()

        rec_dialog = ft.AlertDialog(
            title=ft.Text(book_data['title']),
            content=ft.Column([
                ft.Image(src=book_data['cover_url'], height=200),
                ft.Text(f"Yazar: {book_data['author']}"),
                ft.Text(f"Özet: {book_data['summary'][:200]}..." if book_data['summary'] else "Özet yok."),
            ], tight=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            actions=[
                ft.TextButton("Kapat", on_click=lambda e: self.page.close(rec_dialog)),
                ft.ElevatedButton("Kütüphaneme Ekle", on_click=add_rec, bgcolor=ft.Colors.TEAL_600, color=ft.Colors.WHITE)
            ]
        )
        self.page.open(rec_dialog)

    def create_stat_card(self, title, value, icon, color):
        return ft.Container(
            content=ft.Row([
                ft.Container(
                    content=ft.Icon(icon, color=color, size=24),
                    padding=12,
                    bgcolor=ft.Colors.with_opacity(0.1, color),
                    border_radius=12,
                ),
                ft.Column([
                    ft.Text(title, size=11, color=ft.Colors.GREY_400),
                    ft.Text(value, size=20, weight="bold")
                ], spacing=0)
            ], alignment=ft.MainAxisAlignment.START),
            padding=15,
            bgcolor=ft.Colors.ON_INVERSE_SURFACE,
            border_radius=15,
            expand=True,
        )

    def on_card_hover(self, e):
        e.control.scale = 1.02 if e.data == "true" else 1.0
        e.control.update()

    def toggle_read(self, book_id, current_status):
        # Deprecated in favor of status field, but kept for compatibility if needed
        pass

    def delete_book(self, book_id):
        database.delete_book(book_id)
        self.load_books()

    def render_books(self, books):
        self.books_grid.controls.clear()
        for book in books:
            # book: (id, title, author, isbn, cover_url, shelf_id, is_read, rating, notes, summary, page_count, publisher, borrower_name, borrow_date, status, current_page, ...)
            
            # Calculate progress
            page_count = book[10] if len(book) > 10 and book[10] else 0
            current_page = book[15] if len(book) > 15 and book[15] else 0
            progress = 0
            if page_count > 0:
                progress = min(current_page / page_count, 1.0)
                
            status = book[14] if len(book) > 14 else "Okunacak"
            status_color = ft.Colors.GREY
            if status == "Okunuyor": status_color = ft.Colors.ORANGE
            elif status == "Okundu": status_color = ft.Colors.GREEN
            
            card = ft.Container(
                content=ft.Column([
                    ft.Container(
                        content=ft.Image(
                            src=book[4] if book[4] else "https://via.placeholder.com/150",
                            fit=ft.ImageFit.COVER,
                            border_radius=10,
                        ),
                        expand=True,
                        clip_behavior=ft.ClipBehavior.HARD_EDGE,
                        border_radius=10,
                        shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.with_opacity(0.3, ft.Colors.BLACK))
                    ),
                    ft.Container(height=5),
                    ft.Text(book[1], weight="bold", size=14, no_wrap=True, overflow=ft.TextOverflow.ELLIPSIS),
                    ft.Text(book[2], size=12, color=ft.Colors.GREY_400, no_wrap=True, overflow=ft.TextOverflow.ELLIPSIS),
                    ft.ProgressBar(value=progress, color=status_color, bgcolor=ft.Colors.GREY_800, height=4),
                    ft.Row([
                        ft.Icon(ft.Icons.CIRCLE, size=10, color=status_color),
                        ft.Text(status, size=10, color=status_color)
                    ], spacing=5)
                ], spacing=2),
                padding=10,
                bgcolor=ft.Colors.ON_INVERSE_SURFACE,
                border_radius=15,
                on_click=lambda e, b=book: self.open_book_details(b)
            )
            self.books_grid.controls.append(card)
        self.update()

    def open_book_details(self, book):
        print(f"Opening details for book: {book[1]}")
        try:
            dialog = BookDetailsDialog(book, self.load_books, self.user_id)
            self.page.open(dialog)
        except Exception as e:
            print(f"Error opening book details: {e}")
            self.page.snack_bar = ft.SnackBar(ft.Text(f"Hata: {e}"))
            self.page.snack_bar.open = True
            self.page.update()

