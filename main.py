import asyncio
import logging
import sys
from datetime import datetime
import random

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.client.default import DefaultBotProperties
from aiogram.types import ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, InputMediaPhoto, InputMediaVideo
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramForbiddenError, TelegramUnauthorizedError
from aiogram.fsm.state import State, StatesGroup

from config import TOKEN, ADMIN_ID, CHANNEL_USERNAME, AUTO_POST
from database import (
    init_db, add_user, get_user, add_movie, get_movie_by_code, 
    get_all_movies, get_total_movies_count,
    get_total_users_count, get_today_movies_count,
    get_all_users, search_movies_by_title
)
from movie_code import generate_move_code
from channel_auto_post import ChannelAutoPost

# ==================== STATE CLASSES ====================

class AdminMovie(StatesGroup):
    poster = State()        # Avval poster rasm
    movie_file = State()    # Keyin video
    movie_desc = State()    # So'ng tavsif

class SearchState(StatesGroup):
    waiting_for_query = State()

# ==================== BOTNI ISHGA TUSHIRISH ====================

if not TOKEN:
    print("❌ TOKEN .env faylida topilmadi!")
    sys.exit(1)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

try:
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
    dp = Dispatcher()
    print(f"✅ Bot yaratildi: {TOKEN[:10]}...")
except Exception as e:
    print(f"❌ Bot yaratishda xato: {e}")
    sys.exit(1)

# ==================== BUTTON FUNCTIONS ====================

def phone_btn():
    from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 Telefon raqamni yuborish", request_contact=True)]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

def stats_btn():
    from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔎 Qidirish"), KeyboardButton(text="🎲 Tasodifiy")],
            [KeyboardButton(text="🌟 Bugungi top"), KeyboardButton(text="📊 Haftalik top")],
            [KeyboardButton(text="🎭 Janrlar"), KeyboardButton(text="🎯 Tavsiya")],
            [KeyboardButton(text="ℹ️ Yordam"), KeyboardButton(text="🔙 Asosiy menyu")]
        ],
        resize_keyboard=True,
        input_field_placeholder="Film kodini kiriting..."
    )

def admin_menu():
    from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🎬 Film qo'shish"), KeyboardButton(text="📤 Kanal post")],
            [KeyboardButton(text="⚙️ Sozlamalar"), KeyboardButton(text="📊 Statistika")],
            [KeyboardButton(text="🔢 Barcha kodlar"), KeyboardButton(text="🔙 Asosiy menyu")]
        ],
        resize_keyboard=True
    )

def sub_keyboard(channel_username):
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
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
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔁 Boshqa film",
                    callback_data="another_movie"
                )
            ]
        ]
    )

# ==================== STATISTIKA FUNKSIYALARI ====================

def get_random_top_movies(count=5):
    """Tasodifiy filmlarni qaytaradi"""
    all_movies = get_all_movies()
    if not all_movies:
        return []
    if count >= len(all_movies):
        return random.sample(all_movies, len(all_movies))
    return random.sample(all_movies, count)

def get_today_top_movies(count=3):
    """Bugungi top filmlarni qaytaradi"""
    all_movies = get_all_movies()
    if not all_movies:
        return []
    today = datetime.now().date()
    random.seed(str(today))
    if count >= len(all_movies):
        return random.sample(all_movies, len(all_movies))
    return random.sample(all_movies, count)

def get_weekly_top_movies(count=5):
    """Haftalik top filmlarni qaytaradi"""
    all_movies = get_all_movies()
    if not all_movies:
        return []
    week_number = datetime.now().isocalendar()[1]
    random.seed(f"week_{week_number}")
    if count >= len(all_movies):
        return random.sample(all_movies, len(all_movies))
    return random.sample(all_movies, count)

def get_recommended_movie(user_id=None):
    """Tavsiya etilgan film"""
    all_movies = get_all_movies()
    if not all_movies:
        return None
    if user_id:
        random.seed(str(user_id))
    return random.choice(all_movies)

