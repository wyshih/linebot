import json
import os
import hmac
import hashlib
import openai
import base64
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

line_bot_api = LineBotApi(os.environ.get('CHANNEL_ACCESS_TOKEN'))
channel_secret = os.environ.get('CHANNEL_SECRET')
handler = WebhookHandler(channel_secret)
openai.api_key = os.environ.get('OPENAI_API_KEY')

# 處理Line Request


def linebot(request):
    if request.method != 'POST' or 'X-Line-Signature' not in request.headers:
        return 'Error: Invalid source', 403
    else:
        # get X-Line-Signature header value
        x_line_signature = request.headers['X-Line-Signature']
        # get body value
        body = request.get_data(as_text=True)
        hash = hmac.new(channel_secret.encode('utf-8'),
                        body.encode('utf-8'), hashlib.sha256).digest()
        signature = base64.b64encode(hash).decode('utf-8')

        # Compare x-line-signature request header and the signature
        if x_line_signature == signature:
            try:
                # 解析 JSON
                json_data = json.loads(body)
                handler.handle(body, x_line_signature)
                # 取得 reply token
                tk = json_data['events'][0]['replyToken']
                # 取得 Line訊息
                user_input = json_data['events'][0]['message']['text']
                print(user_input)
                # 將Line訊息發給ChatGPT
                GPT_output = chat_with_gpt(user_input)
                # print(GPT_output)
                # 回傳ChatGPT訊息
                # TextSendMessage(GPT_output))
                line_bot_api.reply_message(tk, TextSendMessage(user_input))

                return 'OK', 200
            except:
                print('error')
        else:
            return 'Invalid signature', 403

# 回傳ChatGPT訊息
# 將LINE 使用者訊息發給ChatGPT，ChatGPT處理後再回傳給 LINE 使用者


def chat_with_gpt(user_input):
    try:
        # 設定提示語句，將使用者輸入的訊息與回覆模板結合
        prompt = f"{user_input}\n\nResponse:"
        # 使用OpenAI API，傳遞模型名稱、訊息角色和內容，以生成機器人回覆
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ]
        )
        # 從回覆中提取機器人的回覆訊息，並去除前後空白
        result = response['choices'][0]['message']['content'].strip()
        return result  # 返回處理過的回覆給LINE使用者
    except openai.Error as e:
        return "Error: OpenAI API"
    except Exception as e:
        return "Error: An unexpected error occurred"
