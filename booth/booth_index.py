import cv2
from pyzbar import pyzbar

import firebase_admin
from firebase_admin import credentials
from firebase_admin import db

import time
import json

boothName = ''

userName = []
userTime = []

Mode = ''

def initFirebase():
    #Firebase database 인증 및 앱 초기화
    #TODO cred = credentials.Certificate('./ticket-4321c-firebase-adminsdk-f5swo-372240e407.json')
    cred = credentials.Certificate('booth/ticket-4321c-firebase-adminsdk-f5swo-372240e407.json')
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
    #TODO file_path = ".\\booth.json"
    file_path = "booth/booth.json"

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
            #TODO 방문 존건 달성 시 포인트 지급
            updateDataToDatabase("user/" + barcode_info, "쿠폰", int(nowCoupon) + 100)
            if alreadyBooth == None:
                alreadyBooth = []
            for j in data["쿠폰조건"][i]:
                alreadyBooth.append(data["쿠폰조건"][i][j])
            print(alreadyBooth)
            updateDataToDatabase("user/" + barcode_info, "이미방문한부스", alreadyBooth)

def pointUse(barcode_info, money):
    """
    포인트 사용을 기록하는 함수
    """
    nowCoupon = db.reference("user/" + barcode_info  + "/방문한부스/" + boothName + "/사용한포인트").get()
    if nowCoupon==None:
        updateDataToDatabase("user/" + barcode_info  + "/방문한부스/" + boothName, "사용한포인트", money)
    else:
        updateDataToDatabase("user/" + barcode_info  + "/방문한부스/" + boothName, "사용한포인트", nowCoupon + money)
def pointSave(barcode_info, money):
    """
    포인트 적립을 기록하는 함수
    """
    nowCoupon = db.reference("user/" + barcode_info  + "/방문한부스/" + boothName + "/적립한포인트").get()
    if nowCoupon==None:
        updateDataToDatabase("user/" + barcode_info  + "/방문한부스/" + boothName, "적립한포인트", money)
    else:
        updateDataToDatabase("user/" + barcode_info  + "/방문한부스/" + boothName, "적립한포인트", nowCoupon + money)


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
        print("(1):포인트 사용, (2)포인트 적립, (3)취소")
        Mode = int(input("사용할 기능을 적어주세요. : "))
        if Mode == 1:
            money = int(input("사용할 금액을 적어주세요. (1000원 단위) : "))
            nowCoupon = db.reference("user/" + barcode_info + "/쿠폰").get()
            if money * 1000 > nowCoupon or money < 0:
                print("사용할 포인트가 보유한 포인트보다 적어야 해요")
                break
            updateDataToDatabase("user/" + barcode_info, "쿠폰", int(nowCoupon) - (money * 1000))
            pointUse(barcode_info, (money * 1000))
            print(str(money*1000) + "원 사용하였습니다.")
        elif Mode == 2:
            if barcode_info not in userName:
                nowCoupon = db.reference("user/" + barcode_info + "/쿠폰").get()
                updateDataToDatabase("user/" + barcode_info, "쿠폰", int(nowCoupon) + 400)
                pointSave(barcode_info, 400)
                print("400원 포인트 적립하였습니다.")
            elif time.time() - userTime[userName.index(barcode_info)] > 60:
                nowCoupon = db.reference("user/" + barcode_info + "/쿠폰").get()
                updateDataToDatabase("user/" + barcode_info, "쿠폰", int(nowCoupon) + 400)
                pointSave(barcode_info, 400)
                print("400원 포인트 적립하였습니다.")
            elif time.time() - userTime[userName.index(barcode_info)] <= 60:
                print("잠시 뒤에 시도해주세요")
        elif Mode == 3:
            break

        if barcode_info not in userName:
            #바코드가 처음 인식 되었을 때
            userName.append(barcode_info)
            userTime.append(time.time())
            updateDataToDatabase("user/" + barcode_info + "/방문한부스/" + boothName + "/", "방문수", 1)

        elif time.time() - userTime[userName.index(barcode_info)] > 60:
            #바코드가 인식되었을 때
            userTime[userName.index(barcode_info)] = time.time()
            addOneToDatabase("user/" + barcode_info + "/방문한부스/" + boothName, "방문수")
        updateDataToDatabase("user/" + barcode_info + "/방문한부스/" + boothName + "/", "방문시간", time.time())
    # return the bounding box of the barcode
    return frame

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
            if keyboard.is_pressed(' '):
                fontpath = "fonts/gulim.ttc"
                font = ImageFont.truetype(fontpath, 40)
                img_pil = Image.fromarray(frame)
                draw = ImageDraw.Draw(img_pil)
                if barcode_info not in userName:
                    draw.text((20, 20),  "포인트가 지급되었어요", font=font, fill=(255, 0, 255))
                    frame = np.array(img_pil)

                    userName.append(barcode_info)
                    userTime.append(time.time())
                    #TODO 조건 완료시 포인트 지급
                    nowCoupon = db.reference("user/" + barcode_info + "/쿠폰").get()
                    updateDataToDatabase("user/" + barcode_info, "쿠폰", int(nowCoupon) + 100)
                    print(userName)

                elif time.time() - userTime[userName.index(barcode_info)] > 60:
                    draw.text((20, 20),  "포인트가 지급되었어요", font=font, fill=(255, 0, 255))
                    frame = np.array(img_pil)

                    userTime[userName.index(barcode_info)] = time.time()
                    #TODO 조건 완료시 포인트 지급
                    nowCoupon = db.reference("user/" + barcode_info + "/쿠폰").get()
                    updateDataToDatabase("user/" + barcode_info, "쿠폰", int(nowCoupon) + 100)
                    print(userName)
            else:   
                fontpath = "fonts/gulim.ttc"
                font = ImageFont.truetype(fontpath, 40)
                img_pil = Image.fromarray(frame)
                draw = ImageDraw.Draw(img_pil)
                draw.text((20, 20),  "인식되었어요", font=font, fill=(255, 0, 0))
                frame = np.array(img_pil)

                if barcode_info not in userName:
                    #바코드가 처음 인식 되었을 때
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
                """
    

def main():
    camera = cv2.VideoCapture(0)
    #cv2.namedWindow('QR코드 스캔 해주세요.', cv2.WND_PROP_FULLSCREEN)
    #cv2.setWindowProperty('QR코드 스캔 해주세요.', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
    ret, frame = camera.read()
    while ret:
        ret, frame = camera.read()
        frame = read_barcodes(frame)
        frame = cv2.resize(frame, (768 ,576))
        cv2.imshow('QR코드 스캔 해주세요.', frame)
        if cv2.waitKey(1) & 0xFF == 27:
            break

    camera.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    while True:
        a=str(input("부스 이름을 입력하세요. : "))
        if a == "1-1" or a == "1-2" or a == "1-3" or a == "2-1" or a == "2-2" or a == "2-3" or a == "3-1" or a == "3-2" or a == "3-3" or a == "물리" or a == "화학" or a == "생물" or a == "수학" or a == "지구과학" or a == "정보":
            boothName = a
            break
        else:
            pass
    initFirebase()
    main()