import os
import json
import re
from flask import Flask, request, abort
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    Configuration, ApiClient, MessagingApi,
    ReplyMessageRequest, TextMessage, FlexMessage, FlexContainer
)
from linebot.v3.webhooks import MessageEvent, TextMessageContent
import anthropic

app = Flask(__name__)

configuration = Configuration(access_token=os.environ["LINE_CHANNEL_ACCESS_TOKEN"])
handler = WebhookHandler(os.environ["LINE_CHANNEL_SECRET"])
claude = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

# ---- สไตล์หมาที่รองรับ ----
DOG_STYLES = {
    "โกลเด้น": "Golden Retriever",
    "ปอม": "Pomeranian",
    "ชิบะ": "Shiba Inu",
    "บีเกิ้ล": "Beagle",
    "พุดเดิ้ล": "Poodle",
    "คอร์กี้": "Corgi",
    "ฮัสกี้": "Husky",
    "ชิวาวา": "Chihuahua",
}

# ตัวอย่างคลิปอ้างอิงแต่ละหัวข้อ
REFERENCE_CLIPS = {
    "อาหาร":     "https://www.tiktok.com/tag/dogfoodtips",
    "อาบน้ำ":    "https://www.tiktok.com/tag/dogbathing",
    "ออกกำลัง": "https://www.tiktok.com/tag/dogexercise",
    "สุขภาพ":    "https://www.tiktok.com/tag/doghealth",
    "ฝึกหมา":   "https://www.tiktok.com/tag/dogtraining",
    "ของเล่น":   "https://www.tiktok.com/tag/dogtoys",
}

# สถานะผู้ใช้ (เก็บ session ชั่วคราว)
user_sessions = {}

HELP_TEXT = """สวัสดีครับ! บอทช่วยสร้างคอนเทนต์หมาน่ารัก

วิธีใช้:
1. พิมพ์หัวข้อตรงๆ เช่น
   "วิธีอาบน้ำหมาโกลเด้น"
   "อาหารที่หมาปอมกินได้"

2. กำหนดสไตล์หมาก่อนได้:
   "/หมา โกลเด้น" แล้วค่อยพิมพ์หัวข้อ

3. พิมพ์ /สไตล์ เพื่อดูสายพันธุ์ที่รองรับ
4. พิมพ์ /ตัวอย่าง เพื่อดูคลิปอ้างอิง"""


def get_dog_style(user_id: str) -> tuple[str, str]:
    """คืนชื่อไทย, ชื่ออังกฤษของสายพันธุ์ที่เลือก"""
    session = user_sessions.get(user_id, {})
    th = session.get("dog_th", "โกลเด้น")
    en = DOG_STYLES.get(th, "Golden Retriever")
    return th, en


def generate_content(topic: str, dog_th: str, dog_en: str) -> dict:
    """เรียก Claude API สร้าง script + CapCut prompt"""
    prompt = f"""คุณเป็น content creator มืออาชีพสำหรับ TikTok/Reels เนื้อหาเกี่ยวกับหมา

สร้างคอนเทนต์สำหรับ:
- หัวข้อ: {topic}
- สายพันธุ์: {dog_th} ({dog_en})
- สไตล์: การ์ตูน Chibi 2D น่ารัก ภาษาไทย สุภาพ

ตอบกลับเป็น JSON เท่านั้น โครงสร้างดังนี้:
{{
  "title": "ชื่อคลิป (สั้น กระชับ)",
  "script": [
    "ประโยคที่ 1 (หมาพูดในมุมมองตัวเอง น่ารัก)",
    "ประโยคที่ 2",
    "ประโยคที่ 3",
    "ประโยคที่ 4",
    "ประโยคที่ 5 (จบด้วย call to action)"
  ],
  "capcut_prompt": "English prompt for CapCut AI video generation, chibi 2D cartoon {dog_en}, kawaii style, pastel colors, talking to camera, [specific action related to topic], soft lighting, cute expression",
  "capcut_style_tips": "3 bullet points in Thai for CapCut settings",
  "hashtags": "#แฮชแท็ก1 #แฮชแท็ก2 #แฮชแท็ก3 #แฮชแท็ก4 #แฮชแท็ก5"
}}"""

    response = claude.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}]
    )

    text = response.content[0].text.strip()
    # ลบ markdown code block ถ้ามี
    text = re.sub(r"```json\s*|\s*```", "", text).strip()
    return json.loads(text)


