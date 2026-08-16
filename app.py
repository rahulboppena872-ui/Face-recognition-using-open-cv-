from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from src.db_connection import get_connection

import os
import shutil
import sys
import subprocess
import base64
import cv2
import numpy as np
from datetime import datetime


app = Flask(__name__)
app.secret_key = "face-recognition-attendance"


# ============================================================
# PATHS
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

MODEL_PATH = os.path.join(
    BASE_DIR,
    "models",
    "trained_model.yml"
)

DATASET_DIR = os.path.join(
    BASE_DIR,
    "dataset"
)


# ============================================================
# GENERATE NEXT ROLL NUMBER
# ============================================================

def get_next_roll_no():

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT COALESCE(MAX(roll_no), 1000) + 1
            FROM users
            """
        )

        return cursor.fetchone()[0]

    finally:
        cursor.close()
        conn.close()


# ============================================================
# GENERATE NEXT FACE ID
# ============================================================

def get_next_face_id():

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT COALESCE(MAX(id), 100) + 1
            FROM users
            """
        )

        return cursor.fetchone()[0]

    finally:
        cursor.close()
        conn.close()


# ============================================================
# IMAGE DECODER
# ============================================================

def decode_image(image_data):

    try:

        if "," in image_data:
            image_data = image_data.split(",", 1)[1]

        image_bytes = base64.b64decode(image_data)

        image_array = np.frombuffer(
            image_bytes,
            dtype=np.uint8
        )

        frame = cv2.imdecode(
            image_array,
            cv2.IMREAD_COLOR
        )

        return frame

    except Exception:
        return None


# ============================================================
# FACE DETECTOR
# ============================================================

face_classifier = cv2.CascadeClassifier(
    cv2.data.haarcascades +
    "haarcascade_frontalface_default.xml"
)


# ============================================================
# HOME
# ============================================================

@app.route("/")
def home():
    return redirect(url_for("admin"))


# ============================================================
# ADMIN PAGE
# ============================================================

@app.route("/admin")
def admin():

    conn = get_connection()
    cursor = conn.cursor()

    try:

        cursor.execute(
            """
            SELECT
                id,
                roll_no,
                name
            FROM users
            ORDER BY roll_no
            """
        )

        students = cursor.fetchall()

    finally:

        cursor.close()
        conn.close()

    return render_template(
        "admin.html",
        students=students
    )


# ============================================================
# CREATE STUDENT
# ============================================================

@app.route("/api/enroll", methods=["POST"])
def api_enroll():

    data = request.get_json(silent=True) or {}

    name = data.get("name", "").strip()

    if not name:

        return jsonify({
            "success": False,
            "message": "Please enter student name."
        }), 400


    roll_no = get_next_roll_no()
    face_id = get_next_face_id()


    conn = get_connection()
    cursor = conn.cursor()

    try:

        cursor.execute(
            """
            INSERT INTO users
            (
                id,
                roll_no,
                name
            )
            VALUES
            (
                %s,
                %s,
                %s
            )
            """,
            (
                face_id,
                roll_no,
                name
            )
        )

        conn.commit()

    except Exception as e:

        conn.rollback()

        return jsonify({
            "success": False,
            "message": f"Database error: {e}"
        }), 500

    finally:

        cursor.close()
        conn.close()


    # Create dataset directory

    dataset_path = os.path.join(
        DATASET_DIR,
        str(face_id)
    )

    os.makedirs(
        dataset_path,
        exist_ok=True
    )


    return jsonify({
        "success": True,
        "message": "Student created successfully.",
        "face_id": face_id,
        "roll_no": roll_no,
        "name": name
    })


# ============================================================
# CAPTURE FACE FROM BROWSER
# ============================================================

@app.route("/api/capture", methods=["POST"])
def api_capture():

    data = request.get_json(silent=True) or {}

    user_id = data.get("user_id")
    image_data = data.get("image")


    if not user_id or not image_data:

        return jsonify({
            "success": False,
            "message": "Missing user ID or image."
        }), 400


    try:
        user_id = int(user_id)

    except ValueError:

        return jsonify({
            "success": False,
            "message": "Invalid user ID."
        }), 400


    frame = decode_image(image_data)


    if frame is None:

        return jsonify({
            "success": False,
            "message": "Could not read camera image."
        }), 400


    gray = cv2.cvtColor(
        frame,
        cv2.COLOR_BGR2GRAY
    )


    faces = face_classifier.detectMultiScale(
        gray,
        scaleFactor=1.3,
        minNeighbors=5,
        minSize=(100, 100)
    )


    if len(faces) == 0:

        return jsonify({
            "success": False,
            "message": "No face detected."
        })


    # Use largest detected face

    x, y, w, h = max(
        faces,
        key=lambda face: face[2] * face[3]
    )


    face = gray[
        y:y + h,
        x:x + w
    ]


    face = cv2.resize(
        face,
        (200, 200)
    )


    dataset_path = os.path.join(
        DATASET_DIR,
        str(user_id)
    )

    os.makedirs(
        dataset_path,
        exist_ok=True
    )


    existing_files = [
        f for f in os.listdir(dataset_path)
        if f.lower().endswith(".jpg")
    ]


    count = len(existing_files) + 1


    filename = os.path.join(
        dataset_path,
        f"user_{count}.jpg"
    )


    cv2.imwrite(
        filename,
        face
    )


    return jsonify({
        "success": True,
        "message": "Face captured.",
        "count": count
    })


