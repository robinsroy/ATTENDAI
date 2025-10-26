import sqlite3

conn = sqlite3.connect('database.db')
cursor = conn.cursor()

# Get attendance for abhi
cursor.execute('''
    SELECT students.name, attendance.date, attendance.period, attendance.status 
    FROM attendance 
    JOIN students ON attendance.student_id = students.id 
    WHERE students.name = 'abhi' 
    ORDER BY attendance.date, attendance.period
''')

results = cursor.fetchall()

print("\n" + "="*70)
print("ATTENDANCE RECORDS FOR ABHI")
print("="*70)

if results:
    for r in results:
        print(f"Date: {r[1]:<15} Period: {r[2]:<10} Status: {r[3]}")
    
    print("\n" + "-"*70)
    print(f"Total Records: {len(results)}")
    
    # Count unique dates
    unique_dates = set([r[1] for r in results])
    print(f"Unique Dates: {len(unique_dates)}")
    print(f"Dates: {sorted(unique_dates)}")
    
    # Count present vs absent
    present = [r for r in results if r[3] == 'Present']
    absent = [r for r in results if r[3] == 'Absent']
    
    print(f"\nPresent Records: {len(present)}")
    print(f"Absent Records: {len(absent)}")
    
    # Days with at least one present
    present_dates = set([r[1] for r in results if r[3] == 'Present'])
    print(f"\nDays with Present: {len(present_dates)}")
    print(f"Present Dates: {sorted(present_dates)}")
    
    # Calculate percentage
    if unique_dates:
        percentage = (len(present_dates) / len(unique_dates)) * 100
        print(f"\nCalculated Percentage: {percentage:.1f}%")
else:
    print("No attendance records found for abhi")

conn.close()
print("="*70)
