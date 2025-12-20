import cv2
import os
from db_connection import get_connection

face_classifier = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)

def face_extractor(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces = face_classifier.detectMultiScale(gray, 1.3, 5)
    for (x, y, w, h) in faces:
        return gray[y:y+h, x:x+w]
    return None

user_id = input("Enter User ID: ")
user_name = input("Enter User Name: ")

conn = get_connection()
cursor = conn.cursor()
cursor.execute("INSERT INTO users (id, name) VALUES (%s, %s)", (user_id, user_name))
conn.commit()

cap = cv2.VideoCapture(0)
count = 0

os.makedirs(f"dataset/{user_id}", exist_ok=True)

while True:
    ret, frame = cap.read()
    if face_extractor(frame) is not None:
        count += 1
        face = cv2.resize(face_extractor(frame), (200, 200))
        file_name = f"dataset/{user_id}/user_{count}.jpg"
        cv2.imwrite(file_name, face)
        cv2.putText(face, str(count), (50, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        cv2.imshow("Face Cropper", face)
    else:
        cv2.imshow("Face Cropper", frame)

    if cv2.waitKey(1) == 13 or count == 50:
        break

cap.release()
cv2.destroyAllWindows()
print("Face data collection completed")
