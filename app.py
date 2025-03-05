from flask import Flask, render_template, request, jsonify, url_for, redirect
import qrcode
import os
import json
from datetime import datetime, timedelta

app = Flask(__name__)

# Ensure QR codes directory exists
if not os.path.exists('static/qr_codes'):
    os.makedirs('static/qr_codes')

# Load or create students data
STUDENTS_FILE = 'students.json'
ATTENDANCE_FILE = 'attendance.json'

def load_data():
    if os.path.exists(STUDENTS_FILE):
        with open(STUDENTS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(STUDENTS_FILE, 'w') as f:
        json.dump(data, f)

def load_attendance():
    if os.path.exists(ATTENDANCE_FILE):
        with open(ATTENDANCE_FILE, 'r') as f:
            return json.load(f)
    return []

def save_attendance(data):
    with open(ATTENDANCE_FILE, 'w') as f:
        json.dump(data, f)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        student_id = request.form['student_id']
        name = request.form['name']
        students = load_data()
        
        if student_id not in students:
            students[student_id] = name
            save_data(students)
            
            # Generate QR code
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(student_id)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            img.save(f'static/qr_codes/{student_id}.png')
            
            return redirect(url_for('students_list'))
    return render_template('register.html')

@app.route('/scan')
def scan():
    return render_template('scan.html')

@app.route('/students')
def students_list():
    students = load_data()
    return render_template('students.html', students=students)

@app.route('/attendance')
def attendance_log():
    attendance = load_attendance()
    students = load_data()
    return render_template('attendance.html', attendance=attendance, students=students)

# Add these variables after the existing ones
LAST_SCAN = {}  # To track last scan time for each student
SCAN_DELAY = 30  # Seconds between allowed scans

@app.route('/log_attendance', methods=['POST'])
def log_attendance():
    data = request.get_json()
    student_id = data.get('student_id')
    students = load_data()
    
    if student_id in students:
        current_time = datetime.now()
        
        # Check if enough time has passed since last scan
        if student_id in LAST_SCAN:
            time_diff = current_time - LAST_SCAN[student_id]['time']
            if time_diff.total_seconds() < SCAN_DELAY:
                return jsonify({'status': 'error', 'message': f'Please wait {SCAN_DELAY - int(time_diff.total_seconds())} seconds'})
        
        # Determine if this is an IN or OUT scan
        scan_type = 'OUT' if student_id in LAST_SCAN and LAST_SCAN[student_id]['type'] == 'IN' else 'IN'
        
        attendance = load_attendance()
        attendance.append({
            'student_id': student_id,
            'name': students[student_id],
            'timestamp': current_time.strftime("%Y-%m-%d %H:%M:%S"),
            'type': scan_type
        })
        save_attendance(attendance)
        
        # Update last scan info
        LAST_SCAN[student_id] = {'time': current_time, 'type': scan_type}
        
        return jsonify({'status': 'success', 'message': f'{scan_type}: Attendance logged for {students[student_id]}'})
    return jsonify({'status': 'error', 'message': 'Student not found'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port)