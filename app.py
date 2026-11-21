from flask import Flask, render_template, request, jsonify
import sqlite3
from pathlib import Path

app = Flask(__name__)
DB = Path(__file__).with_name("registration.db")

def db():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con

def init_db():
    with db() as con:
        con.executescript("""
        CREATE TABLE IF NOT EXISTS students (
            student_id TEXT PRIMARY KEY, full_name TEXT NOT NULL, completed_credits INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS courses (
            course_id TEXT PRIMARY KEY, course_name TEXT NOT NULL, required_credits INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS registrations (
            student_id TEXT NOT NULL, course_id TEXT NOT NULL,
            PRIMARY KEY(student_id, course_id)
        );
        """)
        con.execute("INSERT OR IGNORE INTO students VALUES (?, ?, ?)", ("SV001", "Nguyen Van A", 45))
        con.execute("INSERT OR IGNORE INTO students VALUES (?, ?, ?)", ("SV002", "Tran Thi B", 18))
        con.execute("INSERT OR IGNORE INTO courses VALUES (?, ?, ?)", ("RIPT1305", "Hoc phan mo phong", 30))
        con.execute("INSERT OR IGNORE INTO courses VALUES (?, ?, ?)", ("INT1306", "Hoc phan co dieu kien cao hon", 60))
        con.commit()

# SHARED BUSINESS RULE: one implementation used by both client systems.
def check_registration(student_id, course_id):
    with db() as con:
        student = con.execute("SELECT * FROM students WHERE student_id=?", (student_id,)).fetchone()
        course = con.execute("SELECT * FROM courses WHERE course_id=?", (course_id,)).fetchone()
        if not student:
            return {"eligible": False, "code": "STUDENT_NOT_FOUND", "message": "Khong tim thay sinh vien."}, 404
        if not course:
            return {"eligible": False, "code": "COURSE_NOT_FOUND", "message": "Khong tim thay hoc phan."}, 404
        if student["completed_credits"] < course["required_credits"]:
            return {"eligible": False, "code": "INSUFFICIENT_CREDITS",
                    "message": f"Chua du tin chi: can {course['required_credits']}, hien co {student['completed_credits']}."}, 200
        registered = con.execute("SELECT 1 FROM registrations WHERE student_id=? AND course_id=?",
                                 (student_id, course_id)).fetchone()
        if registered:
            return {"eligible": False, "code": "ALREADY_REGISTERED", "message": "Sinh vien da dang ky hoc phan."}, 200
        return {"eligible": True, "code": "ELIGIBLE", "message": "Du dieu kien dang ky hoc phan."}, 200

@app.get("/")
def home():
    return render_template("index.html")

@app.get("/portal")
def portal():
    return render_template("client.html", system="Cổng thông tin sinh viên", client="portal")

@app.get("/advisor")
def advisor():
    return render_template("client.html", system="Hệ thống cố vấn học tập", client="advisor")

@app.post("/api/eligibility")
def eligibility():
    payload = request.get_json(silent=True) or request.form
    student_id = str(payload.get("studentId", "")).strip().upper()
    course_id = str(payload.get("courseId", "")).strip().upper()
    if not student_id or not course_id:
        return jsonify({"eligible": False, "code": "INVALID_REQUEST",
                        "message": "Vui lòng nhập mã sinh viên và mã học phần."}), 400
    result, status = check_registration(student_id, course_id)
    return jsonify({"studentId": student_id, "courseId": course_id, **result}), status

@app.get("/api/health")
def health():
    return jsonify({"service": "Shared Business Service", "status": "UP"})

if __name__ == "__main__":
    init_db()
    app.run(host="127.0.0.1", port=5000, debug=False)
