import sqlite3

conn = sqlite3.connect("app.db")
c = conn.cursor()

# USERS — ID jako TEXT, bo używamy user_id z URL
c.execute("""
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    name TEXT,
    xp INTEGER DEFAULT 0,
    level INTEGER DEFAULT 1
)
""")

# CHAT MESSAGES
c.execute("""
CREATE TABLE IF NOT EXISTS chat_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT,
    role TEXT,
    content TEXT
)
""")

# STREAK SYSTEM
c.execute("""
CREATE TABLE IF NOT EXISTS user_streaks (
    user_id TEXT PRIMARY KEY,
    current_streak INTEGER DEFAULT 0,
    longest_streak INTEGER DEFAULT 0,
    last_streak_date TEXT
)
""")

# BADGES — globalne
c.execute("""
CREATE TABLE IF NOT EXISTS badges (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    description TEXT
)
""")

# BADGES — przypisane do usera
c.execute("""
CREATE TABLE IF NOT EXISTS user_badges (
    user_id TEXT,
    badge_id INTEGER,
    earned_date TEXT
)
""")

conn.commit()
conn.close()

print("Baza danych gotowa (MVP multi-user) 🎉")
