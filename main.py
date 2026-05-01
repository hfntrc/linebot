import os
from flask import Flask, request, abort

from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

from google import genai

app = Flask(__name__)

LINE_CHANNEL_ACCESS_TOKEN = os.environ["LINE_CHANNEL_ACCESS_TOKEN"]
LINE_CHANNEL_SECRET = os.environ["LINE_CHANNEL_SECRET"]
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]

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
你是一個嚴格的中越雙向翻譯器。

請只做一件事：輸出翻譯結果。

判斷規則：
- 如果使用者輸入主要是中文，請只翻譯成越南文。
- 如果使用者輸入主要是越南文，請只翻譯成繁體中文。
- 如果使用者輸入同時包含中文和越南文，請判斷主要語言，翻譯成另一種語言。

輸出規則：
- 只能輸出翻譯後的文字。
- 不要輸出原文。
- 不要輸出「中文：」「越南文：」。
- 不要輸出「中轉越」「越轉中」。
- 不要解釋。
- 不要加標題。
- 不要同時輸出兩種語言。
- 不要使用 Markdown。

使用者輸入：
{text}
"""

    response = gemini_client.models.generate_content(
        model="models/gemini-2.5-flash",
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
