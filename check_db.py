import database

database.init_db()
shelves = database.get_shelves()
print(f"Shelves: {shelves}")

if not shelves:
    print("No shelves found. Creating a default shelf.")
    database.add_shelf("Genel", "Varsayılan raf")
    print("Default shelf created.")
