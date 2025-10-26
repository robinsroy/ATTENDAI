# app.py
import os
import cv2
import base64
import numpy as np
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
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

# Global variable for face recognition enrolled students
ENROLLED = {}

# Load enrolled students at startup
def init_face_recognition():
    """Load all face encodings at application startup"""
    global ENROLLED
    try:
        from face_utils import load_all_enrollments
        ENROLLED = load_all_enrollments()
        print(f"✅ Loaded {len(ENROLLED)} enrolled students for face recognition")
    except Exception as e:
        print(f"⚠️ Warning: Could not load face encodings: {e}")
        ENROLLED = {}

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

@app.route('/students/register-with-face', methods=['GET', 'POST'])
@login_required
def register_student_with_face():
    """Register student with face capture (NEW - Phase 7)"""
    if current_user.role != 'teacher':
        flash('Access denied! Teachers only.', 'error')
        return redirect(url_for('login'))
    
    if request.method == 'GET':
        return render_template('register_student_with_face.html')
    
    # POST - Handle enrollment with face data
    return render_template('register_student_with_face.html')

@app.route('/students/enroll-with-face', methods=['POST'])
@login_required
def enroll_student_with_face():
    """Process student enrollment with face embeddings"""
    if current_user.role != 'teacher':
        return jsonify({'status': 'error', 'message': 'Access denied'}), 403
    
    try:
        # Get form data
        name = request.form.get('name')
        roll_no = request.form.get('roll_no')
        class_name = request.form.get('class_name')
        email = request.form.get('email')
        images = request.form.getlist('images[]')
        
        # Validation
        if not name or not roll_no:
            return jsonify({'status': 'error', 'message': 'Name and Roll Number are required'})
        
        if len(images) == 0:
            return jsonify({'status': 'error', 'message': 'No face images captured'})
        
        db = SessionLocal()
        
        # Check if roll number exists
        existing_student = db.query(Student).filter(Student.roll_no == roll_no).first()
        if existing_student:
            db.close()
            return jsonify({'status': 'error', 'message': 'Roll Number already exists'})
        
        # Create student record
        new_student = Student(
            name=name,
            roll_no=roll_no,
            class_name=class_name,
            email=email
        )
        db.add(new_student)
        db.commit()
        student_id = new_student.id
        
        # Create user account
        student_user = User(
            username=roll_no,
            password_hash=generate_password_hash(roll_no),
            role='student',
            student_id=student_id,
            email=email
        )
        db.add(student_user)
        db.commit()
        
        # Process face images and generate embeddings
        from face_utils import get_embeddings_from_image_bgr, append_embedding_for_student
        import base64
        import numpy as np
        
        successful_embeddings = 0
        failed_images = 0
        
        # Create dataset folder for raw images (optional)
        student_folder = os.path.join('dataset', roll_no)
        os.makedirs(student_folder, exist_ok=True)
        
        for idx, img_data in enumerate(images):
            try:
                # Decode base64 image
                header, encoded = img_data.split(',', 1)
                img_bytes = base64.b64decode(encoded)
                img_array = np.frombuffer(img_bytes, np.uint8)
                img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
                
                # Save raw image (optional)
                cv2.imwrite(os.path.join(student_folder, f'sample_{idx}.jpg'), img)
                
                # Extract face embeddings
                embeddings, faces = get_embeddings_from_image_bgr(img, enforce_detection=False)
                
                # Save embeddings if face detected
                if len(embeddings) > 0:
                    for emb in embeddings:
                        append_embedding_for_student(str(student_id), emb)
                        successful_embeddings += 1
                else:
                    failed_images += 1
                    
            except Exception as e:
                print(f"Error processing image {idx}: {str(e)}")
                failed_images += 1
        
        # Update student record with encodings path
        new_student.encodings_path = f"encodings/{student_id}.npy"
        db.commit()
        db.close()
        
        # Reload enrollment database in memory
        global ENROLLED
        from face_utils import load_all_enrollments
        ENROLLED = load_all_enrollments()
        
        return jsonify({
            'status': 'success',
            'message': f'Student registered! {successful_embeddings} face samples saved.',
            'student_id': student_id,
            'successful_embeddings': successful_embeddings,
            'failed_images': failed_images
        })
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

#########################
# TIMETABLE MANAGEMENT ROUTES (Teacher only)
#########################

