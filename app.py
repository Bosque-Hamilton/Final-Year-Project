from flask import Flask, render_template, Response, request, redirect
import cv2
import face_recognition
import numpy as np
import mysql.connector
from PIL import Image
import os
import cvzone
import pickle
import datetime
import base64
import time
from io import BytesIO

app = Flask(__name__)

# Set up your MySQL database configuration here
mysql_host = 'localhost'
mysql_user = 'root'
mysql_password = ''
mysql_database = 'face_recognition_db'


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        name = request.form['name']
        student_id = request.form['student_id']
        course = request.form['course']
        year = int(request.form['year'])

        # Capture an image from the webcam
        image = capture_image()

        # Store user information in the database
        try:
            connection = mysql.connector.connect(
                host=mysql_host,
                user=mysql_user,
                password=mysql_password,
                database=mysql_database
            )

            cursor = connection.cursor()

            # Define the SQL query to insert user information
            insert_query = "INSERT INTO student (name, student_id, course, year) VALUES (%s, %s, %s, %s)"
            cursor.execute(insert_query, (name, student_id, course, year))

            image_buffer = BytesIO()
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            image_pil = Image.fromarray(image)
            image_pil.save(image_buffer, format='JPEG')
            image_binary = image_buffer.getvalue()

            # Define the SQL query to insert the image into the Images table
            insert_image_query = "INSERT INTO images (image_name, image_data) VALUES (%s, %s)"

            # Insert the image into the Images table
            cursor.execute(insert_image_query, (f"{name}.jpg", image_binary))

            # Commit changes to the database
            connection.commit()

            cursor.close()
            connection.close()
            
            return redirect('/')

        except mysql.connector.Error as err:
            return f"Error: {err}"

    return render_template('index.html')

def capture_image():
    # Function to capture an image from the webcam
    camera = cv2.VideoCapture(0)

    _, image = camera.read()
    #image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    camera.release()

    return image

file_path = 'EncodeFile.p'  # Replace with the actual file path

# Check if the file exists
if os.path.exists(file_path):
    # Open the file
    with open(file_path, 'rb') as file:
        encodeListKnownWithNames = pickle.load(file)
    encodeListKnown, image_names = encodeListKnownWithNames
    print("Encoded file loaded")
else:
    print(f"Error: File '{file_path}' does not exist.")

# ... (rest of the code)

def recognize_faces(image):
    # Function to recognize faces in the given image and get student ID and name
    rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    face_locations = face_recognition.face_locations(rgb_image)
    face_encodings = face_recognition.face_encodings(rgb_image, face_locations)

    recognized_students = []

    for face_encoding in face_encodings:
        # Perform face recognition
        matches = face_recognition.compare_faces(encodeListKnown, face_encoding)
        name = "Unknown"
        student_id = None

        if True in matches:
            best_match_index = np.argmax(matches)
            name = image_names[best_match_index]
            name = name.replace('.jpg', '')
            student_id = get_student_id_by_name(name)

        recognized_students.append((student_id, name))

    return recognized_students

def get_student_id_by_name(name):
    # Function to retrieve student_id by name from the student table
    try:
        connection = mysql.connector.connect(
            host=mysql_host,
            user=mysql_user,
            password=mysql_password,
            database=mysql_database
        )

        cursor = connection.cursor()

        # Define the SQL query to retrieve student_id by name
        select_query = "SELECT student_id FROM student WHERE name = %s"
        cursor.execute(select_query, (name,))
        result = cursor.fetchone()

        cursor.close()
        connection.close()

        if result:
            return result[0]
        else:
            return None

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None

def record_attendance(student_id, name):
    # Function to record attendance in the attendance table
    try:
        connection = mysql.connector.connect(
            host=mysql_host,
            user=mysql_user,
            password=mysql_password,
            database=mysql_database
        )

        cursor = connection.cursor()

        # Get the current time and date
        current_time = datetime.datetime.now().time()
        current_date = datetime.datetime.now().date()

        # Define the SQL query to insert attendance record
        insert_query = "INSERT INTO attendance (name, student_id, time, date) VALUES (%s, %s, %s, %s)"
        cursor.execute(insert_query, (name, student_id, current_time, current_date))

        # Commit changes to the database
        connection.commit()

        cursor.close()
        connection.close()

    except mysql.connector.Error as err:
        print(f"Error: {err}")

def gen_frames():
    camera = cv2.VideoCapture(0)
    while True:
        success, frame = camera.read()  # read the camera frame
        if not success:
            break
        else:
            # Resize frame of video to 1/4 size for faster face recognition processing
            small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
            # Convert the image from BGR color (which OpenCV uses) to RGB color (which face_recognition uses)
            rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

            # Find all the faces and face encodings in the current frame of video
            face_locations = face_recognition.face_locations(rgb_small_frame)
            face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)
            face_names = []

            for face_encoding in face_encodings:
                # Perform face recognition
                matches = face_recognition.compare_faces(encodeListKnown, face_encoding)
                name = "Unknown"

                if True in matches:
                    best_match_index = np.argmax(matches)
                    name = image_names[best_match_index]
                    name = name.replace('.jpg', '')

                face_names.append(name)

            # Display the results
            for faceLoc, name in zip(face_locations, face_names):
                # Scale back up face locations since the frame we detected in was scaled to 1/4 size
                y1, x2, y2, x1 = faceLoc
                y1, x2, y2, x1 = y1 * 4, x2 * 4, y2 * 4, x1 * 4
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
                font = cv2.FONT_HERSHEY_DUPLEX
                cv2.putText(frame, name, (x1 + 6, y2 - 6), font, 0.5, (255, 255, 255), 1)

            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
    
@app.route('/fr_page')
def fr_page():
    return render_template('fr_page.html')

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')



if __name__ == "__main__":
    
    
    app.run()
