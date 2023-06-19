from telegram import InlineKeyboardButton

PACKAGE_PRICES = {
    'package3': 67.5,
    'package6': 120.0,
    'package12': 210.0
}

START_BUTTONS = [
    [InlineKeyboardButton("👤 My Account", callback_data='account')],
    [InlineKeyboardButton("💰 Purchase Membership", callback_data='purchase')],
    [InlineKeyboardButton("ℹ️ About & Support", callback_data='about')]
]

PACKAGE_BUTTONS = [
    [InlineKeyboardButton("3 Months ($67.5)", callback_data='package3')],
    [InlineKeyboardButton("6 Months ($120)", callback_data='package6')],
    [InlineKeyboardButton("1 Year ($210)", callback_data='package12')],
    [InlineKeyboardButton("⬅️ Back", callback_data='back')]
]


COIN_BUTTONS = [
    [
        InlineKeyboardButton("BTC", callback_data='BTC'),
        InlineKeyboardButton("BCH", callback_data='BCH'),
        InlineKeyboardButton("ETH", callback_data='ETH')
    ],
    [InlineKeyboardButton("⬅️ Back", callback_data='back')]
]

