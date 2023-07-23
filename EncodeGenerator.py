import cv2
import face_recognition
import pickle
import mysql.connector
from PIL import Image
import io
import os

# Set up your MySQL database configuration here
mysql_host = 'localhost'
mysql_user = 'root'
mysql_password = ''
mysql_database = 'face_recognition_db'

def findEncodings(imagesList):
    encodeList = []
    for img in imagesList:
        encode = face_recognition.face_encodings(img)[0]
        encodeList.append(encode)

    return encodeList

def save_image_from_blob(image_blob, image_name):
    with Image.open(io.BytesIO(image_blob)) as img:
        image_file_path = os.path.join("images", image_name)
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

        img = cv2.imread(os.path.join("images", image_name))
        imgList.append(img)
        image_names.append(image_name)

    cursor.close()
    connection.close()

    return imgList, image_names



print("Reading images from SQL and saving to the 'images' folder...")
imgList, image_names = read_images_from_sql()

print("Encoding Started ...")
encodeListKnown = findEncodings(imgList)
encodeListKnownWithNames = [encodeListKnown, image_names]
print("Encoding Complete")

# Save encoded face data and image names to a file
file = open("EncodeFile.p", 'wb')
pickle.dump(encodeListKnownWithNames, file)
file.close()
print("File Saved")
