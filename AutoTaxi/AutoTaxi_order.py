# order模式: 用戶下訂單後 出發去找他 然後停在他旁邊並通知上車
import requests
try:
    import xml.etree.cElementTree as ET 
except ImportError:
    import xml.etree.ElementTree as ET

from flask import Flask
app = Flask(__name__)

from flask import Flask, request, abort
from linebot import  LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage,TextSendMessage, ImageSendMessage, StickerSendMessage, LocationSendMessage, QuickReply, QuickReplyButton, MessageAction, ImageMessage
import boto3
import os
import json
import botocore
import json
import time
import numpy as np
import cv2
from skimage.transform import resize
from scipy.spatial import distance
from tensorflow.keras.models import load_model
from sklearn.metrics.pairwise import cosine_similarity

# 車牌模擬
license_plate_number = "ADC-8767"

# 圖片根目錄
root_folder = "/home/pi/Desktop/AutoTaxi/"

# Line Bot API設定
line_bot_api = LineBotApi('') # 個人資訊恕不提供
handler = WebhookHandler('') # 個人資訊恕不提供

# AWS 登入設定
ACCESS_KEY_ID = '' # 個人資訊恕不提供
ACCESS_SECRET_KEY = '' # 個人資訊恕不提供

# S3 設定
s3 = boto3.resource(
    's3',
    aws_access_key_id=ACCESS_KEY_ID,
    aws_secret_access_key=ACCESS_SECRET_KEY,
)
my_bucket = s3.Bucket('peopleimage')

# 比對人臉 對了回傳True 錯了回傳False
def compare_faces(user_id):
    
    # 優先嘗試使用AWS Rekognition進行人臉比對，如果發生錯誤，馬上轉本地端的人臉比對
    try:
        client=boto3.client('rekognition',aws_access_key_id=ACCESS_KEY_ID,
        aws_secret_access_key=ACCESS_SECRET_KEY,region_name = 'ap-northeast-1')

        imageSource=open(root_folder+user_id+'.jpg','rb') # 下載下來的用戶自拍照
        imageTarget=open(root_folder+'target.jpg','rb') # 拍攝到的人的照片

        # 接收AWS Rekognition回傳的人臉比對json檔
        response=client.compare_faces(SimilarityThreshold=70,
                                    SourceImage={'Bytes': imageSource.read()},
                                    TargetImage={'Bytes': imageTarget.read()})
        
        imageSource.close()
        imageTarget.close()
        
        # 比對分析
        if len(response['FaceMatches']) == 0:
            return False
        
        else:
            print(response['FaceMatches'][0]['Similarity'])
            return True
    
    # 發生錯誤：本地端人臉比對
    except botocore.exceptions.ClientError as error:
        print(error)
        #驗證compares列表中相片的人與valid相片中的人
        valid = root_folder+user_id+'.jpg'
        compares = root_folder+'target.jpg'

        #用OpenCV的Cascade classifier來偵測臉部，不一定跟Facenet一樣要用MTCNN。
        cascade_path = 'haarcascade_frontalface_default.xml'

        #Facenet model尺寸為160×160
        image_size = 160

        # 讀取模型
        model_path = 'facenet_keras.h5'
        model = load_model(model_path)

        #whitening對過曝或低曝圖片進行處理
        def prewhiten(x):
            if x.ndim == 4:
                axis = (1, 2, 3)
                size = x[0].size
            else:
                axis = (0, 1, 2)
                size = x.size
            mean = np.mean(x, axis=axis, keepdims=True)
            std = np.std(x, axis=axis, keepdims=True)
            std_adj = np.maximum(std, 1.0/np.sqrt(size))
            y = (x-mean)/std_adj
            return y

        #L2標準化圖像，可強化其特徵。
        def l2_normalize(x, axis=-1, epsilon=1e-10):
            output = x / np.sqrt(np.maximum(np.sum(np.square(x), axis=axis, keepdims=True), epsilon))
            return output

        #偵測臉孔範圍
        def findface(img, margin):
            cascade = cv2.CascadeClassifier(cascade_path)
            faces = cascade.detectMultiScale(img, scaleFactor=1.1, minNeighbors=3)
            if(len(faces)>0):
                (x, y, w, h) = faces[0]
                face = img[y:y+h, x:x+w]
                faceMargin = np.zeros((h+margin*2, w+margin*2, 3), dtype = 'uint8')
                faceMargin[margin:margin+h, margin:margin+w] = face
                face_area = resize(faceMargin, (image_size, image_size), mode='reflect')
                return face_area
            else:
                return None

        def preProcess(img):
            whitenImg = prewhiten(img)
            whitenImg = whitenImg[np.newaxis, :]
            return whitenImg
        
        # 擷取特徵
        imgValid = valid
        face_area = findface(cv2.imread(imgValid), 6)
        faceImg = preProcess(face_area)
        embs_valid = l2_normalize(np.concatenate(model.predict(faceImg)))

        img_file = compares
        face_area = findface(cv2.imread(img_file), 6)
        faceImg = preProcess(face_area)
        embs = l2_normalize(np.concatenate(model.predict(faceImg)))

        # 計算特徵之間的相似度
        similarity = cosine_similarity([embs_valid], [embs])
        print(valid + '\'s diff with {} is {}'.format(compares, similarity[0][0]))
        
        if similarity[0][0] > 0.7:
            return True
        else:
            return False

