"""
Test the student dashboard period matching
"""
import sqlite3

conn = sqlite3.connect('database.db')
cursor = conn.cursor()

print("\n" + "="*70)
print("TESTING PERIOD TYPE MATCHING")
print("="*70)

# Get sample data
cursor.execute('SELECT period FROM attendance WHERE student_id = 5 LIMIT 3')
att_periods = cursor.fetchall()
print("\n📊 Attendance periods (INTEGER):")
for p in att_periods:
    print(f"   Value: {p[0]}, Type: {type(p[0])}")

cursor.execute('SELECT period FROM timetable WHERE class_name = "10" LIMIT 3')
tt_periods = cursor.fetchall()
print("\n📊 Timetable periods (STRING):")
for p in tt_periods:
    print(f"   Value: {p[0]!r}, Type: {type(p[0])}")

# Simulate the fix
print("\n🔧 Converting timetable periods to int:")
timetable_grid = {}
all_periods = set()

cursor.execute('SELECT day_of_week, period FROM timetable WHERE class_name = "10"')
entries = cursor.fetchall()

for day, period_str in entries:
    # Convert period to int
    period_int = int(period_str) if period_str.isdigit() else int(period_str.split()[-1])
    
    if day not in timetable_grid:
        timetable_grid[day] = {}
    timetable_grid[day][period_int] = period_str  # Store original for display
    all_periods.add(period_int)

print(f"   Converted periods: {sorted(all_periods)}")
print(f"   Type: {type(list(all_periods)[0])}")

# Simulate attendance lookup
print("\n🔍 Testing attendance lookup:")
from datetime import date
today_date = date.today().isoformat()

cursor.execute('SELECT period, status FROM attendance WHERE student_id = 5 AND date = ?', (today_date,))
records = cursor.fetchall()

today_attendance = {}
for period_int, status in records:
    today_attendance[period_int] = status
    print(f"   Period {period_int} (type: {type(period_int)}): {status}")

# Test lookup
print("\n✅ Testing dictionary lookup:")
for period in sorted(all_periods):
    status = today_attendance.get(period, "Not Taken")
    print(f"   Period {period}: {status}")

print("\n" + "="*70)
print("✅ PERIOD MATCHING SHOULD WORK NOW")
print("="*70 + "\n")

conn.close()
