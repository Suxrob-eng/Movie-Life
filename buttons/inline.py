from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def sub_keyboard(channel_username):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📢 Kanalga obuna bo'lish", 
                    url=f"https://t.me/{channel_username.replace('@', '')}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="✅ Obunani tekshirish",
                    callback_data="check_sub"
                )
            ]
        ]
    )

def movie_actions_keyboard(movie_code):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔁 Boshqa film",
                    callback_data="another_movie"
                ),
                InlineKeyboardButton(
                    text="⭐ Saqlash",
                    callback_data=f"save_{movie_code}"
                )
            ]
        ]
    )