from models import SessionLocal, User

db = SessionLocal()
admin = db.query(User).filter(User.username == 'admin').first()

print('\n' + '='*60)
print('ADMIN ACCOUNT VERIFICATION')
print('='*60)
print(f'\n✅ Username: {admin.username}')
print(f'✅ Role: {admin.role}')
print(f'✅ Email: {admin.email}')
print(f'✅ Full Name: {admin.full_name}')
print(f'\n🔗 Login URL: http://localhost:5000/teacher/login')
print(f'🔑 Password: admin')
print('\n' + '='*60 + '\n')

db.close()
