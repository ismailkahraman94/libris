import flet as ft
import database
from ui.app_layout import AppLayout
from ui.dashboard import Dashboard
from ui.add_book import AddBook
from ui.shelves import Shelves
from ui.ebooks import EBooks
from ui.stats import Statistics
from ui.setup_wizard import SetupWizard

def main(page: ft.Page):
    page.title = "Libris"
    page.theme_mode = ft.ThemeMode.DARK
    page.theme = ft.Theme(
        color_scheme_seed=ft.Colors.TEAL,
        visual_density=ft.VisualDensity.ADAPTIVE_PLATFORM_DENSITY,
    )
    page.padding = 0
    page.window_min_width = 1000
    page.window_min_height = 700
    
    # Initialize Database
    database.init_db()

    class LibraryApp:
        def __init__(self, page):
            self.page = page
            self.user = None
            
            # Check if any users exist
            users = database.get_all_users()
            if not users:
                self.show_setup_wizard()
            else:
                # Auto login the first user found
                self.login_success(users[0])

        def show_setup_wizard(self):
            self.page.clean()
            self.setup_wizard = SetupWizard(self.page, self.login_success)
            self.page.add(self.setup_wizard)
            self.page.update()

        def login_success(self, user):
            self.user = user
            self.user_id = user[0]
            self.username = user[1]
            
            # Initialize views with user_id
            self.dashboard = Dashboard(self.user_id)
            self.add_book = AddBook(self.user_id)
            self.shelves = Shelves(self.user_id)
            self.ebooks = EBooks(self.user_id)
            self.stats = Statistics(self.user_id)
            
            self.page.clean()
            self.layout = AppLayout(self, self.page)
            self.page.add(self.layout)
            self.set_page(0)
            
            self.page.snack_bar = ft.SnackBar(ft.Text(f"Hoş geldin, {self.username}!"))
            self.page.snack_bar.open = True
            self.page.update()

        def set_page(self, index):
            self.layout.content_area.content = [
                self.dashboard,
                self.add_book,
                self.shelves,
                self.ebooks,
                self.stats
            ][index]
            self.layout.content_area.update()
            
            # Refresh data when switching tabs
            if index == 0:
                self.dashboard.load_books()
            elif index == 1:
                self.add_book.load_shelves()
            elif index == 2:
                self.shelves.load_shelves()
            elif index == 3:
                self.ebooks.load_ebooks()
            elif index == 4:
                self.stats.load_stats()


    app = LibraryApp(page)

if __name__ == "__main__":
    ft.app(target=main)
