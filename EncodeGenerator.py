import cv2
import face_recognition
import pickle
import os
import psycopg2

# import firebase_admin
# from firebase_admin import credentials, db
# from firebase_admin import storage
#
# cred = credentials.Certificate("serviceAccountKey.json")
# firebase_admin.initialize_app(cred, {
#     'databaseURL': "https://studentattendance-fee90-default-rtdb.firebaseio.com/",
#     'storageBucket': "studentattendance-fee90.appspot.com"
# })

# connection = psycopg2.connect(
#     host="localhost",
#     port="5432",
#     database="Students",
#     user="postgres",
#     password="BossBoss12"
# )
# cursor = connection.cursor()



# import student imgaes
folderPath = 'images'
pathList = os.listdir(folderPath)
print(pathList)
imgList = []
studentIds = []
for path in pathList:
    imgList.append(cv2.imread(os.path.join(folderPath, path)))
    studentIds.append(os.path.splitext(path)[0])





# # Create the table if it doesn't exist
# cursor.execute(
#     "CREATE TABLE IF NOT EXISTS students (id SERIAL PRIMARY KEY, student_id TEXT, image BYTEA, last_attendance_time TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP);")

# Save student images and IDs to the PostgreSQL database
for img, student_id in zip(imgList, studentIds):
    # Convert the image to binary data
    results, img_bytes = cv2.imencode('.png', img)
    img_bytes = img_bytes.tobytes()

    # Insert the student ID and image into the table
    # cursor.execute("INSERT INTO students (student_id, image) VALUES (%s, %s);", (student_id, img_bytes))


    # connection.commit()

# print("Data saved to PostgreSQL database")

# Close the database connection
# cursor.close()
# connection.close()







# #STORING TO DB
#     fileName = f'{folderPath}/{path}'
#     bucket = storage.bucket()
#     blob = bucket.blob(fileName)
#     blob.upload_from_filename(fileName)


    # print(os.path.splitext(path)[0])
print(studentIds)
print(len(imgList))


# print(len(imgModeList))


def findEncodings(images_list):
    encodeLists = []
    for img in images_list:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        encode = face_recognition.face_encodings(img)[0]
        encodeLists.append(encode)

    return encodeLists


print("encoding started.....")
encodeListKnown = findEncodings(imgList)
encodeListKnownWithIds = [encodeListKnown, studentIds]
print("encoding Complete")

file = open("EncodeFile.p", 'wb')
pickle.dump(encodeListKnownWithIds, file)
file.close()
print("File saved")
