from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
from datetime import date

app = Flask(__name__)
app.secret_key = "your_secret_key"

# ----------------- User Login -----------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        conn = sqlite3.connect('library.db')
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM users WHERE email=?", (email,))
        user = cursor.fetchone()
        conn.close()
        if user:
            session['user_id'] = user[0]
            session['user_name'] = user[1]
            return redirect(url_for('home'))
        else:
            return "Invalid email!"
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

def get_current_user():
    return session.get('user_id')

# ----------------- Admin Check -----------------
def is_admin():
    user_id = get_current_user()
    if not user_id:
        return False
    conn = sqlite3.connect('library.db')
    cursor = conn.cursor()
    cursor.execute("SELECT role FROM users WHERE id=?", (user_id,))
    role = cursor.fetchone()[0]
    conn.close()
    return role == "admin"

# ----------------- Inject functions into templates -----------------
@app.context_processor
def inject_helpers():
    return dict(is_admin=is_admin, session=session)

# ----------------- Book Functions -----------------
def get_books(search_query=None):
    conn = sqlite3.connect('library.db')
    cursor = conn.cursor()
    if search_query:
        cursor.execute("SELECT * FROM books WHERE title LIKE ?", ('%' + search_query + '%',))
    else:
        cursor.execute("SELECT * FROM books")
    books = cursor.fetchall()
    conn.close()
    return books

@app.route('/')
def home():
    user_id = get_current_user()
    if not user_id:
        return redirect(url_for('login'))
    books = get_books()
    return render_template('index.html', books=books)

@app.route('/search', methods=['POST'])
def search():
    user_id = get_current_user()
    if not user_id:
        return redirect(url_for('login'))
    query = request.form['query']
    books = get_books(query)
    return render_template('index.html', books=books, search=query)

@app.route('/borrow/<int:book_id>')
def borrow(book_id):
    user_id = get_current_user()
    if not user_id:
        return redirect(url_for('login'))
    
    today = date.today().isoformat()
    conn = sqlite3.connect('library.db')
    cursor = conn.cursor()
    cursor.execute("SELECT copies FROM books WHERE id=?", (book_id,))
    copies = cursor.fetchone()[0]
    
    if copies > 0:
        cursor.execute("UPDATE books SET copies=? WHERE id=?", (copies - 1, book_id))
        cursor.execute("INSERT INTO transactions (user_id, book_id, borrow_date) VALUES (?, ?, ?)",
                       (user_id, book_id, today))
        conn.commit()
    conn.close()
    return redirect(url_for('home'))

@app.route('/return/<int:transaction_id>')
def return_book(transaction_id):
    user_id = get_current_user()
    if not user_id:
        return redirect(url_for('login'))

    today = date.today().isoformat()
    conn = sqlite3.connect('library.db')
    cursor = conn.cursor()
    cursor.execute("SELECT book_id FROM transactions WHERE id=? AND user_id=?", (transaction_id, user_id))
    result = cursor.fetchone()
    if result:
        book_id = result[0]
        cursor.execute("UPDATE books SET copies = copies + 1 WHERE id=?", (book_id,))
        cursor.execute("UPDATE transactions SET return_date=? WHERE id=?", (today, transaction_id))
        conn.commit()
    conn.close()
    return redirect(url_for('mybooks'))

@app.route('/mybooks')
def mybooks():
    user_id = get_current_user()
    if not user_id:
        return redirect(url_for('login'))
    conn = sqlite3.connect('library.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT t.id, b.title, b.author, t.borrow_date
        FROM transactions t
        JOIN books b ON t.book_id = b.id
        WHERE t.user_id=? AND t.return_date IS NULL
    ''', (user_id,))
    borrowed_books = cursor.fetchall()
    conn.close()
    return render_template('mybooks.html', books=borrowed_books)

# ----------------- Admin Routes -----------------
@app.route('/admin/add', methods=['GET', 'POST'])
def add_book():
    if not is_admin():
        return "Access denied!"
    if request.method == 'POST':
        title = request.form['title']
        author = request.form['author']
        copies = int(request.form['copies'])
        genre = request.form['genre']
        conn = sqlite3.connect('library.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO books (title, author, copies, genre) VALUES (?, ?, ?, ?)",
                       (title, author, copies, genre))
        conn.commit()
        conn.close()
        return redirect(url_for('home'))
    return render_template('add_book.html')

@app.route('/admin/remove/<int:book_id>')
def remove_book(book_id):
    if not is_admin():
        return "Access denied!"
    conn = sqlite3.connect('library.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM books WHERE id=?", (book_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('home'))

@app.route('/admin/transactions')
def all_transactions():
    if not is_admin():
        return "Access denied!"
    conn = sqlite3.connect('library.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT t.id, u.name, b.title, t.borrow_date, t.return_date
        FROM transactions t
        JOIN users u ON t.user_id = u.id
        JOIN books b ON t.book_id = b.id
    ''')
    transactions = cursor.fetchall()
    conn.close()
    return render_template('transactions.html', transactions=transactions)

if __name__ == '__main__':
    app.run(debug=True)
