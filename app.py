from flask import Flask, render_template, request, redirect, url_for, flash
from src.db_connection import get_connection

import subprocess
import sys
import os
import shutil


app = Flask(__name__)

app.secret_key = "face-recognition-attendance"


# ============================================================
# Generate Next Roll Number
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

        result = cursor.fetchone()

        return result[0]

    finally:

        cursor.close()
        conn.close()


# ============================================================
# Generate Next Face ID
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

        result = cursor.fetchone()

        return result[0]

    finally:

        cursor.close()
        conn.close()


# ============================================================
# Home
# ============================================================

@app.route("/")
def home():

    return redirect(url_for("admin"))


# ============================================================
# ADMIN / ENROLLMENT
# ============================================================

@app.route("/admin", methods=["GET", "POST"])
def admin():

    # --------------------------------------------------------
    # Enroll New Student
    # --------------------------------------------------------

    if request.method == "POST":

        name = request.form.get("name", "").strip()

        # Validate name
        if not name:

            flash(
                "Please enter the student name.",
                "error"
            )

            return redirect(url_for("admin"))


        # Generate IDs
        roll_no = get_next_roll_no()

        face_id = get_next_face_id()


        # ----------------------------------------------------
        # Save Student in MySQL
        # ----------------------------------------------------

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

            flash(
                f"Database error: {e}",
                "error"
            )

            return redirect(url_for("admin"))


        finally:

            cursor.close()
            conn.close()


        # ----------------------------------------------------
        # Start Face Capture
        # ----------------------------------------------------

        capture_script = os.path.join(
            os.path.dirname(__file__),
            "src",
            "capture_faces.py"
        )


        try:

            subprocess.Popen(
                [
                    sys.executable,
                    capture_script,
                    str(face_id),
                    name
                ],
                cwd=os.path.dirname(__file__)
            )

        except Exception as e:

            # If camera process cannot start,
            # remove the database user we just created.

            conn = get_connection()
            cursor = conn.cursor()

            try:

                cursor.execute(
                    """
                    DELETE FROM users
                    WHERE id = %s
                    """,
                    (face_id,)
                )

                conn.commit()

            finally:

                cursor.close()
                conn.close()


            flash(
                f"Could not start camera: {e}",
                "error"
            )

            return redirect(url_for("admin"))


        # ----------------------------------------------------
        # Success Message
        # ----------------------------------------------------

        flash(
            f"Student {name} created successfully. "
            f"Roll No: {roll_no}. "
            f"Face ID: {face_id}. "
            f"Camera is opening.",
            "success"
        )

        return redirect(url_for("admin"))


    # --------------------------------------------------------
    # Get Registered Students
    # --------------------------------------------------------

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
# ATTENDANCE
# ============================================================

@app.route("/attendance", methods=["GET", "POST"])
def attendance():

    # --------------------------------------------------------
    # Start Attendance
    # --------------------------------------------------------

    if request.method == "POST":

        roll_no = request.form.get(
            "roll_no",
            ""
        ).strip()


        # Validate Roll Number
        if not roll_no.isdigit():

            flash(
                "Enter a valid roll number.",
                "error"
            )

            return redirect(
                url_for("attendance")
            )


        # ----------------------------------------------------
        # Find Student
        # ----------------------------------------------------

        conn = get_connection()
        cursor = conn.cursor()

        try:

            cursor.execute(
                """
                SELECT
                    id,
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


        # Student doesn't exist
        if not student:

            flash(
                f"Roll number {roll_no} does not exist.",
                "error"
            )

            return redirect(
                url_for("attendance")
            )


        # ----------------------------------------------------
        # Student Information
        # ----------------------------------------------------

        face_id = student[0]

        name = student[1]


        # ----------------------------------------------------
        # Start Face Recognition
        # ----------------------------------------------------

        recognition_script = os.path.join(
            os.path.dirname(__file__),
            "src",
            "recognize_face.py"
        )


        try:

            subprocess.Popen(
                [
                    sys.executable,
                    recognition_script,
                    str(face_id)
                ],
                cwd=os.path.dirname(__file__)
            )

        except Exception as e:

            flash(
                f"Could not start camera: {e}",
                "error"
            )

            return redirect(
                url_for("attendance")
            )


        # ----------------------------------------------------
        # Success Message
        # ----------------------------------------------------

        flash(
            f"Camera started for {name} "
            f"(Roll No: {roll_no}).",
            "success"
        )

        return redirect(
            url_for("attendance")
        )


    # --------------------------------------------------------
    # Attendance Page
    # --------------------------------------------------------

    return render_template(
        "attendance.html"
    )


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

    # --------------------------------------------------------
    # Get Student Information
    # --------------------------------------------------------

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


        # Student doesn't exist
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


        # ----------------------------------------------------
        # Delete Attendance First
        # ----------------------------------------------------
        # attendance.user_id has a foreign key to users.id

        cursor.execute(
            """
            DELETE FROM face_attendance
            WHERE user_id = %s
            """,
            (face_id,)
        )


        # ----------------------------------------------------
        # Delete User
        # ----------------------------------------------------

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


    # ========================================================
    # Delete Face Dataset
    # ========================================================

    dataset_path = os.path.join(
        os.path.dirname(__file__),
        "dataset",
        str(face_id)
    )


    if os.path.exists(dataset_path):

        try:

            shutil.rmtree(
                dataset_path
            )

            print(
                f"Deleted dataset: {dataset_path}"
            )

        except Exception as e:

            print(
                f"Could not delete dataset: {e}"
            )


    # ========================================================
    # Retrain Face Recognition Model
    # ========================================================

    train_script = os.path.join(
        os.path.dirname(__file__),
        "src",
        "train_model.py"
    )


    try:

        subprocess.run(
            [
                sys.executable,
                train_script
            ],
            cwd=os.path.dirname(__file__),
            check=True
        )

        print(
            "Face recognition model retrained successfully."
        )


    except Exception as e:

        print(
            f"Model retraining failed: {e}"
        )


    # ========================================================
    # Success
    # ========================================================

    flash(
        f"Student {name} "
        f"(Roll No: {roll_no}) "
        "deleted successfully.",
        "success"
    )


    return redirect(
        url_for("admin")
    )


# ============================================================
# RUN APPLICATION
# ============================================================

if __name__ == "__main__":
    import os

    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=True
    )
