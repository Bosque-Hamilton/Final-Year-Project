import cv2
import face_recognition
import pickle
import mysql.connector
from PIL import Image
import time
import io
import schedule
import threading
import os
import socket


# Set up socket communication
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind(("localhost", 12345))
server_socket.listen(1)

# Global variable to hold the encodings
encodeListKnownWithNames = []

# Set up your MySQL database configuration here
mysql_host = 'localhost'
mysql_user = 'root'
mysql_password = ''
mysql_database = 'face_recognition_db'

def findEncodings(imagesList):
    encodeList = []
    for img in imagesList:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        face_encodings = face_recognition.face_encodings(img)
        if len(face_encodings) > 0:
            # Take the first face encoding (if multiple faces detected, you may handle them differently)
            encode = face_encodings[0]
            encodeList.append(encode)

    return encodeList

def save_image_from_blob(image_blob, image_name):
    with Image.open(io.BytesIO(image_blob)) as img:
        image_file_path = os.path.join("images", f"{image_name}.jpg")
        img.save(image_file_path)



def read_images_from_sql():
    connection = mysql.connector.connect(
        host=mysql_host,
        user=mysql_user,
        password=mysql_password,
        database=mysql_database
    )

    cursor = connection.cursor()

    select_query = "SELECT image_name, image_data FROM Images"
    cursor.execute(select_query)
    images_data = cursor.fetchall()

    imgList = []
    image_names = []

    for image_name, image_data in images_data:
        save_image_from_blob(image_data, image_name)

        img = cv2.imread(os.path.join("images", f"{image_name}.jpg"))
        imgList.append(img)
        image_names.append(image_name)

    cursor.close()
    connection.close()

    return imgList, image_names



# Define the function to run
def run_task():
    print("Reading images from SQL and saving to the 'images' folder...")
    imgList, image_names = read_images_from_sql()

    print("Encoding Started ...")
    encodeListKnown = findEncodings(imgList)
    global encodeListKnownWithNames
    encodeListKnownWithNames = [encodeListKnown, image_names]
    print("Encoding Complete")

    # Save encoded face data and image names to a file
    # file = open("EncodeFile.p", 'wb')
    # pickle.dump(encodeListKnownWithNames, file)
    # file.close()
    # print("File Saved")

# def scheduled_task():
#     while True:
#         run_task()
#         time.sleep(5)  # Sleep for 5 seconds (5 seconds)
#
# # # Schedule the function to run every 1 minute
# # schedule.every(1).minutes.do(run_task)
#
# # Start the scheduled task in a separate thread
# task_thread = threading.Thread(target=scheduled_task)
# task_thread.start()


# file_path = 'EncodeFile.p'  # Replace with the actual file path
#
# # Check if the file exists
# if os.path.exists(file_path):
#     # Open the file
#     with open(file_path, 'rb') as file:
#         encodeListKnownWithNames = pickle.load(file)
#     encodeListKnown, image_names = encodeListKnownWithNames
#
#     print("Encoded file loaded")
# else:
#     print(f"Error: File '{file_path}' does not exist.")


# Send the updated data over the socket
connection, address = server_socket.accept()
with connection:
    data_to_send = pickle.dumps(encodeListKnownWithNames)
    connection.send(data_to_send)
