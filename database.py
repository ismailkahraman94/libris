import sqlite3
import hashlib

def create_connection():
    conn = None
    try:
        conn = sqlite3.connect('library.db')
        return conn
    except sqlite3.Error as e:
        print(e)
    return conn

def create_table(conn, create_table_sql):
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
    except sqlite3.Error as e:
        print(e)

def add_user_columns():
    conn = create_connection()
    c = conn.cursor()
    try:
        c.execute("ALTER TABLE users ADD COLUMN reading_goal INTEGER DEFAULT 20")
    except sqlite3.OperationalError:
        pass
    conn.commit()
    conn.close()

def init_db():
    database = "library.db"

    sql_create_users_table = """ CREATE TABLE IF NOT EXISTS users (
                                    id integer PRIMARY KEY,
                                    username text NOT NULL UNIQUE,
                                    password text NOT NULL,
                                    reading_goal integer DEFAULT 20,
                                    xp integer DEFAULT 0
                                ); """

    sql_create_shelves_table = """ CREATE TABLE IF NOT EXISTS shelves (
                                        id integer PRIMARY KEY,
                                        name text NOT NULL,
                                        description text,
                                        user_id integer,
                                        FOREIGN KEY (user_id) REFERENCES users (id)
                                    ); """

    sql_create_books_table = """ CREATE TABLE IF NOT EXISTS books (
                                    id integer PRIMARY KEY,
                                    title text NOT NULL,
                                    author text,
                                    isbn text,
                                    cover_url text,
                                    shelf_id integer,
                                    is_read integer DEFAULT 0,
                                    rating integer DEFAULT 0,
                                    notes text,
                                    summary text,
                                    page_count integer,
                                    publisher text,
                                    borrower_name text,
                                    borrow_date text,
                                    status text DEFAULT 'Okunacak',
                                    current_page integer DEFAULT 0,
                                    start_date text,
                                    finish_date text,
                                    link text,
                                    user_id integer,
                                    file_path text,
                                    FOREIGN KEY (shelf_id) REFERENCES shelves (id),
                                    FOREIGN KEY (user_id) REFERENCES users (id)
                                ); """

    sql_create_quotes_table = """ CREATE TABLE IF NOT EXISTS quotes (
                                    id integer PRIMARY KEY,
                                    book_id integer,
                                    text text NOT NULL,
                                    page_number integer,
                                    FOREIGN KEY (book_id) REFERENCES books (id) ON DELETE CASCADE
                                ); """

    sql_create_sessions_table = """ CREATE TABLE IF NOT EXISTS reading_sessions (
                                    id integer PRIMARY KEY,
                                    book_id integer,
                                    start_time text,
                                    end_time text,
                                    duration_minutes integer,
                                    pages_read integer,
                                    FOREIGN KEY (book_id) REFERENCES books (id) ON DELETE CASCADE
                                ); """

    sql_create_vocabulary_table = """ CREATE TABLE IF NOT EXISTS vocabulary (
                                    id integer PRIMARY KEY,
                                    user_id integer,
                                    book_id integer,
                                    word text NOT NULL,
                                    definition text,
                                    sentence text,
                                    date_added text,
                                    FOREIGN KEY (user_id) REFERENCES users (id),
                                    FOREIGN KEY (book_id) REFERENCES books (id) ON DELETE CASCADE
                                ); """

    sql_create_tags_table = """ CREATE TABLE IF NOT EXISTS tags (
                                    id integer PRIMARY KEY,
                                    name text NOT NULL UNIQUE,
                                    color text
                                ); """

    sql_create_book_tags_table = """ CREATE TABLE IF NOT EXISTS book_tags (
                                    book_id integer,
                                    tag_id integer,
                                    FOREIGN KEY (book_id) REFERENCES books (id) ON DELETE CASCADE,
                                    FOREIGN KEY (tag_id) REFERENCES tags (id) ON DELETE CASCADE,
                                    PRIMARY KEY (book_id, tag_id)
                                ); """

    conn = create_connection()

    if conn is not None:
        create_table(conn, sql_create_users_table)
        create_table(conn, sql_create_shelves_table)
        create_table(conn, sql_create_books_table)
        create_table(conn, sql_create_quotes_table)
        create_table(conn, sql_create_sessions_table)
        create_table(conn, sql_create_vocabulary_table)
        create_table(conn, sql_create_tags_table)
        create_table(conn, sql_create_book_tags_table)
        
        # Migrations
        migrate_db(conn)
        add_user_columns()
        add_xp_column()
        
        conn.close()
    else:
        print("Error! cannot create the database connection.")

