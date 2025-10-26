"""
Database Migration Script
Adds profile_photo column to students table
Adds teacher profile fields to users table
"""
import sqlite3
import os

def migrate_database():
    db_path = 'database.db'
    
    if not os.path.exists(db_path):
        print("❌ Database file not found!")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check students table
        cursor.execute("PRAGMA table_info(students)")
        student_columns = [column[1] for column in cursor.fetchall()]
        
        if 'profile_photo' in student_columns:
            print("✅ Column 'profile_photo' already exists in students table")
        else:
            cursor.execute("ALTER TABLE students ADD COLUMN profile_photo TEXT")
            conn.commit()
            print("✅ Successfully added 'profile_photo' column to students table")
        
        # Check users table for teacher profile fields
        cursor.execute("PRAGMA table_info(users)")
        user_columns = [column[1] for column in cursor.fetchall()]
        
        teacher_fields = ['full_name', 'phone', 'profile_photo', 'department', 'subject']
        
        for field in teacher_fields:
            if field in user_columns:
                print(f"✅ Column '{field}' already exists in users table")
            else:
                cursor.execute(f"ALTER TABLE users ADD COLUMN {field} TEXT")
                conn.commit()
                print(f"✅ Successfully added '{field}' column to users table")
        
        conn.close()
        print("\n✅ Database migration completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during migration: {str(e)}")
        if conn:
            conn.close()

if __name__ == '__main__':
    print("🔄 Starting database migration...")
    migrate_database()
