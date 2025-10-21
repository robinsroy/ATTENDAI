# app.py
import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import Base, engine, SessionLocal, User, Student, Timetable, Attendance

# Create database tables
Base.metadata.create_all(engine)

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this-in-production'  # Change this in production!

# Setup Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    db = SessionLocal()
    user = db.query(User).get(int(user_id))
    db.close()
    return user

# Home route - redirect to login
@app.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.role == 'teacher':
            return redirect(url_for('teacher_dashboard'))
        elif current_user.role == 'student':
            return redirect(url_for('student_dashboard'))
    return redirect(url_for('login'))

# Main login page (shows options for teacher/student)
@app.route('/login')
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    return render_template('login.html')

#########################
# TEACHER ROUTES
#########################

@app.route('/teacher/register', methods=['GET', 'POST'])
def teacher_register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        email = request.form.get('email')
        
        # Validation
        if not username or not password:
            flash('Username and password are required!', 'error')
            return render_template('teacher_register.html')
        
        if password != confirm_password:
            flash('Passwords do not match!', 'error')
            return render_template('teacher_register.html')
        
        db = SessionLocal()
        
        # Check if username already exists
        existing_user = db.query(User).filter(User.username == username).first()
        if existing_user:
            flash('Username already exists! Please choose another.', 'error')
            db.close()
            return render_template('teacher_register.html')
        
        # Create new teacher
        new_teacher = User(
            username=username,
            password_hash=generate_password_hash(password),
            role='teacher',
            email=email
        )
        
        db.add(new_teacher)
        db.commit()
        db.close()
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('teacher_login'))
    
    return render_template('teacher_register.html')

@app.route('/teacher/login', methods=['GET', 'POST'])
def teacher_login():
    if current_user.is_authenticated and current_user.role == 'teacher':
        return redirect(url_for('teacher_dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        db = SessionLocal()
        user = db.query(User).filter(User.username == username, User.role == 'teacher').first()
        db.close()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('teacher_dashboard'))
        else:
            flash('Invalid username or password!', 'error')
    
    return render_template('teacher_login.html')

@app.route('/teacher/dashboard')
@login_required
def teacher_dashboard():
    if current_user.role != 'teacher':
        flash('Access denied! Teachers only.', 'error')
        return redirect(url_for('login'))
    
    return render_template('teacher_dashboard.html', user=current_user)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('login'))

#########################
# STUDENT MANAGEMENT ROUTES (Teacher only)
#########################

@app.route('/students/register', methods=['GET', 'POST'])
@login_required
def register_student():
    """Teacher registers a new student"""
    if current_user.role != 'teacher':
        flash('Access denied! Teachers only.', 'error')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        roll_no = request.form.get('roll_no')
        class_name = request.form.get('class_name')
        email = request.form.get('email')
        
        # Validation
        if not name or not roll_no:
            flash('Name and Roll Number are required!', 'error')
            return render_template('register_student.html')
        
        db = SessionLocal()
        
        # Check if roll number already exists
        existing_student = db.query(Student).filter(Student.roll_no == roll_no).first()
        if existing_student:
            flash('Roll Number already exists! Please use a unique Roll Number.', 'error')
            db.close()
            return render_template('register_student.html')
        
        # Create new student
        new_student = Student(
            name=name,
            roll_no=roll_no,
            class_name=class_name,
            email=email
        )
        
        db.add(new_student)
        db.commit()
        
        # Create user account for this student
        # Default username = roll_no, default password = roll_no
        student_user = User(
            username=roll_no,
            password_hash=generate_password_hash(roll_no),
            role='student',
            student_id=new_student.id,
            email=email
        )
        
        db.add(student_user)
        db.commit()
        
        flash(f'✅ Student registered successfully! Login Credentials - Username: {roll_no}, Password: {roll_no}', 'success')
        db.close()
        
        return redirect(url_for('view_students'))
    
    return render_template('register_student.html')

@app.route('/students/view')
@login_required
def view_students():
    """View all registered students"""
    if current_user.role != 'teacher':
        flash('Access denied! Teachers only.', 'error')
        return redirect(url_for('login'))
    
    db = SessionLocal()
    students = db.query(Student).all()
    db.close()
    
    return render_template('view_students.html', students=students)

#########################
# STUDENT ROUTES
#########################

@app.route('/student/login', methods=['GET', 'POST'])
def student_login():
    if current_user.is_authenticated and current_user.role == 'student':
        return redirect(url_for('student_dashboard'))
    
    if request.method == 'POST':
        roll_no = request.form.get('roll_no')
        password = request.form.get('password')
        
        db = SessionLocal()
        user = db.query(User).filter(User.username == roll_no, User.role == 'student').first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            flash('Login successful! Welcome back.', 'success')
            db.close()
            return redirect(url_for('student_dashboard'))
        else:
            flash('Invalid roll number or password!', 'error')
            db.close()
    
    return render_template('student_login.html')

