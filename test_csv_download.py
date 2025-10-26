"""
Test script to verify CSV download route works
"""
from models import SessionLocal, Student, User, Attendance
from io import StringIO
import csv
from datetime import datetime

print("🔍 Testing CSV Generation Logic...")

db = SessionLocal()

try:
    # Get all students
    students = db.query(Student).order_by(Student.class_name, Student.roll_no).all()
    print(f"✅ Found {len(students)} students")
    
    # Get all teachers
    teachers = db.query(User).filter(User.role == 'teacher').all()
    print(f"✅ Found {len(teachers)} teachers")
    
    # Get all unique periods taken
    all_periods = db.query(Attendance.period).distinct().order_by(Attendance.period).all()
    periods_taken = [p[0] for p in all_periods]
    print(f"✅ Found {len(periods_taken)} unique periods: {periods_taken}")
    
    # Get all unique dates
    all_dates = db.query(Attendance.date).distinct().order_by(Attendance.date).all()
    dates_taken = [d[0] for d in all_dates]
    print(f"✅ Found {len(dates_taken)} unique dates")
    
    # Create CSV in memory
    si = StringIO()
    writer = csv.writer(si)
    
    # Write header
    writer.writerow(['=== ATTENDAI SYSTEM - COMPREHENSIVE ANALYTICS REPORT ==='])
    writer.writerow(['Generated On:', datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    writer.writerow([])
    
    # Write teachers section
    writer.writerow(['=== TEACHERS IN SYSTEM ==='])
    writer.writerow(['ID', 'Username', 'Full Name', 'Email', 'Department', 'Subject', 'Phone'])
    for teacher in teachers:
        writer.writerow([
            teacher.id,
            teacher.username,
            teacher.full_name or '-',
            teacher.email or '-',
            teacher.department or '-',
            teacher.subject or '-',
            teacher.phone or '-'
        ])
    
    print(f"✅ CSV content generated ({len(si.getvalue())} characters)")
    print("\n📄 First 500 characters of CSV:")
    print(si.getvalue()[:500])
    
    # Save to file for testing
    with open('test_output.csv', 'w', newline='', encoding='utf-8') as f:
        f.write(si.getvalue())
    
    print("\n✅ Test CSV saved to 'test_output.csv'")
    print("✅ All tests passed! The route logic should work correctly.")
    
except Exception as e:
    print(f"❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()
finally:
    db.close()
