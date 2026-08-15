"""
TEMPORARY DEMO ONLY — not the real Voice AI deliverable.

Twilio trial access is blocked in Egypt (team decision pending on how to
proceed with billing). This script proves the actual AI logic works today
by swapping the delivery channel to Telegram, while reusing the exact
same classifier and call_flow functions the real Twilio integration uses.

Run: python telegram_demo.py
Then message your bot on Telegram to simulate the follow-up conversation.
"""
import telebot
from sqlalchemy.orm import Session

from app.core.constants import FollowupResult
from app.core.database import SessionLocal
from app.telephony.call_flows.no_flow import handle_no
from app.telephony.call_flows.yes_flow import handle_yes
from app.telephony.call_flows.unknown_flow import MAX_ATTEMPTS
from app.telephony.stt.arabic_classifier import classify_response
from app.telephony.twilio.response import GREETING_TEXT, NOT_UNDERSTOOD_TEXT

BOT_TOKEN = "8977818304:AAH7I-UYXqd8C6dKJi7eZ5Eo1t3116pPy4k"

# Fill these in with a real followup_id + call_id you created via Swagger,
# same as we did for the incoming.py test earlier.
FOLLOWUP_ID = "PASTE_A_REAL_FOLLOWUP_ID_HERE"
CALL_ID = "PASTE_A_REAL_CALL_ID_HERE"

bot = telebot.TeleBot(BOT_TOKEN)
attempt_counter = {"count": 1}  # simple in-memory counter for this demo only


@bot.message_handler(commands=["start"])
def start(message):
    attempt_counter["count"] = 1
    bot.send_message(message.chat.id, GREETING_TEXT)


@bot.message_handler(func=lambda m: True)
def handle_reply(message):
    speech_text = message.text
    result = classify_response(speech_text)

    db: Session = SessionLocal()
    try:
        if result == FollowupResult.YES:
            handle_yes(db, FOLLOWUP_ID, CALL_ID)
            bot.send_message(message.chat.id, "تمام جدًا، شكرًا لوقتك. يوم سعيد. ✅ (Case marked RESOLVED)")
        elif result == FollowupResult.NO:
            handle_no(db, FOLLOWUP_ID, CALL_ID)
            bot.send_message(message.chat.id, "تمام، هنبعت حد من فريقنا يتواصل معاك تاني. ⚠️ (Case marked NEEDS_HUMAN)")
        else:
            attempt_counter["count"] += 1
            if attempt_counter["count"] > MAX_ATTEMPTS:
                handle_no(db, FOLLOWUP_ID, CALL_ID)
                bot.send_message(message.chat.id, "هنبعت حد من فريقنا. ⚠️ (Unclear twice — escalated to human)")
            else:
                bot.send_message(message.chat.id, NOT_UNDERSTOOD_TEXT)
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    print("Telegram demo bot running. Message it on Telegram to test.")
    bot.infinity_polling()