import random
from datetime import datetime
import json
import os

def generate_move_code():
    """3 xonali unikal film kodi"""
    sonlar = []
    while len(sonlar) < 3:
        son = random.randint(0, 9)
        if son not in sonlar:
            sonlar.append(son)
    kod = str(sonlar[0]) + str(sonlar[1]) + str(sonlar[2])
    return kod

def generate_bulk_codes(count: int = 10):
    """Bir vaqtning o'zida ko'p kodlar yaratish"""
    codes = []
    for _ in range(count):
        while True:
            code = generate_move_code()
            if code not in codes:
                codes.append(code)
                break
    return codes

def get_all_codes_formatted():
    """Barcha film kodlarini chiroyli formatda olish"""
    from database import get_all_movies
    
    movies = get_all_movies()
    if not movies:
        return "📭 Hozircha filmlar mavjud emas"
    
    response = "🎬 <b>BARCHA FILM KODLARI:</b>\n\n"
    for i, (code, desc) in enumerate(movies, 1):
        desc_lines = desc.split('\n')
        title = desc_lines[0] if desc_lines else "Nomsiz film"
        
        # Qisqartirilgan sarlavha
        if len(title) > 40:
            title = title[:40] + "..."
        
        response += f"{i}. <b>{title}</b>\n"
        response += f"   🔢 Kodi: <code>{code}</code>\n\n"
    
    response += f"\n📊 Jami: {len(movies)} ta film"
    return response

def export_codes_to_file():
    """Kodlarni faylga eksport qilish"""
    from database import get_all_movies
    
    movies = get_all_movies()
    if not movies:
        return None
    
    # Fayl nomini yaratish
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"film_codes_{timestamp}.txt"
    
    # Faylga yozish
    with open(filename, 'w', encoding='utf-8') as f:
        f.write("🎬 FILM KODLARI RO'YXATI\n")
        f.write("=" * 50 + "\n")
        f.write(f"🗓 Sana: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n")
        f.write("=" * 50 + "\n\n")
        
        for i, (code, desc) in enumerate(movies, 1):
            desc_lines = desc.split('\n')
            title = desc_lines[0] if desc_lines else "Nomsiz film"
            
            f.write(f"{i}. {title}\n")
            f.write(f"   Kodi: {code}\n")
            
            # Janrni topish
            for line in desc_lines:
                if "Janri:" in line:
                    genre = line.split("Janri:")[1].strip()
                    f.write(f"   Janri: {genre}\n")
                    break
            
            f.write("\n")
    
    return filename

def get_codes_by_genre(genre: str):
    """Janr bo'yicha film kodlari"""
    from database import get_all_movies
    
    movies = get_all_movies()
    if not movies:
        return []
    
    genre_codes = []
    for code, desc in movies:
        desc_lines = desc.split('\n')
        for line in desc_lines:
            if "Janri:" in line and genre.lower() in line.lower():
                genre_codes.append((code, desc))
                break
    
    return genre_codes

def get_random_codes(count: int = 5):
    """Tasodifiy film kodlari"""
    from database import get_all_movies
    
    movies = get_all_movies()
    if not movies:
        return []
    
    if count >= len(movies):
        return movies
    
    return random.sample(movies, count)