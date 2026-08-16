cognition_Attendance_README.md


Face Recognition Attendance System using OpenCV, Python, Flask & MySQL
## 🌐 Live Demo

### 🚀 Railway Deployment

**Primary Live Application:**  
https://face-recognition-using-open-cv-production-8659.up.railway.app

**Alternative Railway URL:**  
https://face-recognition-using-open-cv-production.up.railway.appt-academic-management-system-production-54e0.up.railway.app/

A real-time Face Recognition Attendance System built using Python, OpenCV, Flask, LBPH Face Recognition, and MySQL.

The system allows an administrator to enroll students, automatically generate Roll Numbers and Face IDs, capture face data using a webcam, train the face recognition model, recognize students, mark attendance, view attendance records, and delete students.

Features
Student enrollment through web dashboard

Automatic Roll Number generation

Automatic Face ID generation

Face data collection using webcam

Captures 50 face images per student

Face detection using Haar Cascade

Face recognition using LBPH

Real-time face recognition

MySQL database integration

Automatic attendance marking

Prevents duplicate attendance on the same day

Camera automatically turns OFF after attendance

Attendance records dashboard

Student deletion

Delete attendance records

Delete student's face dataset

Retrain face recognition model after deletion

Flask web application

HTML/CSS user interface

Technologies
Python

Flask

OpenCV

LBPH Face Recognition

MySQL

MySQL Connector

NumPy

HTML

CSS

Project Structure
Face-recognition-using-open-cv--main/
│
├── app.py
├── README.md
├── requirements.txt
├── .gitignore
│
├── database/
│   └── face_recognition.sql
│
├── src/
│   ├── capture_faces.py
│   ├── db_connection.py
│   ├── recognize_face.py
│   └── train_model.py
│
├── templates/
│   ├── admin.html
│   ├── attendance.html
│   └── records.html
│
├── static/
│   └── style.css
│
├── dataset/
│   └── Student face images
│
└── models/
    └── trained_model.yml
Note: Student face images and the trained model are excluded from GitHub using .gitignore.

How to Run
1. Install Dependencies
pip install -r requirements.txt
2. Setup Database
Create the MySQL database:

CREATE DATABASE face_recognition;
Import:

database/face_recognition.sql
Configure your MySQL username, password, host, and database in:

src/db_connection.py
3. Start the Flask Application
python app.py
Open the application:

http://127.0.0.1:5000
Admin Enrollment
Open:

http://127.0.0.1:5000/admin
Enter the student's name.

The system automatically generates:

Student Name : Rahul
Roll Number  : 1001
Face ID      : 101
The camera opens automatically and captures 50 face images.

Train Face Recognition Model
After enrolling students, run:

python src/train_model.py
Example:

Model training completed successfully.
Images used: 100
Users trained: 2
Model saved to: models\trained_model.yml
Attendance
Open:

http://127.0.0.1:5000/attendance
Enter the student's Roll Number.

The system will:

Enter Roll Number
       ↓
Find Student
       ↓
Open Camera
       ↓
Detect Face
       ↓
Recognize Face
       ↓
Check Attendance
       ↓
Mark Attendance
       ↓
Camera OFF
If attendance was already marked:

Status: Already Present
Attendance Records
Open:

http://127.0.0.1:5000/records
The dashboard displays:

Roll Number

Student Name

Attendance Date

Attendance Time

Student Management
The Admin Dashboard allows the administrator to:

View registered students

Enroll new students

Automatically generate Roll Numbers

Automatically generate Face IDs

Delete students

Delete student face data

Delete related attendance records

Retrain the recognition model

Face Recognition
Haar Cascade
Haar Cascade is used for face detection.

haarcascade_frontalface_default.xml
LBPH
LBPH stands for Local Binary Patterns Histograms.

It is used for recognizing registered faces.

The project uses:

opencv-contrib-python
Database
Database name:

face_recognition
Users Table
id
roll_no
name
Example:

id     roll_no     name
---------------------------
101    1001        Rahul
102    1002        Student
Attendance Table
id
user_id
attendance_date
attendance_time
The system prevents duplicate attendance for the same student on the same day.

Complete Workflow
                    ADMIN
                      │
                      ▼
              Enter Student Name
                      │
                      ▼
             Generate Roll Number
                      │
                      ▼
                Generate Face ID
                      │
                      ▼
                Open Camera
                      │
                      ▼
              Capture 50 Images
                      │
                      ▼
                Train Model
                      │
                      ▼
             Student Registered
                      │
                      ▼
                 ATTENDANCE
                      │
                      ▼
               Enter Roll No.
                      │
                      ▼
                Open Camera
                      │
                      ▼
                Detect Face
                      │
                      ▼
               Recognize Face
                      │
                      ▼
              Mark Attendance
                      │
                      ▼
                  Camera OFF
                      │
                      ▼
             ATTENDANCE RECORDS
Project Status
The project has been successfully tested with:

MySQL connection

Flask application

Student enrollment

Automatic Roll Number generation

Automatic Face ID generation

Face data collection

50 images per student

Face model training

Face recognition

Attendance marking

Duplicate attendance prevention

Automatic camera shutdown

Attendance records

Student deletion

Attendance deletion

Face dataset deletion

Model retraining

Admin Dashboard

Attendance Dashboard

Records Dashboard

Latest successful training:

Model training completed successfully.
Images used: 100
Users trained: 2
Model saved to: models\trained_model.yml
.gitignore
__pycache__/
dataset/*
models/trained_model.yml
.env
.venv/
Future Improvements
Admin login authentication

Student login

Attendance filtering by date

Student search

Export attendance to CSV

Export attendance to Excel

Attendance analytics

Monthly attendance reports

Dashboard charts

Multiple camera support

Improved face recognition accuracy

Cloud deployment

Mobile-friendly interface

Email notifications

Role-based access control

Academic Use
This project can be used as:

B.Tech Mini Project

B.Tech Major Project

Python Project

Computer Vision Project

Machine Learning Project

Flask Project

MySQL Database Project

Authors
Rahul Boppena
B.Tech Student
GitHub: https://github.com/rahulboppena872-ui

Koushik G
Project Contributor
GitHub: https://github.com/gangieshettykoushik-18

License
This project is intended for educational and academic purposes