def format_movie_stats(movies_list, title="🎬 Tasodifiy Top Filmlar"):
    """Film ro'yxatini formatda qaytaradi"""
    if not movies_list:
        return "📭 Hozircha filmlar mavjud emas"
    
    response = f"<b>{title}:</b>\n\n"
    
    for i, (code, desc) in enumerate(movies_list, 1):
        desc_lines = desc.split('\n')
        film_title = desc_lines[0] if desc_lines else "Nomsiz film"
        
        genre = "Noma'lum"
        for line in desc_lines:
            if "Janri:" in line:
                genre = line.split("Janri:")[1].strip()
                break
        
        response += f"{i}. <b>{film_title}</b>\n"
        response += f"   🎭 {genre}\n"
        response += f"   🔢 Kodi: <code>{code}</code>\n\n"
    
    return response

# ==================== FILM YUKLASH FUNKSIYALARI ====================

async def save_movie_with_poster(poster_file: str, video_file: str, description: str, code: int):
    """Poster va video bilan filmni saqlash"""
    try:
        # Kombinatsiyalangan tavsif
        formatted_desc = f"{description}\n\n" \
                        f"🔢 <b>KINO KODI:</b> <code>{code}</code>\n" \
                        f"📅 Qo'shilgan sana: {datetime.now().strftime('%d.%m.%Y')}"
        
        # Bazaga saqlash (faqat video file_id saqlanadi)
        success = add_movie(video_file, formatted_desc, code)
        
        if success:
            # Poster file_id ni alohida saqlash (agar kerak bo'lsa)
            # Hozircha faqat log qilamiz
            logging.info(f"Poster file_id: {poster_file}")
            logging.info(f"Video file_id: {video_file}")
            return True
        return False
    except Exception as e:
        logging.error(f"Film saqlash xatosi: {e}")
        return False

# ==================== ASOSIY FUNKSIYALAR ====================

async def check_subscription(user_id: int) -> bool:
    """Foydalanuvchi kanalga obuna bo'lganligini tekshirish"""
    try:
        member = await bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ["member", "administrator", "creator"]
    except Exception as e:
        logging.error(f"Obunani tekshirishda xato: {e}")
        return True  # Test uchun

async def send_welcome_message(user_id: int):
    """Xush kelibsiz xabari"""
    total_movies = get_total_movies_count()
    
    welcome_text = (
        f"🎬 <b>Kino botga xush kelibsiz!</b>\n\n"
        f"📊 Hozirgi holat:\n"
        f"🎥 Filmlar soni: {total_movies} ta\n"
        f"📅 Bugun qo'shildi: {get_today_movies_count()} ta\n\n"
        f"🔢 <b>Film kodini yuboring</b>\n"
        f"yoki quyidagi tugmalardan foydalanishingiz mumkin👇"
    )
    
    await bot.send_message(user_id, welcome_text, reply_markup=stats_btn())

# ==================== HANDLERLAR ====================

# 🚀 START HANDLER
@dp.message(CommandStart())
async def start_handler(message: types.Message):
    user_id = message.from_user.id
    
    # Obunani tekshirish
    if not await check_subscription(user_id):
        await message.answer(
            "📢 Botdan foydalanish uchun avval kanalga obuna bo'ling:",
            reply_markup=sub_keyboard(CHANNEL_USERNAME)
        )
        return
    
    user = get_user(user_id)
    full_name = message.from_user.full_name
    
    if user:
        await send_welcome_message(user_id)
    else:
        await message.answer(
            f"👋 Assalomu Alaykum, {full_name}!\n"
            "📱 Ro'yxatdan o'tish uchun telefon raqamingizni yuboring:",
            reply_markup=phone_btn()
        )

# ✅ OBUNA TEKSHIRISH
@dp.callback_query(F.data == "check_sub")
async def check_subscription_callback(call: CallbackQuery):
    user_id = call.from_user.id
    
    if await check_subscription(user_id):
        await call.message.delete()
        user = get_user(user_id)
        
        if user:
            await send_welcome_message(user_id)
        else:
            await call.message.answer(
                "✅ Obuna tasdiqlandi!\n"
                "📱 Iltimos, telefon raqamingizni yuboring:",
                reply_markup=phone_btn()
            )
    else:
        await call.answer(
            "❌ Hali kanalga obuna bo'lmadingiz!",
            show_alert=True
        )

