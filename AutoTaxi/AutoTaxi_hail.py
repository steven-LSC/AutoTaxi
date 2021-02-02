# 巡邏模式: 出發之後會開始找有在舉手招車同時是會員的人停在他面前 同時發送訊息詢問上車意願 有要的上車的話 回傳上車時間
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
from datetime import datetime

# 儲存拍攝到的目標的會員id
target_user_id = ""

# 圖片根目錄
root_folder = "/home/pi/Desktop/AutoTaxi/"

# Line Bot API設定
line_bot_api = LineBotApi('') #個人資訊恕不提供
handler = WebhookHandler('') #個人資訊恕不提供

# AWS 登入資訊
ACCESS_KEY_ID = '' #個人資訊恕不提供
ACCESS_SECRET_KEY = '' #個人資訊恕不提供

# S3 bucket設定
s3 = boto3.resource(
    's3',
    aws_access_key_id=ACCESS_KEY_ID,
    aws_secret_access_key=ACCESS_SECRET_KEY,
)
my_bucket = s3.Bucket('peopleimage')

# 將拍攝到的圖片進行資料庫比對 看是不是會員 是的話填補user_id 同時回傳True 不是的話回傳False
def check_membership():
    
    global target_user_id
    
    print("拍攝到的目標比對人臉資料庫中，看是不是會員...")
    client=boto3.client('rekognition',aws_access_key_id=ACCESS_KEY_ID,
    aws_secret_access_key=ACCESS_SECRET_KEY,region_name = 'ap-northeast-1')

    target_file = root_folder+'target.jpg'
    target = open(target_file,'rb')
    target = target.read()
    flag = False
    for obj in my_bucket.objects.all():
        response = client.compare_faces(
            SimilarityThreshold=80,
            SourceImage={'S3Object': {'Bucket': 'peopleimage','Name': obj.key}},
            TargetImage={'Bytes': target}
        )
        if len(response['FaceMatches']) >= 1:
            flag = True
            target_user_id = obj.key[:-4]
            break

    return flag

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
        recieve_user_id = event.source.user_id

        # 接收偵測到在招車的會員的確認訊息 並回傳上車時間
        if recieve_user_id == target_user_id and mtext == "@check":

            go_on_time = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
            line_bot_api.push_message(recieve_user_id,TextSendMessage(text="您的上車時間是："+go_on_time))

        else:
            line_bot_api.push_message(recieve_user_id,TextSendMessage(text="要訂車的話請按下方圖文按鈕，謝謝。"))

    

if __name__ == '__main__':

    while True:

        # 執行 往前走同時偵測人 偵測到人後會將圖片存到AutoTaxi目錄以及openpose底下的media目錄
        os.chdir('/home/pi/tensorflow1/models/research/object_detection')
        os.system('python go_straight_person_stop_hail.py')

        # 執行openpose偵測動作
        cmd_openpose = './build/examples/openpose/openpose.bin --image_dir examples/media/ --net_resolution "80x80" --write_json examples/output/ --part_candidates'
        print(os.chdir('/home/pi/Desktop/openpose-master'))
        print(os.system(cmd_openpose))
        print(os.chdir('/home/pi/Desktop/AutoTaxi'))

        # 打開openpose偵測結果的json檔
        with open('/home/pi/Desktop/openpose-master/examples/output/target_keypoints.json', 'r', encoding='utf-8') as f:
            output = json.load(f)
            
        print(len(output['part_candidates'][0]['7']),len(output['part_candidates'][0]['5']),
              len(output['part_candidates'][0]['4']),len(output['part_candidates'][0]['2']))
        
        # 分析舉手動作 如果有舉手同時又是在會員資料庫裡的話就跳出迴圈
        # 舉左手的分析
        if len(output['part_candidates'][0]['7']) > 0 and len(output['part_candidates'][0]['5']) > 0 and output['part_candidates'][0]['7'][1] < output['part_candidates'][0]['5'][1]:
            print("get a person raising left hand")
            # 會員確認
            if check_membership() == True:
                print("he is our member")
                break
            else:
                print("he is not our member")
        # 舉右手的分析
        elif len(output['part_candidates'][0]['4']) > 0 and len(output['part_candidates'][0]['2']) > 0 and output['part_candidates'][0]['4'][1] < output['part_candidates'][0]['2'][1]:
            print("get a person raising right hand")
            # 會員確認
            if check_membership() == True:
                print("he is our member")
                break
            else:
                print("he is not our member")

        else:
            print("got a person but he is not raising hand.")
        
        # 沒有舉手或是有舉手但是不會員的話 執行skip 並繼續迴圈
        print("skip")
        os.chdir('/home/pi/tensorflow1/models/research/object_detection')
        os.system('python skip_person.py')
        print(os.chdir('/home/pi/Desktop/AutoTaxi'))
            
    # 發送訊息給偵測的會員
    line_bot_api.push_message(target_user_id,TextSendMessage(text="似乎偵測到您在招車，確定要上車的話請按下方選單按鈕。"))
    app.run()