def migrate_db(conn):
    c = conn.cursor()
    
    # Check for user_id in shelves
    try:
        c.execute("SELECT user_id FROM shelves LIMIT 1")
    except sqlite3.OperationalError:
        try:
            c.execute("ALTER TABLE shelves ADD COLUMN user_id integer")
            print("Added user_id to shelves")
        except: pass

    # Check for user_id in books
    try:
        c.execute("SELECT user_id FROM books LIMIT 1")
    except sqlite3.OperationalError:
        try:
            c.execute("ALTER TABLE books ADD COLUMN user_id integer")
            print("Added user_id to books")
        except: pass

    # Check for file_path in books
    try:
        c.execute("SELECT file_path FROM books LIMIT 1")
    except sqlite3.OperationalError:
        try:
            c.execute("ALTER TABLE books ADD COLUMN file_path text")
            print("Added file_path to books")
        except: pass

    columns = [
        ("is_read", "integer DEFAULT 0"),
        ("rating", "integer DEFAULT 0"),
        ("notes", "text"),
        ("summary", "text"),
        ("page_count", "integer"),
        ("publisher", "text"),
        ("borrower_name", "text"),
        ("borrow_date", "text"),
        ("status", "text DEFAULT 'Okunacak'"),
        ("current_page", "integer DEFAULT 0"),
        ("start_date", "text"),
        ("finish_date", "text"),
        ("link", "text"),
        ("file_path", "text")
    ]
    
    for col_name, col_type in columns:
        try:
            c.execute(f"ALTER TABLE books ADD COLUMN {col_name} {col_type}")
            print(f"Added column {col_name}")
        except sqlite3.OperationalError:
            pass # Column likely exists
    
    conn.commit()

def register_user(username):
    conn = create_connection()
    # Password is no longer used, storing empty string for compatibility
    try:
        sql = ''' INSERT INTO users(username, password) VALUES(?,?) '''
        cur = conn.cursor()
        cur.execute(sql, (username, ""))
        conn.commit()
        user_id = cur.lastrowid
        
        # Assign orphan data to first user
        if user_id == 1:
            cur.execute("UPDATE shelves SET user_id = ? WHERE user_id IS NULL", (user_id,))
            cur.execute("UPDATE books SET user_id = ? WHERE user_id IS NULL", (user_id,))
            conn.commit()
            
        conn.close()
        return user_id
    except sqlite3.IntegrityError:
        conn.close()
        return None

def login_user(username):
    conn = create_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE username=?", (username,))
    user = cur.fetchone()
    conn.close()
    return user

def get_all_users():
    conn = create_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM users")
    users = c.fetchall()
    conn.close()
    return users

def update_reading_goal(user_id, goal):
    conn = create_connection()
    c = conn.cursor()
    try:
        c.execute("UPDATE users SET reading_goal = ? WHERE id = ?", (goal, user_id))
        conn.commit()
    except sqlite3.Error as e:
        print(e)
    finally:
        conn.close()

def delete_user(user_id):
    conn = create_connection()
    cur = conn.cursor()
    # Delete user's books and shelves first (cascade manually if needed)
    cur.execute("DELETE FROM books WHERE user_id=?", (user_id,))
    cur.execute("DELETE FROM shelves WHERE user_id=?", (user_id,))
    cur.execute("DELETE FROM users WHERE id=?", (user_id,))
    conn.commit()
    conn.close()

def add_shelf(name, description, user_id):
    conn = create_connection()
    sql = ''' INSERT INTO shelves(name,description,user_id)
              VALUES(?,?,?) '''
    cur = conn.cursor()
    cur.execute(sql, (name, description, user_id))
    conn.commit()
    conn.close()
    return cur.lastrowid

