import cv2
import numpy as np
import os

data_path = "dataset"
faces = []
labels = []

for folder in os.listdir(data_path):
    for image in os.listdir(f"{data_path}/{folder}"):
        img_path = f"{data_path}/{folder}/{image}"
        img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
        faces.append(img)
        labels.append(int(folder))

labels = np.array(labels)

model = cv2.face.LBPHFaceRecognizer_create()
model.train(faces, labels)
model.save("models/trained_model.yml")

print("Model training completed")
