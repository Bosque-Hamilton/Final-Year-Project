from flask import Flask, render_template, Response, request, redirect, url_for, session, flash
import cv2
import face_recognition
import numpy as np
import mysql.connector
from PIL import Image
import os
from base64 import b64encode
import io
import cvzone
import pickle
from flask_wtf import CSRFProtect
import secrets
import datetime
import schedule
import base64
import json
import time
from io import BytesIO
# Modify the view_attendance function
from flask import jsonify

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

# # Schedule the function to run every 1 minute
# schedule.every(1).minutes.do(read_images_from_sql)
#
# while True:
#     schedule.run_pending()
#     time.sleep(1)

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

def capture_image():
    # Function to capture an image from the webcam
    camera = cv2.VideoCapture(0)

    _, image = camera.read()
    # image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    camera.release()

    return image

@app.route('/add_prsn', methods=['GET', 'POST'])
def index():
    if 'user_id' in session:
        # User is logged in, show the home page
        if request.method == 'POST':
            name = request.form['name']
            student_id = request.form['student_id']
            course = request.form['course']
            year = int(request.form['year'])
            email = request.form['email']
            gender = request.form['gender']
            date_of_birth = request.form['date_of_birth']

            # # Capture an image from the webcam
            # image = capture_image()
            try:
                # Check if an image was uploaded
                if 'imageInput' in request.files:
                    uploaded_image = request.files['imageInput']

                    # Check if the uploaded file has a valid image extension
                    if uploaded_image.filename and uploaded_image.filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                        image = Image.open(uploaded_image)

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
                            insert_query = "INSERT INTO student (name, student_id, email, gender, date_of_birth, course, year) VALUES (%s, %s, %s, %s, %s, %s, %s)"
                            cursor.execute(insert_query, (name, student_id,email, gender, date_of_birth, course, year))

                            # image_buffer = BytesIO()
                            # image.save(image_buffer, format='JPEG')
                            # image_binary = image_buffer.getvalue()

                            # Resize the image to a desired size
                            desired_width = 640  # Adjust the desired width
                            aspect_ratio = float(image.height) / float(image.width)
                            desired_height = int(desired_width * aspect_ratio)
                            image = image.resize((desired_width, desired_height), Image.ANTIALIAS)

                            # Compress the image
                            compression_quality = 85  # Adjust the compression quality (0-100)
                            output_buffer = io.BytesIO()
                            image.save(output_buffer, format='JPEG', quality=compression_quality)

                            # Get the binary data of the compressed image
                            image_binary = output_buffer.getvalue()

                            # Define the SQL query to insert the image into the Images table
                            insert_image_query = "INSERT INTO images (image_name, image_data) VALUES (%s, %s)"

                            # Insert the image into the Images table
                            cursor.execute(insert_image_query, (name, image_binary))

                            # Commit changes to the database
                            connection.commit()

                            cursor.close()
                            connection.close()

                            print("Image and data inserted successfully.")

                            return redirect('/add_prsn')

                        except mysql.connector.Error as err:
                            return f"Error: {err}"

                    else:
                        print("Invalid image format or no image uploaded.")

                else:
                    print("No image uploaded.")

            except mysql.connector.Error as err:
                return f"Error: {err}"

        return render_template('index.html', name=session['session_name'])
    else:
        # User is not logged in, redirect to login page
        return redirect(url_for('login'))

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