def get_shelves(user_id):
    conn = create_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM shelves WHERE user_id=?", (user_id,))
    rows = cur.fetchall()
    conn.close()
    return rows

def delete_shelf(id):
    conn = create_connection()
    sql = 'DELETE FROM shelves WHERE id=?'
    cur = conn.cursor()
    cur.execute(sql, (id,))
    conn.commit()
    conn.close()

def add_book(title, author, isbn, cover_url, shelf_id, user_id, summary=None, page_count=None, publisher=None, status='Okunacak', current_page=0, start_date=None, finish_date=None, link=None, file_path=None):
    conn = create_connection()
    sql = ''' INSERT INTO books(title, author, isbn, cover_url, shelf_id, user_id, summary, page_count, publisher, status, current_page, start_date, finish_date, link, file_path)
              VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?) '''
    cur = conn.cursor()
    cur.execute(sql, (title, author, isbn, cover_url, shelf_id, user_id, summary, page_count, publisher, status, current_page, start_date, finish_date, link, file_path))
    conn.commit()
    conn.close()
    return cur.lastrowid

def update_book_details(book_id, title, author, shelf_id, rating, notes, summary, borrower_name, borrow_date, status, current_page, start_date, finish_date, file_path=None):
    conn = create_connection()
    
    if file_path is not None:
        sql = ''' UPDATE books
                  SET title = ?, author = ?, shelf_id = ?, rating = ?, notes = ?, summary = ?, borrower_name = ?, borrow_date = ?, status = ?, current_page = ?, start_date = ?, finish_date = ?, file_path = ?
                  WHERE id = ?'''
        params = (title, author, shelf_id, rating, notes, summary, borrower_name, borrow_date, status, current_page, start_date, finish_date, file_path, book_id)
    else:
        sql = ''' UPDATE books
                  SET title = ?, author = ?, shelf_id = ?, rating = ?, notes = ?, summary = ?, borrower_name = ?, borrow_date = ?, status = ?, current_page = ?, start_date = ?, finish_date = ?
                  WHERE id = ?'''
        params = (title, author, shelf_id, rating, notes, summary, borrower_name, borrow_date, status, current_page, start_date, finish_date, book_id)

    cur = conn.cursor()
    cur.execute(sql, params)
    conn.commit()
    conn.close()

def get_books(user_id, shelf_id=None):
    conn = create_connection()
    cur = conn.cursor()
    if shelf_id:
        cur.execute("SELECT * FROM books WHERE user_id=? AND shelf_id=?", (user_id, shelf_id))
    else:
        cur.execute("SELECT * FROM books WHERE user_id=?", (user_id,))
    rows = cur.fetchall()
    conn.close()
    return rows

def delete_book(id):
    conn = create_connection()
    sql = 'DELETE FROM books WHERE id=?'
    cur = conn.cursor()
    cur.execute(sql, (id,))
    conn.commit()
    conn.close()

def check_book_exists(isbn, user_id):
    conn = create_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM books WHERE isbn=? AND user_id=?", (isbn, user_id))
    data = cur.fetchone()
    conn.close()
    return data is not None

def book_exists(user_id, title, author):
    conn = create_connection()
    cur = conn.cursor()
    # Check for exact match on title and author
    cur.execute("SELECT id FROM books WHERE user_id=? AND title=? AND author=?", (user_id, title, author))
    row = cur.fetchone()
    conn.close()
    return row is not None

def get_shelf_book_count(shelf_id):
    conn = create_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM books WHERE shelf_id=?", (shelf_id,))
    count = cur.fetchone()[0]
    conn.close()
    return count

def toggle_read_status(book_id, is_read):
    conn = create_connection()
    sql = ''' UPDATE books
              SET is_read = ?
              WHERE id = ?'''
    cur = conn.cursor()
    cur.execute(sql, (is_read, book_id))
    conn.commit()
    conn.close()

def add_quote(book_id, text, page_number=0):
    conn = create_connection()
    sql = ''' INSERT INTO quotes(book_id, text, page_number) VALUES(?,?,?) '''
    cur = conn.cursor()
    cur.execute(sql, (book_id, text, page_number))
    conn.commit()
    conn.close()

