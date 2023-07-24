import cv2
import face_recognition
import pickle
import os
import psycopg2


# import student imgaes
folderPath = 'images'
pathList = os.listdir(folderPath)
print(pathList)
imgList = []
studentIds = []
for path in pathList:
    imgList.append(cv2.imread(os.path.join(folderPath, path)))
    studentIds.append(os.path.splitext(path)[0])



for img, student_id in zip(imgList, studentIds):
    # Convert the image to binary data
    results, img_bytes = cv2.imencode('.png', img)
    img_bytes = img_bytes.tobytes()

  


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
