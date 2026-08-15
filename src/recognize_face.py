import cv2
import sys
from datetime import datetime
from db_connection import get_connection


MODEL_PATH = "models/trained_model.yml"
CONFIDENCE_THRESHOLD = 60


# -----------------------------
# Get student from database
# -----------------------------
def get_user(user_id):

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "SELECT id, name, roll_no FROM users WHERE id = %s",
            (user_id,)
        )

        return cursor.fetchone()

    finally:
        cursor.close()
        conn.close()


# -----------------------------
# Mark attendance
# -----------------------------
def mark_attendance(user_id):

    conn = get_connection()
    cursor = conn.cursor()

    today = datetime.now().date()
    current_time = datetime.now().time()

    try:

        cursor.execute(
            """
            SELECT id
            FROM attendance
            WHERE user_id = %s
            AND attendance_date = %s
            """,
            (user_id, today)
        )

        existing = cursor.fetchone()

        if existing:
            return "Already Present"

        cursor.execute(
            """
            INSERT INTO attendance
            (user_id, attendance_date, attendance_time)
            VALUES (%s, %s, %s)
            """,
            (user_id, today, current_time)
        )

        conn.commit()

        return "Attendance Marked"

    except Exception as e:

        conn.rollback()

        print("Database error:", e)

        return "Database Error"

    finally:

        cursor.close()
        conn.close()


# -----------------------------
# Get Face ID
# -----------------------------
if len(sys.argv) >= 2:

    user_id = sys.argv[1].strip()

else:

    user_id = input("Enter Student ID: ").strip()


if not user_id.isdigit():

    print("Invalid Student ID.")

    sys.exit(1)


user_id = int(user_id)


# -----------------------------
# Check student
# -----------------------------
user = get_user(user_id)


if user is None:

    print(
        f"Student ID {user_id} "
        f"was not found."
    )

    sys.exit(1)


user_id = user[0]
user_name = user[1]
roll_no = user[2]


print()
print(f"Student: {user_name}")
print(f"Roll No: {roll_no}")
print(f"Face ID: {user_id}")
print()
print("Opening camera...")
print("Look at the camera.")
print()


# -----------------------------
# Load LBPH model
# -----------------------------
try:

    model = cv2.face.LBPHFaceRecognizer_create()

    model.read(MODEL_PATH)

except Exception as e:

    print(
        "Error loading trained model:",
        e
    )

    sys.exit(1)


# -----------------------------
# Load Haar Cascade
# -----------------------------
face_classifier = cv2.CascadeClassifier(
    cv2.data.haarcascades +
    "haarcascade_frontalface_default.xml"
)


if face_classifier.empty():

    print(
        "Error: Haar Cascade "
        "could not be loaded."
    )

    sys.exit(1)


# -----------------------------
# Open camera
# -----------------------------
cap = cv2.VideoCapture(0)


if not cap.isOpened():

    print(
        "Error: Could not open webcam."
    )

    sys.exit(1)


attendance_completed = False


# -----------------------------
# Face recognition
# -----------------------------
while True:

    ret, frame = cap.read()

    if not ret:

        print(
            "Error: Could not read webcam."
        )

        break


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


    for (x, y, w, h) in faces:

        face = gray[
            y:y + h,
            x:x + w
        ]


        try:

            predicted_id, distance = model.predict(
                face
            )

        except Exception:

            continue


        # -----------------------------
        # Correct student
        # -----------------------------
        if (
            predicted_id == user_id
            and distance <= CONFIDENCE_THRESHOLD
        ):

            status = mark_attendance(
                user_id
            )


            print(
                f"User: {user_name} | "
                f"Roll No: {roll_no} | "
                f"Face ID: {user_id} | "
                f"Distance: {distance:.2f}"
            )

            print(
                f"Status: {status}"
            )


            cv2.rectangle(
                frame,
                (x, y),
                (x + w, y + h),
                (0, 255, 0),
                2
            )


            cv2.putText(
                frame,
                user_name,
                (x, y - 45),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.9,
                (0, 255, 0),
                2
            )


            cv2.putText(
                frame,
                status,
                (x, y - 15),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2
            )


            cv2.imshow(
                "Face Recognition Attendance",
                frame
            )


            # Keep result visible for 2 seconds
            cv2.waitKey(2000)


            attendance_completed = True

            break


        # -----------------------------
        # Wrong student
        # -----------------------------
        else:

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


    # -----------------------------
    # Automatically stop
    # -----------------------------
    if attendance_completed:

        break


    cv2.imshow(
        "Face Recognition Attendance",
        frame
    )


    # ENTER = manual exit
    if cv2.waitKey(1) & 0xFF == 13:

        break


# -----------------------------
# Camera OFF
# -----------------------------
cap.release()

cv2.destroyAllWindows()


print()
print("Camera OFF.")
print("Attendance process completed.")