def update_attendance(name):
    try:
        connection = mysql.connector.connect(
            host=mysql_host,
            user=mysql_user,
            password=mysql_password,
            database=mysql_database
        )
        cursor = connection.cursor()

        # Calculate the total attendance count for the given student with "present" attendance
        count_present_query = "SELECT COUNT(*) FROM attendance WHERE name = %s AND attendance = 'present'"
        cursor.execute(count_present_query, (name,))
        result_present = cursor.fetchone()
        total_attendance_count = result_present[0]

        # Calculate the total lectures missed count for the given student with "absent" attendance
        count_absent_query = "SELECT COUNT(*) FROM attendance WHERE name = %s AND attendance = 'absent'"
        cursor.execute(count_absent_query, (name,))
        result_absent = cursor.fetchone()
        total_lectures_missed = result_absent[0]

        # print("Total Attendance Count:", total_attendance_count)
        # print("Total Lectures Missed:", total_lectures_missed)

        # Update the total_attendance and total_lectures_missed columns in the student table
        update_query = "UPDATE student SET total_attendance = %s, total_lectures_missed = %s WHERE name = %s"
        cursor.execute(update_query, (total_attendance_count, total_lectures_missed, name))
        connection.commit()

        print('Attendance Table Updated')

        cursor.close()
        connection.close()

    except mysql.connector.Error as err:
        print(f"Error updating attendance: {err}")
        return None

def update_attendance_for_all_students():
    try:
        connection = mysql.connector.connect(
            host=mysql_host,
            user=mysql_user,
            password=mysql_password,
            database=mysql_database
        )
        cursor = connection.cursor()

        # Get all student names from the database
        cursor.execute("SELECT name FROM student")
        all_student_names = [name[0] for name in cursor.fetchall()]

        # Update attendance for each student
        for name in all_student_names:
            update_attendance(name)

        cursor.close()
        connection.close()

    except mysql.connector.Error as err:
        print(f"Error updating attendance: {err}")
        return None

# Call the function to update attendance for all students
update_attendance_for_all_students()

def update_last_attendance(name):
    try:
        connection = mysql.connector.connect(
            host=mysql_host,
            user=mysql_user,
            password=mysql_password,
            database=mysql_database
        )
        cursor = connection.cursor()

        # Get the latest attendance time for the given name
        latest_attendance_query = "SELECT MAX(time) FROM attendance WHERE name = %s"
        cursor.execute(latest_attendance_query, (name,))
        latest_attendance_time = cursor.fetchone()[0]

        if latest_attendance_time is not None:
            # Create a datetime object with the current date and add the timedelta to it
            current_date = datetime.date.today()
            latest_attendance_datetime = datetime.datetime.combine(current_date, datetime.time()) + latest_attendance_time

            # Convert the datetime object to a string
            latest_attendance_time_str = latest_attendance_datetime.strftime("%Y-%m-%d %H:%M:%S")


            # Update the last_attendance column in the student table
            update_last_attendance_query = "UPDATE student SET last_attendance = %s WHERE name = %s"
            cursor.execute(update_last_attendance_query, (latest_attendance_time_str, name))
            connection.commit()

        cursor.close()
        connection.close()

    except mysql.connector.Error as err:
        print(f"Error updating last_attendance: {err}")