# 📱 TELEFON RAQAM QABUL QILISH
@dp.message(F.contact)
async def get_user_contact(message: types.Message):
    user_id = message.from_user.id
    full_name = message.from_user.full_name
    username = message.from_user.username or ""
    phone_number = message.contact.phone_number
    
    if not phone_number:
        await message.answer("❌ Telefon raqami noto'g'ri formatda")
        return
    
    try:
        existing_user = get_user(user_id)
        
        if existing_user:
            # Yangilash
            add_user(user_id, full_name, username, phone_number)
            await message.answer(
                "✅ Ma'lumotlaringiz yangilandi!",
                reply_markup=ReplyKeyboardRemove()
            )
            await send_welcome_message(user_id)
        else:
            # Yangi foydalanuvchi
            success = add_user(user_id, full_name, username, phone_number)
            
            if success:
                await message.answer(
                    "✅ Ro'yxatdan o'tdingiz! 🎉",
                    reply_markup=ReplyKeyboardRemove()
                )
                await send_welcome_message(user_id)
            else:
                await message.answer(
                    "❌ Ro'yxatdan o'tishda xatolik yuz berdi. Qayta urinib ko'ring."
                )
    except Exception as e:
        logging.error(f"Telefon raqam qabul qilish xatosi: {e}")
        await message.answer(
            "❌ Texnik xatolik yuz berdi. Keyinroq urinib ko'ring."
        )

# ==================== ADMIN KOMANDALARI ====================

# 👑 ADMIN PANEL
@dp.message(Command("admin"))
async def admin_handler(message: types.Message):
    user_id = message.from_user.id

    if user_id == ADMIN_ID:
        await message.answer(
            "👑 <b>Admin paneliga xush kelibsiz!</b>\n\n"
            "Quyidagi buyruqlardan foydalaning:\n"
            "🎬 /addmovie - Film qo'shish\n"
            "📊 /stats - Statistika\n"
            "🔢 /allcodes - Barcha kodlar\n\n"
            "Yoki quyidagi tugmalardan foydalaning:",
            reply_markup=admin_menu()
        )
    else:
        await message.answer("❌ Bu buyruq faqat admin uchun!")

# 📊 STATISTIKA
@dp.message(Command("stats"))
@dp.message(F.text == "📊 Statistika")
async def stats_handler(message: types.Message):
    """Bot statistikasi"""
    user_id = message.from_user.id
    if user_id != ADMIN_ID:
        await message.answer("❌ Bu buyruq faqat admin uchun!")
        return
    
    total_users = get_total_users_count()
    total_movies = get_total_movies_count()
    today_movies = get_today_movies_count()
    
    stats_text = f"""
📊 <b>BOT STATISTIKASI</b>

👥 <b>Foydalanuvchilar:</b> {total_users} ta
🎬 <b>Filmlar:</b> {total_movies} ta
📅 <b>Bugun qo'shildi:</b> {today_movies} ta

⏰ <b>Server vaqti:</b> {datetime.now().strftime('%d.%m.%Y %H:%M')}
"""
    
    await message.answer(stats_text)

# 🔢 BARCHA KODLAR
@dp.message(Command("allcodes"))
@dp.message(F.text == "🔢 Barcha kodlar")
async def all_codes_handler(message: types.Message):
    """Barcha film kodlarini ko'rsatish"""
    user_id = message.from_user.id
    if user_id != ADMIN_ID:
        await message.answer("❌ Bu buyruq faqat admin uchun!")
        return
    
    movies = get_all_movies()
    if not movies:
        await message.answer("📭 Hozircha filmlar mavjud emas")
        return
    
    response = "🎬 <b>BARCHA FILM KODLARI:</b>\n\n"
    for i, (code, desc) in enumerate(movies, 1):
        desc_lines = desc.split('\n')
        title = desc_lines[0] if desc_lines else "Nomsiz film"
        
        if len(title) > 40:
            title = title[:40] + "..."
        
        response += f"{i}. <b>{title}</b>\n"
        response += f"   🔢 Kodi: <code>{code}</code>\n\n"
    
    response += f"\n📊 Jami: {len(movies)} ta film"
    
    await message.answer(response)

