import sqlite3
from datetime import datetime
from typing import Optional, List, Tuple
import logging

def init_db():
    """Bazani ishga tushirish"""
    conn = sqlite3.connect('movie_bot.db')
    cursor = conn.cursor()
    
    # Foydalanuvchilar jadvali
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            full_name TEXT,
            username TEXT,
            phone_number TEXT,
            registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Filmlar jadvali
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS movies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_id TEXT NOT NULL,
            description TEXT NOT NULL,
            code INTEGER UNIQUE NOT NULL,
            date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Reklama tarixi
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ads_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            ad_type TEXT,
            sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    ''')
    
    # Kanal postlar
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS channel_posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            movie_code INTEGER,
            post_url TEXT,
            posted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (movie_code) REFERENCES movies (code)
        )
    ''')
    
    # Qidiruv statistikasi
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS search_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            query TEXT,
            searched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    logging.info("✅ Baza ishga tushirildi")

# ==================== FOYDALANUVCHILAR ====================

def add_user(user_id: int, full_name: str, username: str, phone_number: str) -> bool:
    """Foydalanuvchi qo'shish"""
    try:
        conn = sqlite3.connect('movie_bot.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO users (user_id, full_name, username, phone_number)
            VALUES (?, ?, ?, ?)
        ''', (user_id, full_name, username, phone_number))
        
        conn.commit()
        conn.close()
        logging.info(f"✅ Foydalanuvchi qo'shildi: {user_id}")
        return True
    except Exception as e:
        logging.error(f"Foydalanuvchi qo'shish xatosi: {e}")
        return False

def get_user(user_id: int) -> Optional[Tuple]:
    """Foydalanuvchini olish"""
    try:
        conn = sqlite3.connect('movie_bot.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        user = cursor.fetchone()
        
        conn.close()
        return user
    except Exception as e:
        logging.error(f"Foydalanuvchi olish xatosi: {e}")
        return None

def get_all_users() -> List[int]:
    """Barcha foydalanuvchilar ID larini olish"""
    try:
        conn = sqlite3.connect('movie_bot.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT user_id FROM users')
        users = [row[0] for row in cursor.fetchall()]
        
        conn.close()
        return users
    except Exception as e:
        logging.error(f"Barcha foydalanuvchilar olish xatosi: {e}")
        return []

def get_total_users_count() -> int:
    """Jami foydalanuvchilar soni"""
    try:
        conn = sqlite3.connect('movie_bot.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM users')
        count = cursor.fetchone()[0]
        
        conn.close()
        return count
    except Exception as e:
        logging.error(f"Foydalanuvchilar soni olish xatosi: {e}")
        return 0

# ==================== FILMLAR ====================

def add_movie(file_id: str, description: str, code: int) -> bool:
    """Film qo'shish"""
    try:
        conn = sqlite3.connect('movie_bot.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO movies (file_id, description, code)
            VALUES (?, ?, ?)
        ''', (file_id, description, code))
        
        conn.commit()
        conn.close()
        logging.info(f"✅ Film qo'shildi: {code}")
        return True
    except Exception as e:
        logging.error(f"Film qo'shish xatosi: {e}")
        return False

def get_movie_by_code(code: int) -> Optional[Tuple]:
    """Filmni kod orqali olish"""
    try:
        conn = sqlite3.connect('movie_bot.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT file_id, description FROM movies WHERE code = ?', (code,))
        movie = cursor.fetchone()
        
        conn.close()
        return movie
    except Exception as e:
        logging.error(f"Film olish xatosi: {e}")
        return None

def get_all_movies() -> List[Tuple]:
    """Barcha filmlarni olish"""
    try:
        conn = sqlite3.connect('movie_bot.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT code, description FROM movies ORDER BY id DESC')
        movies = cursor.fetchall()
        
        conn.close()
        return movies
    except Exception as e:
        logging.error(f"Barcha filmlar olish xatosi: {e}")
        return []

