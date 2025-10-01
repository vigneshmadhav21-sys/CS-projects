import sqlite3

conn = sqlite3.connect('library.db')
cursor = conn.cursor()

# Books Table
cursor.execute('''
CREATE TABLE IF NOT EXISTS books (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    author TEXT,
    copies INTEGER,
    genre TEXT
)
''')

# Users Table
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    role TEXT,
    email TEXT
)
''')

# Transactions Table
cursor.execute('''
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    book_id INTEGER,
    borrow_date TEXT,
    return_date TEXT,
    FOREIGN KEY(user_id) REFERENCES users(id),
    FOREIGN KEY(book_id) REFERENCES books(id)
)
''')

# Example Books
books = [
    ("Harry Potter", "J.K. Rowling", 5, "Fantasy"),
    ("Atomic Habits", "James Clear", 3, "Self-help"),
    ("Clean Code", "Robert Martin", 2, "Programming")
]
cursor.executemany("INSERT INTO books (title, author, copies, genre) VALUES (?, ?, ?, ?)", books)

# Example Users
users = [
    ("Alice", "member", "alice@example.com"),
    ("Bob", "member", "bob@example.com"),
    ("Admin", "admin", "admin@example.com")
]
cursor.executemany("INSERT INTO users (name, role, email) VALUES (?, ?, ?)", users)

conn.commit()
conn.close()
print("✅ Database setup complete with example books and users!")
