"""
Database Migration Script
Adds profile_photo column to students table
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
        
        # Check if column already exists
        cursor.execute("PRAGMA table_info(students)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'profile_photo' in columns:
            print("✅ Column 'profile_photo' already exists in students table")
        else:
            # Add the profile_photo column
            cursor.execute("ALTER TABLE students ADD COLUMN profile_photo TEXT")
            conn.commit()
            print("✅ Successfully added 'profile_photo' column to students table")
        
        conn.close()
        print("\n✅ Database migration completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during migration: {str(e)}")
        if conn:
            conn.close()

if __name__ == '__main__':
    print("🔄 Starting database migration...")
    migrate_database()
