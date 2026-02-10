import os
from aiogram import Bot
from aiogram.types import InputMediaPhoto, InputMediaVideo
from config import CHANNEL_USERNAME, AUTO_POST
import logging

class ChannelAutoPost:
    @staticmethod
    async def post_to_channel(bot: Bot, movie_file: str, description: str, code: int):
        """Filmlarni kanalga avtomatik joylash"""
        if not AUTO_POST:
            logging.info("Avtomatik post o'chirilgan")
            return False
        
        try:
            # Tavsifni formatlash
            final_desc = f"{description}\n\n" \
                        f"🎬 @{bot.username}\n" \
                        f"🔢 Film kodi: {code}\n" \
                        f"📢 {CHANNEL_USERNAME}\n" \
                        f"#KinoKodi_{code} #Film #Kino"
            
            # Kanalga post qilish
            await bot.send_video(
                chat_id=CHANNEL_USERNAME,
                video=movie_file,
                caption=final_desc,
                parse_mode="HTML"
            )
            
            logging.info(f"Film {code} kanalga joylandi")
            return True
            
        except Exception as e:
            logging.error(f"Kanal post xatosi: {e}")
            return False
    
    @staticmethod
    async def post_movie_with_poster(bot: Bot, video_file: str, poster_file: str, description: str, code: int):
        """Poster va video bilan kanalga post qilish"""
        if not AUTO_POST:
            return False
        
        try:
            final_desc = f"{description}\n\n" \
                        f"🎬 To'liq video: @{bot.username}\n" \
                        f"🔢 Film kodi: {code}\n" \
                        f"📢 {CHANNEL_USERNAME}\n" \
                        f"#Film #Kino #{code}"
            
            # Media guruh (poster + video)
            media_group = [
                InputMediaPhoto(
                    media=poster_file,
                    caption=final_desc,
                    parse_mode="HTML"
                ),
                InputMediaVideo(media=video_file)
            ]
            
            await bot.send_media_group(
                chat_id=CHANNEL_USERNAME,
                media=media_group
            )
            
            return True
        except Exception as e:
            logging.error(f"Media group post xatosi: {e}")
            return False
    
    @staticmethod
    async def send_daily_update(bot: Bot):
        """Kundalik yangiliklarni kanalga jo'natish"""
        try:
            from database import get_total_movies_count, get_recent_movies
            from datetime import datetime
            
            total_movies = get_total_movies_count()
            recent_movies = get_recent_movies(3)
            
            update_text = f"🎬 <b>Kundalik Yangiliklar</b>\n\n" \
                         f"📅 {datetime.now().strftime('%d.%m.%Y')}\n" \
                         f"🎥 Jami filmlar: {total_movies} ta\n\n" \
                         f"<b>So'nggi qo'shilgan filmlar:</b>\n"
            
            for i, (code, desc, _) in enumerate(recent_movies, 1):
                lines = desc.split('\n')
                title = lines[0] if lines else "Nomsiz film"
                update_text += f"{i}. {title}\n   🔢 {code}\n"
            
            update_text += f"\n📲 @{bot.username}\n📢 {CHANNEL_USERNAME}"
            
            await bot.send_message(
                chat_id=CHANNEL_USERNAME,
                text=update_text,
                parse_mode="HTML"
            )
            
        except Exception as e:
            logging.error(f"Daily update xatosi: {e}")