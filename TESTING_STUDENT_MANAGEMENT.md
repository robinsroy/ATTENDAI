# Testing Guide - Student Management Features

## Quick Start Testing

### Prerequisites
1. Server is running: `python app.py`
2. You have a teacher account
3. You have at least one student registered (with and without face)

---

## Test 1: Delete Student with Face Enrolled

### Setup:
- Need a student with face enrollment completed

### Steps:
1. **Login as Teacher**
   - Go to: http://localhost:5000/teacher/login
   - Use your teacher credentials

2. **Navigate to Students**
   - Click "View Students" from dashboard
   - OR go to: http://localhost:5000/students/view

3. **Identify Test Student**
   - Find a student with "✅ Face Enrolled" status
   - Note their name and roll number

4. **Click Delete Button**
   - Find the "🗑️ Delete" button in Actions column
   - Click it

5. **Verify Modal Appears**
   - ✅ Modal should overlay the page
   - ✅ Should show student name and roll number
   - ✅ Should list what will be deleted:
     - Student record
     - Face encodings
     - User account
     - All attendance records
   - ✅ Should show red warning: "This action cannot be undone!"

6. **Test Cancel**
   - Click "Cancel" button
   - ✅ Modal should close
   - ✅ Student should still be in the list
   - Try again and press ESC key
   - ✅ Modal should close
   - Try again and click outside modal
   - ✅ Modal should close

7. **Confirm Deletion**
   - Click delete button again
   - Click "Delete Student" button
   - ✅ Should redirect to view students page
   - ✅ Should show success message: "✅ Student [Name] (Roll: [Number]) has been deleted successfully!"
   - ✅ Student should no longer appear in the list

8. **Verify Data Removed**
   ```python
   # Check encodings folder
   # File encodings/[student_id].npy should be deleted
   
   # Try to login as deleted student
   # Should fail with "Invalid credentials"
   ```

---

## Test 2: Delete Student WITHOUT Face (Pending)

### Setup:
- Need a student registered but no face enrolled yet

### Steps:
1. **Find Pending Student**
   - Look for student with "⏳ Pending" status badge

2. **Click Delete**
   - Click "🗑️ Delete" button

3. **Verify Modal**
   - ✅ Should show student information
   - ✅ Should show deletion warning

4. **Confirm Deletion**
   - Click "Delete Student"
   - ✅ Should delete successfully
   - ✅ No error about missing encodings file

---

## Test 3: Complete Face Enrollment

### Setup:
- Need a student with "Pending" status

### Steps:
1. **Verify Button Visibility**
   - ✅ Students with "✅ Face Enrolled" should NOT show enrollment button
   - ✅ Students with "⏳ Pending" should show "📸 Enroll Face" button

2. **Click Enroll Face Button**
   - Find pending student
   - Click "📸 Enroll Face" button

3. **Verify Redirect**
   - ✅ Should redirect to: `/students/register-with-face?student_id=[ID]`
   - ✅ Should show form with student info

4. **Verify Pre-filled Data**
   - ✅ Name field should be filled and read-only
   - ✅ Roll number should be filled and read-only
   - ✅ Class should be filled and read-only
   - ✅ Email should be filled and read-only
   - ✅ Should show blue info banner: "📌 Completing Face Enrollment"

5. **Complete Enrollment**
   - Click "Next: Capture Face →"
   - Allow camera access
   - Capture at least 5 face images
   - Click "Complete Enrollment"

6. **Verify Success**
   - ✅ Should show success message: "Face enrollment completed! X face samples saved."
   - ✅ Click "View Students"
   - ✅ Student should now show "✅ Face Enrolled" status
   - ✅ "📸 Enroll Face" button should be gone
   - ✅ Only "🗑️ Delete" button should remain

7. **Verify Student Can Login**
   - Logout from teacher account
   - Go to: http://localhost:5000/student/login
   - Login with student credentials (roll_no as username and password)
   - ✅ Should login successfully

---

## Test 4: Error Handling

### Test 4a: Invalid Student ID (Delete)
1. Open browser console (F12)
2. Try to access: http://localhost:5000/students/delete/99999 (POST)
3. ✅ Should show error: "Student not found!"

### Test 4b: Non-Teacher Access (Delete)
1. Logout teacher
2. Login as student
3. Try to access delete URL
4. ✅ Should show: "Access denied! Teachers only."

### Test 4c: Non-Teacher Access (Enrollment)
1. As student, try to access: http://localhost:5000/students/register-with-face
2. ✅ Should show: "Access denied! Teachers only."

---

## Test 5: UI/UX Verification

### Visual Checks:
1. **Buttons Alignment**
   - ✅ Action buttons should be side-by-side
   - ✅ Green "Enroll" button should be before Red "Delete" button
   - ✅ Buttons should have proper spacing

2. **Button Hover Effects**
   - Hover over "📸 Enroll Face"
   - ✅ Should have darker green background
   - Hover over "🗑️ Delete"
   - ✅ Should have darker red background