def get_quotes(book_id):
    conn = create_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM quotes WHERE book_id=?", (book_id,))
    rows = cur.fetchall()
    conn.close()
    return rows

def delete_quote(quote_id):
    conn = create_connection()
    sql = 'DELETE FROM quotes WHERE id=?'
    cur = conn.cursor()
    cur.execute(sql, (quote_id,))
    conn.commit()
    conn.close()

def update_book_progress(book_id, current_page):
    conn = create_connection()
    # Also update status to 'Okunuyor' if it was 'Okunacak'
    sql = ''' UPDATE books
              SET current_page = ?, status = CASE WHEN status = 'Okunacak' THEN 'Okunuyor' ELSE status END
              WHERE id = ?'''
    cur = conn.cursor()
    cur.execute(sql, (current_page, book_id))
    conn.commit()
    conn.close()

def update_book_cover(book_id, cover_url):
    conn = create_connection()
    sql = ''' UPDATE books
              SET cover_url = ?
              WHERE id = ?'''
    cur = conn.cursor()
    cur.execute(sql, (cover_url, book_id))
    conn.commit()
    conn.close()

def get_user_goal(user_id):
    conn = create_connection()
    cur = conn.cursor()
    cur.execute("SELECT reading_goal FROM users WHERE id=?", (user_id,))
    result = cur.fetchone()
    conn.close()
    return result[0] if result else 20

def update_user_goal(user_id, goal):
    conn = create_connection()
    cur = conn.cursor()
    cur.execute("UPDATE users SET reading_goal=? WHERE id=?", (goal, user_id))
    conn.commit()
    conn.close()

def add_reading_session(book_id, start_time, end_time, duration_minutes, pages_read):
    conn = create_connection()
    sql = ''' INSERT INTO reading_sessions(book_id, start_time, end_time, duration_minutes, pages_read)
              VALUES(?,?,?,?,?) '''
    cur = conn.cursor()
    cur.execute(sql, (book_id, start_time, end_time, duration_minutes, pages_read))
    conn.commit()
    conn.close()

def get_reading_sessions(book_id):
    conn = create_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM reading_sessions WHERE book_id=? ORDER BY start_time DESC", (book_id,))
    rows = cur.fetchall()
    conn.close()
    return rows

def get_user_reading_sessions(user_id):
    conn = create_connection()
    cur = conn.cursor()
    # Join with books to filter by user_id
    sql = """
        SELECT rs.*, b.title 
        FROM reading_sessions rs
        JOIN books b ON rs.book_id = b.id
        WHERE b.user_id = ?
        ORDER BY rs.start_time DESC
    """
    cur.execute(sql, (user_id,))
    rows = cur.fetchall()
    conn.close()
    return rows

def get_total_reading_time(user_id):
    conn = create_connection()
    cur = conn.cursor()
    sql = """
        SELECT SUM(rs.duration_minutes)
        FROM reading_sessions rs
        JOIN books b ON rs.book_id = b.id
        WHERE b.user_id = ?
    """
    cur.execute(sql, (user_id,))
    result = cur.fetchone()
    conn.close()
    return result[0] if result[0] else 0

def get_total_pages_read_in_sessions(user_id):
    conn = create_connection()
    cur = conn.cursor()
    sql = """
        SELECT SUM(rs.pages_read)
        FROM reading_sessions rs
        JOIN books b ON rs.book_id = b.id
        WHERE b.user_id = ?
    """
    cur.execute(sql, (user_id,))
    result = cur.fetchone()
    conn.close()
    return result[0] if result[0] else 0