# ============================================================
# TRAIN MODEL
# ============================================================

@app.route("/api/train", methods=["POST"])
def api_train():

    train_script = os.path.join(
        BASE_DIR,
        "src",
        "train_model.py"
    )


    try:

        result = subprocess.run(
            [
                sys.executable,
                train_script
            ],
            cwd=BASE_DIR,
            capture_output=True,
            text=True,
            timeout=120
        )


        if result.returncode != 0:

            return jsonify({
                "success": False,
                "message": result.stderr[-1000:]
            }), 500


        return jsonify({
            "success": True,
            "message": "Face recognition model trained successfully."
        })


    except Exception as e:

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


# ============================================================
# ATTENDANCE PAGE
# ============================================================

@app.route("/attendance")
def attendance():

    return render_template(
        "attendance.html"
    )


# ============================================================
# START ATTENDANCE
# ============================================================

@app.route("/api/attendance/start", methods=["POST"])
def attendance_start():

    data = request.get_json(silent=True) or {}

    roll_no = str(
        data.get("roll_no", "")
    ).strip()


    if not roll_no.isdigit():

        return jsonify({
            "success": False,
            "message": "Enter a valid roll number."
        }), 400


    conn = get_connection()
    cursor = conn.cursor()

    try:

        cursor.execute(
            """
            SELECT
                id,
                roll_no,
                name
            FROM users
            WHERE roll_no = %s
            """,
            (int(roll_no),)
        )

        student = cursor.fetchone()

    finally:

        cursor.close()
        conn.close()


    if not student:

        return jsonify({
            "success": False,
            "message": f"Roll number {roll_no} does not exist."
        }), 404


    return jsonify({
        "success": True,
        "face_id": student[0],
        "roll_no": student[1],
        "name": student[2]
    })


# ============================================================
# RECOGNIZE FACE + MARK ATTENDANCE
# ============================================================

