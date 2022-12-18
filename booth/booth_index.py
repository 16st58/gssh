import cv2
from pyzbar import pyzbar

import firebase_admin
from firebase_admin import credentials
from firebase_admin import db

import time
import json

boothName = '동아리'

boothList = ['동아리', '동아리1', '동아리2', '동아리3', '동아리4']
userName = []
userTime = []

def initFirebase():
    #Firebase database 인증 및 앱 초기화
    cred = credentials.Certificate('booth\\ticket-4321c-firebase-adminsdk-f5swo-372240e407.json')
    firebase_admin.initialize_app(cred,{
        'databaseURL' : 'https://ticket-4321c-default-rtdb.firebaseio.com'
    })

def updateDataToDatabase(url, key, value):
    """
    데이터를 업데이트 하는 함수
    @param url : DB주소
    @param key : 데이터 키
    @param value : 데이터 값
    """
    dir = db.reference(url)
    dir.update({key : value})

def addOneToDatabase(url, key):
    """
    데이터를 1만큼 증가시켜주는 함수
    @param url : DB주소
    @param key : 데이터 키
    """
    dir = db.reference(url)
    row = dir.get()
    i = row[key]
    i = i + 1
    dir.update({key : i})

def getPointCheck(barcode_info):
    """
    부스json파일을 읽고 쿠폰을 받을 수 있는 조건인지 검사, 이후 쿠폰 발행
    @param barcode_info : 바코드 번호(개인 번호)
    """
    file_path = "booth\\booth.json"

    with open(file_path, 'r', encoding='UTF8') as file:
        data = json.load(file)
    for i in data["쿠폰조건"]:
        clear = True
        for j in data["쿠폰조건"][i]:
            alreadyBooth =  db.reference("user/" + barcode_info + "/이미방문한부스").get()
            if alreadyBooth != None and data["쿠폰조건"][i][j] in alreadyBooth:
                clear = False
                break
            if data["쿠폰조건"][i][j] not in db.reference("user/" + barcode_info + "/방문한부스/").get():
                clear = False
                break
        if clear == True:
            nowCoupon = db.reference("user/" + barcode_info + "/쿠폰").get()
            updateDataToDatabase("user/" + barcode_info, "쿠폰", int(nowCoupon) + 100)
            if alreadyBooth == None:
                alreadyBooth = []
            for j in data["쿠폰조건"][i]:
                alreadyBooth.append(data["쿠폰조건"][i][j])
            print(alreadyBooth)
            updateDataToDatabase("user/" + barcode_info, "이미방문한부스", alreadyBooth)


def read_barcodes(frame):
    """
    바코드 읽는 함수
    """
    barcodes = pyzbar.decode(frame)
    for barcode in barcodes:
        x, y, w, h = barcode.rect
        # 1
        barcode_info = barcode.data.decode('utf-8')
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

        # 2
        font = cv2.FONT_HERSHEY_DUPLEX
        cv2.putText(frame, barcode_info, (x + 6, y - 6), font, 2.0, (255, 255, 255), 1)
        #barcode_info가 바코드 정보

        # 3
        if(barcode_info.isdigit()):
            with open("barcode_result.txt", mode='w') as file:
                file.write("Recognized Barcode:" + barcode_info)

                if barcode_info not in userName:
                    """
                    바코드가 처음 인식 되었을 때
                    """
                    userName.append(barcode_info)
                    userTime.append(time.time())
                    updateDataToDatabase("user/" + barcode_info + "/방문한부스/" + boothName + "/", "방문수", 1)
                    getPointCheck(barcode_info)


                elif time.time() - userTime[userName.index(barcode_info)] > 60:
                    #바코드가 인식되었을 때
                    userTime[userName.index(barcode_info)] = time.time()
                    addOneToDatabase("user/" + barcode_info + "/" + boothName + "/방문한부스/", "방문수")
                    getPointCheck(barcode_info)
                updateDataToDatabase("user/" + barcode_info + "/방문한부스/" + boothName + "/", "방문시간", time.time())
    # return the bounding box of the barcode
    return frame

def main():
    camera = cv2.VideoCapture(0)
    ret, frame = camera.read()
    while ret:
        ret, frame = camera.read()
        frame = read_barcodes(frame)
        cv2.imshow('Real Time Barcode Scanner', frame)
        if cv2.waitKey(1) & 0xFF == 27:
            break

    camera.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    initFirebase()
    main()