@app.route('/timetable/manage', methods=['GET', 'POST'])
@login_required
def manage_timetable():
    """Teacher manages timetable entries"""
    if current_user.role != 'teacher':
        flash('Access denied! Teachers only.', 'error')
        return redirect(url_for('login'))
    
    db = SessionLocal()
    
    if request.method == 'POST':
        class_name = request.form.get('class_name')
        day_of_week = request.form.get('day_of_week')
        period = request.form.get('period')
        subject = request.form.get('subject')
        start_time = request.form.get('start_time')
        end_time = request.form.get('end_time')
        
        # Validation
        if not class_name or not day_of_week or not period:
            flash('Class, Day, and Period are required!', 'error')
        else:
            # Create new timetable entry
            new_entry = Timetable(
                class_name=class_name,
                day_of_week=day_of_week,
                period=period,
                subject=subject,
                start_time=start_time,
                end_time=end_time
            )
            db.add(new_entry)
            db.commit()
            flash(f'Timetable entry added successfully for {class_name} - {day_of_week} - {period}!', 'success')
    
    # Get all timetable entries sorted by day and period
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    timetable_entries = db.query(Timetable).all()
    
    # Sort entries
    timetable_entries.sort(key=lambda x: (day_order.index(x.day_of_week) if x.day_of_week in day_order else 999, x.period))
    
    db.close()
    
    return render_template('manage_timetable.html', timetable_entries=timetable_entries)

@app.route('/timetable/bulk-add', methods=['POST'])
@login_required
def bulk_add_timetable():
    """Add all 5 periods for a day at once"""
    if current_user.role != 'teacher':
        flash('Access denied! Teachers only.', 'error')
        return redirect(url_for('login'))
    
    db = SessionLocal()
    
    class_name = request.form.get('class_name')
    day_of_week = request.form.get('day_of_week')
    
    if not class_name or not day_of_week:
        flash('Class and Day are required!', 'error')
        db.close()
        return redirect(url_for('manage_timetable'))
    
    added_count = 0
    
    # Add all 5 periods
    for i in range(1, 6):
        subject = request.form.get(f'subject_{i}')
        start_time = request.form.get(f'start_time_{i}')
        end_time = request.form.get(f'end_time_{i}')
        
        if subject and start_time and end_time:
            new_entry = Timetable(
                class_name=class_name,
                day_of_week=day_of_week,
                period=str(i),  # Period 1, 2, 3, 4, 5
                subject=subject,
                start_time=start_time,
                end_time=end_time
            )
            db.add(new_entry)
            added_count += 1
    
    db.commit()
    db.close()
    
    flash(f'Successfully added {added_count} periods for {class_name} - {day_of_week}!', 'success')
    return redirect(url_for('manage_timetable'))

@app.route('/timetable/delete/<int:id>', methods=['POST'])
@login_required
def delete_timetable(id):
    """Delete a timetable entry"""
    if current_user.role != 'teacher':
        flash('Access denied! Teachers only.', 'error')
        return redirect(url_for('login'))
    
    db = SessionLocal()
    entry = db.query(Timetable).get(id)
    
    if entry:
        db.delete(entry)
        db.commit()
        flash('Timetable entry deleted successfully!', 'success')
    else:
        flash('Timetable entry not found!', 'error')
    
    db.close()
    return redirect(url_for('manage_timetable'))

