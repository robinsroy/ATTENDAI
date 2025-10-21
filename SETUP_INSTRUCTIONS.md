# AttendAI - Setup Instructions

## Quick Start Command

**Always use this command to activate the environment and install packages:**

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass; .\attend\Scripts\Activate.ps1; pip install -r requirements.txt
```

## Why This Command?

- **Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass**: Allows PowerShell to run the activation script (only affects current PowerShell session)
- **.\attend\Scripts\Activate.ps1**: Activates the 'attend' virtual environment
- **pip install -r requirements.txt**: Installs all required packages

## Running the Application

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass; .\attend\Scripts\Activate.ps1; python app.py
```

Then open your browser to: **http://127.0.0.1:5000**

## Installed Packages (requirements.txt)

```
Flask==2.3.2
SQLAlchemy==2.0.21
flask-login==0.6.2
Werkzeug==2.3.8
numpy==1.23.5
opencv-python==4.9.0.80
deepface==0.0.79
tensorflow==2.13.0
pandas==2.2.2
openpyxl==3.1.2
Pillow==10.0.0
```

## Fixed Dependency Issues

The project had TensorFlow/ml_dtypes compatibility issues which were resolved by:
1. Upgrading pip to latest version (25.2)
2. Using TensorFlow 2.13.0 with compatible dependencies
3. Allowing TensorFlow to manage its sub-dependencies (jax, jaxlib, ml-dtypes, protobuf)

## Current Status

✅ **Phase 1-7 Complete:**
- Teacher registration and authentication
- Student registration (basic and with face)
- Student login and dashboard
- Timetable management
- Face capture with webcam (15 frames)
- Face embedding extraction working

🚀 **Next Phase:**
- Phase 8: Real-time attendance marking with face recognition

## Troubleshooting

If you encounter import errors:
1. Make sure virtual environment is activated (you should see `(attend)` in terminal)
2. Re-run the installation command above
3. Check Python version is 3.10.11: `python --version`

## Project Structure

```
AttendAI/
├── attend/              # Virtual environment
├── templates/           # HTML templates
├── static/             # CSS, JS, images
├── encodings/          # Face embeddings (.npy files)
├── dataset/            # Face images organized by roll number
├── app.py              # Main Flask application
├── models.py           # Database models
├── face_utils.py       # Face recognition utilities
├── database.db         # SQLite database
└── requirements.txt    # Python dependencies
```