# 🎬 FILM QO'SHISH (YANGI VERSIYA - POSTER BILAN)
@dp.message(Command("addmovie"))
@dp.message(F.text == "🎬 Film qo'shish")
async def add_movie_command(message: types.Message, state: FSMContext):
    """Film qo'shishni boshlash (poster bilan)"""
    user_id = message.from_user.id
    
    if user_id != ADMIN_ID:
        await message.answer("❌ Bu amal faqat admin uchun!")
        return
    
    await message.answer(
        "🎬 <b>Yangi film qo'shish (Poster bilan)</b>\n\n"
        "1. Avval film POSTER rasmini yuboring\n"
        "2. Keyin film VIDEOSINI yuboring\n"
        "3. So'ng film tavsifini yuboring\n\n"
        "❌ Bekor qilish: /cancel",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(AdminMovie.poster)

# POSTER RASMNI QABUL QILISH
@dp.message(AdminMovie.poster, F.photo)
async def get_poster_photo(message: types.Message, state: FSMContext):
    """Film posterini qabul qilish"""
    try:
        # Eng yuqori sifatli rasmni olish
        poster_file = message.photo[-1].file_id
        
        await state.update_data(poster_file=poster_file)
        
        await message.answer(
            "✅ Poster rasm qabul qilindi!\n\n"
            "📹 Endi film VIDEOSINI yuboring:"
        )
        await state.set_state(AdminMovie.movie_file)
        
    except Exception as e:
        logging.error(f"Poster qabul qilish xatosi: {e}")
        await message.answer(f"❌ Xatolik: {str(e)}")
        await state.clear()

@dp.message(AdminMovie.poster)
async def wrong_poster_file(message: types.Message):
    """Noto'g'ri poster fayli"""
    await message.answer(
        "❌ Iltimos, faqat RASM yuboring!\n"
        "Poster rasmini yuboring yoki /cancel deb yozing"
    )

# VIDEONI QABUL QILISH
@dp.message(AdminMovie.movie_file, F.video)
async def get_movie_video(message: types.Message, state: FSMContext):
    """Film videosini qabul qilish"""
    try:
        movie_file = message.video.file_id
        
        await state.update_data(video_file=movie_file)
        
        await message.answer(
            "✅ Video qabul qilindi!\n\n"
            "📝 Endi film TAVSIFINI yuboring:\n"
            "Masalan:\n"
            "Film nomi\n"
            "Janri: Fantastika, Sarguzasht\n"
            "Davomiyligi: 120 daqiqa\n"
            "Til: O'zbekcha tarjima\n"
            "Sifati: HD"
        )
        await state.set_state(AdminMovie.movie_desc)
        
    except Exception as e:
        logging.error(f"Video qabul qilish xatosi: {e}")
        await message.answer(f"❌ Xatolik: {str(e)}")
        await state.clear()

@dp.message(AdminMovie.movie_file)
async def wrong_video_file(message: types.Message):
    """Noto'g'ri video fayli"""
    await message.answer(
        "❌ Iltimos, faqat VIDEO yuboring!\n"
        "MP4 formatidagi videoni yuboring yoki /cancel deb yozing"
    )

# FILM TAVSIFINI QABUL QILISH VA SAQLASH
@dp.message(AdminMovie.movie_desc)
async def get_movie_description(message: types.Message, state: FSMContext):
    """Film tavsifini qabul qilish va bazaga saqlash"""
    try:
        movie_desc = message.text
        
        if len(movie_desc.strip()) < 5:
            await message.answer("❌ Tavsif juda qisqa! Kamida 5 ta belgi bo'lishi kerak.")
            return
        
        # Stateni olish
        data = await state.get_data()
        poster_file = data.get('poster_file')
        video_file = data.get('video_file')
        
        if not poster_file or not video_file:
            await message.answer("❌ Poster yoki video topilmadi! Qaytadan boshlang.")
            await state.clear()
            return
        
        # Film kodi yaratish
        code = generate_move_code()
        
        # Tavsifni formatlash
        lines = movie_desc.split('\n')
        formatted_desc = ""
        
        for line in lines:
            if line.strip():
                formatted_desc += f"{line.strip()}\n"
        
        # Kod va sanani qo'shish
        formatted_desc += f"\n🔢 <b>KINO KODI:</b> <code>{code}</code>\n"
        formatted_desc += f"📅 Qo'shilgan sana: {datetime.now().strftime('%d.%m.%Y')}"
        
        # Bazaga saqlash
        success = await save_movie_with_poster(poster_file, video_file, formatted_desc, code)
        
        if success:
            # Filmi adminga yuborish (poster + video media guruh)
            media_group = [
                InputMediaPhoto(
                    media=poster_file,
                    caption=formatted_desc,
                    parse_mode="HTML"
                ),
                InputMediaVideo(media=video_file)
            ]
            
            await bot.send_media_group(
                chat_id=message.chat.id,
                media=media_group
            )
            
            await message.answer(
                f"✅ <b>Film muvaffaqiyatli yuklandi!</b>\n"
                f"🎬 Kodi: <code>{code}</code>\n"
                f"🖼 Poster bilan birga saqlandi\n\n"
                f"❓ Foydalanuvchilar shu kodni yuborish orqali filmni ko'rishi mumkin.",
                parse_mode="HTML",
                reply_markup=admin_menu()
            )
            
            # KANALGA AVTOMATIK POST QILISH (POSTER + VIDEO)
            if AUTO_POST:
                try:
                    channel_success = await ChannelAutoPost.post_movie_with_poster(
                        bot, video_file, poster_file, formatted_desc, code
                    )
                    if channel_success:
                        await message.answer("✅ Film kanalga ham joylandi! (Poster bilan)")
                    else:
                        await message.answer("⚠️ Kanalga post qilishda xatolik")
                except Exception as e:
                    logging.error(f"Kanal post xatosi: {e}")
                    await message.answer("⚠️ Kanal post qilishda xatolik")
        else:
            await message.answer("❌ Filmni bazaga saqlashda xatolik!")
        
        # Stateni tozalash
        await state.clear()
        
    except Exception as e:
        logging.error(f"Film tavsifini saqlash xatosi: {e}")
        await message.answer(f"❌ Xatolik: {str(e)}")
        await state.clear()

# BEKOR QILISH
@dp.message(Command("cancel"))
async def cancel_handler(message: types.Message, state: FSMContext):
    """Bekor qilish"""
    current_state = await state.get_state()
    if current_state is None:
        return
    
    await state.clear()
    await message.answer("❌ Amal bekor qilindi.", reply_markup=admin_menu())

# ⚙️ SOZLAMALAR
@dp.message(F.text == "⚙️ Sozlamalar")
async def settings_handler(message: types.Message):
    """Bot sozlamalari"""
    user_id = message.from_user.id
    if user_id != ADMIN_ID:
        await message.answer("❌ Bu buyruq faqat admin uchun!")
        return
    
    try:
        bot_info = await bot.get_me()
        bot_username = bot_info.username
    except:
        bot_username = "Noma'lum"
    
    settings_text = f"""
⚙️ <b>Bot Sozlamalari</b>

📢 <b>Kanal:</b> {CHANNEL_USERNAME}
🤖 <b>Bot:</b> @{bot_username}
👑 <b>Admin:</b> {ADMIN_ID}

🔄 <b>Avtomatik post:</b> {'✅ Yoqilgan' if AUTO_POST else '❌ O\'chirilgan'}
🎬 <b>Poster bilan:</b> ✅ Yoqilgan

📊 <b>Statistika:</b> /stats
"""
    
    await message.answer(settings_text)

# 📤 KANAL POST
@dp.message(F.text == "📤 Kanal post")
async def autopost_button_handler(message: types.Message):
    """Avtomatik posting sozlamalari"""
    user_id = message.from_user.id
    if user_id != ADMIN_ID:
        await message.answer("❌ Bu buyruq faqat admin uchun!")
        return
    
    await message.answer(
        f"🎬 <b>Avtomatik Kanal Posting</b>\n\n"
        f"Yangi filmlar avtomatik kanalga joylanadi.\n"
        f"Holat: {'🟢 Yoqilgan' if AUTO_POST else '🔴 O\'chirilgan'}\n"
        f"Format: 🖼 Poster + 📹 Video\n\n"
        f"Kanal: {CHANNEL_USERNAME}"
    )

# ==================== STATISTIKA HANDLERLARI ====================

# 🎲 TASODIFIY FILMLAR
@dp.message(Command("random"))
@dp.message(F.text == "🎲 Tasodifiy")
async def random_movies_handler(message: types.Message):
    """Tasodifiy top filmlarni ko'rsatish"""
    random_movies = get_random_top_movies(5)
    response = format_movie_stats(random_movies, "🎲 Tasodifiy Top 5 Film")
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🔄 Yangi tasodifiy filmlar",
                callback_data="refresh_random"
            )
        ]
    ])
    
    await message.answer(response, reply_markup=keyboard, parse_mode="HTML")

