import cv2
import numpy as np
import os

DATASET_PATH = "dataset"
MODEL_DIR = "models"
MODEL_PATH = os.path.join(MODEL_DIR, "trained_model.yml")


def main():
    if not os.path.exists(DATASET_PATH):
        print("Error: dataset folder not found.")
        return

    faces = []
    labels = []

    for folder in os.listdir(DATASET_PATH):

        folder_path = os.path.join(DATASET_PATH, folder)

        if not os.path.isdir(folder_path):
            continue

        if not folder.isdigit():
            print(f"Skipping invalid folder: {folder}")
            continue

        user_id = int(folder)

        for image_name in os.listdir(folder_path):

            image_path = os.path.join(folder_path, image_name)

            img = cv2.imread(
                image_path,
                cv2.IMREAD_GRAYSCALE
            )

            if img is None:
                print(f"Skipping invalid image: {image_path}")
                continue

            faces.append(img)
            labels.append(user_id)

    if not faces:
        print("Error: No face images found in dataset.")
        return

    labels = np.array(labels, dtype=np.int32)

    os.makedirs(MODEL_DIR, exist_ok=True)

    model = cv2.face.LBPHFaceRecognizer_create()

    model.train(faces, labels)

    model.save(MODEL_PATH)

    print("\nModel training completed successfully.")
    print(f"Images used: {len(faces)}")
    print(f"Users trained: {len(set(labels))}")
    print(f"Model saved to: {MODEL_PATH}")


if __name__ == "__main__":
    main()