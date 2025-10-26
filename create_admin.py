"""
Create default admin user
Username: admin
Password: admin
"""
from models import SessionLocal, User
from werkzeug.security import generate_password_hash

def create_admin():
    db = SessionLocal()
    
    # Check if admin already exists
    existing_admin = db.query(User).filter(User.username == 'admin').first()
    
    if existing_admin:
        print("ℹ️  Admin user already exists!")
        print(f"   Username: {existing_admin.username}")
        print(f"   Role: {existing_admin.role}")
        db.close()
        return
    
    # Create admin user
    admin_user = User(
        username='admin',
        password_hash=generate_password_hash('admin'),
        role='admin',
        email='admin@attendai.com',
        full_name='System Administrator'
    )
    
    db.add(admin_user)
    db.commit()
    
    print("\n" + "="*60)
    print("✅ ADMIN USER CREATED SUCCESSFULLY!")
    print("="*60)
    print("\n📋 Login Credentials:")
    print("   Username: admin")
    print("   Password: admin")
    print("   Role: Admin")
    print("\n🔗 Login URL: http://localhost:5000/teacher/login")
    print("   (Use the teacher login page)")
    print("\n⚠️  IMPORTANT: Change the password after first login!")
    print("="*60 + "\n")
    
    db.close()

if __name__ == '__main__':
    create_admin()
