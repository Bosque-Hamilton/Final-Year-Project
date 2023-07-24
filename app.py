
from flask import Flask, render_template, Response, request, flash, redirect
import cv2
import face_recognition
import numpy as np
import os
import pickle
import cvzone
import mysql.connector



app=Flask(__name__, static_url_path='/static')
app.secret_key = 'myverysecretandlongrandomstring12345'

# Replace with the actual file path
file_path = 'EncodeFile.p'  

# Check if the file exists
if os.path.exists(file_path):
    # Open the file
    with open(file_path, 'rb') as file:
        encodeListKnownWithIds = pickle.load(file)
    # Split file into two: encodings and names file
    encodeListKnown, studentIds = encodeListKnownWithIds
    print("Encoded file loaded")
else:
    print(f"Error: File '{file_path}' does not exist.")



 
 
 
 
 
 #DATABASE CREATION
    
conn = mysql.connector.connect(
    host='127.0.0.1',
    user='root',
    password='BossBoss12',
    database='project'
)
c = conn.cursor()
    
    
def gen_frames():  
    camera = cv2.VideoCapture(0)

    import time
    table_name = f"attendance_{int(time.time())}"

     # Create a new table for this session
    try:
        create_table_query = f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            id INT AUTO_INCREMENT PRIMARY KEY,
            student_name VARCHAR(255),
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        c.execute(create_table_query)
        conn.commit()
    except mysql.connector.Error as e:
        print(f"Error while creating the table: {e}")

    
    known_faces = set()
    while True:
        # read the camera frame
        success, frame = camera.read()  
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
            student_name = []

            
            for face_encoding in face_encodings:
                # See if the face is a match for the known face(s)
                matches = face_recognition.compare_faces(encodeListKnown, face_encoding)
               
                name = "Unknown"


                # Or instead, use the known face with the smallest distance to the new face
                face_distances = face_recognition.face_distance(encodeListKnown, face_encoding)
                best_match_index = np.argmin(face_distances)
                if matches[best_match_index]:
                    name = studentIds[best_match_index]

                student_name.append(name)

            new_faces = [name for name in student_name if name not in known_faces]
            if new_faces:
                try:
                    # Construct the INSERT query
                    values_to_insert = ", ".join([f'("{name}")' for name in new_faces])
                    query = f"INSERT INTO {table_name} (student_name) VALUES {values_to_insert}"

                    # Execute the query
                    c.execute(query)

                    # Commit the changes to the database
                    conn.commit()
                    known_faces.update(new_faces)
                except mysql.connector.Error as e:
                    print(f"Error while inserting data into the table: {e}")

             

                       

            # Display the results
            for faceLoc, name in zip(face_locations, student_name):
                y1, x2, y2, x1 = faceLoc
                y1, x2, y2, x1 = y1 * 4, x2 * 4, y2 * 4, x1 * 4
                bbox = 10 + x1, 10 + y1, x2 - x1, y2 - y1
                img = cvzone.cornerRect(frame, bbox, rt=0)

                # Draw a box around the face
                # Draw a label with a name below the face
                cv2.rectangle(frame, (x1, y2 - 35), (x2, y2), (42, 228, 57), cv2.BORDER_CONSTANT)
                font = cv2.FONT_HERSHEY_DUPLEX
                cv2.putText(frame, str(name), (x1 + 20, y2 - 20), font, 1.0, (255, 255, 255), 1)

            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/')
def index():
    return render_template('Login/login.html')
@app.route('/login', methods=['POST'])
def login():
    # Get the submitted username and password from the form
    username = request.form['username']
    password = request.form['password']

    # Replace these hardcoded credentials with your actual authentication logic
    if username == 'charles' and password == 'charles':
        # Authentication successful, redirect to the main page
        return render_template('index.html')
    else:
        # Authentication failed, show an error message or redirect to the login page
       flash('Incorrect email or password.', 'error')
    return redirect('/')





# def index():
#     return render_template('index.html')
@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')
@app.route('/attendance')
def show_attendance():
    
    # Retrieve the attendance data from the database
    c.execute("SELECT * FROM attendance")
    attendance_data = c.fetchall()

    # Close the database connection
    conn.close()

    # Render the attendance template and pass the attendance data
    return render_template('attendance.html', attendance_data=attendance_data)

if __name__=='__main__':
   

    app.run(debug=True)