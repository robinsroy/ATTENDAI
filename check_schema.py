import sqlite3

conn = sqlite3.connect('database.db')
cursor = conn.cursor()

cursor.execute('SELECT sql FROM sqlite_master WHERE type="table" AND name="attendance"')
schema = cursor.fetchone()[0]
print('\nAttendance Table Schema:')
print(schema)

conn.close()
