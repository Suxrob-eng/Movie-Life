import asyncio
from aiogram import Bot
from aiogram.types import Message
from database import get_all_users
import logging

class ReklamaManager:
    @staticmethod
    async def send_reklama_to_all(bot: Bot, message: Message, delay: float = 0.5):
        """Barcha foydalanuvchilarga reklama yuborish"""
        users = get_all_users()
        total = len(users)
        success = 0
        failed = 0
        blocked = 0
        
        status_msg = await message.answer(f"📤 Reklama jo'natilmoqda...\n📊 Jami: {total} ta foydalanuvchi")
        
        for user_id in users:
            try:
                # Original xabarni copy qilish
                if message.video:
                    await bot.send_video(
                        chat_id=user_id,
                        video=message.video.file_id,
                        caption=message.caption if message.caption else "",
                        reply_markup=message.reply_markup
                    )
                elif message.photo:
                    await bot.send_photo(
                        chat_id=user_id,
                        photo=message.photo[-1].file_id,
                        caption=message.caption if message.caption else "",
                        reply_markup=message.reply_markup
                    )
                elif message.document:
                    await bot.send_document(
                        chat_id=user_id,
                        document=message.document.file_id,
                        caption=message.caption if message.caption else "",
                        reply_markup=message.reply_markup
                    )
                else:
                    await bot.send_message(
                        chat_id=user_id,
                        text=message.text if message.text else message.caption,
                        reply_markup=message.reply_markup,
                        parse_mode="HTML"
                    )
                success += 1
                
                # Statistikani yangilash
                if (success + failed) % 10 == 0:
                    await status_msg.edit_text(
                        f"📤 Reklama jo'natilmoqda...\n\n"
                        f"✅ Muvaffaqiyatli: {success}\n"
                        f"❌ Xato: {failed}\n"
                        f"🚫 Bloklagan: {blocked}\n"
                        f"📦 Jami: {total}"
                    )
                
                await asyncio.sleep(delay)  # Spamdan saqlash
                
            except Exception as e:
                failed += 1
                if "blocked" in str(e).lower() or "deactivated" in str(e).lower():
                    blocked += 1
                logging.error(f"Reklama xatosi {user_id}: {e}")
        
        # Yakuniy natija
        result_text = (
            f"✅ <b>Reklama jo'natish yakunlandi!</b>\n\n"
            f"📊 <b>Natijalar:</b>\n"
            f"✅ <b>Muvaffaqiyatli:</b> {success} ta\n"
            f"❌ <b>Xato:</b> {failed} ta\n"
            f"🚫 <b>Bloklagan:</b> {blocked} ta\n"
            f"📦 <b>Jami:</b> {total} ta\n\n"
            f"📈 <b>Muvaffaqiyat darajasi:</b> {success/total*100:.1f}%"
        )
        
        await status_msg.edit_text(result_text, parse_mode="HTML")
    
    @staticmethod
    def format_ad_preview(message: Message):
        """Reklama oldindan ko'rish formati"""
        if message.video:
            return f"🎥 Video: {message.video.file_name if message.video.file_name else 'Video'}"
        elif message.photo:
            return f"🖼 Rasm: {message.caption[:50] if message.caption else 'Rasm'}"
        elif message.document:
            return f"📎 Fayl: {message.document.file_name}"
        else:
            return f"📝 Text: {message.text[:100] if message.text else 'Xabar'}"