CREATE TABLE IF NOT EXISTS user_streaks (
    user_id INTEGER PRIMARY KEY,
    current_streak INTEGER NOT NULL DEFAULT 0,
    longest_streak INTEGER NOT NULL DEFAULT 0,
    last_streak_date DATE,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Inicjalizacja streaków dla istniejących użytkowników
INSERT OR IGNORE INTO user_streaks (user_id, current_streak, longest_streak, last_streak_date)
SELECT id AS user_id,
       0 AS current_streak,
       0 AS longest_streak,
       NULL AS last_streak_date
FROM users;
