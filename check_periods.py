import sqlite3

conn = sqlite3.connect('database.db')
cursor = conn.cursor()

cursor.execute('PRAGMA table_info(attendance)')
cols = cursor.fetchall()
print('\nAttendance Table Columns:')
for c in cols:
    print(f'{c[1]:15} - {c[2]}')

cursor.execute('PRAGMA table_info(timetable)')
cols = cursor.fetchall()
print('\nTimetable Table Columns:')
for c in cols:
    print(f'{c[1]:15} - {c[2]}')

# Check actual data
cursor.execute('SELECT period FROM attendance LIMIT 3')
att_periods = cursor.fetchall()
print('\nSample Attendance periods:', [p[0] for p in att_periods])
print('Type:', type(att_periods[0][0]) if att_periods else 'No data')

cursor.execute('SELECT period FROM timetable LIMIT 3')
tt_periods = cursor.fetchall()
print('\nSample Timetable periods:', [p[0] for p in tt_periods])
print('Type:', type(tt_periods[0][0]) if tt_periods else 'No data')

conn.close()
