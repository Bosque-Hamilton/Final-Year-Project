from flask import Flask, render_template, Response, request, redirect, url_for, session
import cv2
import face_recognition
import numpy as np
import mysql.connector
from PIL import Image
import os
import cvzone
import pickle
from flask_wtf import CSRFProtect
import secrets
import datetime
import base64
import time
from io import BytesIO

app = Flask(__name__)
secret_key = secrets.token_hex(16)  # Generate a 32-character random hexadecimal string
app.secret_key = secret_key  # Replace with your own secret key

# Initialize CSRF protection
csrf = CSRFProtect(app)

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
            cursor.execute(insert_image_query, (name, image_binary))

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
    try:
        connection = mysql.connector.connect(
            host=mysql_host,
            user=mysql_user,
            password=mysql_password,
            database=mysql_database
        )
        
        cursor = connection.cursor()
    
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


            recognized_students.append(name)
            
            
        return recognized_students
    
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None
    

# def get_student_id_by_name(name):
#     # Function to retrieve student_id by name from the student table
#     try:
#         connection = mysql.connector.connect(
#             host=mysql_host,
#             user=mysql_user,
#             password=mysql_password,
#             database=mysql_database
#         )

#         cursor = connection.cursor()

#         # Define the SQL query to retrieve student_id by name
#         select_query = "SELECT student_id FROM student WHERE name = %s"
#         cursor.execute(select_query, (name))
#         result = cursor.fetchone()

#         cursor.close()
#         connection.close()

#         if result:
#             return result[0]
#         else:
#             return None

#     except mysql.connector.Error as err:
#         print(f"Error: {err}")
#         return None

# def record_attendance(student_id, name):
#     # Function to record attendance in the attendance table
#     try:
#         connection = mysql.connector.connect(
#             host=mysql_host,
#             user=mysql_user,
#             password=mysql_password,
#             database=mysql_database
#         )

#         cursor = connection.cursor()

#         # Get the current time and date
#         current_time = datetime.datetime.now().time()
#         current_date = datetime.datetime.now().date()

#         # Define the SQL query to insert attendance record
#         insert_query = "INSERT INTO attendance (name, student_id, time, date) VALUES (%s, %s, %s, %s)"
#         cursor.execute(insert_query, (name, student_id, current_time, current_date))

#         # Commit changes to the database
#         connection.commit()

#         cursor.close()
#         connection.close()

#     except mysql.connector.Error as err:
#         print(f"Error: {err}")

def gen_frames():
    try:
        connection = mysql.connector.connect(
            host=mysql_host,
            user=mysql_user,
            password=mysql_password,
            database=mysql_database
        )
        cursor = connection.cursor()

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

                # Record attendance for the frame (all recognized faces)
                for name in face_names:
                    select_query = "SELECT student_id FROM student WHERE name = %s"
                    cursor.execute(select_query, (name,))  # Pass name as a single-element tuple

                    res = cursor.fetchone()
                    student_id = res[0]
                    
                    # Define the SQL query to check if an attendance record already exists within the last 2 hours
                    check_existing_query = "SELECT COUNT(*) FROM attendance WHERE name = %s AND date = %s AND time >= %s"
                    two_hours_ago = (datetime.datetime.now() - datetime.timedelta(hours=2)).time()

                    cursor.execute(check_existing_query, (name, str(datetime.date.today()), str(two_hours_ago)))
                    result = cursor.fetchone()
                    attendance_count = result[0]

                    # Check if the result is not None before accessing its elements
                    if result is not None:
                        attendance_count = result[0]

                        if attendance_count == 0:
                            # If no attendance record exists within the last 2 hours, insert a new record
                            # Get the current time and date
                            current_time = datetime.datetime.now().time()
                            current_date = datetime.date.today()

                            # Define the SQL query to insert attendance record
                            insert_query = "INSERT INTO attendance (name, student_id, time, date) VALUES (%s, %s, %s, %s)"
                            if student_id is not None:
                                cursor.execute(insert_query, (name, student_id, str(current_time), str(current_date)))
                                connection.commit()
                                print("Attendance recorded.")
                            else:
                                print("Student ID not found for the recognized name.")
                        else:
                            print("Attendance already recorded within the last 2 hours.")


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

        # Close cursor and connection after exiting the loop
        cursor.close()
        connection.close()

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None
    
@app.route('/attendance')
def view_attendance():
    try:
        connection = mysql.connector.connect(
            host=mysql_host,
            user=mysql_user,
            password=mysql_password,
            database=mysql_database
        )
        cursor = connection.cursor()

        # Define the SQL query to select attendance data from the database
        select_query = "SELECT name, student_id, time, date FROM attendance"

        cursor.execute(select_query)
        attendance_data = cursor.fetchall()

        # Close cursor and connection after fetching data
        cursor.close()
        connection.close()

        # Pass the attendance_data to the template and render it
        return render_template('attendance.html', attendance_data=attendance_data)

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return "An error occurred while fetching attendance data."


    
@app.route('/fr_page')
def fr_page():
    return render_template('fr_page.html')

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        password = request.form['password']
        email = request.form['email']
        course = request.form['course']
        gender = request.form['gender']

        try:
            connection = mysql.connector.connect(
                host=mysql_host,
                user=mysql_user,
                password=mysql_password,
                database=mysql_database
            )

            cursor = connection.cursor()

            # Define the SQL query to insert lecturer information
            insert_query = "INSERT INTO lecturer (name, password, email, course, gender) VALUES (%s, %s, %s, %s, %s)"
            cursor.execute(insert_query, (name, password, email, course, gender))

            # Commit changes to the database
            connection.commit()

            cursor.close()
            connection.close()

            # Redirect to a success page or another endpoint
            return redirect('/signup-success')

        except mysql.connector.Error as err:
            return f"Error: {err}"

    return render_template('signup.html')

@app.route('/signup-success')
def signup_success():
    return "Signup Successful! Thank you for registering."

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        # Connect to the MySQL database
        try:
            connection = mysql.connector.connect(
                host=mysql_host,
                user=mysql_user,
                password=mysql_password,
                database=mysql_database
            )

            cursor = connection.cursor()

            # Define the SQL query to check if the email and password match in the lecturer table
            select_query = "SELECT * FROM lecturer WHERE email = %s AND password = %s"
            cursor.execute(select_query, (email, password))
            result = cursor.fetchone()

            cursor.close()
            connection.close()

            if result:
                # Login successful
                # You can store the lecturer's information in the session for future use
                session['user_id'] = result[0]
                session['name'] = result[1]
                session['email'] = result[2]
                # Add more fields from the lecturer table as needed

                return redirect('/')  # Redirect to the dashboard page after login

            else:
                # Login failed, show an error message
                return render_template('login.html', error_message="Invalid email or password")

        except mysql.connector.Error as err:
            return f"Error: {err}"

    return render_template('login.html')



if __name__ == "__main__":
    
    
    app.run(debug=True)