# 去S3裡面搜尋有沒有user_id.jpg 有的話回傳true 沒有的話回傳false
def check_database(user_id):
    print("搜尋資料庫中...")
    flag = False
    for obj in my_bucket.objects.all():
        if obj.key == user_id+".jpg":
            flag = True
            break
    print("搜尋結束")
    return flag

# 從S3下載user的自拍照到root_folder/user_id.jpg
def download_selfie(user_id):

    img_dir = root_folder+user_id+".jpg"
    open(img_dir, 'w').close()
    my_bucket.download_file(user_id+".jpg", img_dir)

# 回傳這張照片是否是人臉
def check_face(img_dir):

    client=boto3.client('rekognition',aws_access_key_id=ACCESS_KEY_ID,
    aws_secret_access_key=ACCESS_SECRET_KEY,region_name = 'ap-northeast-1')

    imageSource=open(img_dir,'rb')

    # 接收AWS Rekognition檢查這張圖片的臉部資訊的json檔
    response = client.detect_faces(Image={'Bytes': imageSource.read()},Attributes=['ALL'])
    
    if len(response['FaceDetails']) == 0:
        return False
    else:
        True

@app.route("/callback", methods=['POST'])

def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message= (TextMessage,ImageMessage))

def handle_message(event):

    if event.message.type == "text":

        mtext = event.message.text
        user_id = event.source.user_id

        if mtext == "@order":

            print("接收到訂單")
            print("檢查使用者是否有上傳過自拍照")
            # 檢查S3裡面有沒有這個user的照片
            flag = check_database(user_id)
            
            # 沒有的話請他上傳
            if flag == False:
                print("使用者沒有上傳過自拍照")
                line_bot_api.push_message(user_id,TextSendMessage(text="資料庫裡沒有您的照片，請自拍一張後傳給我，謝謝。"))
            
            #有的話發動車子
            else:
                print("使用者上傳過自拍照")
                line_bot_api.push_message(user_id,TextSendMessage(text="車子已經出動，車牌號碼是"+license_plate_number+"，看到車子的話可以舉手示意，謝謝。"))

                # 出發前，先將使用者的自拍照下載下來
                print("把使用者的自拍照下載下來")
                download_selfie(user_id)
                
                # 執行往前走尋找人 如果是人 就拍照 然後將圖片下載到AutoTaxi目錄下
                os.chdir('/home/pi/tensorflow1/models/research/object_detection')
                os.system('python go_straight_person_stop.py')
                os.chdir('/home/pi/Desktop/AutoTaxi')
                print("car find a person. check if he is the right one.")

                while True:

                    # 比對是否就是下訂單的人 是的話就跳出迴圈
                    if compare_faces(user_id) == True:
                        print("he is the right one")
                        break
                    # 不是下訂單的人
                    else:
                        print("he is not the right one")
                        # 執行略過這個人的程式
                        print("skip the person")
                        os.chdir('/home/pi/tensorflow1/models/research/object_detection')
                        os.system('python skip_person.py')
                        # 繼續往前走尋找人
                        os.system('python go_straight_person_stop.py')
                        os.chdir('/home/pi/Desktop/AutoTaxi')

                # 傳訊息給下訂單的人
                print("found the person, send message.")
                line_bot_api.push_message(user_id,TextSendMessage(text="找到你了 請上車"))
        
        # 其他文字輸入處理
        else:
            line_bot_api.push_message(user_id,TextSendMessage(text="要訂車的話請按下方圖文按鈕，謝謝。"))

    else:
        print("接收到圖片")
        message_content = line_bot_api.get_message_content(event.message.id)
        user_id = event.source.user_id

        # 下載使用者上傳的圖片到user_id.jpg
        img_dir = root_folder+user_id+".jpg"
        open(img_dir, 'w').close()
        with open(img_dir,'wb') as fd:
            for i in message_content.iter_content():
                fd.write(i)
        print("下載使用者上傳的圖片")

        # 先檢查這張圖片是不是臉
        if check_face(img_dir) == False:
            print("使用者上傳的不是臉")
            line_bot_api.push_message(user_id,TextSendMessage(text="這張照片好像不是臉喔，請重新上傳。"))

        # 確定是臉之後 上傳到S3
        else:
            print("使用者上傳的確實是臉")
            print("檢查使用者是不是已經上傳過照片")
            # 查看S3裡面有沒有該名使用者的自拍照
            flag = check_database(user_id)
            # 有的話就複寫
            if flag == True:
                print("使用者上傳過照片，準備複寫")
                line_bot_api.push_message(user_id,TextSendMessage(text="即將更新您的自拍照，請稍等..."))

            # 沒有的話就上傳
            else:
                print("使用者沒有上傳過照片，準備上傳")
                line_bot_api.push_message(user_id,TextSendMessage(text="即將上傳您的自拍照至資料庫，請稍等..."))

            # 上傳到S3
            img = open(img_dir,'rb')
            my_bucket.put_object(Key= user_id+".jpg", Body=img)

            # 回復成功訊息
            print("上傳使用者照片成功!")
            line_bot_api.push_message(user_id,TextSendMessage(text="成功將您的照片上傳至資料庫"))

if __name__ == '__main__':
    app.run()