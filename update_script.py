# update_script.py

import requests
import time
from app import create_app, db
from models import MasterRecord

def update_dynamic_data():
    """Veritabanındaki tüm kayıtların dinamik verilerini (puan, popülerlik, oy sayısı) günceller."""
    app = create_app()
    with app.app_context():
        records_to_update = MasterRecord.query.all()
        total_records = len(records_to_update)
        print(f"Toplam {total_records} kayıt güncellenecek...")
        
        # Jikan API hızı: Dakikada 60 istek. Saniyede 1 istek güvenlidir.
        # Her istek arası 1.2 saniye bekleyerek dakikada 50 isteği garantileriz.
        delay_between_requests = 1.2 

        for i, record in enumerate(records_to_update):
            # Sadece Anime ve Manga türündeki kayıtların Jikan API'si var.
            if record.record_type not in ['Anime', 'Manga']:
                print(f"({i+1}/{total_records}) Atlanıyor (Tür Anime/Manga değil): {record.original_title}")
                continue

            api_type = 'anime' if record.record_type == 'Anime' else 'manga'
            url = f"https://api.jikan.moe/v4/{api_type}/{record.mal_id}"
            
            try:
                print(f"({i+1}/{total_records}) İsteniyor: {record.original_title}...")
                response = requests.get(url)
                response.raise_for_status() # Hatalı isteklerde (404, 500 vb.) hata fırlat
                data = response.json().get('data')
                
                if not data:
                    print(f"--> Uyarı: {record.original_title} için API'den 'data' alınamadı, atlanıyor.")
                    continue
                
                # Verileri güncelle (dinamik alanlar + yeni alanlar)
                record.score = data.get('score')
                record.popularity = data.get('popularity')
                record.scored_by = data.get('scored_by')
                record.members = data.get('members')
                record.favorites = data.get('favorites')

                # Status ve yayın tarihleri: geçişleri yakala
                aired = data.get('aired') or {}
                from_date = aired.get('from')
                to_date = aired.get('to')
                record.aired_from = from_date or record.aired_from
                record.aired_to = to_date or record.aired_to
                # Themes (bazı serilerde returns under "themes" array)
                theme_names = []
                for t in (data.get('themes') or []):
                    name = t.get('name') if isinstance(t, dict) else None
                    if name: theme_names.append(name)
                if theme_names:
                    record.themes = ", ".join(sorted(set(theme_names)))

                # Status değişimi (Currently Airing -> Finished Airing gibi)
                status_from_api = data.get('status')
                record.status = status_from_api or record.status
                
                print(f"--> Guncellendi: Puan: {record.score}, Popülerlik: {record.popularity}, Oylayan: {record.scored_by}, Status: {record.status}")
                
                # Her başarılı güncellemeden sonra commit'lemek, bir hata durumunda
                # önceki başarılı işlemleri korur.
                db.session.commit()

            except requests.exceptions.HTTPError as e:
                # API'den 4xx veya 5xx gibi bir hata dönerse (örn. kayıt bulunamadı, çok fazla istek)
                print(f"--> HATA ({record.original_title}): HTTP Hatası {e.response.status_code}. Bu kayıt atlanıyor.")
                db.session.rollback() # Olası session problemlerini önlemek için
                continue
            except requests.exceptions.RequestException as e:
                # Bağlantı hatası gibi durumlarda
                print(f"--> HATA ({record.original_title}): Bağlantı Hatası - {e}. Bu kayıt atlanıyor.")
                db.session.rollback()
                continue
            except Exception as e:
                # Beklenmedik diğer tüm hatalar için
                print(f"--> BEKLENMEDİK HATA ({record.original_title}): {e}. Bu kayıt atlanıyor.")
                db.session.rollback()
                continue
            
            # Her istek arasında bekle
            time.sleep(delay_between_requests)

        print("Tüm kayıtların güncellenmesi tamamlandı!")

if __name__ == "__main__":
    update_dynamic_data()