def build_flex_message(data: dict, dog_th: str, ref_url: str | None) -> dict:
    """สร้าง LINE Flex Message จากข้อมูล content"""
    script_text = "\n".join(
        f"{i+1}. {line}" for i, line in enumerate(data["script"])
    )

    bubbles = [
        {
            "type": "bubble",
            "header": {
                "type": "box", "layout": "vertical",
                "backgroundColor": "#FFF3E0", "paddingAll": "16px",
                "contents": [
                    {"type": "text", "text": "🐶 " + data["title"],
                     "weight": "bold", "size": "lg", "color": "#BF360C", "wrap": True}
                ]
            },
            "body": {
                "type": "box", "layout": "vertical", "spacing": "md",
                "contents": [
                    {"type": "text", "text": "📝 บทพูดหมา", "weight": "bold", "color": "#5D4037"},
                    {"type": "text", "text": script_text, "wrap": True,
                     "size": "sm", "color": "#4E342E"},
                    {"type": "separator"},
                    {"type": "text", "text": "🎬 CapCut Prompt", "weight": "bold", "color": "#1565C0"},
                    {"type": "text", "text": data["capcut_prompt"], "wrap": True,
                     "size": "sm", "color": "#1A237E"},
                    {"type": "separator"},
                    {"type": "text", "text": "⚙️ ตั้งค่า CapCut", "weight": "bold", "color": "#2E7D32"},
                    {"type": "text", "text": data["capcut_style_tips"], "wrap": True,
                     "size": "sm", "color": "#1B5E20"},
                    {"type": "separator"},
                    {"type": "text", "text": data["hashtags"], "wrap": True,
                     "size": "xs", "color": "#6A1B9A"},
                ]
            },
            "footer": {
                "type": "box", "layout": "vertical", "spacing": "sm",
                "contents": [
                    {"type": "button", "style": "primary", "color": "#FF6F00",
                     "action": {"type": "uri", "label": "เปิด CapCut",
                                "uri": "https://www.capcut.com/"},
                     "height": "sm"},
                    *(
                        [{"type": "button", "style": "secondary",
                          "action": {"type": "uri", "label": "ดูตัวอย่างคลิป", "uri": ref_url},
                          "height": "sm"}]
                        if ref_url else []
                    )
                ]
            }
        }
    ]

    return {"type": "carousel", "contents": bubbles}


def find_reference(topic: str) -> str | None:
    for keyword, url in REFERENCE_CLIPS.items():
        if keyword in topic:
            return url
    return None


@app.route("/webhook", methods=["POST"])
def webhook():
    signature = request.headers.get("X-Line-Signature", "")
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return "OK"


@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event: MessageEvent):
    user_id = event.source.user_id
    text = event.message.text.strip()

    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)

        # --- คำสั่งพิเศษ ---
        if text == "/สไตล์":
            breeds = "\n".join(f"• {th} ({en})" for th, en in DOG_STYLES.items())
            reply = TextMessage(text=f"สายพันธุ์ที่รองรับ:\n{breeds}\n\nพิมพ์: /หมา ชื่อสายพันธุ์\nเช่น: /หมา ปอม")

        elif text.startswith("/หมา "):
            breed = text.replace("/หมา ", "").strip()
            if breed in DOG_STYLES:
                user_sessions.setdefault(user_id, {})["dog_th"] = breed
                reply = TextMessage(text=f"เลือกสายพันธุ์ {breed} แล้วครับ!\nตอนนี้พิมพ์หัวข้อที่ต้องการได้เลย")
            else:
                reply = TextMessage(text=f"ไม่มีสายพันธุ์ '{breed}' นะครับ\nพิมพ์ /สไตล์ เพื่อดูรายการ")

        elif text == "/ตัวอย่าง":
            links = "\n".join(f"• {k}: {v}" for k, v in REFERENCE_CLIPS.items())
            reply = TextMessage(text=f"คลิปอ้างอิงตามหัวข้อ:\n{links}")

        elif text in ("/help", "/ช่วย", "help", "ช่วย"):
            reply = TextMessage(text=HELP_TEXT)

        # --- สร้าง content จากหัวข้อ ---
        else:
            try:
                dog_th, dog_en = get_dog_style(user_id)

                # แจ้งว่ากำลังประมวลผล
                line_bot_api.reply_message(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[TextMessage(
                            text=f"กำลังสร้าง content หมา{dog_th} เรื่อง '{text}' อยู่นะคะ รอสักครู่..."
                        )]
                    )
                )

                # สร้าง content
                data = generate_content(text, dog_th, dog_en)
                ref_url = find_reference(text)
                flex_body = build_flex_message(data, dog_th, ref_url)

                # ส่ง Flex Message (ต้องใช้ push เพราะ reply token ใช้ไปแล้ว)
                from linebot.v3.messaging import PushMessageRequest
                line_bot_api.push_message(
                    PushMessageRequest(
                        to=user_id,
                        messages=[FlexMessage(
                            alt_text=f"Content: {data['title']}",
                            contents=FlexContainer.from_dict(flex_body)
                        )]
                    )
                )
                return "OK"

            except json.JSONDecodeError:
                reply = TextMessage(text="เกิดข้อผิดพลาดในการสร้าง content ลองใหม่อีกครั้งนะคะ")
            except Exception as e:
                reply = TextMessage(text=f"ขออภัย เกิดข้อผิดพลาด: {str(e)[:100]}")

        line_bot_api.reply_message(
            ReplyMessageRequest(reply_token=event.reply_token, messages=[reply])
        )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
