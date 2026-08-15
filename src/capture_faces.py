import cv2
import os
import sys
from db_connection import get_connection


# -----------------------------
# Load Haar Cascade
# -----------------------------
face_classifier = cv2.CascadeClassifier(
    cv2.data.haarcascades +
    "haarcascade_frontalface_default.xml"
)


if face_classifier.empty():
    print("Error: Haar Cascade could not be loaded.")
    sys.exit(1)


# -----------------------------
# Face extraction
# -----------------------------
def face_extractor(img):

    gray = cv2.cvtColor(
        img,
        cv2.COLOR_BGR2GRAY
    )

    faces = face_classifier.detectMultiScale(
        gray,
        scaleFactor=1.3,
        minNeighbors=5
    )

    for (x, y, w, h) in faces:

        return gray[
            y:y + h,
            x:x + w
        ]

    return None


# -----------------------------
# Get student details
# -----------------------------
if len(sys.argv) >= 3:

    user_id = sys.argv[1]
    user_name = sys.argv[2]

else:

    user_id = input("Enter User ID: ").strip()
    user_name = input("Enter User Name: ").strip()


# -----------------------------
# Validate ID
# -----------------------------
if not user_id.isdigit():

    print("Error: User ID must contain only numbers.")
    sys.exit(1)


user_id = int(user_id)


if not user_name:

    print("Error: User name cannot be empty.")
    sys.exit(1)


# -----------------------------
# Check user exists
# -----------------------------
conn = get_connection()
cursor = conn.cursor()

try:

    cursor.execute(
        "SELECT id, name FROM users WHERE id = %s",
        (user_id,)
    )

    user = cursor.fetchone()

finally:

    cursor.close()
    conn.close()


if not user:

    print(
        f"Error: User ID {user_id} "
        f"does not exist in database."
    )

    sys.exit(1)


# Use database name
user_name = user[1]


# -----------------------------
# Dataset directory
# -----------------------------
dataset_path = os.path.join(
    "dataset",
    str(user_id)
)

os.makedirs(
    dataset_path,
    exist_ok=True
)


# -----------------------------
# Open camera
# -----------------------------
cap = cv2.VideoCapture(0)

if not cap.isOpened():

    print("Error: Could not open webcam.")
    sys.exit(1)


count = 0

print()
print("Face capture started.")
print(f"Student: {user_name}")
print(f"Face ID: {user_id}")
print()
print("Look at the camera and slowly move your face.")
print("Press ENTER to stop.")
print()


# -----------------------------
# Capture faces
# -----------------------------
while True:

    ret, frame = cap.read()

    if not ret:

        print("Error: Could not read camera.")
        break


    face = face_extractor(frame)


    if face is not None:

        count += 1

        face = cv2.resize(
            face,
            (200, 200)
        )


        file_name = os.path.join(
            dataset_path,
            f"user_{count}.jpg"
        )


        cv2.imwrite(
            file_name,
            face
        )


        display_face = face.copy()


        cv2.putText(
            display_face,
            str(count),
            (50, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (255, 255, 255),
            2
        )


        cv2.imshow(
            "Face Capture",
            display_face
        )

    else:

        cv2.imshow(
            "Face Capture",
            frame
        )


    # Stop with ENTER
    if cv2.waitKey(1) & 0xFF == 13:

        break


    # Automatically stop at 50
    if count >= 50:

        break


# -----------------------------
# Cleanup
# -----------------------------
cap.release()
cv2.destroyAllWindows()


print()
print("Face data collection completed.")
print(f"User: {user_name}")
print(f"User ID: {user_id}")
print(f"Images captured: {count}")
print(f"Dataset location: {dataset_path}")