# 🌟 BUGUNGI TOP
@dp.message(Command("today"))
@dp.message(F.text == "🌟 Bugungi top")
async def today_top_handler(message: types.Message):
    """Bugungi top filmlar"""
    today_movies = get_today_top_movies(3)
    response = format_movie_stats(today_movies, "🌟 Bugungi Top Filmlar")
    await message.answer(response, parse_mode="HTML")

# 📊 HAFTALIK TOP
@dp.message(Command("weekly"))
@dp.message(F.text == "📊 Haftalik top")
async def weekly_top_handler(message: types.Message):
    """Haftalik top filmlar"""
    weekly_movies = get_weekly_top_movies(5)
    response = format_movie_stats(weekly_movies, "📊 Haftalik Top 5 Film")
    await message.answer(response, parse_mode="HTML")

# 🎯 SHAXSIY TAVSIYA
@dp.message(Command("recommend"))
@dp.message(F.text == "🎯 Tavsiya")
async def recommend_handler(message: types.Message):
    """Shaxsiy tavsiya"""
    user_id = message.from_user.id
    recommended = get_recommended_movie(user_id)
    
    if recommended:
        code, desc = recommended
        desc_lines = desc.split('\n')
        film_title = desc_lines[0] if desc_lines else "Nomsiz film"
        
        response = f"🎯 <b>Siz uchun tavsiya:</b>\n\n"
        response += f"<b>{film_title}</b>\n"
        response += f"\n🔢 Kino kodi: <code>{code}</code>\n\n"
        response += f"❓ Bu filmni ko'rish uchun shu kodni yuboring"
        
        await message.answer(response, parse_mode="HTML")
    else:
        await message.answer("📭 Tavsiya qilish uchun filmlar mavjud emas")

