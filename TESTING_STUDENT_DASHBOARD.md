# Student Dashboard Testing Guide

## Quick Start Testing

### Prerequisites
✅ Server is running at: http://localhost:5000
✅ Student enrolled: S03 (abhi)
✅ Class: Class 10
✅ Face recognition loaded: 15 embeddings

## Test Scenario 1: Basic Dashboard View

### Steps:
1. Open browser: http://localhost:5000/student/login
2. Login with:
   - **Roll Number**: `S03`
   - **Password**: `abhi123`
3. Should redirect to student dashboard

### Expected Results:
- ✅ Header shows: "🎓 Attendance System - Student Portal"
- ✅ User info displays: "abhi (S03)"
- ✅ Statistics cards show:
  - Attendance Rate (percentage)
  - Days Present (count)
  - Total Records (count)
  - Class: Class 10

### Screenshot Areas:
- Top statistics row with 4 cards
- Profile card with student details
- Change Password button

## Test Scenario 2: Timetable View

### Steps:
1. Scroll to "📅 My Class Timetable - Class 10" section
2. Check if timetable is displayed

### Expected Results:

**If Timetable Exists:**
- ✅ Grid with days (Monday-Saturday) as rows
- ✅ Periods (Period 1, 2, 3, etc.) as columns
- ✅ Each cell shows:
  - Subject name
  - Start time - End time
  - Attendance status (if today)
- ✅ Today's day highlighted with yellow border
- ✅ Legend at bottom showing color codes

**If No Timetable:**
- ✅ Message: "No timetable has been created for your class (Class 10) yet."
- ✅ Instruction to contact teacher

### To Add Timetable (as Teacher):
1. Open new tab: http://localhost:5000/login
2. Login as teacher: `teacher1` / `teacher123`
3. Go to "Manage Timetable"
4. Add entries for Class 10:

**Example Entry 1:**
- Class: Class 10
- Day: Monday
- Period: Period 1
- Subject: Mathematics
- Start Time: 09:00
- End Time: 10:00

**Example Entry 2:**
- Class: Class 10
- Day: Monday
- Period: Period 2
- Subject: Physics
- Start Time: 10:00
- End Time: 11:00

**Example Entry 3:**
- Class: Class 10
- Day: Tuesday
- Period: Period 1
- Subject: Chemistry
- Start Time: 09:00
- End Time: 10:00

5. Refresh student dashboard to see timetable

## Test Scenario 3: Attendance Status Display

### Setup:
1. Login as teacher: http://localhost:5000/login
2. Go to "Mark Attendance"
3. Select:
   - Class: Class 10
   - Period: Period 1 (or current period)
4. Click "Start Session"
5. Allow camera access
6. Wait for face recognition to detect student
7. Click "Stop Session"

