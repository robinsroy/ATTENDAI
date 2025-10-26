import sqlite3

conn = sqlite3.connect('database.db')
cursor = conn.cursor()

cursor.execute('SELECT name, roll_no, class_name FROM students ORDER BY class_name, name')
students = cursor.fetchall()

print("\nStudents by Class:")
print("="*60)

current_class = None
count = 0

for name, roll_no, class_name in students:
    class_display = class_name if class_name else "No Class"
    
    if class_display != current_class:
        if current_class is not None:
            print(f"  Subtotal: {count} students\n")
        current_class = class_display
        count = 0
        print(f"\n{current_class}:")
        print("-" * 60)
    
    count += 1
    print(f"  {count}. {name} ({roll_no})")

print(f"  Subtotal: {count} students\n")

conn.close()
