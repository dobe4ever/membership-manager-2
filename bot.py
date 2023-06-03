from database import engine
from admincommands import kick_expired_members
from sqlalchemy import text
import os
from datetime import date
import telegram
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ChatMemberHandler
from telegram.error import BadRequest, Unauthorized

token = os.environ['TOKEN']
group_id = os.environ['GROUP_ID']

def start(update, context):
    user = update.effective_user
    user_id = user.id
    username = user.username
    public_name = user.first_name  # Assuming the first name is the public name

    # Update user information in the database
    with engine.connect() as conn:
        result = conn.execute(text("SELECT * FROM users WHERE user_id = :user_id"), {'user_id': user_id})
        user_data = result.fetchone()

        if user_data:
            # User exists, update username and public name if different
            if user_data.username != username or user_data.public_name != public_name:
                conn.execute(
                    text("UPDATE users SET username = :username, public_name = :public_name WHERE user_id = :user_id"),
                    {'username': username, 'public_name': public_name, 'user_id': user_id}
                )
        else:
            # User doesn't exist, insert new row
            conn.execute(
                text("INSERT INTO users (user_id, username, public_name, active) VALUES (:user_id, :username, :public_name, 0)"),
                {'user_id': user_id, 'username': username, 'public_name': public_name}
            )

    # Check user membership status and send personalized message
    with engine.connect() as conn:
        result = conn.execute(text("SELECT * FROM users WHERE user_id = :user_id"), {'user_id': user_id})
        user_data = result.fetchone()

        if user_data:
            active = user_data.active

            if active == 1:
                signup_date = user_data.signup_date
                expiration_date = user_data.expiration_date

                message = f"Hi {public_name},\n\nYou are a member. Your membership started on {signup_date} and ends on {expiration_date}."

                # Create inline keyboard with buttons for active members
                keyboard = [
                    [InlineKeyboardButton("Access members area", callback_data='members_area')],
                    [InlineKeyboardButton("Extend membership time", callback_data='extend_membership')]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)

                # Send message with buttons
                context.bot.send_message(chat_id=user_id, text=message, reply_markup=reply_markup)
            else:
                message = f"Hi {public_name},\n\nYou are not a member."

                # Send message without buttons
                context.bot.send_message(chat_id=user_id, text=message)

    # Send message with main buttons
    main_buttons_message = "Feel free to explore the options below."

    keyboard = [
        [KeyboardButton("Account")],
        [KeyboardButton("Purchase Membership")],
        [KeyboardButton("About & Support")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    context.bot.send_message(chat_id=user_id, text=main_buttons_message, reply_markup=reply_markup)

kick_handler = CommandHandler('kick0s', kick_expired_members)

def new_member(update, context):
    # Extract new member information
    user = update.message.new_chat_members[0]
    user_id = user.id
    username = user.username
    public_name = user.first_name

    # Update user information in the database
    with engine.connect() as conn:
        result = conn.execute(text("SELECT * FROM users WHERE user_id = :user_id"), {'user_id': user_id})
        user_data = result.fetchone()

        if user_data:
            # User exists, update username and public name if different
            if user_data.username != username or user_data.public_name != public_name:
                conn.execute(
                    text("UPDATE users SET username = :username, public_name = :public_name WHERE user_id = :user_id"),
                    {'username': username, 'public_name': public_name, 'user_id': user_id}
                )
        else:
            # User doesn't exist, insert new row
            conn.execute(
                text("INSERT INTO users (user_id, username, public_name, active) VALUES (:user_id, :username, :public_name, 0)"),
                {'user_id': user_id, 'username': username, 'public_name': public_name}
            )

    # Call kick_expired_members function
    kick_expired_members(update, context)

def main():
    updater = Updater(token=token, use_context=True)
    dispatcher = updater.dispatcher

    # Add start handlers
    start_handler = CommandHandler('start', start)
    dispatcher.add_handler(start_handler)
  
    # Add kick handlers
    kick_handler = CommandHandler('kick0s', kick_expired_members)
    dispatcher.add_handler(kick_handler)

    # Add new member handler
    new_member_handler = MessageHandler(Filters.status_update.new_chat_members, new_member)
    dispatcher.add_handler(new_member_handler)

    updater.start_polling()

if __name__ == '__main__':
    main()