### Verification in Student Dashboard:
1. Refresh student dashboard (http://localhost:5000/student/dashboard)
2. Go to timetable section
3. Find today's row
4. Locate the period you just marked

### Expected Results:
- ✅ Period cell shows "Present" badge (green)
- ✅ Unmarked periods show "Not Taken" badge (gray)
- ✅ Status updates immediately after refresh

## Test Scenario 4: Interactive Period Details

### Steps:
1. In the timetable grid, click on any period cell (that has a subject)
2. Modal popup should appear

### Expected Modal Content:
- ✅ Title: "📚 Period Details"
- ✅ Day: (e.g., Monday)
- ✅ Period: (e.g., Period 1)
- ✅ Subject: (e.g., Mathematics)
- ✅ Time: (e.g., 09:00 - 10:00)
- ✅ Attendance Status:
  - "Present" (green) if marked
  - "Absent" (red) if marked absent
  - "Not Taken" (gray) if not yet marked

### Close Modal:
- Click X button in top-right
- OR click outside the modal
- Modal should close smoothly

## Test Scenario 5: Attendance History

### Steps:
1. Scroll to "📊 My Attendance History" section
2. Check the table

### Expected Results:

**If Records Exist:**
- ✅ Table with columns: Date, Period, Status
- ✅ Records sorted by date (most recent first)
- ✅ Status badges colored correctly:
  - Green for Present
  - Red for Absent
- ✅ Shows latest 20 records
- ✅ If >20 records, shows "Showing latest 20 records out of X total"

**If No Records:**
- ✅ Empty state icon: 📭
- ✅ Message: "No attendance records yet."
- ✅ Instruction about face recognition

## Test Scenario 6: Today's Highlight

### Steps:
1. Check current day of the week (e.g., Monday)
2. Find that day's row in timetable

### Expected Results:
- ✅ All cells in today's row have yellow/golden background (#fff3cd)
- ✅ Border is thicker and colored (#ffc107)
- ✅ Clearly distinguishable from other days
- ✅ Easy to spot today's schedule at a glance

## Test Scenario 7: Responsive Design

### Steps:
1. Resize browser window to different widths:
   - Desktop (1400px+)
   - Tablet (768px-1024px)
   - Mobile (< 768px)

### Expected Results:
- ✅ Statistics cards reflow to grid
- ✅ Profile info cards stack appropriately
- ✅ Timetable scrolls horizontally on smaller screens
- ✅ Modal popup centers on all screen sizes
- ✅ No overlapping text or broken layout

## Test Scenario 8: Empty Class Assignment

### Setup:
1. Create a new student without class assignment
2. Login as that student

### Expected Results:
- ✅ Statistics show "N/A" for class
- ✅ No timetable section displayed (or empty state)
- ✅ Attendance history works normally
- ✅ Profile shows "Not Assigned" for class

## Test Scenario 9: Change Password

### Steps:
1. In student dashboard, click "Change Password" button
2. Enter:
   - Current Password: `abhi123`
   - New Password: `newpass123`
   - Confirm Password: `newpass123`
3. Submit

### Expected Results:
- ✅ Redirect back to dashboard
- ✅ Success message: "Password changed successfully!"
- ✅ Can logout and login with new password
- ✅ Old password no longer works

## Test Scenario 10: Statistics Calculation

### Verification:
1. Count attendance records manually
2. Check statistics cards

### Expected Calculations:
- **Total Records**: Count all entries in attendance table for this student
- **Present Count**: Count entries where status = 'Present'
- **Attendance Percentage**: (Present Count / Total Records) × 100, rounded to 1 decimal

### Example:
- Total: 10 records
- Present: 8 records
- Percentage: 80.0%

## Common Issues & Fixes

### Issue 1: "No timetable has been created"
**Fix**: Login as teacher and add timetable entries for Class 10

### Issue 2: Attendance not showing in timetable
**Fix**: 
- Ensure attendance is marked for TODAY's date
- Check that the period name matches exactly (e.g., "Period 1")
- Refresh the page

### Issue 3: Modal not opening
**Fix**:
- Don't click on empty cells (-)
- Only cells with subjects are clickable
- Check browser console for JavaScript errors

### Issue 4: Today not highlighted
**Fix**:
- Check system date/time is correct
- Verify day name matches timetable entries exactly
- Case-sensitive: "Monday" not "monday"

### Issue 5: Statistics showing 0%
**Fix**:
- Normal if no attendance records exist yet
- Mark some attendance to see updates
- Statistics calculate automatically

## Browser Compatibility

### Tested Browsers:
- ✅ Google Chrome (Latest)
- ✅ Microsoft Edge (Latest)
- ✅ Firefox (Latest)
- ✅ Safari (Latest)

### Required Features:
- JavaScript enabled
- Cookies enabled (for login session)
- CSS Grid support
- Flexbox support

## Visual Checklist

When viewing the dashboard, you should see:

**Header Section:**
- [ ] Purple gradient background
- [ ] Title: "🎓 Attendance System - Student Portal"
- [ ] Student name and roll number displayed
- [ ] Logout button (white with border)

**Statistics Section:**
- [ ] 4 cards in a row (or wrapped on small screens)
- [ ] Large bold numbers (36px font)
- [ ] Purple color (#667eea) for values
- [ ] Small uppercase labels in gray

**Profile Section:**
- [ ] White card with shadow
- [ ] 4 info items in grid
- [ ] Left border on each item (purple)
- [ ] Change Password button (purple gradient)

**Timetable Section:**
- [ ] White card with shadow
- [ ] Grid table with days and periods
- [ ] Purple header for periods
- [ ] Darker purple for day column
- [ ] Today's row highlighted in yellow
- [ ] Status badges (green/red/gray)
- [ ] Legend at bottom with color codes

**Attendance History Section:**
- [ ] White card with shadow
- [ ] Table with alternating row hover
- [ ] Status badges matching timetable
- [ ] Sorted by date (newest first)
- [ ] Pagination info if >20 records

**Modal Popup:**
- [ ] Semi-transparent dark overlay
- [ ] White centered box with shadow
- [ ] Close button (X) in top-right
- [ ] Period details clearly displayed
- [ ] Status badge matching main view

## Performance Checklist

- [ ] Page loads in < 2 seconds
- [ ] No JavaScript errors in console
- [ ] No missing images or broken links
- [ ] Smooth animations and transitions
- [ ] Modal opens/closes instantly
- [ ] Hover effects work smoothly

## Accessibility Checklist

- [ ] All text readable (good contrast)
- [ ] Interactive elements have hover states
- [ ] Modal can be closed with click
- [ ] Table headers properly labeled
- [ ] Color not sole indicator (text + color for status)
- [ ] Font sizes appropriate (12px minimum)

## Success Criteria

✅ **All Test Scenarios Pass**
✅ **No Console Errors**
✅ **Responsive on All Devices**
✅ **Data Displays Accurately**
✅ **Interactive Features Work**
✅ **Professional Appearance**

## Next Steps After Testing

1. ✅ Verify all features work correctly
2. ✅ Test with multiple students and classes
3. ✅ Add more timetable entries for full week
4. ✅ Mark attendance for multiple periods
5. ✅ Test edge cases (no data, lots of data)
6. 📝 Document any bugs found
7. 🚀 Move to Phase 10: System polish and optimization

---

**System Status**: ✅ Ready for Testing
**Test Environment**: http://localhost:5000
**Student Login**: S03 / abhi123
**Teacher Login**: teacher1 / teacher123
