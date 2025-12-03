import json
import asyncio
from datetime import datetime, time
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes, CommandHandler
from pytz import timezone

# ---------------------- Bot Manager ----------------------
class BotManager:
    def __init__(self, token, group_id):
        self.token = token
        self.group_id = group_id
        self.audio_file = "saved_file.json"
        self.stats_file = "stats.json"
        self.group_file = "group_id.json"

        self.last_audio_file_id = None
        self.last_voice_file_id = None
        self.stats = {
            "users": {},
            "types": {"text": 0, "photo": 0, "video": 0, "sticker": 0},
            "joins": 0,
            "leaves": 0,
        }

        self.load_audio()
        self.load_stats()

    def save_audio(self):
        data = {"audio": self.last_audio_file_id, "voice": self.last_voice_file_id}
        with open(self.audio_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load_audio(self):
        try:
            with open(self.audio_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.last_audio_file_id = data.get("audio")
                self.last_voice_file_id = data.get("voice")
        except:
            pass

    def save_stats(self):
        with open(self.stats_file, "w", encoding="utf-8") as f:
            json.dump(self.stats, f, ensure_ascii=False, indent=2)

    def load_stats(self):
        try:
            with open(self.stats_file, "r", encoding="utf-8") as f:
                self.stats = json.load(f)
        except:
            pass

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.message:
            return

        text = update.message.text.lower() if update.message.text else ""
        text = text.replace("ي", "ی").replace("ك", "ک")
        user = update.message.from_user
        username = user.first_name or user.username or "کاربر ناشناس"

        self.stats["users"][username] = self.stats["users"].get(username, 0) + 1
        if update.message.text:
            self.stats["types"]["text"] += 1
        elif update.message.photo:
            self.stats["types"]["photo"] += 1
        elif update.message.video:
            self.stats["types"]["video"] += 1
        elif update.message.sticker:
            self.stats["types"]["sticker"] += 1
        self.save_stats()

        if update.message.audio:
            self.last_audio_file_id = update.message.audio.file_id
            self.save_audio()
            await update.message.reply_text("🎵 آهنگ ذخیره شد ✅")
            return

        if update.message.voice:
            self.last_voice_file_id = update.message.voice.file_id
            self.save_audio()
            await update.message.reply_text("🎤 ویس ذخیره شد ✅")
            return

        if "اهنگ هستی" in text or "آهنگ هستی" in text or "اهنگ خر" in text:
            try:
                if self.last_audio_file_id:
                    await update.message.reply_audio(audio=self.last_audio_file_id)
                elif self.last_voice_file_id:
                    await update.message.reply_voice(voice=self.last_voice_file_id)
                else:
                    await update.message.reply_text("فعلاً آهنگی ذخیره نشده 😅")
            except:
                self.last_audio_file_id = None
                self.last_voice_file_id = None
                self.save_audio()
            return

        responses = {
            "هعی": "زمونه بدی شده نگران نباش 🤖❤️",
            "هی ربات": "زمونه بدی شده نگران نباش 🤖❤️",
            "سوپرمنی": "باید حواسم به گروه باشه 💪😎",
            "ریدم": "بیشتر بری دهن خرا پر میشه 💩",
            "عجیب": "عجیب مجیب 👀",
            "هستی": "خر💩",
            "😂😂😂😂": "الهی توت باشه بخندی 😂🍾",
            "به کیرم": "از داشته‌هات مایه بذار نه از خواسته‌هات 😎",
            "چخبر": "از دسته تبر تو آدم بی‌خبر 🪓😂",
            "چه خبر": "از دسته تبر تو آدم بی‌خبر 🪓😂",
        }

        for key, val in responses.items():
            if key in text:
                await update.message.reply_text(val)
                return

    async def handle_join(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        self.stats["joins"] += 1
        self.save_stats()

    async def handle_leave(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        self.stats["leaves"] += 1
        self.save_stats()

    async def send_report(self, context: ContextTypes.DEFAULT_TYPE, chat_id=None):
        target = chat_id or self.group_id
        if not target:
            return

        total = sum(self.stats["types"].values())

        if not self.stats["users"] or total == 0:
            await context.bot.send_message(chat_id=target, text="🟢 گزارش امروز\n\n❗️آمار یافت نشد")
        else:
            sorted_users = sorted(self.stats["users"].items(), key=lambda x: x[1], reverse=True)
            top = "\n".join([f"{i+1}- {u} ({c})" for i, (u, c) in enumerate(sorted_users[:5])])
            msg = (
                f"🟢 گزارش فعالیت امروز\n\n"
                f"👥 کاربران فعال: {len(self.stats['users'])}\n"
                f"🔥 بیشترین فعالیت:\n{top}\n\n"
                f"💬 پیام‌ها: {total}\n"
                f"🎥 ویدیو: {self.stats['types']['video']}\n"
                f"📄 متن: {self.stats['types']['text']}\n"
                f"📷 عکس: {self.stats['types']['photo']}\n"
                f"😜 استیکر: {self.stats['types']['sticker']}\n\n"
                f"➕ ادها: {self.stats['joins']}   ➖ خروج‌ها: {self.stats['leaves']}\n\n"
                f"📅 {datetime.now().strftime('%Y/%m/%d')}"
            )
            await context.bot.send_message(chat_id=target, text=msg)

        self.stats["users"].clear()
        self.stats["types"] = {"text": 0, "photo": 0, "video": 0, "sticker": 0}
        self.stats["joins"] = 0
        self.stats["leaves"] = 0
        self.save_stats()

    async def clean_message(self, context: ContextTypes.DEFAULT_TYPE):
        if self.group_id:
            await context.bot.send_message(chat_id=self.group_id, text="✅ پاکسازی خودکار گروه فعال شد")

    def run(self):
        app = ApplicationBuilder().token(self.token).build()

        app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, self.handle_message))
        app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, self.handle_join))
        app.add_handler(MessageHandler(filters.StatusUpdate.LEFT_CHAT_MEMBER, self.handle_leave))
        app.add_handler(CommandHandler("report", self.send_report))

        iran = timezone("Asia/Tehran")
        job_queue = app.job_queue
        job_queue.run_daily(self.send_report, time=time(hour=23, minute=55, tzinfo=iran))
        job_queue.run_daily(self.clean_message, time=time(hour=5, minute=0, tzinfo=iran))

        print("🤖 Bot Running...")
        app.run_polling()


# ---------------------- Run Bot ----------------------
TOKEN = "8420996125:AAEFbB-ZHqVjdX_svLFAiQ9obwCsrHpYK1I"
GROUP_ID = -1003154654793

bot = BotManager(TOKEN, GROUP_ID)
bot.run()

# ---------------------- Flask Keep Alive ----------------------
from flask import Flask
from threading import Thread

app2 = Flask('')

@app2.route('/')
def home():
    return "Bot is Alive!"

def run():
    app2.run(host='0.0.0.0', port=8080)

t = Thread(target=run)
t.start()