def add_xp_column():
    conn = create_connection()
    c = conn.cursor()
    try:
        c.execute("ALTER TABLE users ADD COLUMN xp INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass
    conn.commit()
    conn.close()

def get_user_xp(user_id):
    conn = create_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT xp FROM users WHERE id=?", (user_id,))
        result = cur.fetchone()
        return result[0] if result else 0
    except:
        return 0
    finally:
        conn.close()

def add_xp(user_id, amount):
    conn = create_connection()
    cur = conn.cursor()
    cur.execute("UPDATE users SET xp = xp + ? WHERE id=?", (amount, user_id))
    conn.commit()
    conn.close()

def add_word(user_id, book_id, word, definition, sentence):
    conn = create_connection()
    sql = ''' INSERT INTO vocabulary(user_id, book_id, word, definition, sentence, date_added)
              VALUES(?,?,?,?,?, datetime('now')) '''
    cur = conn.cursor()
    cur.execute(sql, (user_id, book_id, word, definition, sentence))
    conn.commit()
    conn.close()

def get_words(book_id):
    conn = create_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM vocabulary WHERE book_id=? ORDER BY id DESC", (book_id,))
    rows = cur.fetchall()
    conn.close()
    return rows

def delete_word(word_id):
    conn = create_connection()
    sql = 'DELETE FROM vocabulary WHERE id=?'
    cur = conn.cursor()
    cur.execute(sql, (word_id,))
    conn.commit()
    conn.close()

def get_current_streak(user_id):
    conn = create_connection()
    cur = conn.cursor()
    # Get unique reading dates for the user, ordered by date desc
    sql = """
        SELECT DISTINCT substr(rs.start_time, 1, 10) as rdate
        FROM reading_sessions rs
        JOIN books b ON rs.book_id = b.id
        WHERE b.user_id = ?
        ORDER BY rdate DESC
    """
    cur.execute(sql, (user_id,))
    rows = cur.fetchall()
    conn.close()
    
    if not rows:
        return 0
        
    import datetime
    
    dates = [datetime.datetime.strptime(r[0], "%Y-%m-%d").date() for r in rows]
    today = datetime.date.today()
    
    streak = 0
    
    # Check if read today
    if dates[0] == today:
        streak = 1
        last_date = today
    elif dates[0] == today - datetime.timedelta(days=1):
        streak = 1
        last_date = dates[0]
    else:
        return 0 # Streak broken or not started today/yesterday
        
    # Check previous days
    for i in range(1, len(dates)):
        if dates[i] == last_date - datetime.timedelta(days=1):
            streak += 1
            last_date = dates[i]
        else:
            break
            
    return streak

# --- Tags ---
def create_tag(name, color="#2196F3"):
    conn = create_connection()
    try:
        sql = ''' INSERT INTO tags(name, color) VALUES(?,?) '''
        cur = conn.cursor()
        cur.execute(sql, (name, color))
        conn.commit()
        tag_id = cur.lastrowid
        conn.close()
        return tag_id
    except sqlite3.IntegrityError:
        conn.close()
        return None # Tag already exists

def get_all_tags():
    conn = create_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM tags ORDER BY name")
    rows = cur.fetchall()
    conn.close()
    return rows

def add_tag_to_book(book_id, tag_id):
    conn = create_connection()
    try:
        sql = ''' INSERT INTO book_tags(book_id, tag_id) VALUES(?,?) '''
        cur = conn.cursor()
        cur.execute(sql, (book_id, tag_id))
        conn.commit()
    except sqlite3.IntegrityError:
        pass # Already tagged
    conn.close()

def remove_tag_from_book(book_id, tag_id):
    conn = create_connection()
    sql = 'DELETE FROM book_tags WHERE book_id=? AND tag_id=?'
    cur = conn.cursor()
    cur.execute(sql, (book_id, tag_id))
    conn.commit()
    conn.close()

def get_book_tags(book_id):
    conn = create_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT t.id, t.name, t.color 
        FROM tags t
        JOIN book_tags bt ON t.id = bt.tag_id
        WHERE bt.book_id = ?
    """, (book_id,))
    rows = cur.fetchall()
    conn.close()
    return rows

def add_user(username, password):
    conn = create_connection()
    try:
        # In a real app, hash the password!
        sql = ''' INSERT INTO users(username, password, reading_goal) VALUES(?,?,?) '''
        cur = conn.cursor()
        cur.execute(sql, (username, password, 20))
        conn.commit()
        return cur.lastrowid
    except sqlite3.Error as e:
        print(e)
        return None
    finally:
        conn.close()

def get_user(username):
    conn = create_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE username=?", (username,))
    rows = cur.fetchall()
    conn.close()
    if rows:
        return rows[0]
    return None
