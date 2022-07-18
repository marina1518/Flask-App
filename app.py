import cv2
import face_recognition
import numpy as np
from io import BytesIO
import base64
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from flask import Flask, request
from flask_cors import CORS
import json


def ConvertFromBase64ToNumpy(data_uri):
    dimensions = (100, 100)
    image_b64 = data_uri.split(",")[1]
    binary = base64.b64decode(image_b64)
    image = np.asarray(bytearray(binary), dtype="uint8")
    image = cv2.imdecode(image, cv2.IMREAD_COLOR)
    image = cv2.resize(image, (100, 100))
    return image


# Use a service account
cred = credentials.Certificate(
    'react-image-storage-97f83-firebase-adminsdk-fja8d-f0c120cd9a.json')
firebase_admin.initialize_app(cred)
db = firestore.client()


def ReadDataFromFireBase(mails):
    images = []
    usersData = {}
    # mails = ["fady@gmail.com", "magy@gmail.com"]
    for mail in mails:
        # mail = "fady@gmail.com"
        users_images_ref = db.collection(u'{}'.format(mail))
        #! get docs of "fady@gmail.com"
        docs = users_images_ref.stream()
        for doc in docs:
            images.append(doc.to_dict()['base64'])
            # print("img ",doc.to_dict()['base64'])
            # print(f'{doc.id} => {doc.to_dict()}')
        #! Store this user info before going through the next user data
        usersData[mail] = images
        #! reset the images list again to hold the new user images only
        images = []
    return usersData


def GetUsersImagesInNUmpyFormat(usersData):
    """ Convert the 50 images of each user into numpy array to be ready to verification in one shot """
    usersData_NumpyFormat = {}
    for user in usersData:
        usersData_NumpyFormat[user] = []
    for user in usersData:
        # user is "gamilfady605@gmail.com"
        for img in usersData[f'{user}']:
            numpyImage = ConvertFromBase64ToNumpy(img)
            usersData_NumpyFormat[user].append(numpyImage)
    return usersData_NumpyFormat


def CompareSimilarity(img1_encoding, img2_encoding):
    result = face_recognition.compare_faces([img1_encoding], img2_encoding)
    return result


# usersData = ReadDataFromFireBase(["fadygamil@gmail.com", "magymagdy@gmail.com", "tota@gmail.com"])
# print("magy has {} images ".format(len(usersData['magymagdy@gmail.com'])))
# print("fady has {} images ".format(len(usersData['fadygamil@gmail.com'])))

# usersData_NumpyFormat = GetUsersImagesInNUmpyFormat(usersData)
# print(len(usersData_NumpyFormat['fadygamil@gmail.com']))
# print(len(usersData_NumpyFormat['magymagdy@gmail.com']))

# for user in usersData_NumpyFormat:
#    print(user)

#! Flask App
app = Flask(__name__)
CORS(app, support_credentials=True)


@app.route('/face_id', methods=['GET', 'POST'])
def welcome():
    res = json.loads(request.data)
    # mail string constant keda byd5loha fel frontend lel backend we el backend byb3thaly

    registeredUsersMails = res['mails']
    usersData = ReadDataFromFireBase(registeredUsersMails)
    usersData_NumpyFormat = GetUsersImagesInNUmpyFormat(usersData)

    CurrentUserMail = res['CurrUser']
    CurrentUserData = ReadDataFromFireBase(CurrentUserMail)
    CurrentUserData_NumpyFormat = GetUsersImagesInNUmpyFormat(CurrentUserData)
    LoggingUserImage = CurrentUserData_NumpyFormat[CurrentUserMail[0]][0]
    LoggingUserImageEncoding = face_recognition.face_encodings(LoggingUserImage)[
        0]

    ValidUser = False
    for user in usersData_NumpyFormat:
        validationImage = usersData_NumpyFormat[user][0]
        validationImageEncoding = face_recognition.face_encodings(validationImage)[
            0]
        if CompareSimilarity(LoggingUserImageEncoding, validationImageEncoding)[0] == True:
            return {"result": user}
    if ValidUser == False:
        return {"result": "Not Valid"}


if __name__ == '__main__':
    #app.run(host='0.0.0.0', port=5000)
    app.run(debug=True)


# #! for the first image
# # Read the image
# img1 = usersData_NumpyFormat['fadygamil@gmail.com'][0]
# # get the image encoding
# img1_encoding = face_recognition.face_encodings(img1)[0]

# #! for the first image
# # Read the image
# img2 = usersData_NumpyFormat['fadygamil@gmail.com'][1]
# # get the image encoding
# img2_encoding = face_recognition.face_encodings(img2)[0]

# result = CompareSimilarity(img1_encoding, img2_encoding)
# print(result)


# print(type(result))