@app.route('/student/dashboard')
@login_required
def student_dashboard():
    if current_user.role != 'student':
        flash('Access denied! Students only.', 'error')
        return redirect(url_for('login'))
    
    db = SessionLocal()
    student = db.query(Student).get(current_user.student_id)
    
    # Get attendance records for this student
    attendance_records = db.query(Attendance).filter(
        Attendance.student_id == current_user.student_id
    ).order_by(Attendance.date.desc()).all()
    
    db.close()
    
    return render_template('student_dashboard.html', 
                         user=current_user, 
                         student=student,
                         attendance_records=attendance_records)

@app.route('/student/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    if current_user.role != 'student':
        flash('Access denied! Students only.', 'error')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        # Validation
        if not current_password or not new_password:
            flash('All fields are required!', 'error')
            return render_template('change_password.html')
        
        if new_password != confirm_password:
            flash('New passwords do not match!', 'error')
            return render_template('change_password.html')
        
        # Check current password
        if not check_password_hash(current_user.password_hash, current_password):
            flash('Current password is incorrect!', 'error')
            return render_template('change_password.html')
        
        # Update password
        db = SessionLocal()
        user = db.query(User).get(current_user.id)
        user.password_hash = generate_password_hash(new_password)
        db.commit()
        db.close()
        
        flash('Password changed successfully!', 'success')
        return redirect(url_for('student_dashboard'))
    
    return render_template('change_password.html')

# Setup demo route - creates initial test data
@app.route('/setup_demo')
def setup_demo():
    """
    Create demo users for testing
    Teacher: username='teacher1', password='teacher123'
    Student: username='student1', password='student123'
    """
    db = SessionLocal()
    
    try:
        # Create demo teacher if doesn't exist
        if not db.query(User).filter(User.username=='teacher1').first():
            teacher = User(
                username='teacher1',
                password_hash=generate_password_hash('teacher123'),
                role='teacher',
                email='teacher@example.com'
            )
            db.add(teacher)
            print("✅ Demo teacher created: teacher1/teacher123")
        
        # Create demo student if doesn't exist
        if not db.query(Student).filter(Student.roll_no=='S101').first():
            student = Student(
                name='Demo Student',
                roll_no='S101',
                class_name='Class A',
                email='student@example.com'
            )
            db.add(student)
            db.commit()
            
            # Create user account for this student
            student_user = User(
                username='S101',  # username is roll_no
                password_hash=generate_password_hash('S101'),  # default password is roll_no
                role='student',
                student_id=student.id
            )
            db.add(student_user)
            print("✅ Demo student created: S101/S101")
        
        db.commit()
        return """
        <h2>✅ Demo Setup Complete!</h2>
        <p><strong>Teacher Login:</strong></p>
        <ul>
            <li>Username: teacher1</li>
            <li>Password: teacher123</li>
        </ul>
        <p><strong>Student Login:</strong></p>
        <ul>
            <li>Username: S101</li>
            <li>Password: S101</li>
        </ul>
        <p><a href="/login">Go to Login Page</a></p>
        """
    except Exception as e:
        db.rollback()
        return f"<h2>❌ Error setting up demo: {str(e)}</h2>"
    finally:
        db.close()

# Database check route
@app.route('/check_db')
def check_db():
    """Check database status and show table info"""
    db = SessionLocal()
    
    try:
        users_count = db.query(User).count()
        students_count = db.query(Student).count()
        timetable_count = db.query(Timetable).count()
        attendance_count = db.query(Attendance).count()
        
        return f"""
        <h2>📊 Database Status</h2>
        <ul>
            <li><strong>Users:</strong> {users_count}</li>
            <li><strong>Students:</strong> {students_count}</li>
            <li><strong>Timetable Entries:</strong> {timetable_count}</li>
            <li><strong>Attendance Records:</strong> {attendance_count}</li>
        </ul>
        <p><a href="/setup_demo">Setup Demo Data</a></p>
        <p><a href="/login">Go to Login</a></p>
        """
    finally:
        db.close()

if __name__ == '__main__':
    print("=" * 50)
    print("🚀 Starting Attendance System")
    print("=" * 50)
    print("📍 Database initialized at: database.db")
    print("🌐 Server running at: http://localhost:5000")
    print("=" * 50)
    print("\n🔗 Quick Links:")
    print("   - Login: http://localhost:5000/login")
    print("   - Check DB: http://localhost:5000/check_db")
    print("   - Setup Demo: http://localhost:5000/setup_demo")
    print("=" * 50)
    
    app.run(host='0.0.0.0', port=5000, debug=True)
