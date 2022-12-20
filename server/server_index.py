import time

import firebase_admin
from firebase_admin import credentials
from firebase_admin import db

boothName = ['동아리', '동아리1', '동아리11']
memberNumber = {} #동아리 방문한 회원 수(중복 제외)
reMemberNumber = {} #재방문한 사람 수
totalMemberNumber = {} #전체 동아리 방문 수(중복 포함)

def initFirebase():
    #Firebase database 인증 및 앱 초기화
    cred = credentials.Certificate('server\\ticket-4321c-firebase-adminsdk-f5swo-372240e407.json')
    firebase_admin.initialize_app(cred,{
        'databaseURL' : 'https://ticket-4321c-default-rtdb.firebaseio.com'
    })

def readFirebase(path):
    ref = db.reference(path)
    row = ref.get()
    return row

def updateDataToDatabase(url, key, value):
    dir = db.reference(url)
    dir.update({key : value})

def main():
    while True:
        memberNumber = {} #동아리 방문한 회원 수(중복 제외)
        reMemberNumber = {} #재방문한 사람 수
        totalMemberNumber = {} #전체 동아리 방문 수(중복 포함)
        recentMemberNumber = {} #최근 동아리 방문 수
        usePoint = {} #지출한 포인트(방문자 기준)
        getPoint = {} #적립한 포인트(방문자 기준)

        for i in boothName:
            memberNumber[i] = 0 #동아리 방문한 회원 수(중복 제외)
            reMemberNumber[i] = 0 #재방문한 사람 수
            totalMemberNumber[i] = 0 #전체 동아리 방문 수(중복 포함)
            recentMemberNumber[i] = 0 #전체 동아리 방문 수(중복 포함)
            usePoint[i] = 0 #지출한 포인트(방문자 기준)
            getPoint[i] = 0 #적립한 포인트(방문자 기준)

        readFirebaseJson = readFirebase("user/")
        print(readFirebaseJson)
        if readFirebaseJson != None:
            for i in readFirebaseJson:
                for j in range(len(boothName)):
                    try:
                        visitsNumber = int(readFirebaseJson[i]["방문한부스"][boothName[j]]['방문수'])
                        memberNumber[boothName[j]]+=1
                        totalMemberNumber[boothName[j]] += visitsNumber
                        if visitsNumber > 1:
                            reMemberNumber[boothName[j]]+=1
                        if time.time() - readFirebaseJson[i]["방문한부스"][boothName[j]]['방문시간'] < 60*5:
                            recentMemberNumber[boothName[j]]+=1
                    except:
                        pass
                    try:
                        usePoint[boothName[j]] += int(readFirebaseJson[i]["방문한부스"][boothName[j]]['사용한 포인트'])
                    except:
                        pass
                    try:
                        getPoint[boothName[j]] += int(readFirebaseJson[i]["방문한부스"][boothName[j]]['적립한 포인트'])
                    except:
                        pass
        
        #memberNumber=sorted(memberNumber.items(),key=lambda x:x[1],reverse=True)
        #reMemberNumber=sorted(reMemberNumber.items(),key=lambda x:x[1],reverse=True)
        #totalMemberNumber=sorted(totalMemberNumber.items(),key=lambda x:x[1],reverse=True)
        
        updateDataToDatabase("data/", "방문 회원 수", memberNumber)
        updateDataToDatabase("data/", "재방문 회원 수", reMemberNumber)
        updateDataToDatabase("data/", "총 방문 회원 수", totalMemberNumber)
        updateDataToDatabase("data/", "최근 방문 회원 수", recentMemberNumber)
        updateDataToDatabase("data/", "사용한 포인트", usePoint)
        updateDataToDatabase("data/", "적립한 포인트", getPoint)
        time.sleep(60)
if __name__ == '__main__':
    initFirebase()
    main()