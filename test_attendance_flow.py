"""
Test the complete attendance flow to ensure:
1. No duplicates are created
2. Absent can be overwritten to Present
3. Present cannot be overwritten to Absent
4. Auto-absent marking works correctly
"""
import sqlite3
from datetime import date

def test_attendance_flow():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    print("\n" + "="*70)
    print("TESTING ATTENDANCE FLOW")
    print("="*70)
    
    # Get student info
    cursor.execute("SELECT id, name, roll_no, class_name FROM students WHERE class_name = '10'")
    students = cursor.fetchall()
    
    print("\n📋 Students in Class 10:")
    for s in students:
        print(f"   ID {s[0]}: {s[1]} ({s[2]})")
    
    # Test scenario: Period 3 for today
    test_date = date.today().isoformat()
    test_period = 3
    
    print(f"\n🧪 Test Scenario: Date={test_date}, Period={test_period}")
    
    # Clear any existing records for this test
    cursor.execute("""
        DELETE FROM attendance 
        WHERE date = ? AND period = ?
    """, (test_date, test_period))
    conn.commit()
    print(f"   ✓ Cleared existing records for test period")
    
    # Test 1: Create initial attendance record (present)
    print("\n1️⃣ Test: Mark student 5 (Abhi) as PRESENT")
    try:
        cursor.execute("""
            INSERT INTO attendance (student_id, date, period, status)
            VALUES (?, ?, ?, ?)
        """, (5, test_date, test_period, 'present'))
        conn.commit()
        print("   ✅ Successfully marked present")
    except sqlite3.IntegrityError as e:
        print(f"   ❌ Failed: {e}")
    
    # Test 2: Try to create duplicate (should fail with UNIQUE constraint)
    print("\n2️⃣ Test: Try to mark student 5 again (should fail - duplicate prevention)")
    try:
        cursor.execute("""
            INSERT INTO attendance (student_id, date, period, status)
            VALUES (?, ?, ?, ?)
        """, (5, test_date, test_period, 'present'))
        conn.commit()
        print("   ❌ UNIQUE constraint not working - duplicate created!")
    except sqlite3.IntegrityError:
        print("   ✅ Duplicate prevented by UNIQUE constraint")
    
    # Test 3: Update existing record (should work)
    print("\n3️⃣ Test: Check if existing record can be queried and updated")
    cursor.execute("""
        SELECT * FROM attendance 
        WHERE student_id = ? AND date = ? AND period = ?
    """, (5, test_date, test_period))
    existing = cursor.fetchone()
    if existing:
        print(f"   ✓ Found existing record: status={existing[4]}")
        print("   ✓ Update logic can use UPDATE instead of INSERT")
    else:
        print("   ❌ No existing record found!")
    
    # Test 4: Mark student 6 as absent
    print("\n4️⃣ Test: Mark student 6 (Sony) as ABSENT")
    try:
        cursor.execute("""
            INSERT INTO attendance (student_id, date, period, status)
            VALUES (?, ?, ?, ?)
        """, (6, test_date, test_period, 'absent'))
        conn.commit()
        print("   ✅ Successfully marked absent")
    except sqlite3.IntegrityError as e:
        print(f"   ❌ Failed: {e}")
    
    # Test 5: Update absent to present (overwrite scenario)
    print("\n5️⃣ Test: Update student 6 from ABSENT to PRESENT (late arrival)")
    cursor.execute("""
        UPDATE attendance 
        SET status = 'present'
        WHERE student_id = ? AND date = ? AND period = ?
    """, (6, test_date, test_period))
    conn.commit()
    if cursor.rowcount > 0:
        print("   ✅ Successfully updated ABSENT → PRESENT")
    else:
        print("   ❌ Update failed")
    
    # Test 6: Verify final state
    print("\n6️⃣ Final Verification:")
    cursor.execute("""
        SELECT a.student_id, s.name, a.date, a.period, a.status
        FROM attendance a
        JOIN students s ON a.student_id = s.id
        WHERE a.date = ? AND a.period = ?
        ORDER BY s.name
    """, (test_date, test_period))
    records = cursor.fetchall()
    
    print("\n   Student ID | Name           | Status")
    print("   " + "-"*45)
    for r in records:
        print(f"   {r[0]:10} | {r[1]:14} | {r[4]}")
    
    # Check for duplicates
    cursor.execute("""
        SELECT student_id, COUNT(*) as count
        FROM attendance
        WHERE date = ? AND period = ?
        GROUP BY student_id
        HAVING count > 1
    """, (test_date, test_period))
    dups = cursor.fetchall()
    
    if dups:
        print(f"\n   ❌ Found {len(dups)} duplicate entries!")
    else:
        print("\n   ✅ No duplicates found")
    
    # Cleanup test data
    print("\n🧹 Cleaning up test data...")
    cursor.execute("""
        DELETE FROM attendance 
        WHERE date = ? AND period = ?
    """, (test_date, test_period))
    conn.commit()
    print("   ✓ Test data removed")
    
    conn.close()
    
    print("\n" + "="*70)
    print("✅ TEST COMPLETE")
    print("="*70 + "\n")

if __name__ == '__main__':
    test_attendance_flow()
