"""
Fix duplicate attendance records and add unique constraint
"""
import sqlite3

def fix_duplicates():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    print("\n" + "="*70)
    print("FIXING DUPLICATE ATTENDANCE RECORDS")
    print("="*70)
    
    # Show current duplicates
    print("\n1. Finding duplicates...")
    cursor.execute("""
        SELECT student_id, date, period, COUNT(*) as count, GROUP_CONCAT(id) as ids
        FROM attendance
        GROUP BY student_id, date, period
        HAVING count > 1
    """)
    duplicates = cursor.fetchall()
    
    if duplicates:
        print(f"   Found {len(duplicates)} duplicate groups:")
        for dup in duplicates:
            student_id, date, period, count, ids = dup
            print(f"   - Student {student_id}, Date {date}, Period {period}: {count} records (IDs: {ids})")
        
        # Delete duplicates (keep the first one)
        print("\n2. Removing duplicates (keeping earliest ID)...")
        for dup in duplicates:
            student_id, date, period, count, ids = dup
            id_list = [int(x) for x in ids.split(',')]
            # Keep the first ID, delete the rest
            keep_id = min(id_list)
            delete_ids = [x for x in id_list if x != keep_id]
            
            for del_id in delete_ids:
                cursor.execute("DELETE FROM attendance WHERE id = ?", (del_id,))
                print(f"   ✓ Deleted record ID {del_id}")
        
        conn.commit()
        print(f"\n   ✅ Removed {sum([len(ids.split(','))-1 for _, _, _, _, ids in duplicates])} duplicate records")
    else:
        print("   ✓ No duplicates found!")
    
    # Check if unique constraint already exists
    print("\n3. Checking for UNIQUE constraint...")
    cursor.execute("PRAGMA index_list(attendance)")
    indexes = cursor.fetchall()
    
    has_unique = False
    for index in indexes:
        index_name = index[1]
        if 'unique' in index_name.lower():
            cursor.execute(f"PRAGMA index_info({index_name})")
            cols = cursor.fetchall()
            if len(cols) == 3:  # student_id, date, period
                has_unique = True
                print(f"   ✓ Unique constraint already exists: {index_name}")
                break
    
    if not has_unique:
        print("   Adding UNIQUE constraint...")
        # Create new table with constraint
        cursor.execute("""
            CREATE TABLE attendance_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                period INTEGER NOT NULL,
                status TEXT NOT NULL,
                UNIQUE(student_id, date, period),
                FOREIGN KEY (student_id) REFERENCES students (id)
            )
        """)
        
        # Copy data
        cursor.execute("""
            INSERT INTO attendance_new (id, student_id, date, period, status)
            SELECT id, student_id, date, period, status
            FROM attendance
        """)
        
        # Drop old table and rename
        cursor.execute("DROP TABLE attendance")
        cursor.execute("ALTER TABLE attendance_new RENAME TO attendance")
        
        conn.commit()
        print("   ✅ UNIQUE constraint added!")
    
    # Show final state
    print("\n4. Final verification:")
    cursor.execute("SELECT COUNT(*) FROM attendance")
    total = cursor.fetchone()[0]
    print(f"   Total records: {total}")
    
    cursor.execute("""
        SELECT student_id, date, period, COUNT(*) as count
        FROM attendance
        GROUP BY student_id, date, period
        HAVING count > 1
    """)
    remaining_dups = cursor.fetchall()
    
    if remaining_dups:
        print(f"   ⚠️ Still have {len(remaining_dups)} duplicates!")
    else:
        print("   ✅ No duplicates remaining!")
    
    # Show all records
    print("\n5. Current attendance records:")
    cursor.execute("""
        SELECT a.id, s.name, a.date, a.period, a.status
        FROM attendance a
        JOIN students s ON a.student_id = s.id
        ORDER BY s.name, a.date, a.period
    """)
    records = cursor.fetchall()
    
    print("\n   ID | Student Name      | Date       | Period | Status")
    print("   " + "-"*60)
    for r in records:
        print(f"   {r[0]:2} | {r[1]:17} | {r[2]} | {r[3]:6} | {r[4]}")
    
    conn.close()
    
    print("\n" + "="*70)
    print("✅ DUPLICATE FIX COMPLETE!")
    print("="*70 + "\n")

if __name__ == '__main__':
    fix_duplicates()
