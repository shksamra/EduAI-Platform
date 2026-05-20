import sqlite3
from datetime import datetime
import pandas as pd
import database as db 

def init_db():
    conn = sqlite3.connect('learning_platform.db')
    c = conn.cursor()
    # 1. Create table with a 'role' column
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (username TEXT PRIMARY KEY, password TEXT, role TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS vault 
                 (username TEXT, type TEXT, title TEXT, date TEXT, content TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS scores 
                 (username TEXT, score INTEGER, total INTEGER, date TEXT)''')

    # 2. Create the MASTER ADMIN account automatically
    # Username: Admin | Password: Mtech2025
    c.execute("INSERT OR IGNORE INTO users (username, password, role) VALUES (?, ?, ?)", 
          ("Admin", "Mtech2025", "admin"))
    
    conn.commit()
    conn.close()

def get_detailed_admin_data():
    conn = sqlite3.connect('learning_platform.db')
    # 1. Fetch all users
    users = pd.read_sql_query("SELECT username, role FROM users", conn)
    # 2. Fetch all summaries (Activity)
    vault = pd.read_sql_query("SELECT username, type, title, date FROM vault", conn)
    # 3. Fetch all quiz results (Performance)
    scores = pd.read_sql_query("SELECT username, score, total, date FROM scores", conn)
    conn.close()
    return users, vault, scores

# CRITICAL: Call the function so it runs when the app starts
init_db()

def register_user(u, p):
    try:
        conn = sqlite3.connect('learning_platform.db')
        # Every person who registers themselves is a 'student'
        conn.execute("INSERT INTO users VALUES (?, ?, ?)", (u, p, "student"))
        conn.commit()
        conn.close()
        return True
    except: return False

def verify_user(u, p):
    conn = sqlite3.connect('learning_platform.db')
    curr = conn.cursor()
    # Check password AND get the role
    curr.execute("SELECT role FROM users WHERE username=? AND password=?", (u, p))
    res = curr.fetchone()
    conn.close()
    return res[0] if res else None # Returns 'admin', 'student', or None


def add_to_vault(user, doc_type, title, content):
    # 1. Open the connection
    conn = sqlite3.connect("learning_platform.db")
    c = conn.cursor()

    date_str = datetime.now().strftime("%Y-%m-%d %H:%M")

    # 2. Use 'c.execute' instead of 'db.execute'
    # Also ensuring it saves to the 'vault' table we established earlier
    c.execute(
        "INSERT INTO vault VALUES (?, ?, ?, ?, ?)",
        (user, doc_type, title, date_str, content),
    )

    # 3. Commit and close
    conn.commit()
    conn.close()

def get_history(user):
    conn = sqlite3.connect('learning_platform.db')
    curr = conn.cursor()
    curr.execute("SELECT type, title, date, content FROM history WHERE username=? ORDER BY date DESC", (user,))
    return curr.fetchall()

def get_vault_data(user):
    # 1. Open the connection to the database file
    conn = sqlite3.connect('learning_platform.db')
    c = conn.cursor()
    
    # 2. Execute the select query
    # We fetch all the data belonging to the logged-in user
    c.execute("SELECT type, title, date, content FROM vault WHERE username=?", (user,))
    
    # 3. Get the results
    data = c.fetchall()
    
    # 4. Close the connection
    conn.close()
    
    return data

def delete_vault_item(username, title, date):
    conn = sqlite3.connect('learning_platform.db')
    c = conn.cursor()
    # We use username, title, and date to ensure we delete the correct record
    c.execute("DELETE FROM vault WHERE username = ? AND title = ? AND date = ?", (username, title, date))
    conn.commit()
    conn.close()

# Add this to database.py if not already there
def save_score(user, score, total):
    conn = sqlite3.connect('learning_platform.db')
    c = conn.cursor()
    # Ensure current date is used
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M") 
    c.execute("INSERT INTO scores (username, score, total, date) VALUES (?, ?, ?, ?)", 
              (user, score, total, date_str))
    conn.commit()
    conn.close()


# Admin-only function to see everything
def get_admin_analytics():
    conn = sqlite3.connect('learning_platform.db')
    c = conn.cursor()
    c.execute("SELECT username, score, total, date FROM scores")
    scores = c.fetchall()
    c.execute("SELECT username, title, type FROM vault")
    vault = c.fetchall()
    conn.close()
    return scores, vault
