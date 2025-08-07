# update_script.py

import requests
import time
from app import create_app, db
from models import MasterRecord

def update_scores_and_popularity():
    """Veritabanındaki tüm kayıtların puanını ve popülerliğini günceller."""
    app = create_app()
    with app.app_context():
        records_to_update = MasterRecord.query.all()
        total_records = len(records_to_update)
        print(f"Toplam {total_records} kayıt güncellenecek...")
        
        # Jikan API hızı: Dakikada 60 istek. Saniyede 1 istek güvenlidir (50/dakika).
        # Her istek arası 1.2 saniye bekleyerek dakikada 50 isteği garantileriz.
        delay_between_requests = 1.2 

        for i, record in enumerate(records_to_update):
            api_type = 'anime' if record.record_type == 'Anime' else 'manga'
            url = f"https://api.jikan.moe/v4/{api_type}/{record.mal_id}"
            
            try:
                print(f"({i+1}/{total_records}) İsteniyor: {record.original_title}...")
                response = requests.get(url)
                response.raise_for_status() # Hatalı isteklerde (404, 500 vb.) hata fırlat
                data = response.json().get('data')
                
                if not data:
                    print(f"Uyarı: {record.original_title} için API'den 'data' alınamadı, atlanıyor.")
                    continue
                
                # Verileri güncelle
                record.score = data.get('score')
                record.popularity = data.get('popularity')
                
                # Değişiklikleri hemen commit'lemek yerine, döngü sonunda toplu halde yapabiliriz.
                # Ancak her birini ayrı commit'lemek, bir hata durumunda öncekilerin kaydedilmesini sağlar.
                db.session.commit()
                print(f"--> Guncellendi: Puan: {record.score}, Popülerlik: {record.popularity}")

            except requests.exceptions.HTTPError as e:
                # API'den 4xx veya 5xx gibi bir hata dönerse (örn. kayıt bulunamadı)
                print(f"HATA ({record.original_title}): HTTP Hatası {e.response.status_code}. Bu kayıt atlanıyor.")
                continue # Hata alınan kaydı atla ve bir sonrakine geç
            except requests.exceptions.RequestException as e:
                # Bağlantı hatası gibi durumlarda
                print(f"HATA ({record.original_title}): Bağlantı Hatası - {e}. Bu kayıt atlanıyor.")
                continue
            except Exception as e:
                # Beklenmedik diğer tüm hatalar için
                print(f"BEKLENMEDİK HATA ({record.original_title}): {e}. Bu kayıt atlanıyor.")
                continue
            
            # Her istek arasında bekle
            time.sleep(delay_between_requests)

        print("Tüm kayıtların güncellenmesi tamamlandı!")

if __name__ == "__main__":
    update_scores_and_popularity()