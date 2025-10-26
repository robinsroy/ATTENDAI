# models.py
from sqlalchemy import Column, Integer, String, Date, Time, ForeignKey
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import date
from flask_login import UserMixin

Base = declarative_base()
engine = create_engine('sqlite:///database.db', echo=False, future=True)
SessionLocal = sessionmaker(bind=engine)

class User(UserMixin, Base):
    """User table for both teachers and students"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False)  # 'teacher' or 'student'
    email = Column(String, nullable=True)
    student_id = Column(Integer, ForeignKey('students.id'), nullable=True)  # Link to student record if role is student
    
    # Teacher profile fields
    full_name = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    profile_photo = Column(String, nullable=True)
    department = Column(String, nullable=True)
    subject = Column(String, nullable=True)
    
    # Relationship
    student = relationship("Student", back_populates="user", foreign_keys=[student_id])
    
    # Flask-login required methods (UserMixin provides default implementations)
    def get_id(self):
        return str(self.id)

class Student(Base):
    """Student information table"""
    __tablename__ = 'students'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    roll_no = Column(String, unique=True, nullable=False)
    class_name = Column(String, nullable=True)
    email = Column(String, nullable=True)
    encodings_path = Column(String, nullable=True)  # path to .npy file with face embeddings
    profile_photo = Column(String, nullable=True)  # path to profile photo
    
    # Relationship
    user = relationship("User", back_populates="student", foreign_keys=[User.student_id])
    attendance_records = relationship("Attendance", back_populates="student")

class Timetable(Base):
    """Timetable/Schedule table"""
    __tablename__ = 'timetable'
    
    id = Column(Integer, primary_key=True)
    class_name = Column(String, nullable=False)
    day_of_week = Column(String, nullable=False)  # e.g., 'Monday', 'Tuesday'
    period = Column(String, nullable=False)       # e.g., 'Period 1', 'Period 2'
    subject = Column(String, nullable=True)       # e.g., 'Mathematics', 'Physics'
    start_time = Column(String, nullable=True)    # e.g., '09:00'
    end_time = Column(String, nullable=True)      # e.g., '10:00'

class Attendance(Base):
    """Attendance records table"""
    __tablename__ = 'attendance'
    
    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey('students.id'), nullable=False)
    date = Column(String, default=date.today().isoformat())
    period = Column(String, nullable=False)
    status = Column(String, default='Present')  # 'Present' or 'Absent'
    
    # Relationship
    student = relationship("Student", back_populates="attendance_records")

# Function to initialize the database
def init_db():
    """Create all tables in the database"""
    Base.metadata.create_all(engine)
    print("✅ Database tables created successfully!")

if __name__ == '__main__':
    init_db()