def gen_frames(session_name):
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
                    matches = face_recognition.compare_faces(encodeListKnown, face_encoding, tolerance=0.42)
                    name = "Unknown"

                    face_distances = face_recognition.face_distance(encodeListKnown, face_encoding)

                    if len(face_distances) > 0:
                        best_match_index = np.argmin(face_distances)

                        # print("Face Distances:", face_distances)

                        if matches[best_match_index]:
                            name = image_names[best_match_index]
                            name = name.replace('.jpg', '')

                    face_names.append(name)

                # Create a set to keep track of processed recognized faces
                processed_recognized_faces = set()

                # Record attendance for the frame (all recognized faces)
                for name in face_names:
                    if name not in processed_recognized_faces:
                        select_query = "SELECT student_id, course, year FROM student WHERE name = %s"
                        cursor.execute(select_query, (name,))  # Pass name as a single-element tuple

                        res = cursor.fetchone()
                        if res is not None:
                            student_id, course, year = res

                            # Define the SQL query to check if an attendance record already exists within the last 2 hours
                            check_existing_query = "SELECT COUNT(*) FROM attendance WHERE name = %s AND date = %s AND time >= %s"
                            two_hours_ago = (datetime.datetime.now() - datetime.timedelta(hours=2)).time()

                            cursor.execute(check_existing_query, (name, str(datetime.date.today()), str(two_hours_ago)))
                            result = cursor.fetchone()
                            attendance_count = result[0]

                            if attendance_count == 0:
                                # If no attendance record exists within the last 2 hours, insert a new record
                                # Get the current time and date
                                current_time = datetime.datetime.now().time()
                                current_date = datetime.date.today()

                                # Define the SQL query to insert attendance record
                                insert_query = "INSERT INTO attendance (name, attendance, student_id, course, student_year, lecturer, time, date) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"

                                if student_id is not None:
                                    cursor.execute(insert_query, (
                                    name, "present", student_id, course, year, session_name, str(current_time),
                                    str(current_date)))
                                    connection.commit()
                                    print("Attendance recorded.")
                                else:
                                    print("Student ID not found for the recognized name.")
                            else:
                                # Update the attendance column to "present" for an existing record within the last 2 hours
                                update_attendance_query = "UPDATE attendance SET attendance = %s, time = %s WHERE name = %s AND date = %s AND time >= %s"
                                current_time = datetime.datetime.now().time()

                                # Check if the attendance is already marked as "present" for the given name and date
                                check_present_query = "SELECT COUNT(*) FROM attendance WHERE name = %s AND date = %s AND attendance = %s AND time >= %s"
                                cursor.execute(check_present_query,
                                               (name, str(datetime.date.today()), "present", str(two_hours_ago)))
                                result = cursor.fetchone()
                                attendance_count_now = result[0]

                                if attendance_count_now == 0:
                                    # If no attendance record with "present" exists within the last 2 hours, update the attendance
                                    cursor.execute(update_attendance_query, (
                                        "present", str(current_time), name, str(datetime.date.today()),
                                        str(two_hours_ago)))
                                    connection.commit()
                                    print("Attendance updated for:", name)

                            # Add the processed recognized face to the set
                            processed_recognized_faces.add(name)

                # Update the attendance for unrecognized faces (not recorded)
                for name in image_names:
                    if name not in face_names:
                        select_query = "SELECT student_id, course, year FROM student WHERE name = %s"
                        cursor.execute(select_query, (name,))  # Pass name as a single-element tuple
                        res = cursor.fetchone()

                        if res is not None:
                            student_id, course, year = res
                            current_time = datetime.datetime.now().time()
                            current_date = datetime.date.today()

                            # Check if an attendance record already exists within the last 2 hours for the unrecognized face
                            check_existing_query = "SELECT COUNT(*) FROM attendance WHERE name = %s AND date = %s AND time >= %s"
                            two_hours_ago = (datetime.datetime.now() - datetime.timedelta(hours=2)).time()

                            cursor.execute(check_existing_query,
                                           (name, str(datetime.date.today()), str(two_hours_ago)))
                            result = cursor.fetchone()
                            attendance_count = result[0]

                            if attendance_count == 0:
                                # If no attendance record exists within the last 2 hours, insert a new record with "absent" attendance
                                insert_query = "INSERT INTO attendance (name, student_id, course, student_year, lecturer, time, date, attendance) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
                                cursor.execute(insert_query, (
                                    name, student_id, course, year, session_name, str(current_time),
                                    str(current_date), "absent"))
                                connection.commit()
                                print("Attendance recorded as absent for:", name)

                # Update the total_attendance and last_attendance columns in the student table
                for name in face_names:
                    # update_attendance(name)
                    update_last_attendance(name)

                # Display the results
                for faceLoc, name in zip(face_locations, face_names):
                    # Scale back up face locations since the frame we detected in was scaled to 1/4 size
                    # y1 top *= 4
                    # x2 right *= 4
                    # y2 bottom *= 4
                    # x1 left *= 4
                    y1, x2, y2, x1 = faceLoc
                    y1, x2, y2, x1 = y1 * 4, x2 * 4, y2 * 4, x1 * 4
                    bbox = 10 + x1, 10 + y1, x2 - x1, y2 - y1
                    img = cvzone.cornerRect(frame, bbox, rt=0)

                    # Draw a box around the face
                    # cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)

                    # Draw a label with a name below the face
                    # cv2.rectangle(frame, (x1, y2 - 35), (x2, y2), (42, 228, 57), cv2.BORDER_CONSTANT)
                    font = cv2.FONT_HERSHEY_DUPLEX
                    # cv2.putText(frame, str(name), (x1 + 20, y2 - 20), font, 1.0, (255, 255, 255), 1)
                    cv2.putText(frame, name, (x1 + 20,y2-6), font, 0.5, (255, 255, 255), 1)

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

