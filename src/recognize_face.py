import cv2
import os
import sys
import time
from datetime import datetime

from db_connection import get_connection


# ============================================================
# SETTINGS
# ============================================================

FACE_ID = int(sys.argv[1]) if len(sys.argv) > 1 else None

if FACE_ID is None:
    print("Error: Face ID is required.")
    print("Usage: python src/recognize_face.py <face_id>")
    sys.exit(1)


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MODEL_PATH = os.path.join(
    BASE_DIR,
    "models",
    "trained_model.yml"
)

CASCADE_PATH = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"


# ============================================================
# CHECK MODEL
# ============================================================

if not os.path.exists(MODEL_PATH):
    print("Error: Trained model not found.")
    print(f"Expected location: {MODEL_PATH}")
    print()
    print("Run:")
    print("python src/train_model.py")
    sys.exit(1)


# ============================================================
# GET STUDENT INFORMATION
# ============================================================

conn = None
cursor = None

try:

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, roll_no, name
        FROM users
        WHERE id = %s
        """,
        (FACE_ID,)
    )

    student = cursor.fetchone()

finally:

    if cursor:
        cursor.close()

    if conn:
        conn.close()


if not student:

    print(f"Error: User ID {FACE_ID} does not exist.")
    sys.exit(1)


user_id = student[0]
roll_no = student[1]
student_name = student[2]


print()
print("==========================================")
print("   FACE RECOGNITION ATTENDANCE")
print("==========================================")
print(f"Student : {student_name}")
print(f"Roll No : {roll_no}")
print(f"Face ID : {user_id}")
print("==========================================")
print()


# ============================================================
# MARK ATTENDANCE
# ============================================================

def mark_attendance(user_id):

    conn = None
    cursor = None

    try:

        conn = get_connection()
        cursor = conn.cursor()

        today = datetime.now().date()
        current_time = datetime.now().time()

        # ----------------------------------------------------
        # Check whether attendance already exists today
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT id
            FROM face_attendance
            WHERE user_id = %s
            AND attendance_date = %s
            """,
            (
                user_id,
                today
            )
        )

        existing_record = cursor.fetchone()

        if existing_record:

            return "Already Marked"

        # ----------------------------------------------------
        # Insert attendance
        # ----------------------------------------------------

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
                user_id,
                today,
                current_time
            )
        )

        conn.commit()

        return "Attendance Marked"

    except Exception as e:

        if conn:
            conn.rollback()

        print()
        print(f"Attendance database error: {e}")
        print()

        return "Database Error"

    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()


# ============================================================
# LOAD HAAR CASCADE
# ============================================================

face_cascade = cv2.CascadeClassifier(CASCADE_PATH)

if face_cascade.empty():

    print("Error: Haar Cascade could not be loaded.")
    sys.exit(1)


# ============================================================
# LOAD LBPH MODEL
# ============================================================

try:

    recognizer = cv2.face.LBPHFaceRecognizer_create()

except AttributeError:

    print()
    print("Error: OpenCV face module is not available.")
    print()
    print("Install:")
    print("pip install opencv-contrib-python")
    sys.exit(1)


try:

    recognizer.read(MODEL_PATH)

except Exception as e:

    print(f"Error loading trained model: {e}")
    sys.exit(1)


# ============================================================
# OPEN CAMERA
# ============================================================

cap = cv2.VideoCapture(0)

if not cap.isOpened():

    print()
    print("Error: Could not open camera.")
    print("Make sure your webcam is connected.")
    print()

    sys.exit(1)


# ============================================================
# CAMERA SETTINGS
# ============================================================

cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)


attendance_completed = False
attendance_completed_time = None

attendance_message = ""


# ============================================================
# FACE RECOGNITION LOOP
# ============================================================

while True:

    ret, frame = cap.read()

    if not ret:

        print("Error: Could not read camera frame.")
        break


    # --------------------------------------------------------
    # Convert frame to grayscale
    # --------------------------------------------------------

    gray = cv2.cvtColor(
        frame,
        cv2.COLOR_BGR2GRAY
    )


    # --------------------------------------------------------
    # Detect faces
    # --------------------------------------------------------

    faces = face_cascade.detectMultiScale(
        gray,
        scaleFactor=1.3,
        minNeighbors=5,
        minSize=(100, 100)
    )


    # --------------------------------------------------------
    # Process detected faces
    # --------------------------------------------------------

    for (x, y, w, h) in faces:

        face_region = gray[
            y:y + h,
            x:x + w
        ]


        # ----------------------------------------------------
        # Recognize face
        # ----------------------------------------------------

        try:

            predicted_id, confidence = recognizer.predict(
                face_region
            )

        except Exception:

            predicted_id = -1
            confidence = 999


        # LBPH confidence:
        # Lower = better match
        #
        # 100 is used as a reasonable threshold.
        # You can make this stricter later.

        if predicted_id == FACE_ID and confidence < 100:

            # ------------------------------------------------
            # Face matched
            # ------------------------------------------------

            cv2.rectangle(
                frame,
                (x, y),
                (x + w, y + h),
                (0, 255, 0),
                2
            )


            cv2.putText(
                frame,
                student_name,
                (x, y - 35),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 255, 0),
                2
            )


            cv2.putText(
                frame,
                f"Roll No: {roll_no}",
                (x, y - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2
            )


            # -----------------------------------------------
            # Mark attendance only once
            # -----------------------------------------------

            if not attendance_completed:

                attendance_message = mark_attendance(
                    user_id
                )

                attendance_completed = True

                # Start the 10-second timer
                attendance_completed_time = time.time()


        else:

            # ------------------------------------------------
            # Wrong student
            # ------------------------------------------------

            cv2.rectangle(
                frame,
                (x, y),
                (x + w, y + h),
                (0, 0, 255),
                2
            )


            cv2.putText(
                frame,
                "Face Not Matched",
                (x, y - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 0, 255),
                2
            )


    # ========================================================
    # AFTER ATTENDANCE IS MARKED
    # KEEP CAMERA ON FOR 10 SECONDS
    # ========================================================

    if attendance_completed:

        elapsed_time = (
            time.time()
            - attendance_completed_time
        )

        remaining_time = max(
            0,
            10 - int(elapsed_time)
        )


        # ----------------------------------------------------
        # Success message
        # ----------------------------------------------------

        if attendance_message == "Attendance Marked":

            message = "Attendance Marked Successfully!"

        elif attendance_message == "Already Marked":

            message = "Attendance Already Marked Today"

        else:

            message = attendance_message


        cv2.putText(
            frame,
            message,
            (30, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.75,
            (0, 255, 0),
            2
        )


        cv2.putText(
            frame,
            f"Camera closing in {remaining_time} seconds...",
            (30, 75),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (255, 255, 255),
            2
        )


        # ----------------------------------------------------
        # Close after 10 seconds
        # ----------------------------------------------------

        if elapsed_time >= 10:

            break


    else:

        # ----------------------------------------------------
        # Normal camera message
        # ----------------------------------------------------

        cv2.putText(
            frame,
            "Look at the camera",
            (30, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.75,
            (255, 255, 255),
            2
        )


    # ========================================================
    # SHOW CAMERA
    # ========================================================

    cv2.imshow(
        "Face Recognition Attendance",
        frame
    )


    # ========================================================
    # ENTER = MANUAL EXIT
    # ========================================================

    key = cv2.waitKey(1) & 0xFF

    if key == 13:

        break


# ============================================================
# CAMERA OFF
# ============================================================

cap.release()

cv2.destroyAllWindows()


print()
print("==========================================")
print("Camera OFF.")
print("Attendance process completed.")
print("==========================================")