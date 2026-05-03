# LINE Dog Content Bot — คู่มือ Deploy

## สิ่งที่ต้องเตรียม

| สิ่งที่ต้องการ | ที่ไหน | ฟรีไหม |
|---|---|---|
| LINE Official Account | https://manager.line.biz | ✅ ฟรี |
| LINE Channel Access Token | LINE Developers Console | ✅ ฟรี |
| LINE Channel Secret | LINE Developers Console | ✅ ฟรี |
| Anthropic API Key | https://console.anthropic.com | ✅ $5 free credit |
| Render.com Account | https://render.com | ✅ ฟรี |
| GitHub Account (สำหรับ deploy) | https://github.com | ✅ ฟรี |

---

## ขั้นตอนที่ 1 — สร้าง LINE Messaging API Channel

1. ไปที่ https://developers.line.biz
2. สร้าง Provider ใหม่ (ถ้ายังไม่มี)
3. Create Channel → เลือก **Messaging API**
4. กรอกข้อมูล channel
5. ไปที่แท็บ **Messaging API**:
   - เปิด **Allow bot to join group chats** (ถ้าต้องการ)
   - ปิด **Auto-reply messages**
   - ปิด **Greeting messages**
6. คัดลอก **Channel Secret** (แท็บ Basic settings)
7. กด **Issue** เพื่อรับ **Channel Access Token** (แท็บ Messaging API)

---

## ขั้นตอนที่ 2 — รับ Anthropic API Key

1. ไปที่ https://console.anthropic.com
2. สมัครบัญชี (ฟรี มี $5 credit)
3. ไปที่ **API Keys** → Create Key
4. คัดลอก key ไว้ (เห็นครั้งเดียว!)

---

## ขั้นตอนที่ 3 — Upload โค้ดขึ้น GitHub

```bash
# สร้าง repo ใหม่บน GitHub แล้ว:
git init
git add .
git commit -m "Initial LINE dog bot"
git remote add origin https://github.com/YOUR_USERNAME/line-dog-bot.git
git push -u origin main
```

---

## ขั้นตอนที่ 4 — Deploy บน Render.com

1. ไปที่ https://render.com → New → **Web Service**
2. เชื่อม GitHub repo ที่เพิ่ง push
3. ตั้งค่า:
   - **Name**: line-dog-bot
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn main:app --bind 0.0.0.0:$PORT`
4. เพิ่ม **Environment Variables**:
   ```
   LINE_CHANNEL_ACCESS_TOKEN = [ค่าจากขั้นตอนที่ 1]
   LINE_CHANNEL_SECRET       = [ค่าจากขั้นตอนที่ 1]
   ANTHROPIC_API_KEY         = [ค่าจากขั้นตอนที่ 2]
   ```
5. กด **Create Web Service**
6. รอ deploy เสร็จ จะได้ URL เช่น `https://line-dog-bot.onrender.com`

---

## ขั้นตอนที่ 5 — ตั้ง Webhook ใน LINE

1. กลับไปที่ LINE Developers Console
2. แท็บ **Messaging API** → **Webhook settings**
3. ใส่ Webhook URL: `https://line-dog-bot.onrender.com/webhook`
4. กด **Verify** → ต้องขึ้น **Success**
5. เปิด **Use webhook**

---

## วิธีใช้งาน

### พิมพ์ใน LINE:
```
วิธีอาบน้ำหมาโกลเด้น
```
→ บอทจะส่ง: บทพูดหมา 5 ประโยค + CapCut prompt พร้อมใช้

```
/หมา ปอม
```
→ เปลี่ยนสายพันธุ์เป็นปอมเมเรเนียน

```
/สไตล์
```
→ ดูสายพันธุ์ทั้งหมดที่รองรับ

```
/ตัวอย่าง
```
→ ดูลิงก์คลิปอ้างอิงแต่ละหัวข้อ

---

## ขั้นตอนทำคลิปใน CapCut หลังได้ prompt

1. เปิด CapCut → **AI Video** หรือ **Text to Video**
2. วาง CapCut Prompt ที่ได้จาก LINE
3. เลือก style: **Cartoon** / **Anime** / **Kawaii**
4. Generate → เลือก version ที่ชอบ
5. เพิ่มเสียง TTS ไทย: เลือกเสียง **น้องนุ่น** หรือ **น้องใหม่**
6. วางบทพูดเป็น subtitle อัตโนมัติ
7. Export 9:16 สำหรับ TikTok/Reels

---

## หมายเหตุ

- Render.com free tier จะ sleep หลังไม่มีคนใช้ 15 นาที request แรกจะช้า ~30 วิ
- Claude API $5 free credit ใช้ได้ประมาณ 500-1000 คลิป (ใช้นานมาก)
- LINE free tier ส่งได้ 200 push messages/เดือน (push = ส่งหาผู้ใช้ก่อน) reply ไม่จำกัด
