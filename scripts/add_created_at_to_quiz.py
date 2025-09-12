import sqlite3

DB_PATH = 'instance/agriquest.db'

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

try:
    cursor.execute("ALTER TABLE quiz ADD COLUMN created_at DATETIME;")
    print("Column 'created_at' added successfully.")
except sqlite3.OperationalError as e:
    print(f"Error: {e}")
finally:
    conn.commit()
    conn.close()