3. **Modal Styling**
   - ✅ Modal should center on screen
   - ✅ Background should be semi-transparent dark
   - ✅ Modal content should have white background
   - ✅ Text should be readable
   - ✅ Warning text should be red and bold

4. **Responsive Design**
   - Resize browser window
   - ✅ Modal should remain centered
   - ✅ Buttons should remain visible
   - ✅ Table should scroll horizontally if needed

---

## Test 6: Edge Cases

### Test 6a: Multiple Quick Clicks
1. Click delete button
2. While modal is open, click delete button on another student
3. ✅ Should update modal with new student info (or prevent second click)

### Test 6b: Delete During Face Enrollment
1. Start face enrollment for a student
2. In another tab, delete that student
3. Complete enrollment in first tab
4. ✅ Should show error (student not found)

### Test 6c: No Students
1. Delete all students
2. ✅ Should show empty state message
3. ✅ Should show "Register Student" link

---

## Test 7: Data Integrity

### Verify Database Cleanup:
After deleting a student, check:

```python
# Open Python shell in project directory
from app import SessionLocal, Student, User, Attendance

db = SessionLocal()

# Check student record is gone
roll_no = "S154"  # Replace with deleted student's roll number
student = db.query(Student).filter_by(roll_no=roll_no).first()
print(f"Student exists: {student is not None}")  # Should be False

# Check user account is gone
user = db.query(User).filter_by(username=roll_no).first()
print(f"User exists: {user is not None}")  # Should be False

# Check attendance records are gone
# (Use student_id from before deletion)
attendance = db.query(Attendance).filter_by(student_id=5).all()
print(f"Attendance records: {len(attendance)}")  # Should be 0

db.close()
```

### Verify File System Cleanup:
```powershell
# Check encodings folder
Get-ChildItem -Path "encodings" -Filter "5.npy"  # Should not exist

# Check dataset folder (if used)
Test-Path "dataset\S154"  # Should not exist or be empty
```

---

## Common Issues and Solutions

### Issue 1: Modal Not Appearing
**Symptom**: Click delete, nothing happens
**Check**: 
- Browser console for JavaScript errors
- Ensure modal HTML is present in view_students.html
- Check modal CSS (display: flex when shown)

### Issue 2: Delete Button Doesn't Work
**Symptom**: Click confirm, no deletion occurs
**Check**:
- Network tab in browser DevTools
- Check if POST request is sent
- Check Flask console for errors
- Verify route is defined in app.py

### Issue 3: Enrollment Button Not Showing
**Symptom**: Pending student has no enrollment button
**Check**:
- Verify student.encodings_path is None in database
- Check Jinja2 template condition
- Refresh page (Ctrl+F5)

### Issue 4: Pre-filled Data Not Working
**Symptom**: Enrollment page shows empty form
**Check**:
- URL should have `?student_id=X` parameter
- Check app.py GET route handles student_id
- Verify student exists in database

---

## Quick Smoke Test (5 minutes)

Run this quick test to verify everything works:

1. ✅ Login as teacher
2. ✅ Go to View Students
3. ✅ Click delete on a student → Modal appears
4. ✅ Click Cancel → Modal closes
5. ✅ Click delete again → Click Confirm → Student deleted
6. ✅ Find pending student → Click "📸 Enroll Face"
7. ✅ Verify form is pre-filled
8. ✅ Capture 3-5 face images
9. ✅ Complete enrollment → Verify status changes to "Face Enrolled"
10. ✅ Verify enrollment button is gone
11. ✅ Logout and login as newly enrolled student
12. ✅ Verify student can access dashboard

---

## Performance Testing

### Test with Multiple Students:
1. Create 20-30 students (mix of enrolled and pending)
2. Load view students page
3. ✅ Page should load in < 2 seconds
4. ✅ Delete modal should appear instantly
5. ✅ Delete operation should complete in < 1 second

---

## Browser Compatibility

Test on multiple browsers:
- ✅ Chrome/Edge (Chromium)
- ✅ Firefox
- ✅ Safari (if available)

---

## Success Criteria

All tests pass when:
1. ✅ Delete functionality works with confirmation
2. ✅ All related data is removed (database + files)
3. ✅ Face enrollment completion works
4. ✅ Pre-filled data is read-only
5. ✅ Status updates correctly
6. ✅ No JavaScript errors in console
7. ✅ No Python errors in Flask console
8. ✅ UI is responsive and user-friendly
9. ✅ Security checks prevent unauthorized access
10. ✅ Error messages are clear and helpful

---

## Report Issues

If you find bugs:
1. Note the exact steps to reproduce
2. Check browser console for errors
3. Check Flask console for errors
4. Note your browser and OS
5. Take screenshots if helpful

---

## Next Steps After Testing

Once all tests pass:
- Document any issues found and fixed
- Update QUICK_REFERENCE.md if needed
- Consider adding automated tests
- Deploy to production (if applicable)
