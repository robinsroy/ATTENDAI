import sqlite3
from collections import defaultdict

conn = sqlite3.connect('database.db')
cursor = conn.cursor()

# Get all students
cursor.execute('SELECT id, name, roll_no, class_name FROM students')
students = cursor.fetchall()

# Get all attendance records
cursor.execute('SELECT student_id, date, period, status FROM attendance')
attendance_records = cursor.fetchall()

print("\n" + "="*80)
print("CLASS-WISE ATTENDANCE SUMMARY")
print("="*80)

# Calculate class-wise statistics
class_stats = defaultdict(lambda: {'students': 0, 'total_records': 0, 'present': 0, 'absent': 0})

for student in students:
    student_id = student[0]
    class_name = student[3] or 'No Class'
    
    # Count student
    class_stats[class_name]['students'] += 1
    
    # Get student's attendance records
    student_records = [r for r in attendance_records if r[0] == student_id]
    
    # Count records
    class_stats[class_name]['total_records'] += len(student_records)
    
    # Count present (case-insensitive)
    present_count = len([r for r in student_records if r[3].lower() == 'present'])
    class_stats[class_name]['present'] += present_count
    
    # Count absent (case-insensitive)
    absent_count = len([r for r in student_records if r[3].lower() == 'absent'])
    class_stats[class_name]['absent'] += absent_count

# Print results
print(f"\n{'Class':<15} {'Students':<12} {'Total Records':<15} {'Present':<10} {'Absent':<10} {'%':<10}")
print("-" * 80)

for class_name in sorted(class_stats.keys()):
    stats = class_stats[class_name]
    percentage = (stats['present'] / stats['total_records'] * 100) if stats['total_records'] > 0 else 0
    
    print(f"{class_name:<15} {stats['students']:<12} {stats['total_records']:<15} {stats['present']:<10} {stats['absent']:<10} {percentage:.2f}%")

conn.close()
print("="*80)
