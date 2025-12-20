# Face Recognition System using OpenCV, Python & MySQL

This project implements a real-time face recognition system using OpenCV and Python.
It captures face images, trains a recognition model using LBPH algorithm, and identifies users through a webcam.
User details are stored and retrieved from a MySQL database.

## Features
- Face detection using Haar Cascade
- Face recognition using LBPH
- MySQL database integration
- Real-time webcam recognition

## Technologies
- Python
- OpenCV
- MySQL
- NumPy

## How to Run

1. Install dependencies  
pip install -r requirements.txt

2. Setup database  
Import `database/face_recognition.sql`

3. Capture face data  
python src/capture_faces.py

4. Train model  
python src/train_model.py

5. Recognize face  
python src/recognize_face.py

## Author
Koushik Gangishetty 