# 🔙 ASOSIY MENYU
@dp.message(F.text == "🔙 Asosiy menyu")
async def back_button_handler(message: types.Message):
    await message.answer(
        "🔙 Asosiy menyuga qaytdingiz.\n\n🔢 Film kodini yuboring:",
        reply_markup=stats_btn()
    )

# ==================== INLINE CALLBACKLAR ====================

# 🔄 YANGI TASODIFIY FILMLAR
@dp.callback_query(F.data == "refresh_random")
async def refresh_random_handler(callback: CallbackQuery):
    """Yangi tasodifiy filmlarni yuklash"""
    random_movies = get_random_top_movies(5)
    response = format_movie_stats(random_movies, "🎲 Tasodifiy Top 5 Film")
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🔄 Yangi tasodifiy filmlar",
                callback_data="refresh_random"
            )
        ]
    ])
    
    await callback.message.edit_text(response, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer("🔄 Yangi tasodifiy filmlar yuklandi!")

# ==================== QIDIRUV TIZIMI ====================

@dp.message(F.text == "🔎 Qidirish")
async def search_button_handler(message: types.Message, state: FSMContext):
    """Film qidirish"""
    await message.answer(
        "🔍 <b>Film qidirish</b>\n\n"
        "Film nomini yoki janrini yozing:",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(SearchState.waiting_for_query)

@dp.message(SearchState.waiting_for_query)
async def process_search_query(message: types.Message, state: FSMContext):
    """Qidiruv natijalarini ko'rsatish"""
    query = message.text.strip()
    
    if len(query) < 2:
        await message.answer("❌ Iltimos, kamida 2 ta belgi kiriting")
        return
    
    movies = search_movies_by_title(query)
    
    if not movies:
        await message.answer(
            f"❌ '{query}' bo'yicha film topilmadi\n\n"
            f"Qayta urinib ko'ring yoki boshqa so'z kiriting:",
            reply_markup=stats_btn()
        )
        await state.clear()
        return
    
    response = f"🔍 <b>Qidiruv natijalari:</b> '{query}'\n\n"
    
    for i, (code, desc) in enumerate(movies[:10], 1):
        desc_lines = desc.split('\n')
        title = desc_lines[0] if desc_lines else "Nomsiz film"
        
        response += f"{i}. <b>{title}</b>\n"
        response += f"   🔢 Kodi: <code>{code}</code>\n\n"
    
    if len(movies) > 10:
        response += f"... va yana {len(movies) - 10} ta film\n"
    
    response += "\n🔢 Film kodini kiriting yoki qayta qidiring"
    
    await message.answer(response, reply_markup=stats_btn(), parse_mode="HTML")
    await state.clear()

# ==================== YORDAM ====================

@dp.message(Command("help"))
@dp.message(F.text == "ℹ️ Yordam")
async def help_handler(message: types.Message):
    help_text = """
🎬 <b>Kino Bot Buyruqlari:</b>

🚀 <b>/start</b> - Botni ishga tushirish
🎲 <b>/random</b> - Tasodifiy 5 film
🌟 <b>/today</b> - Bugungi top 3 film
📊 <b>/weekly</b> - Haftalik top 5 film
🎯 <b>/recommend</b> - Shaxsiy tavsiya
ℹ️ <b>/help</b> - Yordam ko'rsatish

👑 <b>Admin buyruqlari:</b>
🎬 /addmovie - Film qo'shish (Poster bilan)
📊 /stats - Statistika
🔢 /allcodes - Barcha kodlar

📱 <i>Telefon raqam yuboring yoki film kodini kiriting!</i>
"""
    await message.answer(help_text, parse_mode="HTML")

# ==================== ASOSIY FILM KODI QABUL QILISH ====================

@dp.message(F.text)
async def send_movie_by_code(message: types.Message):
    # Agar bu boshqa komanda bo'lsa
    if message.text.startswith('/'):
        return
    
    # Agar admin menyusida bo'lsa
    admin_buttons = ["🎬 Film qo'shish", "📤 Kanal post", "⚙️ Sozlamalar", 
                    "🔢 Barcha kodlar", "📊 Statistika", "🔙 Asosiy menyu"]
    if message.text in admin_buttons:
        return
    
    # Raqam ekanligini tekshirish
    if not message.text.isdigit():
        # Agar qidiruv boshlanmagan bo'lsa
        await message.answer("🔢 Film kodini kiriting (faqat raqamlar) yoki 🔎 Qidirish tugmasini bosing")
        return
    
    # Filmni bazadan qidirish
    try:
        movie_code = int(message.text)
        movie = get_movie_by_code(movie_code)

        if movie:
            movie_file, movie_desc = movie
            
            keyboard = movie_actions_keyboard(movie_code)
            
            await message.answer_video(
                video=movie_file,
                caption=movie_desc,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
        else:
            await message.answer("❌ Bunday film kodi topilmadi")
    except ValueError:
        await message.answer("❌ Iltimos faqat raqamlardan iborat film kodini yuboring")

# ==================== CALLBACK HANDLERLAR ====================

@dp.callback_query(F.data == "another_movie")
async def another_movie_handler(callback: CallbackQuery):
    await callback.message.answer("🔢 Boshqa film kodini kiriting:")
    await callback.answer()

# ==================== ASOSIY FUNKSIYA ====================

async def main():
    try:
        # Bot tokenini tekshirish
        me = await bot.get_me()
        print(f"✅ Bot faollashtirildi: @{me.username}")
        print(f"✅ Bot ID: {me.id}")
        print(f"✅ Bot nomi: {me.full_name}")
        print(f"✅ Kanal: {CHANNEL_USERNAME}")
        print(f"✅ Admin ID: {ADMIN_ID}")
        print(f"✅ Avtomatik post: {AUTO_POST}")
        
        # Bazani ishga tushirish
        init_db()
        print("✅ Bazani ishga tushirish bajarildi")
        
        # Statistikani ko'rsatish
        total_users = get_total_users_count()
        total_movies = get_total_movies_count()
        print(f"📊 Foydalanuvchilar: {total_users} ta")
        print(f"🎬 Filmlar: {total_movies} ta")
        
        # Botni ishga tushirish
        print("✅ Bot ishga tushmoqda...")
        await dp.start_polling(bot)
        
    except TelegramUnauthorizedError:
        print("❌ Noto'g'ri token! Iltimos, .env faylida to'g'ri token kiriting")
        print("❌ Token olish uchun @BotFather ga murojaat qiling")
    except Exception as e:
        print(f"❌ Xato yuz berdi: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())