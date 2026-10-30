from flask import Flask, render_template, request, redirect, url_for, session, jsonify, Response
from models.db import get_db, init_db
import os, json, datetime, base64, csv, io
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "super_secret_key"
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

if not os.path.exists('database.db'):
    init_db()

# ---------- LOGIN ----------
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u = request.form['username']
        p = request.form['password']
        db = get_db()
        admin = db.execute("SELECT * FROM admins WHERE username=? AND password=?", (u, p)).fetchone()
        db.close()
        if admin:
            session['admin'] = u
            return redirect(url_for('dashboard'))
        return render_template('login.html', error="Invalid username or password")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ---------- DASHBOARD ----------
@app.route('/dashboard')
def dashboard():
    if 'admin' not in session:
        return redirect(url_for('login'))
    db = get_db()
    students = db.execute("SELECT * FROM students ORDER BY student_id DESC").fetchall()
    today = datetime.date.today().isoformat()
    today_count = db.execute("SELECT COUNT(DISTINCT enrollment_no) FROM attendance WHERE attendance_date=?", (today,)).fetchone()[0]
    db.close()
    return render_template('dashboard.html', students=students, today=today, today_count=today_count)

# ---------- REGISTER ----------
@app.route('/register')
def register_page():
    if 'admin' not in session:
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/register_student', methods=['POST'])
def register_student():
    if 'admin' not in session:
        return jsonify({"ok": False, "msg": "Not logged in"}), 401
    data = request.get_json()
    enrollment = data['enrollment_no'].strip()
    name = data['name'].strip()
    dept = data['department']
    
    header, encoded = data['image'].split(",", 1)
    fname = secure_filename(f"{enrollment}.jpg")
    with open(os.path.join(app.config['UPLOAD_FOLDER'], fname), "wb") as f:
        f.write(base64.b64decode(encoded))

    db = get_db()
    try:
        db.execute("INSERT INTO students (enrollment_no, name, department, face_encoding, image_path) VALUES (?,?,?,?,?)",
            (enrollment, name, dept, json.dumps(data['encoding']), fname))
        db.commit()
        db.close()
        return jsonify({"ok": True})
    except Exception:
        db.close()
        return jsonify({"ok": False, "msg": "Enrollment number already exists"})

# ---------- ATTENDANCE API ----------
@app.route('/attendance')
def attendance_page():
    if 'admin' not in session:
        return redirect(url_for('login'))
    return render_template('attendance.html')

@app.route('/encodings')
def get_encodings():
    db = get_db()
    rows = db.execute("SELECT enrollment_no, name, department, face_encoding FROM students WHERE face_encoding IS NOT NULL").fetchall()
    db.close()
    return jsonify([{"enrollment_no": r["enrollment_no"], "name": r["name"], "department": r["department"], "encoding": json.loads(r["face_encoding"])} for r in rows])

@app.route('/mark_attendance', methods=['POST'])
def mark_attendance():
    data = request.get_json()
    enrollment = data['enrollment_no']
    today = datetime.date.today().isoformat()
    db = get_db()
    exists = db.execute("SELECT 1 FROM attendance WHERE enrollment_no=? AND attendance_date=?", (enrollment, today)).fetchone()
    if exists:
        db.close()
        return jsonify({"ok": False, "msg": "Already marked present today"})
    db.execute("INSERT INTO attendance (enrollment_no, attendance_date) VALUES (?,?)", (enrollment, today))
    db.commit()
    db.close()
    return jsonify({"ok": True, "msg": "Attendance marked!"})

# ---------- REPORTS ----------
@app.route('/reports')
def reports():
    if 'admin' not in session:
        return redirect(url_for('login'))
    db = get_db()
    records = db.execute("""
        SELECT a.attendance_id, s.name, s.enrollment_no, s.department, a.attendance_date, a.status
        FROM attendance a JOIN students s ON a.enrollment_no = s.enrollment_no
        ORDER BY a.attendance_date DESC
    """).fetchall()
    db.close()
    return render_template('reports.html', records=records)

@app.route('/export_csv')
def export_csv():
    if 'admin' not in session:
        return redirect(url_for('login'))
    db = get_db()
    rows = db.execute("""
        SELECT s.name, s.enrollment_no, s.department, a.attendance_date, a.status
        FROM attendance a JOIN students s ON a.enrollment_no = s.enrollment_no
        ORDER BY a.attendance_date DESC
    """).fetchall()
    db.close()

    out = io.StringIO()
    w = csv.writer(out)
    w.writerow(["Name", "Enrollment", "Department", "Date", "Status"])
    for r in rows:
        w.writerow(list(r))
    return Response(out.getvalue(), mimetype="text/csv", headers={"Content-Disposition": "attachment;filename=attendance.csv"})

if __name__ == '__main__':
    app.run(debug=True)