@app.route('/timetable/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_timetable(id):
    """Edit a timetable entry"""
    if current_user.role != 'teacher':
        flash('Access denied! Teachers only.', 'error')
        return redirect(url_for('login'))
    
    db = SessionLocal()
    entry = db.query(Timetable).get(id)
    
    if not entry:
        flash('Timetable entry not found!', 'error')
        db.close()
        return redirect(url_for('manage_timetable'))
    
    if request.method == 'POST':
        entry.class_name = request.form.get('class_name')
        entry.day_of_week = request.form.get('day_of_week')
        entry.period = request.form.get('period')
        entry.subject = request.form.get('subject')
        entry.start_time = request.form.get('start_time')
        entry.end_time = request.form.get('end_time')
        
        db.commit()
        flash('Timetable entry updated successfully!', 'success')
        db.close()
        return redirect(url_for('manage_timetable'))
    
    db.close()
    return render_template('edit_timetable.html', entry=entry)

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
    
    # Get timetable for student's class
    timetable_entries = []
    if student.class_name:
        timetable_entries = db.query(Timetable).filter(
            Timetable.class_name == student.class_name
        ).order_by(Timetable.day_of_week, Timetable.period).all()
    
    # Organize timetable by day and period
    days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
    timetable_grid = {}
    all_periods = set()
    
    for entry in timetable_entries:
        if entry.day_of_week not in timetable_grid:
            timetable_grid[entry.day_of_week] = {}
        timetable_grid[entry.day_of_week][entry.period] = entry
        all_periods.add(entry.period)
    
    # Sort periods (Period 1, Period 2, etc.)
    sorted_periods = sorted(list(all_periods), key=lambda x: int(x) if x.isdigit() else (int(x.split()[-1]) if x.split()[-1].isdigit() else 0))
    
    # Get today's date and day
    from datetime import datetime
    today = datetime.now()
    today_date = today.strftime('%Y-%m-%d')
    today_day = today.strftime('%A')
    
    # Create attendance lookup: {period: status} for today
    # Handle both "1" and "Period 1" format
    today_attendance = {}
    for record in attendance_records:
        if record.date == today_date:
            # Store with period number only (normalize)
            period_num = record.period.split()[-1] if ' ' in record.period else record.period
            today_attendance[period_num] = record.status
    
    # Calculate attendance statistics
    total_records = len(attendance_records)
    present_count = sum(1 for r in attendance_records if r.status == 'Present')
    attendance_percentage = round((present_count / total_records * 100), 1) if total_records > 0 else 0
    
    db.close()
    
    return render_template('student_dashboard.html', 
                         user=current_user, 
                         student=student,
                         attendance_records=attendance_records,
                         timetable_grid=timetable_grid,
                         days_order=days_order,
                         sorted_periods=sorted_periods,
                         today_day=today_day,
                         today_date=today_date,
                         today_attendance=today_attendance,
                         attendance_percentage=attendance_percentage,
                         total_records=total_records,
                         present_count=present_count)

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

#########################
# ATTENDANCE ROUTES
#########################

# Global variable for current attendance session
attendance_session = {
    'active': False,
    'class_name': None,
    'period': None,
    'date': None,
    'marked_students': set()
}

@app.route('/attendance/mark')
@login_required
def mark_attendance():
    """Attendance marking page for teachers"""
    if current_user.role != 'teacher':
        flash('Access denied. Teachers only.', 'danger')
        return redirect(url_for('index'))
    
    db = SessionLocal()
    try:
        # Get unique class names from students
        classes = db.query(Student.class_name).distinct().all()
        classes = [c[0] for c in classes if c[0]]
        
        # Count enrolled students (with face encodings)
        enrolled_count = db.query(Student).filter(Student.encodings_path.isnot(None)).count()
        
        return render_template('mark_attendance.html', 
                             classes=classes,
                             enrolled_count=enrolled_count)
    finally:
        db.close()

@app.route('/attendance/start-session', methods=['POST'])
@login_required
def start_attendance_session():
    """Start an attendance marking session"""
    if current_user.role != 'teacher':
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        data = request.json
        class_name = data.get('class_name')
        period = data.get('period')
        
        if not class_name or not period:
            return jsonify({'error': 'Class and period are required'}), 400
        
        from datetime import date
        today = date.today().isoformat()
        
        # Update global session
        attendance_session['active'] = True
        attendance_session['class_name'] = class_name
        attendance_session['period'] = period
        attendance_session['date'] = today
        attendance_session['marked_students'] = set()
        
        return jsonify({
            'success': True,
            'message': 'Attendance session started',
            'session': {
                'class_name': class_name,
                'period': period,
                'date': today
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/attendance/recognize-frame', methods=['POST'])
@login_required
def recognize_frame():
    """Process a video frame and recognize faces"""
    print("🔍 Recognition request received")
    
    if current_user.role != 'teacher':
        print("❌ Access denied - not a teacher")
        return jsonify({'error': 'Access denied'}), 403
    
    if not attendance_session['active']:
        print("❌ No active session")
        return jsonify({'error': 'No active session'}), 400
    
    print(f"✅ Session active: Class={attendance_session['class_name']}, Period={attendance_session['period']}")
    print(f"📊 ENROLLED students: {len(ENROLLED)}")
    
    try:
        data = request.json
        image_data = data.get('image')
        
        if not image_data:
            print("❌ No image data provided")
            return jsonify({'error': 'No image provided'}), 400
        
        print("📸 Decoding image...")
        # Decode base64 image
        image_data = image_data.split(',')[1] if ',' in image_data else image_data
        image_bytes = base64.b64decode(image_data)
        nparr = np.frombuffer(image_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if frame is None:
            print("❌ Invalid image - could not decode")
            return jsonify({'error': 'Invalid image'}), 400
        
        print(f"✅ Image decoded: {frame.shape}")
        
        # Import face recognition functions
        from face_utils import get_embeddings_from_image_bgr, match_embedding_to_db
        
        print("🧠 Extracting face embeddings...")
        # Extract embeddings from frame
        embeddings_list, faces = get_embeddings_from_image_bgr(frame)
        
        if not embeddings_list or len(embeddings_list) == 0:
            print("⚠️ No face detected in frame")
            return jsonify({'recognized': False, 'message': 'No face detected'})
        
        # Use the first detected face
        embedding = embeddings_list[0]
        print(f"✅ Embeddings extracted: shape={embedding.shape}")
        
        # Match against enrolled students
        print(f"🔍 Matching against {len(ENROLLED)} enrolled students...")
        matched_id, confidence = match_embedding_to_db(embedding, ENROLLED, threshold=0.40)
        
        if matched_id is None:
            print("⚠️ No match found")
            return jsonify({'recognized': False, 'message': 'Face not recognized'})
        
        print(f"✅ Match found! Student ID: {matched_id}, Confidence: {confidence}")
        
        # Check if already marked in this session
        if matched_id in attendance_session['marked_students']:
            return jsonify({
                'recognized': True,
                'already_marked': True,
                'message': 'Student already marked in this session'
            })
        
        # Get student info and mark attendance
        db = SessionLocal()
        try:
            student = db.query(Student).filter(Student.id == matched_id).first()
            
            if not student:
                return jsonify({'recognized': False, 'message': 'Student not found in database'})
            
            # Check if already marked today for this period
            from datetime import date
            today = date.today().isoformat()
            
            existing = db.query(Attendance).filter(
                Attendance.student_id == matched_id,
                Attendance.date == today,
                Attendance.period == attendance_session['period']
            ).first()
            
            if existing:
                attendance_session['marked_students'].add(matched_id)
                return jsonify({
                    'recognized': True,
                    'already_marked': True,
                    'student': {
                        'id': student.id,
                        'name': student.name,
                        'roll_no': student.roll_no,
                        'class_name': student.class_name
                    },
                    'message': 'Student already marked today for this period'
                })
            
            # Mark attendance
            attendance = Attendance(
                student_id=matched_id,
                date=today,
                period=attendance_session['period'],
                status='present'
            )
            db.add(attendance)
            db.commit()
            
            # Add to session marked students
            attendance_session['marked_students'].add(matched_id)
            
            return jsonify({
                'recognized': True,
                'newly_marked': True,
                'student': {
                    'id': student.id,
                    'name': student.name,
                    'roll_no': student.roll_no,
                    'class_name': student.class_name
                },
                'confidence': float(confidence),
                'message': f'Attendance marked for {student.name}'
            })
            
        finally:
            db.close()
            
    except Exception as e:
        print(f"Error in recognize_frame: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/attendance/stop-session', methods=['POST'])
@login_required
def stop_attendance_session():
    """Stop the current attendance session"""
    if current_user.role != 'teacher':
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        marked_count = len(attendance_session['marked_students'])
        
        # Reset session
        attendance_session['active'] = False
        attendance_session['class_name'] = None
        attendance_session['period'] = None
        attendance_session['date'] = None
        attendance_session['marked_students'] = set()
        
        return jsonify({
            'success': True,
            'message': f'Session ended. {marked_count} students marked.',
            'marked_count': marked_count
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("=" * 50)
    print("🚀 Starting Attendance System")
    print("=" * 50)
    print("📍 Database initialized at: database.db")
    
    # Initialize face recognition
    init_face_recognition()
    
    print("🌐 Server running at: http://localhost:5000")
    print("=" * 50)
    print("\n🔗 Quick Links:")
    print("   - Login: http://localhost:5000/login")
    print("   - Check DB: http://localhost:5000/check_db")
    print("   - Setup Demo: http://localhost:5000/setup_demo")
    print("=" * 50)
    
    app.run(host='0.0.0.0', port=5000, debug=True)
