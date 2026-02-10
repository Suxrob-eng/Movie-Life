from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def phone_btn():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 Telefon raqamni yuborish", request_contact=True)]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

def stats_btn():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔎 Qidirish"), KeyboardButton(text="🎲 Tasodifiy")],
            [KeyboardButton(text="🌟 Bugungi top"), KeyboardButton(text="📊 Haftalik top")],
            [KeyboardButton(text="🎭 Janrlar"), KeyboardButton(text="🎯 Tavsiya")],
            [KeyboardButton(text="ℹ️ Yordam"), KeyboardButton(text="📊 Statistika")]
        ],
        resize_keyboard=True,
        input_field_placeholder="Film kodini kiriting..."
    )

def admin_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🎬 Film qo'shish"), KeyboardButton(text="📤 Kanal post")],
            [KeyboardButton(text="⚙️ Sozlamalar"), KeyboardButton(text="📊 Statistika")],
            [KeyboardButton(text="🔢 Barcha kodlar"), KeyboardButton(text="🔙 Asosiy menyu")]
        ],
        resize_keyboard=True
    )

def main_menu():
    return stats_btn()