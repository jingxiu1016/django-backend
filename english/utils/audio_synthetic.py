"""******************************** 开始
    author:惊修
    time:$
   ******************************* 结束"""
import websocket
import datetime
import hashlib
import base64
import hmac
import json
from urllib.parse import urlencode
import time
import ssl
from wsgiref.handlers import format_date_time
from datetime import datetime
from time import mktime
import _thread as thread
import os


# 创建一个可合成语音的对象
from django.conf import settings


class TextToAudio(object):
    # 初始化
    def __init__(self, text):
        self.AppID = '5e8ffef3'
        self.ApiKey = '1a5a5a198f60755d162cd73619af7022'
        self.ApiSecret = '2bf02a812630e02f452063204aa3aa49'
        self.Text = text

        # 公共参数
        self.CommonArgs = {'app_id': self.AppID}
        # 业务参数
        self.BusinessArgs = {
            'aue': 'lame',
            'sfl': 1,
            'auf': "audio/L16;rate=16000",
            'vcn': 'xiaoyan',
            "tte": "utf8"
        }
        self.Data = {
            'status': 2,
            'text': str(base64.b64encode(self.Text.encode('utf-8')), 'UTF8')
        }

    # 拼接URL
    def create_url(self):
        url = 'wss://tts-api.xfyun.cn/v2/tts'
        # 生成RFC1123格式的时间戳
        now = datetime.now()
        date = format_date_time(mktime(now.timetuple()))

        # 拼接字符串
        signature_origin = "host: " + "ws-api.xfyun.cn" + "\n"
        signature_origin += "date: " + date + "\n"
        signature_origin += "GET " + "/v2/tts " + "HTTP/1.1"
        # 进行hmac-sha256进行加密
        signature_sha = hmac.new(self.ApiSecret.encode('utf-8'), signature_origin.encode('utf-8'),
                                 digestmod=hashlib.sha256).digest()
        signature_sha = base64.b64encode(signature_sha).decode(encoding='utf-8')

        authorization_origin = "api_key=\"%s\", algorithm=\"%s\", headers=\"%s\", signature=\"%s\"" % (
            self.ApiKey, "hmac-sha256", "host date request-line", signature_sha)
        authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode(encoding='utf-8')
        # 将请求的鉴权参数组合为字典
        v = {
            "authorization": authorization,
            "date": date,
            "host": "ws-api.xfyun.cn"
        }
        # 拼接鉴权参数，生成url
        url = url + '?' + urlencode(v)
        return url

class createWebSocket(object):

    def __init__(self,text):
        self.temp = TextToAudio(text=text)
        self.url = self.temp.create_url()
        self.ws = None

    def start(self):
        self.ws = websocket.WebSocketApp(self.url,
                                on_message=self.on_message,
                                on_error=self.on_error,
                                on_close=self.on_close)
        self.ws.on_open = self.on_open
        self.ws.run_forever(sslopt={'cert_reqs': ssl.CERT_NONE})
        return self.ws

    def on_message(self, message):
        try:
            message = json.loads(message)
            code = message["code"]
            sid = message["sid"]
            audio = message["data"]["audio"]
            audio = base64.b64decode(audio)
            status = message["data"]["status"]
            if status == 2:
                print("ws is closed")
                self.ws.close()
            if code != 0:
                errMsg = message["message"]
                print("sid:%s call error:%s code is:%s" % (sid, errMsg, code))
            else:

                with open(str(settings.BASE_DIR)+'\\'+'media/audio/word.mp3', 'ab') as f:
                    f.write(audio)

        except Exception as e:
            print("receive msg,but parse exception:", e)

    def on_error(self, error):
        print('error', error)

    def on_close(self):
        print('close')
    def on_open(self):
        def run(*args):
            d = {"common": self.temp.CommonArgs,
                 "business": self.temp.BusinessArgs,
                 "data": self.temp.Data,
                 }
            d = json.dumps(d)
            self.ws.send(d)
            if os.path.exists(str(settings.BASE_DIR)+'\\'+'media/audio/word.mp3'):
                os.remove(str(settings.BASE_DIR)+'\\'+'media/audio/word.mp3')

        thread.start_new_thread(run, ())