# ... your existing Flask app setup and other routes ...

current_time = datetime.datetime.now().time()
current_date = datetime.date.today()

@app.route('/attendance_data')
def get_attendance_data():
    try:
        connection = mysql.connector.connect(
            host=mysql_host,
            user=mysql_user,
            password=mysql_password,
            database=mysql_database
        )
        cursor = connection.cursor()

        # Define the SQL query to select attendance data from the database
        select_query = "SELECT name, student_id, time, date, attendance FROM attendance WHERE time >= %s AND date = %s"

        cursor.execute(select_query, (current_time, current_date,))
        attendance_data = cursor.fetchall()

        # Close cursor and connection after fetching data
        cursor.close()
        connection.close()

        # Convert the attendance time (timedelta) to a string representation
        serialized_attendance_data = []
        for row in attendance_data:
            serialized_row = list(row)
            serialized_row[2] = str(row[2])  # Convert timedelta to string
            serialized_attendance_data.append(serialized_row)

        # Return the attendance data as JSON
        return {'attendance_data': serialized_attendance_data}

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return {'error': 'An error occurred while fetching attendance data.'}, 500
    
@app.route('/fr_page')
def fr_page():
    if 'user_id' in session:
        return render_template('fr_page.html')
    else:
        return redirect('/')

@app.route('/video_feed')
def video_feed():
    session_name = session.get('session_name', 'Unknown')
    return Response(gen_frames(session_name), mimetype='multipart/x-mixed-replace; boundary=frame')

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
            return redirect('/')

        except mysql.connector.Error as err:
            return f"Error: {err}"

    return render_template('signup.html')

@app.route('/signup-success')
def signup_success():
    return "Signup Successful! Thank you for registering."

