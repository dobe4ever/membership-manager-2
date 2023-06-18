from settings import START_BUTTONS, PACKAGE_BUTTONS, COIN_BUTTONS, PACKAGE_PRICES
from utils import calculate_amount
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode, Update
from telegram.ext import MessageHandler, Filters, CallbackContext, CommandHandler, Updater, CallbackQueryHandler
from database import kick_expired_members, new_member, transaction_in_progress, get_user_membership, add_or_update_user, get_address, release_address
import os

bot_token = os.environ['TOKEN']
group_id = os.environ['GROUP_ID']


def start(update: Update, context: CallbackContext):
    user = update.effective_user
    first_name = user.first_name

    # Call add_or_update_user() to add or update the user in the database
    add_or_update_user(update)

    # Create inline keyboard markup using the constant START_BUTTONS
    reply_markup = InlineKeyboardMarkup(START_BUTTONS)

    # Personalize the welcome message with the user's first name
    welcome_message = f"Welcome to the members manager bot, {first_name}!"

    # Send the personalized welcome message with inline keyboard
    update.message.reply_text(welcome_message, reply_markup=reply_markup)


def handle_back(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    # Create inline keyboard markup using the constant START_BUTTONS
    reply_markup = InlineKeyboardMarkup(START_BUTTONS)

    # Send welcome message with inline keyboard
    query.message.edit_text('Welcome to the members manager bot!', reply_markup=reply_markup)


def handle_purchase(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    # Check if the user already has an active transaction
    transaction_data = transaction_in_progress(update.effective_user.id)
    
    if transaction_data is not None:
        amount, type, address = transaction_data
        cancel_button = InlineKeyboardButton("Cancel Transaction", callback_data='cancel')
        keyboard = [[cancel_button]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        message = f"You have an active transaction. Complete payment or cancel before starting a new one.\n\n" \
                  f"Send: `{amount}` {type}\n" \
                  f"Address: `{address}`\n\n" \
                  
        query.message.reply_text(message, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
        return    

    # Create inline keyboard markup using the constant PACKAGE_BUTTONS
    reply_markup = InlineKeyboardMarkup(PACKAGE_BUTTONS)
    query.message.edit_text('Please select a package:', reply_markup=reply_markup)


def handle_package_selection(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()    

    # Create inline keyboard markup using the constant COIN_BUTTONS
    reply_markup = InlineKeyboardMarkup(COIN_BUTTONS)
    query.message.edit_text('Now select a payment method:', reply_markup=reply_markup)
    context.user_data['selected_package'] = query.data


def handle_coin_selection(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    # Check if the user already has an active transaction
    transaction_data = transaction_in_progress(update.effective_user.id)
    
    if transaction_data is not None:
        amount, type, address = transaction_data
        cancel_button = InlineKeyboardButton("Cancel Transaction", callback_data='cancel')
        keyboard = [[cancel_button]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        message = f"You have an active transaction. Complete payment or cancel before starting a new one.\n\n" \
                  f"Send: `{amount}` {type}\n" \
                  f"Address: `{address}`\n\n"

        query.message.reply_text(message, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
        return  

    if 'selected_package' not in context.user_data:
        # Create inline keyboard markup using the PACKAGE_BUTTONS constant
        reply_markup = InlineKeyboardMarkup(PACKAGE_BUTTONS)
        query.message.reply_text('Please select a package first:', reply_markup=reply_markup)
        return
    
    # Prepare the necessary data to calculate the amount and retrieve an address for the specific coin
    selected_package = context.user_data['selected_package']
    package_price = PACKAGE_PRICES.get(selected_package, 0.0)

    coin = query.data

    # Retrieve the user's ID from the update object (assuming it's stored there)
    user_id = update.effective_user.id

    # Calculate the amount based on the package price and coin
    amount = calculate_amount(package_price, coin)

    # Call get_address() to retrieve an address for the specified coin & save userid, address, coin & amount to the addresses table.
    address = get_address(coin, user_id, amount)

    if address is None:
        query.message.reply_text('No available address found. Please choose a different coin or try again in a few minutes.')
        return

    cancel_button = InlineKeyboardButton("Cancel Transaction", callback_data='cancel')
    keyboard = [[cancel_button]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.message.edit_text(
        f"Please send `{amount}` {coin} to the address below within 1 hour:\n\n`{address}`\n\n"
        "Once the payment hits the blockchain, you will receive a confirmation message automatically.",
        reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)


def handle_cancel_transaction(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    # Retrieve the user's ID from the update object (assuming it's stored there)
    user_id = update.effective_user.id

    # Check if there is an active transaction for the user
    if transaction_in_progress(user_id):
        # Reset the user data to remove any stored package and coin information
        context.user_data.clear()

        # Release the address associated with the user
        release_address(user_id)

        # Send appropiate message with START_BUTTONS constant
        reply_markup = InlineKeyboardMarkup(START_BUTTONS)
        query.message.edit_text('Transaction cancelled. Start a new transaction if you wish.', reply_markup=reply_markup)
    else:
        reply_markup = InlineKeyboardMarkup(START_BUTTONS)
        query.message.reply_text('There is no active transaction to cancel.', reply_markup=reply_markup)


def handle_account(update, context):
    user = update.effective_user
    user_id = user.id
    public_name = user.first_name

    active, signup_date, expiration_date = get_user_membership(user_id)

    if active:
        message = f"Hi {public_name},\nYou are a member. Your membership started on {signup_date} and ends on {expiration_date}.\n\n[Access Private Group](https://t.me/+EsIH9Bty8gdhMWU9)\n[Access Members Website](https://members.bitcoin4ever.org)"

        # Create inline keyboard markup using the constant START_BUTTONS
        reply_markup = InlineKeyboardMarkup(START_BUTTONS)

        # Send message with Markdown and inline keyboard markup
        context.bot.send_message(chat_id=user_id, text=message, disable_web_page_preview=True, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)
    else:
        message = f"Hi {public_name},\nYou are not a member. Feel free to purchase a Membership below."

        # Create inline keyboard markup using the constant START_BUTTONS
        reply_markup = InlineKeyboardMarkup(START_BUTTONS)

        # Send message without buttons
        context.bot.send_message(chat_id=user_id, text=message, reply_markup=reply_markup)


def handle_about(update, context):
    # Create an inline keyboard with the 'Back' button
    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("< Back", callback_data='back')]])

    about_text = (
        "Here's what you can expect from this membership:\n\n"
        "🔒 Access to our private group: Join our exclusive Telegram group to interact with other traders, ask questions, and get market updates.\n\n"
        "📈 Members-only website: Gain entry to our dedicated website, offering valuable resources such as Bitcoin reports, a premium education center, and powerful trading tools.\n"
        "\nExplore the possibilities and elevate your trading experience with us! 👥💼💰\n\n"
        f"Have any questions or need assistance? Please don't hesitate to [contact our admin](https://t.me/dobe4ever) for support."
    )
    
    # Send the about and support message with the inline keyboard
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=about_text,
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )


###TESTING###

import logging
import os
import requests
from datetime import datetime
import threading
import time
from telegram import Bot

# Configure logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

def error_handler(update, context):
    """Log the error and handle it gracefully."""
    logger.error(msg="Exception occurred", exc_info=context.error)

def keep_alive():
    while True:
        response = requests.get(f'https://api.telegram.org/bot{bot_token}/getMe')
        print("Keep-alive executed at", datetime.now(), "status code:", response.status_code)
        #print("Response status code:", response.status_code)
        #print("Response content:", response.content)
        time.sleep(600)  # Delay execution for 10 minute


def execute_kick_expired_members(bot_token, group_id):
    while True:
        # Create an instance of the bot using the provided token
        bot = Bot(token=bot_token)
        # Execute the kick_expired_members function
        kick_expired_members(bot, group_id)
        time.sleep(7200)  # Delay execution for 2 hours


def main():
    # Pass the session to the updater
    updater = Updater(bot_token, use_context=True)
    dp = updater.dispatcher

    # Add the error handler
    dp.add_error_handler(error_handler)

    # Add the new_member handler (triggers when new member joins the group)
    dp.add_handler(MessageHandler(Filters.status_update.new_chat_members, new_member))

    # Handlers that trigger on button clicks or commands
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CallbackQueryHandler(handle_about, pattern='^about$'))
    dp.add_handler(CallbackQueryHandler(handle_back, pattern='^back$'))
    dp.add_handler(CallbackQueryHandler(handle_account, pattern='^account$'))
    dp.add_handler(CallbackQueryHandler(handle_purchase, pattern='^purchase$'))
    dp.add_handler(CallbackQueryHandler(handle_package_selection, pattern='^package'))
    dp.add_handler(CallbackQueryHandler(handle_coin_selection, pattern='^BTC$|^BCH$|^ETH$'))
    dp.add_handler(CallbackQueryHandler(handle_cancel_transaction, pattern='^cancel$'))

    # Start & keep the bot running
    updater.start_polling()


    # Create a separate thread for executing kick_alive
    kick_alive_thread = threading.Thread(target=keep_alive)
    kick_alive_thread.daemon = True
    kick_alive_thread.start()
  

    # Create a separate thread for executing kick_expired_members
    kick_expired_members_thread = threading.Thread(target=execute_kick_expired_members, args=(bot_token, group_id))
    kick_expired_members_thread.daemon = True
    kick_expired_members_thread.start()


    updater.idle()
    updater.stop()

if __name__ == '__main__':
    main()
