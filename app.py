
from flask import Flask, render_template, Response
import cv2
import face_recognition
import numpy as np
import os
import pickle
import cvzone



app=Flask(__name__)




file_path = 'EncodeFile.p'  # Replace with the actual file path

# Check if the file exists
if os.path.exists(file_path):
    # Open the file
    with open(file_path, 'rb') as file:
        encodeListKnownWithIds = pickle.load(file)
    # Rest of your code...
    encodeListKnown, studentIds = encodeListKnownWithIds
    print("Encoded file loaded")
else:
    print(f"Error: File '{file_path}' does not exist.")








# # Load a sample picture and learn how to recognize it.
# krish_image = face_recognition.load_image_file("Krish/krish.jpg")
# krish_face_encoding = face_recognition.face_encodings(krish_image)[0]

# # Load a second sample picture and learn how to recognize it.
# bradley_image = face_recognition.load_image_file("Bradley/bradley.jpg")
# bradley_face_encoding = face_recognition.face_encodings(bradley_image)[0]

# # Create arrays of known face encodings and their names
# known_face_encodings = [
#     krish_face_encoding,
#     bradley_face_encoding
# ]
# known_face_names = [
#     "Krish",
#     "Bradly"
# ]
# # Initialize some variables

# face_encodings = []
# face_names = []


# process_this_frame = True










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
                # See if the face is a match for the known face(s)
                matches = face_recognition.compare_faces(encodeListKnown, face_encoding)
               
                name = "Unknown"


                # Or instead, use the known face with the smallest distance to the new face
                face_distances = face_recognition.face_distance(encodeListKnown, face_encoding)
                best_match_index = np.argmin(face_distances)
                if matches[best_match_index]:
                    name = studentIds[best_match_index]

                face_names.append(name)
            # print (face_names)

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
                cv2.rectangle(frame, (x1, y2 - 35), (x2, y2), (42, 228, 57), cv2.BORDER_CONSTANT)
                font = cv2.FONT_HERSHEY_DUPLEX
                cv2.putText(frame, str(name), (x1 + 20, y2 - 20), font, 1.0, (255, 255, 255), 1)

            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/')
def index():
    return render_template('index.html')
@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')
if __name__=='__main__':
    app.run(debug=True)