@app.route('/', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        # User is already logged in, redirect to the home page
        return redirect('/dashboard')

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
                session['session_name'] = result[1]
                session['email'] = result[2]
                # Add more fields from the lecturer table as needed

                return redirect('/dashboard')  # Redirect to the home page after login

            else:
                # Login failed, show an error message
                return render_template('login.html', error_message="Invalid email or password")

        except mysql.connector.Error as err:
            return f"Error: {err}"

    return render_template('login.html')


@app.route('/logout', methods=['GET', 'POST'])
def logout():
    # Clear the user information from the session
    session.clear()
    # Redirect the user to the login page after logout
    return redirect('/')


@app.route('/dashboard')
def dashboard():
    # Check if the user is logged in by verifying the 'user_id' in the session
    if 'user_id' in session:
        try:
            # Connect to the MySQL database
            connection = mysql.connector.connect(
                host=mysql_host,
                user=mysql_user,
                password=mysql_password,
                database=mysql_database
            )
            cursor = connection.cursor()

            session_name = session.get('session_name', 'Unknown')

            # Fetch attendance data from the database
            select_query = "SELECT student.name, student.student_id, attendance.lecturer, attendance.time, attendance.date, attendance.attendance FROM attendance JOIN student ON attendance.student_id = student.student_id WHERE attendance.lecturer = %s"
            cursor.execute(select_query, (session_name,))
            attendance_data = cursor.fetchall()

            cursor.close()
            connection.close()

            return render_template('dashboard.html', attendance_data=attendance_data)

        except mysql.connector.Error as err:
            return f"Error: {err}"
    else:
        return redirect('/')

@app.route('/student_info/<string:student_name>', methods=['GET'])
def student_info(student_name):
    if 'user_id' in session:
        try:
            connection = mysql.connector.connect(
                host=mysql_host,
                user=mysql_user,
                password=mysql_password,
                database=mysql_database
            )
            cursor = connection.cursor()

            # Define the SQL query to retrieve student information by name
            select_query = "SELECT * FROM student WHERE name = %s"
            cursor.execute(select_query, (student_name,))
            student_data = cursor.fetchone()

            # Define the SQL query to retrieve the image_data for the student from the images table
            select_image_query = "SELECT image_data FROM images WHERE image_name = %s"
            cursor.execute(select_image_query, (student_name,))
            image_data = cursor.fetchone()

            cursor.close()
            connection.close()

            if student_data:
                # If the student data is found, pass it along with image_data to the template
                if image_data:
                    # The image data is stored in a tuple, so we need to extract it from the first element
                    image_data_blob = image_data[0]
                    # Convert the BLOB image_data back to JPEG format
                    image_data_base64 = base64.b64encode(image_data_blob).decode('utf-8')
                else:
                    image_data_base64 = None

                return render_template('student_info.html', student_data=student_data, image_data_base64=image_data_base64)
            else:
                # If student data is not found, display an error message or redirect to another page
                return "Student information not found."

        except mysql.connector.Error as err:
            return f"Error: {err}"

    else:
        redirect('/')

@app.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    if 'user_id' in session:
        try:
            # Connect to the MySQL database
            connection = mysql.connector.connect(
                host=mysql_host,
                user=mysql_user,
                password=mysql_password,
                database=mysql_database
            )
            cursor = connection.cursor()

            if request.method == 'POST':
                # Retrieve the user_id from the session
                user_id = session['user_id']

                # Get the form data submitted by the user
                name = request.form['name']
                email = request.form['email']
                course = request.form['course']
                password = request.form['password']

                update_query = "UPDATE lecturer SET name = %s, email = %s, course = %s, password = %s WHERE id = %s"
                cursor.execute(update_query, (name, email, course, password, user_id))

                # Include the password field in the update query only if it's not empty
                if password:
                    update_query += ", password = %s"
                    cursor.execute(update_query, (name, email, course, password, user_id))
                else:
                    cursor.execute(update_query, (name, email, course, user_id))

                # Update the session data with the new name and email (if changed)
                session['session_name'] = name
                session['email'] = email

                print("Received Form Data:", request.form)
                # Commit the changes to the database
                connection.commit()

                flash('Profile updated successfully', 'success')
                return redirect('/dashboard')  # Redirect to the same edit_profile page after saving changes

            else:
                # If the request is a GET request, fetch the current user's data
                user_id = session['user_id']
                select_query = "SELECT name, email, course FROM lecturer WHERE id = %s"
                cursor.execute(select_query, (user_id,))
                user_data = cursor.fetchone()

                # Convert the user_data tuple to a dictionary for easier access in the template
                user_data_dict = {
                    'name': user_data[0],
                    'email': user_data[1],
                    'course': user_data[2],
                }
                # Add other fields as needed

                return render_template('edit_profile.html', user_data=user_data_dict)

        except mysql.connector.Error as err:
            flash('An error occurred while updating the profile', 'error')
            return redirect('/dashboard')  # Redirect to the dashboard or another page on error

        finally:
            # Close cursor and connection after the operation
            cursor.close()
            connection.close()
    else:
        return redirect('/')

if __name__ == "__main__":
    
    
    app.run()