@app.route("/api/recognize", methods=["POST"])
def api_recognize():

    data = request.get_json(silent=True) or {}

    face_id = data.get("face_id")
    image_data = data.get("image")


    if not face_id or not image_data:

        return jsonify({
            "success": False,
            "message": "Missing face ID or image."
        }), 400


    try:

        face_id = int(face_id)

    except ValueError:

        return jsonify({
            "success": False,
            "message": "Invalid face ID."
        }), 400


    if not os.path.exists(MODEL_PATH):

        return jsonify({
            "success": False,
            "message": "Trained face model not found. Please enroll students first."
        }), 500


    frame = decode_image(image_data)


    if frame is None:

        return jsonify({
            "success": False,
            "message": "Could not read camera image."
        }), 400


    gray = cv2.cvtColor(
        frame,
        cv2.COLOR_BGR2GRAY
    )


    faces = face_classifier.detectMultiScale(
        gray,
        scaleFactor=1.3,
        minNeighbors=5,
        minSize=(100, 100)
    )


    if len(faces) == 0:

        return jsonify({
            "success": False,
            "recognized": False,
            "message": "No face detected."
        })


    try:

        recognizer = cv2.face.LBPHFaceRecognizer_create()

        recognizer.read(
            MODEL_PATH
        )

    except Exception as e:

        return jsonify({
            "success": False,
            "message": f"Could not load face model: {e}"
        }), 500


    # Largest face

    x, y, w, h = max(
        faces,
        key=lambda face: face[2] * face[3]
    )


    face = gray[
        y:y + h,
        x:x + w
    ]


    try:

        predicted_id, confidence = recognizer.predict(
            face
        )

    except Exception:

        return jsonify({
            "success": False,
            "recognized": False,
            "message": "Face could not be recognized."
        })


    # Lower confidence = better match

    if predicted_id != face_id or confidence >= 100:

        return jsonify({
            "success": True,
            "recognized": False,
            "message": "Face not matched.",
            "confidence": round(float(confidence), 2)
        })


    # ========================================================
    # FACE MATCHED
    # ========================================================

    conn = get_connection()
    cursor = conn.cursor()

    try:

        cursor.execute(
            """
            SELECT
                id,
                roll_no,
                name
            FROM users
            WHERE id = %s
            """,
            (face_id,)
        )

        student = cursor.fetchone()


        if not student:

            return jsonify({
                "success": False,
                "message": "Student not found."
            }), 404


        today = datetime.now().date()
        current_time = datetime.now().time()


        # Check duplicate

        cursor.execute(
            """
            SELECT id
            FROM face_attendance
            WHERE user_id = %s
            AND attendance_date = %s
            """,
            (
                face_id,
                today
            )
        )


        existing = cursor.fetchone()


        if existing:

            return jsonify({
                "success": True,
                "recognized": True,
                "attendance_marked": False,
                "already_marked": True,
                "message": "Attendance already marked today.",
                "name": student[2],
                "roll_no": student[1],
                "confidence": round(float(confidence), 2)
            })


        # Mark attendance

        cursor.execute(
            """
            INSERT INTO face_attendance
            (
                user_id,
                attendance_date,
                attendance_time
            )
            VALUES
            (
                %s,
                %s,
                %s
            )
            """,
            (
                face_id,
                today,
                current_time
            )
        )


        conn.commit()


        return jsonify({
            "success": True,
            "recognized": True,
            "attendance_marked": True,
            "already_marked": False,
            "message": "Attendance marked successfully!",
            "name": student[2],
            "roll_no": student[1],
            "confidence": round(float(confidence), 2)
        })


    except Exception as e:

        conn.rollback()

        return jsonify({
            "success": False,
            "message": f"Attendance error: {e}"
        }), 500


    finally:

        cursor.close()
        conn.close()


# ============================================================
# ATTENDANCE RECORDS
# ============================================================

@app.route("/records")
def records():

    conn = get_connection()
    cursor = conn.cursor()

    try:

        cursor.execute(
            """
            SELECT
                u.roll_no,
                u.name,
                a.attendance_date,
                a.attendance_time
            FROM face_attendance a
            JOIN users u
                ON a.user_id = u.id
            ORDER BY
                a.attendance_date DESC,
                a.attendance_time DESC
            """
        )

        attendance_records = cursor.fetchall()

    finally:

        cursor.close()
        conn.close()


    return render_template(
        "records.html",
        records=attendance_records
    )


# ============================================================
# DELETE USER
# ============================================================

@app.route(
    "/delete_user/<int:user_id>",
    methods=["POST"]
)
def delete_user(user_id):

    conn = get_connection()
    cursor = conn.cursor()

    try:

        cursor.execute(
            """
            SELECT
                id,
                roll_no,
                name
            FROM users
            WHERE id = %s
            """,
            (user_id,)
        )

        user = cursor.fetchone()


        if not user:

            flash(
                "Student not found.",
                "error"
            )

            return redirect(
                url_for("admin")
            )


        face_id = user[0]
        roll_no = user[1]
        name = user[2]


        # Delete face attendance

        cursor.execute(
            """
            DELETE FROM face_attendance
            WHERE user_id = %s
            """,
            (face_id,)
        )


        # Delete student

        cursor.execute(
            """
            DELETE FROM users
            WHERE id = %s
            """,
            (face_id,)
        )


        conn.commit()


    except Exception as e:

        conn.rollback()

        flash(
            f"Could not delete student: {e}",
            "error"
        )

        return redirect(
            url_for("admin")
        )


    finally:

        cursor.close()
        conn.close()


    # Delete dataset

    dataset_path = os.path.join(
        DATASET_DIR,
        str(face_id)
    )


    if os.path.exists(dataset_path):

        try:

            shutil.rmtree(
                dataset_path
            )

        except Exception as e:

            print(
                f"Could not delete dataset: {e}"
            )


    # Retrain model if possible

    train_script = os.path.join(
        BASE_DIR,
        "src",
        "train_model.py"
    )


    try:

        subprocess.run(
            [
                sys.executable,
                train_script
            ],
            cwd=BASE_DIR,
            check=True,
            timeout=120
        )

    except Exception as e:

        print(
            f"Model retraining failed: {e}"
        )


    flash(
        f"Student {name} (Roll No: {roll_no}) deleted successfully.",
        "success"
    )


    return redirect(
        url_for("admin")
    )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=int(
            os.environ.get(
                "PORT",
                5000
            )
        ),
        debug=True
    )