from flask import Flask, render_template, request, redirect, url_for, jsonify
from datetime import datetime, timedelta
import qrcode
import cv2
import os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key')

# Simple in-memory storage for MVP
students = {}
attendance_log = []
last_scan = {}  # Track last scan time for each student

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        student_id = request.form['student_id']
        name = request.form['name']
        
        # Generate QR code
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(student_id)
        qr.make(fit=True)
        qr_image = qr.make_image(fill_color="black", back_color="white")
        
        # Save QR code
        qr_path = f"static/qr_codes/{student_id}.png"
        os.makedirs('static/qr_codes', exist_ok=True)
        qr_image.save(qr_path)
        
        # Store student data
        students[student_id] = {
            'name': name,
            'qr_code': qr_path
        }
        
        return redirect(url_for('view_qr', student_id=student_id))
    return render_template('register.html')

@app.route('/view_qr/<student_id>')
def view_qr(student_id):
    if student_id in students:
        return render_template('view_qr.html', student=students[student_id])
    return "Student not found", 404

@app.route('/scan')
def scan():
    return render_template('scan.html')

@app.route('/log_attendance', methods=['POST'])
def log_attendance():
    student_id = request.json.get('student_id')
    current_time = datetime.now()
    
    if student_id in students:
        # Check if student has scanned recently
        if student_id in last_scan:
            time_since_last_scan = current_time - last_scan[student_id]
            if time_since_last_scan.total_seconds() < 30:
                return jsonify({
                    'status': 'error',
                    'message': 'Please wait 30 seconds before scanning again'
                })
        
        # Determine if this is entry or exit
        is_entry = True
        if attendance_log:
            # Check last record for this student
            student_records = [record for record in attendance_log if record['student_id'] == student_id]
            if student_records:
                is_entry = student_records[-1]['type'] == 'exit'
        
        # Record new attendance
        last_scan[student_id] = current_time
        attendance_log.append({
            'student_id': student_id,
            'name': students[student_id]['name'],
            'timestamp': current_time.strftime('%Y-%m-%d %H:%M:%S'),
            'type': 'entry' if is_entry else 'exit'
        })
        return jsonify({
            'status': 'success',
            'message': f'{"Entry" if is_entry else "Exit"} recorded successfully'
        })
    return jsonify({'status': 'error', 'message': 'Student not found'})

@app.route('/attendance_log')
def view_attendance():
    return render_template('attendance_log.html', attendance_log=attendance_log)

@app.route('/students')
def view_students():
    return render_template('students_list.html', students=students)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)