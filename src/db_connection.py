import os
import mysql.connector


def get_connection():
    # Railway
    if os.getenv("DB_HOST"):
        return mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            port=int(os.getenv("DB_PORT", "3306")),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME")
        )

    # Local computer
    return mysql.connector.connect(
        host="localhost",
        port=3306,
        user="root",
        password="Rahul@21",
        database="face_recognition"
    )