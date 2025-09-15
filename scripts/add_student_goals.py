# Simple migration helper: add daily_goal and weekly_goal columns to student table if missing
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'instance', 'agriquest.db')

def column_exists(conn, table, column):
    cur = conn.execute(f"PRAGMA table_info('{table}')")
    cols = [r[1] for r in cur.fetchall()]
    return column in cols

if __name__ == '__main__':
    if not os.path.exists(DB_PATH):
        print('Database not found at', DB_PATH)
        raise SystemExit(1)
    conn = sqlite3.connect(DB_PATH)
    try:
        if not column_exists(conn, 'student', 'daily_goal'):
            print('Adding daily_goal column')
            conn.execute("ALTER TABLE student ADD COLUMN daily_goal INTEGER DEFAULT 1 NOT NULL")
        else:
            print('daily_goal exists')
        if not column_exists(conn, 'student', 'weekly_goal'):
            print('Adding weekly_goal column')
            conn.execute("ALTER TABLE student ADD COLUMN weekly_goal INTEGER DEFAULT 5 NOT NULL")
        else:
            print('weekly_goal exists')
        conn.commit()
        print('Migration complete')
    finally:
        conn.close()
