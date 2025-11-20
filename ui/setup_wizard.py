import flet as ft
import database

class SetupWizard(ft.Container):
    def __init__(self, page: ft.Page, on_complete):
        super().__init__()
        self.page = page
        self.on_complete = on_complete
        self.expand = True
        self.alignment = ft.alignment.center
        
        self.current_step = 0
        
        # Step 1: Welcome
        self.step1 = ft.Column(
            [
                ft.Icon(ft.Icons.LIBRARY_BOOKS_ROUNDED, size=80, color=ft.Colors.TEAL_400),
                ft.Text("Libris'e Hoşgeldiniz", size=40, weight=ft.FontWeight.BOLD, color=ft.Colors.TEAL_400),
                ft.Text("Kişisel kütüphanenizi yönetmenin en modern yolu.", size=16, color=ft.Colors.GREY_400),
                ft.Container(height=20),
                ft.ElevatedButton(
                    "Başlayalım", 
                    on_click=self.next_step,
                    style=ft.ButtonStyle(
                        padding=20,
                        shape=ft.RoundedRectangleBorder(radius=10),
                        bgcolor=ft.Colors.TEAL_600,
                        color=ft.Colors.WHITE
                    )
                )
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=10
        )
        
        # Step 2: Personalization
        self.name_field = ft.TextField(label="Adınız", border_radius=10, prefix_icon=ft.Icons.PERSON)
        
        self.step2 = ft.Column(
            [
                ft.Text("Sizi Tanıyalım", size=30, weight=ft.FontWeight.BOLD),
                ft.Text("Size nasıl hitap edelim?", color=ft.Colors.GREY_400),
                ft.Container(height=20),
                ft.Container(content=self.name_field, width=300),
                ft.Container(height=20),
                ft.ElevatedButton(
                    "Devam Et", 
                    on_click=self.save_name,
                    style=ft.ButtonStyle(
                        padding=20,
                        shape=ft.RoundedRectangleBorder(radius=10),
                        bgcolor=ft.Colors.TEAL_600,
                        color=ft.Colors.WHITE
                    )
                )
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER
        )
        
        # Step 3: Goals
        self.goal_slider = ft.Slider(min=1, max=100, divisions=99, value=20, label="{value} Kitap")
        
        self.step3 = ft.Column(
            [
                ft.Icon(ft.Icons.TRACK_CHANGES, size=60, color=ft.Colors.ORANGE_400),
                ft.Text("Okuma Hedefi", size=30, weight=ft.FontWeight.BOLD),
                ft.Text("Bu yıl kaç kitap okumayı hedefliyorsunuz?", color=ft.Colors.GREY_400),
                ft.Container(height=30),
                ft.Container(content=self.goal_slider, width=400),
                ft.Container(height=20),
                ft.ElevatedButton(
                    "Kurulumu Tamamla", 
                    on_click=self.finish_setup,
                    style=ft.ButtonStyle(
                        padding=20,
                        shape=ft.RoundedRectangleBorder(radius=10),
                        bgcolor=ft.Colors.TEAL_600,
                        color=ft.Colors.WHITE
                    )
                )
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER
        )
        
        self.content = self.step1

    def next_step(self, e):
        self.current_step += 1
        self.update_view()

    def update_view(self):
        if self.current_step == 0:
            self.content = self.step1
        elif self.current_step == 1:
            self.content = self.step2
        elif self.current_step == 2:
            self.content = self.step3
        self.update()

    def save_name(self, e):
        name = self.name_field.value
        if not name:
            self.page.snack_bar = ft.SnackBar(ft.Text("Lütfen bir isim girin!"))
            self.page.snack_bar.open = True
            self.page.update()
            return
            
        # Create default user if not exists
        # We use a fixed username 'default' but display name is what user entered
        # For simplicity, we'll store the display name as the username in the DB
        # and use a dummy password.
        
        if not database.get_user(name):
            database.add_user(name, "nopassword")
        
        self.user = database.get_user(name)
        self.next_step(e)

    def finish_setup(self, e):
        # Save goal
        goal = int(self.goal_slider.value)
        database.update_reading_goal(self.user[0], goal)
        
        # Create default shelves
        database.add_shelf("Okunacaklar", "Henüz başlamadığım kitaplar", self.user[0])
        database.add_shelf("Okuyorum", "Şu an okuduğum kitaplar", self.user[0])
        database.add_shelf("Okundu", "Bitirdiğim kitaplar", self.user[0])
        database.add_shelf("Favoriler", "En sevdiğim kitaplar", self.user[0])
        
        self.on_complete(self.user)
