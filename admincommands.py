from database import engine
from sqlalchemy import text
import os
from datetime import date
import telegram

token = os.environ['TOKEN']
group_id = os.environ['GROUP_ID']

def kick_expired_members(update, context):
    with engine.connect() as conn:
        result = conn.execute(text("SELECT * FROM users WHERE active = 0"))
        rows = result.fetchall()
        rows_as_dicts = [dict(row._asdict()) for row in rows]

        bot = context.bot
        for row in rows_as_dicts:
            user_id = row['user_id']
            try:
                bot.ban_chat_member(chat_id=group_id, user_id=user_id)
                bot.send_message(chat_id=user_id, text="Your subscription has expired. You have been removed from the group.")
            except telegram.error.BadRequest as e:
                print(f"Failed to ban user {user_id}: {e}")
        
        conn.execute(text("UPDATE users SET active = 0 WHERE active = 1 AND expiration_date < :today"), {'today': date.today()})
        
        update.message.reply_text("Expired members kicked and updated in the database.")