def get_total_movies_count() -> int:
    """Jami film soni"""
    try:
        conn = sqlite3.connect('movie_bot.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM movies')
        count = cursor.fetchone()[0]
        
        conn.close()
        return count
    except Exception as e:
        logging.error(f"Filmlar soni olish xatosi: {e}")
        return 0

def get_movies_by_page(page: int, limit: int) -> List[Tuple]:
    """Sahifalab film olish"""
    try:
        offset = (page - 1) * limit
        conn = sqlite3.connect('movie_bot.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT code, description FROM movies 
            ORDER BY id DESC 
            LIMIT ? OFFSET ?
        ''', (limit, offset))
        
        movies = cursor.fetchall()
        conn.close()
        return movies
    except Exception as e:
        logging.error(f"Sahifalab film olish xatosi: {e}")
        return []

def get_recent_movies(limit: int = 5) -> List[Tuple]:
    """So'nggi qo'shilgan filmlar"""
    try:
        conn = sqlite3.connect('movie_bot.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT code, description, date_added 
            FROM movies 
            ORDER BY date_added DESC 
            LIMIT ?
        ''', (limit,))
        
        movies = cursor.fetchall()
        conn.close()
        return movies
    except Exception as e:
        logging.error(f"So'nggi filmlar olish xatosi: {e}")
        return []

def search_movies_by_title(keyword: str) -> List[Tuple]:
    """Film nomi bo'yicha qidirish"""
    try:
        conn = sqlite3.connect('movie_bot.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT code, description 
            FROM movies 
            WHERE description LIKE ? 
            ORDER BY date_added DESC
        ''', (f'%{keyword}%',))
        
        movies = cursor.fetchall()
        conn.close()
        return movies
    except Exception as e:
        logging.error(f"Film qidirish xatosi: {e}")
        return []

def get_today_movies_count() -> int:
    """Bugungi qo'shilgan filmlar soni"""
    try:
        conn = sqlite3.connect('movie_bot.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT COUNT(*) FROM movies 
            WHERE DATE(date_added) = DATE('now')
        ''')
        
        count = cursor.fetchone()[0]
        conn.close()
        return count
    except Exception as e:
        logging.error(f"Bugungi filmlar soni xatosi: {e}")
        return 0

# ==================== REKLAMA VA STATISTIKA ====================

def add_ad_record(user_id: int, ad_type: str):
    """Reklama yuborish tarixini qo'shish"""
    try:
        conn = sqlite3.connect('movie_bot.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO ads_history (user_id, ad_type)
            VALUES (?, ?)
        ''', (user_id, ad_type))
        
        conn.commit()
        conn.close()
    except Exception as e:
        logging.error(f"Reklama tarixi xatosi: {e}")

def get_ad_stats() -> dict:
    """Reklama statistikasi"""
    try:
        conn = sqlite3.connect('movie_bot.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM ads_history')
        total_ads = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(DISTINCT user_id) FROM ads_history')
        reached_users = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total_ads': total_ads,
            'reached_users': reached_users
        }
    except Exception as e:
        logging.error(f"Reklama statistikasi xatosi: {e}")
        return {'total_ads': 0, 'reached_users': 0}

# ==================== KANAL POSTLARI ====================

def add_channel_post(movie_code: int, post_url: str):
    """Kanal postini qo'shish"""
    try:
        conn = sqlite3.connect('movie_bot.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO channel_posts (movie_code, post_url)
            VALUES (?, ?)
        ''', (movie_code, post_url))
        
        conn.commit()
        conn.close()
        logging.info(f"✅ Kanal posti qo'shildi: {movie_code}")
    except Exception as e:
        logging.error(f"Kanal posti qo'shish xatosi: {e}")

def get_channel_posts_count() -> int:
    """Kanal postlari soni"""
    try:
        conn = sqlite3.connect('movie_bot.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM channel_posts')
        count = cursor.fetchone()[0]
        
        conn.close()
        return count
    except Exception as e:
        logging.error(f"Kanal postlari soni xatosi: {e}")
        return 0