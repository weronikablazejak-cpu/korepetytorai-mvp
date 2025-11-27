import sqlite3
from datetime import datetime, date
from openai import OpenAI

# Twój klucz (pobierz z config lub wpisz)
client = OpenAI(api_key="TU_WKLEJ_SWÓJ_KLUCZ")


# ----------------------------------------
# DB CONNECTION
# ----------------------------------------
def get_connection():
    return sqlite3.connect("app.db")


# ----------------------------------------
# USER CREATION
# ----------------------------------------
def ensure_user(user_id: str):
    conn = get_connection()
    c = conn.cursor()

    c.execute("SELECT id FROM users WHERE id=?", (user_id,))
    exists = c.fetchone()

    if not exists:
        c.execute(
            "INSERT INTO users (id, name, xp, level) VALUES (?, ?, 0, 1)",
            (user_id, f"User {user_id}")
        )
        conn.commit()

    conn.close()


# ----------------------------------------
# BADGES — INIT
# ----------------------------------------
def ensure_badges_exist():
    conn = get_connection()
    c = conn.cursor()

    default_badges = [
        ("Pierwsza Lekcja", "Zadałeś pierwsze pytanie"),
        ("5 Lekcji", "Udzieliłeś 5 odpowiedzi"),
        ("Dzienny Streak 3", "Utrzymałeś streak przez 3 dni"),
        ("Dzienny Streak 7", "Utrzymałeś streak przez 7 dni"),
        ("Uczeń Poziomu 5", "Osiągnąłeś poziom 5")
    ]

    for name, desc in default_badges:
        c.execute("SELECT id FROM badges WHERE name=?", (name,))
        if not c.fetchone():
            c.execute(
                "INSERT INTO badges (name, description) VALUES (?, ?)",
                (name, desc)
            )

    conn.commit()
    conn.close()


# ----------------------------------------
# STREAK LOGIC
# ----------------------------------------
def update_streak(user_id: str):
    conn = get_connection()
    c = conn.cursor()

    today = date.today().isoformat()

    # Pobierz streak usera
    c.execute("SELECT current_streak, longest_streak, last_streak_date FROM user_streaks WHERE user_id=?",
              (user_id,))
    row = c.fetchone()

    if not row:
        new_streak = 1
        longest = 1
        c.execute(
            "INSERT INTO user_streaks (user_id, current_streak, longest_streak, last_streak_date) VALUES (?, ?, ?, ?)",
            (user_id, 1, 1, today)
        )
    else:
        curr, longest, last_date = row

        if last_date is None:
            new_streak = 1
            longest = max(longest, 1)
        else:
            last = datetime.strptime(last_date, "%Y-%m-%d").date()
            diff = (date.today() - last).days

            if diff == 0:
                new_streak = curr
            elif diff == 1:
                new_streak = curr + 1
            else:
                new_streak = 1

        longest = max(longest, new_streak)

        c.execute("""
            UPDATE user_streaks
            SET current_streak=?, longest_streak=?, last_streak_date=?
            WHERE user_id=?
        """, (new_streak, longest, today, user_id))

    conn.commit()
    conn.close()

    return new_streak, longest


# ----------------------------------------
# AWARD BADGES
# ----------------------------------------
def award_badges(user_id: str, message_count: int, level: int, streak: int):
    conn = get_connection()
    c = conn.cursor()

    earned_now = []

    # 1 — pierwsza wiadomość
    if message_count == 1:
        earned_now.append("Pierwsza Lekcja")

    # 2 — 5 wiadomości
    if message_count == 5:
        earned_now.append("5 Lekcji")

    # 3 — streak
    if streak == 3:
        earned_now.append("Dzienny Streak 3")
    if streak == 7:
        earned_now.append("Dzienny Streak 7")

    # 4 — poziom
    if level == 5:
        earned_now.append("Uczeń Poziomu 5")

    # zapisz
    for badge_name in earned_now:
        c.execute("SELECT id FROM badges WHERE name=?", (badge_name,))
        row = c.fetchone()
        if not row:
            continue
        badge_id = row[0]

        c.execute("SELECT 1 FROM user_badges WHERE user_id=? AND badge_id=?",
                  (user_id, badge_id))
        if not c.fetchone():
            c.execute(
                "INSERT INTO user_badges (user_id, badge_id, earned_date) VALUES (?, ?, ?)",
                (user_id, badge_id, date.today().isoformat())
            )

    conn.commit()
    conn.close()

    return earned_now


# ----------------------------------------
# MAIN PROCESS MESSAGE
# ----------------------------------------
def process_message(user_id: str, message: str):
    ensure_user(user_id)
    ensure_badges_exist()

    conn = get_connection()
    c = conn.cursor()

    # zapis wiadomości usera
    c.execute("INSERT INTO chat_messages (user_id, role, content) VALUES (?, 'user', ?)",
              (user_id, message))

    # policz ile wiadomości miał user
    c.execute("SELECT COUNT(*) FROM chat_messages WHERE user_id=?", (user_id,))
    msg_count = c.fetchone()[0]

    # XP
    base_xp = 5
    bonus = 5 if len(message) > 80 else 0
    xp = base_xp + bonus

    # update xp + level
    c.execute("SELECT xp, level FROM users WHERE id=?", (user_id,))
    xp_prev, level = c.fetchone()

    new_xp_total = xp_prev + xp

    while new_xp_total >= level * 100:
        level += 1

    c.execute("UPDATE users SET xp=?, level=? WHERE id=?",
              (new_xp_total, level, user_id))

    # streak
    streak, longest = update_streak(user_id)

    # GPT response
    response = client.chat.completions.create(
        model="gpt-4.1",
        messages=[
            {"role": "system", "content": "Jesteś KorepetytoremAI."},
            {"role": "user", "content": message}
        ]
    )
    answer = response.choices[0].message.content

    # zapis odpowiedzi
    c.execute("INSERT INTO chat_messages (user_id, role, content) VALUES (?, 'assistant', ?)",
              (user_id, answer))

    conn.commit()
    conn.close()

    # badges
    new_badges = award_badges(user_id, msg_count, level, streak)

    return answer, xp, new_xp_total, level, streak, new_badges
