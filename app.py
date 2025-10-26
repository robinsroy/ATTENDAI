# app.py
import os
import csv
import cv2
import base64
import numpy as np
from io import StringIO
from datetime import datetime, timedelta
from collections import defaultdict
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, make_response
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
        elif current_user.role == 'admin':
            return redirect(url_for('admin_dashboard'))
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
    if current_user.is_authenticated:
        if current_user.role == 'teacher':
            return redirect(url_for('teacher_dashboard'))
        elif current_user.role == 'admin':
            return redirect(url_for('admin_dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        db = SessionLocal()
        # Allow both teacher and admin login through this page
        user = db.query(User).filter(
            User.username == username,
            User.role.in_(['teacher', 'admin'])
        ).first()
        db.close()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            flash('Login successful!', 'success')
            # Redirect based on role
            if user.role == 'admin':
                return redirect(url_for('admin_dashboard'))
            else:
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

@app.route('/teacher/settings', methods=['GET', 'POST'])
@login_required
def teacher_settings():
    """Teacher settings page - profile, preferences, password change"""
    if current_user.role != 'teacher':
        flash('Access denied! Teachers only.', 'error')
        return redirect(url_for('login'))
    
    db = SessionLocal()
    teacher = db.query(User).get(current_user.id)
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'update_profile':
            # Update profile information
            teacher.full_name = request.form.get('full_name')
            teacher.email = request.form.get('email')
            teacher.phone = request.form.get('phone')
            teacher.department = request.form.get('department')
            teacher.subject = request.form.get('subject')
            
            db.commit()
            flash('Profile updated successfully!', 'success')
        
        elif action == 'upload_photo':
            if 'profile_photo' not in request.files:
                flash('No file uploaded!', 'error')
            else:
                file = request.files['profile_photo']
                if file.filename == '':
                    flash('No file selected!', 'error')
                elif file:
                    # Save profile photo
                    import os
                    from werkzeug.utils import secure_filename
                    
                    # Create uploads directory if not exists
                    upload_folder = os.path.join('static', 'uploads', 'teachers')
                    os.makedirs(upload_folder, exist_ok=True)
                    
                    # Save with teacher username as filename
                    ext = os.path.splitext(file.filename)[1]
                    filename = f"{teacher.username}{ext}"
                    filepath = os.path.join(upload_folder, filename)
                    file.save(filepath)
                    
                    # Update teacher record
                    teacher.profile_photo = f"uploads/teachers/{filename}"
                    db.commit()
                    flash('Profile photo updated successfully!', 'success')
        
        elif action == 'change_password':
            current_password = request.form.get('current_password')
            new_password = request.form.get('new_password')
            confirm_password = request.form.get('confirm_password')
            
            # Validation
            if not current_password or not new_password or not confirm_password:
                flash('All password fields are required!', 'error')
            elif new_password != confirm_password:
                flash('New passwords do not match!', 'error')
            elif not check_password_hash(teacher.password_hash, current_password):
                flash('Current password is incorrect!', 'error')
            else:
                # Update password
                teacher.password_hash = generate_password_hash(new_password)
                db.commit()
                flash('Password changed successfully!', 'success')
    
    # Get statistics for dashboard
    total_students = db.query(Student).count()
    total_attendance = db.query(Attendance).count()
    total_classes = len(set([s.class_name for s in db.query(Student).all() if s.class_name]))
    
    db.close()
    
    return render_template('teacher_settings.html',
                         user=current_user,
                         teacher=teacher,
                         total_students=total_students,
                         total_attendance=total_attendance,
                         total_classes=total_classes)

@app.route('/reports/analytics')
@login_required
def reports_analytics():
    """View attendance reports and analytics"""
    if current_user.role != 'teacher':
        flash('Access denied! Teachers only.', 'error')
        return redirect(url_for('login'))
    
    db = SessionLocal()
    
    # Get all students
    students = db.query(Student).all()
    
    # Get all attendance records
    attendance_records = db.query(Attendance).all()
    
    # Calculate statistics
    total_students = len(students)
    enrolled_students = len([s for s in students if s.encodings_path])
    pending_students = total_students - enrolled_students
    
    # Get unique classes
    classes = list(set([s.class_name for s in students if s.class_name]))
    
    # Calculate period-wise statistics
    period_stats = defaultdict(lambda: {'total': 0, 'present': 0, 'absent': 0})
    for record in attendance_records:
        period = record.period
        period_stats[period]['total'] += 1
        if record.status.lower() == 'present':
            period_stats[period]['present'] += 1
        else:
            period_stats[period]['absent'] += 1
    
    # Calculate student-wise statistics
    student_stats = []
    for student in students:
        student_records = [r for r in attendance_records if r.student_id == student.id]
        total_records = len(student_records)
        present_count = len([r for r in student_records if r.status.lower() == 'present'])
        absent_count = total_records - present_count
        attendance_percentage = (present_count / total_records * 100) if total_records > 0 else 0
        
        student_stats.append({
            'id': student.id,
            'name': student.name,
            'roll_no': student.roll_no,
            'class_name': student.class_name or '-',
            'total_records': total_records,
            'present': present_count,
            'absent': absent_count,
            'percentage': round(attendance_percentage, 2)
        })
    
    # Sort by percentage (descending)
    student_stats.sort(key=lambda x: x['percentage'], reverse=True)
    
    # Class-wise statistics
    class_stats = defaultdict(lambda: {'students': 0, 'total_records': 0, 'present': 0, 'absent': 0})
    for student in students:
        class_name = student.class_name or 'No Class'
        class_stats[class_name]['students'] += 1
        student_records = [r for r in attendance_records if r.student_id == student.id]
        class_stats[class_name]['total_records'] += len(student_records)
        class_stats[class_name]['present'] += len([r for r in student_records if r.status.lower() == 'present'])
        class_stats[class_name]['absent'] += len([r for r in student_records if r.status.lower() == 'absent'])
    
    # Calculate overall statistics
    total_attendance_records = len(attendance_records)
    total_present = len([r for r in attendance_records if r.status.lower() == 'present'])
    total_absent = total_attendance_records - total_present
    overall_percentage = (total_present / total_attendance_records * 100) if total_attendance_records > 0 else 0
    
    # Prepare chart data (arrays for Chart.js)
    class_names = sorted(list(class_stats.keys()))
    class_present_data = [class_stats[c]['present'] for c in class_names]
    class_absent_data = [class_stats[c]['absent'] for c in class_names]
    
    period_names = sorted(list(period_stats.keys()))
    period_present_data = [period_stats[p]['present'] for p in period_names]
    period_absent_data = [period_stats[p]['absent'] for p in period_names]
    
    db.close()
    
    return render_template('reports_analytics.html',
                         total_students=total_students,
                         enrolled_students=enrolled_students,
                         pending_students=pending_students,
                         classes=classes,
                         total_attendance_records=total_attendance_records,
                         total_present=total_present,
                         total_absent=total_absent,
                         overall_percentage=round(overall_percentage, 2),
                         student_stats=student_stats,
                         period_stats=dict(period_stats),
                         class_stats=dict(class_stats),
                         class_names=class_names,
                         class_present_data=class_present_data,
                         class_absent_data=class_absent_data,
                         period_names=period_names,
                         period_present_data=period_present_data,
                         period_absent_data=period_absent_data)

@app.route('/reports/download')
@login_required
def download_report():
    """Download attendance report as CSV"""
    if current_user.role != 'teacher':
        flash('Access denied! Teachers only.', 'error')
        return redirect(url_for('login'))
    
    db = SessionLocal()
    
    # Get all attendance records with student info
    attendance_records = db.query(Attendance).order_by(Attendance.date.desc(), Attendance.period).all()
    
    # Create CSV in memory
    si = StringIO()
    writer = csv.writer(si)
    
    # Write header
    writer.writerow(['Roll Number', 'Student Name', 'Class', 'Date', 'Period', 'Status'])
    
    # Write attendance records
    for record in attendance_records:
        student = db.query(Student).filter_by(id=record.student_id).first()
        if student:
            # Handle date - might be string or date object
            date_str = record.date if isinstance(record.date, str) else record.date.strftime('%Y-%m-%d')
            
            writer.writerow([
                student.roll_no,
                student.name,
                student.class_name or '-',
                date_str,
                record.period,
                record.status
            ])
    
    db.close()
    
    # Create response
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = f"attachment; filename=attendance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    output.headers["Content-type"] = "text/csv"
    
    return output

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
    if current_user.role not in ['teacher', 'admin']:
        flash('Access denied! Teachers and admins only.', 'error')
        return redirect(url_for('login'))
    
    db = SessionLocal()
    students = db.query(Student).all()
    db.close()
    
    return render_template('view_students.html', students=students)

@app.route('/students/delete/<int:id>', methods=['POST'])
@login_required
def delete_student(id):
    """Delete a student and all associated data"""
    if current_user.role != 'teacher':
        flash('Access denied! Teachers only.', 'error')
        return redirect(url_for('login'))
    
    db = SessionLocal()
    try:
        # Find the student
        student = db.query(Student).filter_by(id=id).first()
        if not student:
            flash('Student not found!', 'error')
            return redirect(url_for('view_students'))
        
        student_name = student.name
        roll_no = student.roll_no
        
        # Delete face encodings file if it exists
        if student.encodings_path and os.path.exists(student.encodings_path):
            try:
                os.remove(student.encodings_path)
            except Exception as e:
                print(f"Error deleting encodings file: {e}")
        
        # Delete associated user account
        user = db.query(User).filter_by(username=student.roll_no).first()
        if user:
            db.delete(user)
        
        # Delete all attendance records for this student
        db.query(Attendance).filter_by(student_id=id).delete()
        
        # Delete the student record
        db.delete(student)
        db.commit()
        
        flash(f'✅ Student {student_name} (Roll: {roll_no}) has been deleted successfully!', 'success')
    except Exception as e:
        db.rollback()
        flash(f'❌ Error deleting student: {str(e)}', 'error')
    finally:
        db.close()
    
    return redirect(url_for('view_students'))

@app.route('/students/register-with-face', methods=['GET', 'POST'])
@login_required
def register_student_with_face():
    """Register student with face capture (NEW - Phase 7)"""
    if current_user.role != 'teacher':
        flash('Access denied! Teachers only.', 'error')
        return redirect(url_for('login'))
    
    if request.method == 'GET':
        # Check if we're completing enrollment for an existing student
        student_id = request.args.get('student_id')
        student_data = None
        
        if student_id:
            db = SessionLocal()
            student = db.query(Student).filter_by(id=int(student_id)).first()
            if student:
                student_data = {
                    'id': student.id,
                    'name': student.name,
                    'roll_no': student.roll_no,
                    'class_name': student.class_name,
                    'email': student.email
                }
            db.close()
        
        return render_template('register_student_with_face.html', student=student_data)
    
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
        student_id = request.form.get('student_id')  # For completing enrollment
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
        
        # Check if we're completing enrollment for existing student
        if student_id:
            # Completing enrollment for existing student
            existing_student = db.query(Student).filter_by(id=int(student_id)).first()
            if not existing_student:
                db.close()
                return jsonify({'status': 'error', 'message': 'Student not found'})
            
            student_id = existing_student.id
            is_new_student = False
        else:
            # New student registration
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
            is_new_student = True
        
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
        student = db.query(Student).filter_by(id=student_id).first()
        student.encodings_path = f"encodings/{student_id}.npy"
        db.commit()
        db.close()
        
        # Reload enrollment database in memory
        global ENROLLED
        from face_utils import load_all_enrollments
        ENROLLED = load_all_enrollments()
        
        success_message = f'Face enrollment completed! {successful_embeddings} face samples saved.' if not is_new_student else f'Student registered! {successful_embeddings} face samples saved.'
        
        return jsonify({
            'status': 'success',
            'message': success_message,
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
# ADMIN ROUTES
#########################

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    """Admin dashboard - user management and system overview"""
    if current_user.role != 'admin':
        flash('Access denied! Admins only.', 'error')
        return redirect(url_for('login'))
    
    db = SessionLocal()
    
    # Get statistics
    total_teachers = db.query(User).filter(User.role == 'teacher').count()
    total_students = db.query(Student).count()
    total_classes = db.query(Student.class_name).distinct().count()
    total_attendance = db.query(Attendance).count()
    
    # Get recent users (last 10)
    recent_teachers = db.query(User).filter(User.role == 'teacher').order_by(User.id.desc()).limit(5).all()
    recent_students = db.query(Student).order_by(Student.id.desc()).limit(5).all()
    
    db.close()
    
    return render_template('admin_dashboard.html',
                         total_teachers=total_teachers,
                         total_students=total_students,
                         total_classes=total_classes,
                         total_attendance=total_attendance,
                         recent_teachers=recent_teachers,
                         recent_students=recent_students)

@app.route('/admin/users')
@login_required
def admin_users():
    """View and manage all users (teachers and students)"""
    if current_user.role != 'admin':
        flash('Access denied! Admins only.', 'error')
        return redirect(url_for('login'))
    
    db = SessionLocal()
    
    # Get all teachers
    teachers = db.query(User).filter(User.role == 'teacher').all()
    
    # Get all students with their user accounts
    students = db.query(Student).all()
    
    db.close()
    
    return render_template('admin_users.html', teachers=teachers, students=students)

@app.route('/admin/users/delete/<user_type>/<int:user_id>', methods=['POST'])
@login_required
def admin_delete_user(user_type, user_id):
    """Delete a user (teacher or student)"""
    if current_user.role != 'admin':
        return jsonify({'error': 'Access denied'}), 403
    
    db = SessionLocal()
    
    try:
        if user_type == 'teacher':
            user = db.query(User).filter(User.id == user_id, User.role == 'teacher').first()
            if user:
                db.delete(user)
                db.commit()
                flash(f'Teacher {user.username} deleted successfully!', 'success')
            else:
                flash('Teacher not found!', 'error')
                
        elif user_type == 'student':
            student = db.query(Student).filter(Student.id == user_id).first()
            if student:
                # Delete associated user account if exists
                if student.user_account:
                    db.delete(student.user_account)
                # Delete attendance records
                db.query(Attendance).filter(Attendance.student_id == user_id).delete()
                # Delete student
                db.delete(student)
                db.commit()
                flash(f'Student {student.name} deleted successfully!', 'success')
            else:
                flash('Student not found!', 'error')
        
        db.close()
        
    except Exception as e:
        db.rollback()
        db.close()
        flash(f'Error deleting user: {str(e)}', 'error')
    
    return redirect(url_for('admin_users'))

@app.route('/admin/analytics')
@login_required
def admin_analytics():
    """Admin analytics - dedicated admin analytics page"""
    if current_user.role != 'admin':
        flash('Access denied! Admins only.', 'error')
        return redirect(url_for('login'))
    
    db = SessionLocal()
    
    # Get all teachers
    total_teachers = db.query(User).filter(User.role == 'teacher').count()
    
    # Get all students
    students = db.query(Student).all()
    
    # Get all attendance records
    attendance_records = db.query(Attendance).all()
    
    # Calculate statistics
    total_students = len(students)
    enrolled_students = len([s for s in students if s.encodings_path])
    pending_students = total_students - enrolled_students
    
    # Get unique classes
    classes = list(set([s.class_name for s in students if s.class_name]))
    
    # Calculate period-wise statistics
    from collections import defaultdict
    period_stats = defaultdict(lambda: {'total': 0, 'present': 0, 'absent': 0})
    for record in attendance_records:
        period = record.period
        period_stats[period]['total'] += 1
        if record.status.lower() == 'present':
            period_stats[period]['present'] += 1
        else:
            period_stats[period]['absent'] += 1
    
    # Calculate student-wise statistics
    student_stats = []
    for student in students:
        student_records = [r for r in attendance_records if r.student_id == student.id]
        total_records = len(student_records)
        present_count = len([r for r in student_records if r.status.lower() == 'present'])
        absent_count = total_records - present_count
        attendance_percentage = (present_count / total_records * 100) if total_records > 0 else 0
        
        student_stats.append({
            'id': student.id,
            'name': student.name,
            'roll_no': student.roll_no,
            'class_name': student.class_name or '-',
            'total_records': total_records,
            'present': present_count,
            'absent': absent_count,
            'percentage': round(attendance_percentage, 2)
        })
    
    # Sort by percentage (descending)
    student_stats.sort(key=lambda x: x['percentage'], reverse=True)
    
    # Class-wise statistics
    class_stats = defaultdict(lambda: {'students': 0, 'total_records': 0, 'present': 0, 'absent': 0})
    for student in students:
        class_name = student.class_name or 'No Class'
        class_stats[class_name]['students'] += 1
        student_records = [r for r in attendance_records if r.student_id == student.id]
        class_stats[class_name]['total_records'] += len(student_records)
        class_stats[class_name]['present'] += len([r for r in student_records if r.status.lower() == 'present'])
        class_stats[class_name]['absent'] += len([r for r in student_records if r.status.lower() == 'absent'])
    
    # Calculate overall statistics
    total_attendance_records = len(attendance_records)
    total_present = len([r for r in attendance_records if r.status.lower() == 'present'])
    total_absent = total_attendance_records - total_present
    overall_percentage = (total_present / total_attendance_records * 100) if total_attendance_records > 0 else 0
    
    # Prepare chart data (arrays for Chart.js)
    class_names = sorted(list(class_stats.keys()))
    class_present_data = [class_stats[c]['present'] for c in class_names]
    class_absent_data = [class_stats[c]['absent'] for c in class_names]
    
    period_names = sorted(list(period_stats.keys()))
    period_present_data = [period_stats[p]['present'] for p in period_names]
    period_absent_data = [period_stats[p]['absent'] for p in period_names]
    
    db.close()
    
    return render_template('admin_analytics.html',
                         total_teachers=total_teachers,
                         total_students=total_students,
                         enrolled_students=enrolled_students,
                         pending_students=pending_students,
                         classes=classes,
                         total_records=total_attendance_records,
                         total_attendance_records=total_attendance_records,
                         total_present=total_present,
                         total_absent=total_absent,
                         overall_percentage=round(overall_percentage, 1),
                         student_stats=student_stats,
                         class_stats=dict(class_stats),
                         period_stats=dict(period_stats),
                         class_names=class_names,
                         class_present_data=class_present_data,
                         class_absent_data=class_absent_data,
                         period_names=period_names,
                         period_present_data=period_present_data,
                         period_absent_data=period_absent_data,
                         is_admin=True)

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
        # Convert period to int for consistency with attendance table
        period_int = int(entry.period) if entry.period.isdigit() else int(entry.period.split()[-1])
        timetable_grid[entry.day_of_week][period_int] = entry
        all_periods.add(period_int)
    
    # Sort periods (already integers now)
    sorted_periods = sorted(list(all_periods))
    
    # Get today's date and day
    from datetime import datetime
    today = datetime.now()
    today_date = today.strftime('%Y-%m-%d')
    today_day = today.strftime('%A')
    
    # Create attendance lookup: {period: status} for today
    today_attendance = {}
    for record in attendance_records:
        if record.date == today_date:
            # period is already an integer in the database
            today_attendance[record.period] = record.status
    
    # Calculate attendance statistics
    total_records = len(attendance_records)
    present_count = sum(1 for r in attendance_records if r.status.lower() == 'present')
    absent_count = sum(1 for r in attendance_records if r.status.lower() == 'absent')
    
    # Get unique dates to count total days
    unique_dates = len(set([r.date for r in attendance_records]))
    
    # Calculate percentage: (days present / total days) * 100
    # Count unique dates where student was present
    present_dates = set([r.date for r in attendance_records if r.status.lower() == 'present'])
    days_present = len(present_dates)
    days_absent = unique_dates - days_present
    
    # Calculate overall attendance percentage based on unique days
    attendance_percentage = round((days_present / unique_dates * 100), 1) if unique_dates > 0 else 0.0
    
    # Load student data before closing session to avoid DetachedInstanceError
    student_data = {
        'id': student.id,
        'name': student.name,
        'roll_no': student.roll_no,
        'class_name': student.class_name,
        'email': student.email,
        'profile_photo': student.profile_photo,
        'encodings_path': student.encodings_path
    }
    
    # Convert timetable entries to dict to avoid DetachedInstanceError
    timetable_dict = {}
    for day, periods in timetable_grid.items():
        timetable_dict[day] = {}
        for period, entry in periods.items():
            timetable_dict[day][period] = {
                'subject': entry.subject,
                'start_time': entry.start_time,
                'end_time': entry.end_time,
                'day_of_week': entry.day_of_week,
                'period': entry.period
            }
    
    # Convert attendance records to list of dicts
    attendance_list = [{
        'date': r.date,
        'period': r.period,
        'status': r.status
    } for r in attendance_records]
    
    db.close()
    
    return render_template('student_dashboard.html', 
                         user=current_user, 
                         student=student_data,
                         attendance_records=attendance_list,
                         timetable_grid=timetable_dict,
                         days_order=days_order,
                         sorted_periods=sorted_periods,
                         today_day=today_day,
                         today_date=today_date,
                         today_attendance=today_attendance,
                         attendance_percentage=attendance_percentage,
                         total_records=total_records,
                         present_count=days_present,
                         absent_count=days_absent,
                         unique_dates=unique_dates)

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

@app.route('/student/profile', methods=['GET', 'POST'])
@login_required
def student_profile():
    """Student profile page - view details, change password, upload photo"""
    if current_user.role != 'student':
        flash('Access denied! Students only.', 'error')
        return redirect(url_for('login'))
    
    db = SessionLocal()
    student = db.query(Student).get(current_user.student_id)
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'change_password':
            current_password = request.form.get('current_password')
            new_password = request.form.get('new_password')
            confirm_password = request.form.get('confirm_password')
            
            # Validation
            if not current_password or not new_password or not confirm_password:
                flash('All password fields are required!', 'error')
            elif new_password != confirm_password:
                flash('New passwords do not match!', 'error')
            elif not check_password_hash(current_user.password_hash, current_password):
                flash('Current password is incorrect!', 'error')
            else:
                # Update password
                user = db.query(User).get(current_user.id)
                user.password_hash = generate_password_hash(new_password)
                db.commit()
                flash('Password changed successfully!', 'success')
        
        elif action == 'upload_photo':
            if 'profile_photo' not in request.files:
                flash('No file uploaded!', 'error')
            else:
                file = request.files['profile_photo']
                if file.filename == '':
                    flash('No file selected!', 'error')
                elif file:
                    # Save profile photo
                    import os
                    from werkzeug.utils import secure_filename
                    
                    # Create uploads directory if not exists
                    upload_folder = os.path.join('static', 'uploads', 'profiles')
                    os.makedirs(upload_folder, exist_ok=True)
                    
                    # Save with student roll number as filename
                    ext = os.path.splitext(file.filename)[1]
                    filename = f"{student.roll_no}{ext}"
                    filepath = os.path.join(upload_folder, filename)
                    file.save(filepath)
                    
                    # Update student record
                    student.profile_photo = f"uploads/profiles/{filename}"
                    db.commit()
                    flash('Profile photo updated successfully!', 'success')
    
    # Get attendance statistics
    attendance_records = db.query(Attendance).filter(
        Attendance.student_id == current_user.student_id
    ).all()
    
    # Count unique dates where student was present
    unique_dates = len(set([r.date for r in attendance_records]))
    present_dates = set([r.date for r in attendance_records if r.status.lower() == 'present'])
    days_present = len(present_dates)
    days_absent = unique_dates - days_present
    
    total_records = len(attendance_records)
    attendance_percentage = round((days_present / unique_dates * 100), 1) if unique_dates > 0 else 0.0
    
    # Load student data before closing session to avoid DetachedInstanceError
    student_data = {
        'id': student.id,
        'name': student.name,
        'roll_no': student.roll_no,
        'class_name': student.class_name,
        'email': student.email,
        'profile_photo': student.profile_photo,
        'encodings_path': student.encodings_path
    }
    
    db.close()
    
    return render_template('student_profile.html',
                         user=current_user,
                         student=student_data,
                         total_records=total_records,
                         present_count=days_present,
                         absent_count=days_absent,
                         attendance_percentage=attendance_percentage)

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
        matched_id, confidence = match_embedding_to_db(embedding, ENROLLED, threshold=0.60)
        
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
                # Only allow overwrite if currently marked as absent
                if existing.status.lower() == 'absent':
                    existing.status = 'present'
                    db.commit()
                    attendance_session['marked_students'].add(matched_id)
                    return jsonify({
                        'recognized': True,
                        'updated': True,
                        'student': {
                            'id': student.id,
                            'name': student.name,
                            'roll_no': student.roll_no,
                            'class_name': student.class_name
                        },
                        'message': f'Attendance updated from ABSENT to PRESENT for {student.name}'
                    })
                else:
                    # Already marked present - don't overwrite
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
                        'message': f'{student.name} is already marked PRESENT for this period'
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
    """Stop the current attendance session and mark absent students"""
    if current_user.role != 'teacher':
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        if not attendance_session['active']:
            return jsonify({'error': 'No active session'}), 400
        
        db = SessionLocal()
        try:
            # Get all students in the class
            class_name = attendance_session['class_name']
            period = attendance_session['period']
            date_today = attendance_session['date']
            
            # Get all enrolled students in this class
            students_in_class = db.query(Student).filter(
                Student.class_name == class_name,
                Student.encodings_path.isnot(None)  # Only enrolled students
            ).all()
            
            marked_present_count = len(attendance_session['marked_students'])
            marked_absent_count = 0
            
            # Mark absent for students who were not detected
            for student in students_in_class:
                if student.id not in attendance_session['marked_students']:
                    # Check if already has a record for today's period
                    existing = db.query(Attendance).filter(
                        Attendance.student_id == student.id,
                        Attendance.date == date_today,
                        Attendance.period == period
                    ).first()
                    
                    if not existing:
                        # Create new absent record
                        attendance = Attendance(
                            student_id=student.id,
                            date=date_today,
                            period=period,
                            status='absent'
                        )
                        db.add(attendance)
                        marked_absent_count += 1
                    # If existing and was already marked absent, keep it
            
            db.commit()
            
            # Reset session
            marked_count = marked_present_count
            attendance_session['active'] = False
            attendance_session['class_name'] = None
            attendance_session['period'] = None
            attendance_session['date'] = None
            attendance_session['marked_students'] = set()
            
            return jsonify({
                'success': True,
                'message': f'Session ended. {marked_present_count} present, {marked_absent_count} marked absent.',
                'marked_present': marked_present_count,
                'marked_absent': marked_absent_count,
                'total_marked': marked_present_count + marked_absent_count
            })
        finally:
            db.close()
            
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
