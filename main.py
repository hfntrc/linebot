import os
from flask import Flask, request, abort

from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

from google import genai

app = Flask(__name__)

LINE_CHANNEL_ACCESS_TOKEN = os.environ["AsxmHm9evu7N0iz8nh3shkMIxx3jqOIbCiRZQNSNc7eDNzDbi5ppl8cPrFGpzQjkGa3K3zNddZaTRCTMfYaEnEPBg63cv9oMzxnBHOJ4EzH97PzBIsYA94UZ03FeeycNETzwLLjnfU4Qlv+ppZvLeQdB04t89/1O/w1cDnyilFU="]
LINE_CHANNEL_SECRET = os.environ["3df11ff4746162900267ffc1d177e212"]
GEMINI_API_KEY = os.environ["AIzaSyB2PA_ukUCZ71SosFLsjgLg-9bjpeKf7aA"]

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

gemini_client = genai.Client(api_key=GEMINI_API_KEY)


@app.route("/", methods=["GET"])
def home():
    return "Bot is running", 200


@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature")
    body = request.get_data(as_text=True)

    if signature is None:
        abort(400)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    except Exception as e:
        print("Webhook error:", e)
        abort(500)

    return "OK", 200


def translate(text):
    prompt = f"""
請在中文與越南文之間翻譯。
規則：
- 中文 → 越南文
- 越南文 → 繁體中文
- 只輸出翻譯結果，不要解釋

{text}
"""

    response = gemini_client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt,
    )

    return response.text.strip()


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_text = event.message.text

    try:
        result = translate(user_text)
    except Exception as e:
        print("Translate error:", e)
        result = "翻譯錯誤，請稍後再試"

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=result)
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)