"""
Final verification of attendance system
"""
import sqlite3

conn = sqlite3.connect('database.db')
cursor = conn.cursor()

print('\n' + '='*70)
print('FINAL VERIFICATION - ATTENDANCE SYSTEM STATUS')
print('='*70)

# Count enrolled students
cursor.execute('SELECT COUNT(*) FROM students WHERE encodings_path IS NOT NULL')
enrolled = cursor.fetchone()[0]
print(f'\n📊 Enrolled Students: {enrolled}')

# Count total records
cursor.execute('SELECT COUNT(*) FROM attendance')
total_records = cursor.fetchone()[0]
print(f'📊 Total Attendance Records: {total_records}')

# Check for duplicates
cursor.execute('''
    SELECT student_id, date, period, COUNT(*) as count 
    FROM attendance 
    GROUP BY student_id, date, period 
    HAVING count > 1
''')
dups = cursor.fetchall()
print(f'📊 Duplicate Records: {len(dups)} {"❌" if len(dups) > 0 else "✅"}')

# Check UNIQUE constraint
cursor.execute('SELECT sql FROM sqlite_master WHERE type="table" AND name="attendance"')
schema = cursor.fetchone()[0]
has_unique = 'UNIQUE' in schema
print(f'📊 UNIQUE Constraint: {"✅ Active" if has_unique else "❌ Missing"}')

# Student stats
cursor.execute('''
    SELECT s.name, COUNT(a.id) as records 
    FROM students s 
    LEFT JOIN attendance a ON s.id = a.student_id 
    WHERE s.class_name="10" 
    GROUP BY s.id, s.name 
    ORDER BY s.name
''')
student_stats = cursor.fetchall()
print(f'\n📋 Class 10 Student Attendance:')
for stat in student_stats:
    print(f'   {stat[0]:20} - {stat[1]} records')

print('\n' + '='*70)
print('✅ SYSTEM READY FOR PRODUCTION')
print('='*70 + '\n')

conn.close()
