# Kurolist

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-2.0+-green.svg)](https://flask.palletsprojects.com)
[![SQLite](https://img.shields.io/badge/SQLite-3.0+-yellow.svg)](https://sqlite.org)
[![License](https://img.shields.io/badge/License-MIT-orange.svg)](LICENSE)

---

## 🇹🇷 Türkçe

### 📖 Proje Hakkında

Kurolist, anime ve manga tutkunları için geliştirilmiş kapsamlı bir liste yönetim sistemidir. Kullanıcılar anime/manga koleksiyonlarını organize edebilir, puanlayabilir ve takip edebilir. MyAnimeList'ten veri içe aktarma özelliği ile mevcut listenizi kolayca taşıyabilirsiniz.

### ✨ Özellikler

- 🎯 **Gelişmiş Arama**: Başlık, tür, tema, demografik grup ve stüdyoya göre filtreleme
- 📚 **Liste Yönetimi**: İzleme durumu, bölüm takibi, puanlama ve notlar
- 🔄 **MAL İçe Aktarım**: MyAnimeList XML export dosyalarını otomatik içe aktarma
- 🌍 **Çok Dilli Destek**: Türkçe ve İngilizce dil desteği
- 🎨 **Modern UI/UX**: Responsive tasarım ve tema değiştirme
- 📊 **İstatistikler**: Pasta grafik ile liste durumu görselleştirmesi
- 👑 **Top Listesi**: Weighted score algoritması ile en iyi anime/manga sıralaması
- 🔐 **Kullanıcı Yönetimi**: Güvenli kayıt ve giriş sistemi
- ⚡ **Sonsuz Kaydırma**: Performanslı sayfalama ile hızlı gezinme

### 🛠️ Teknolojiler

- **Backend**: Flask, SQLAlchemy, Alembic
- **Veritabanı**: SQLite
- **Frontend**: HTML5, CSS3, JavaScript (ES6+)
- **Çeviri**: Flask-Babel
- **API**: Jikan API (MyAnimeList)
- **Grafik**: Chart.js
- **Stil**: CSS Grid, Flexbox, CSS Variables

### 🚀 Kurulum

#### Gereksinimler
- Python 3.8+
- pip
- Git

#### Adımlar

1. **Repository'yi klonlayın**
```bash
git clone https://github.com/kullaniciadi/kurolist.git
cd kurolist
```

2. **Sanal ortam oluşturun**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# veya
venv\Scripts\activate     # Windows
```

3. **Bağımlılıkları yükleyin**
```bash
pip install -r requirements.txt
```

4. **Çevre değişkenlerini ayarlayın**
```bash
# .env dosyası oluşturun
touch .env  # Linux/Mac
# veya
echo. > .env  # Windows

# .env dosyasına aşağıdaki değişkenleri ekleyin:
SECRET_KEY=your-super-secret-key-change-this-in-production
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=your-email@gmail.com
```

5. **Veritabanını başlatın**
```bash
flask db upgrade
```

6. **Uygulamayı çalıştırın**
```bash
python app.py
```

Uygulama `http://localhost:5000` adresinde çalışacaktır.

### 📁 Proje Yapısı

```
kurolist/
├── app.py                 # Ana Flask uygulaması
├── main.py               # Ana blueprint ve route'lar
├── auth.py               # Kimlik doğrulama sistemi
├── admin.py              # Admin paneli
├── models.py             # Veritabanı modelleri
├── forms.py              # Form sınıfları
├── extensions.py         # Flask extension'ları
├── static/               # Statik dosyalar
│   ├── css/             # Stil dosyaları
│   └── js/              # JavaScript dosyaları
├── templates/            # HTML şablonları
├── migrations/           # Veritabanı migration'ları
└── translations/         # Çeviri dosyaları
```

### 🔧 Konfigürasyon

#### Çevre Değişkenleri

```env
SECRET_KEY=your-secret-key-here
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=your-email@gmail.com
```

#### Veritabanı

Uygulama varsayılan olarak SQLite kullanır. PostgreSQL veya MySQL kullanmak için `app.py` dosyasındaki `SQLALCHEMY_DATABASE_URI`'yi güncelleyin.

### 📱 Kullanım

#### Kullanıcı İşlemleri
1. **Kayıt Ol**: `/auth/register` adresinden hesap oluşturun
2. **Giriş Yap**: `/auth/login` adresinden giriş yapın
3. **Profil**: `/profile` adresinden istatistiklerinizi görün

#### Liste Yönetimi
1. **Arama**: `/search` adresinden anime/manga arayın
2. **Listeye Ekle**: Arama sonuçlarından istediğinizi listeye ekleyin
3. **Listemi Görüntüle**: `/my-list` adresinden listenizi yönetin
4. **Güncelle**: Durum, bölüm ve puan bilgilerini güncelleyin

#### MAL İçe Aktarım
1. MyAnimeList'ten XML export dosyası indirin
2. `/my-list` sayfasından "MAL İçe Aktar" butonuna tıklayın
3. XML dosyasını yükleyin ve seçenekleri belirleyin
4. İçe aktarımı başlatın

### 🔌 API Endpoints

#### Arama API
- `GET /api/advanced-search` - Gelişmiş arama
- `GET /api/record/<id>` - Kayıt detayları

#### Liste API
- `POST /list/add/<id>` - Listeye ekle
- `POST /list/update/<id>` - Liste öğesini güncelle
- `POST /list/delete/<id>` - Liste öğesini sil

#### İçe Aktarım API
- `POST /import/mal` - MAL XML dosyası içe aktarımı

### 🎨 Tema Sistemi

Uygulama otomatik olarak sistem temasını algılar ve manuel tema değiştirme seçeneği sunar:
- 🌙 Koyu tema (varsayılan)
- ☀️ Açık tema

### 📊 İstatistikler

Profil sayfasında şu istatistikleri görebilirsiniz:
- Toplam anime/manga sayısı
- Durum bazında dağılım (pasta grafik)
- Ortalama puan
- Toplam izlenen bölüm sayısı

### 🚀 Deployment

#### Production Sunucu
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

#### Docker (önerilen)
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "app:app"]
```

### 🤝 Katkıda Bulunma

1. Fork yapın
2. Feature branch oluşturun (`git checkout -b feature/amazing-feature`)
3. Değişikliklerinizi commit edin (`git commit -m 'Add amazing feature'`)
4. Branch'inizi push edin (`git push origin feature/amazing-feature`)
5. Pull Request oluşturun

### 📝 Lisans

Bu proje MIT lisansı altında lisanslanmıştır. Detaylar için `LICENSE` dosyasına bakın.

### 📞 İletişim

- **Canlı Site**: [https://kurolist.xyz](https://kurolist.xyz)
- **GitHub Repository**: [https://github.com/kullaniciadi/kurolist](https://github.com/kullaniciadi/kurolist)
- **Sorun Bildirimi**: [Issues](https://github.com/kullaniciadi/kurolist/issues)

---

## 🇺🇸 English

### 📖 About the Project

Kurolist is a comprehensive list management system developed for anime and manga enthusiasts. Users can organize, rate, and track their anime/manga collections. With the MyAnimeList data import feature, you can easily transfer your existing list.

### ✨ Features

- 🎯 **Advanced Search**: Filter by title, genre, theme, demographic group, and studio
- 📚 **List Management**: Watch status, episode tracking, rating, and notes
- 🔄 **MAL Import**: Automatic import of MyAnimeList XML export files
- 🌍 **Multi-language Support**: Turkish and English language support
- 🎨 **Modern UI/UX**: Responsive design and theme switching
- 📊 **Statistics**: Visual representation of list status with pie charts
- 👑 **Top List**: Best anime/manga ranking with weighted score algorithm
- 🔐 **User Management**: Secure registration and login system
- ⚡ **Infinite Scroll**: Fast navigation with efficient pagination

### 🛠️ Technologies

- **Backend**: Flask, SQLAlchemy, Alembic
- **Database**: SQLite
- **Frontend**: HTML5, CSS3, JavaScript (ES6+)
- **Translation**: Flask-Babel
- **API**: Jikan API (MyAnimeList)
- **Charts**: Chart.js
- **Styling**: CSS Grid, Flexbox, CSS Variables

### 🚀 Installation

#### Requirements
- Python 3.8+
- pip
- Git

#### Steps

1. **Clone the repository**
```bash
git clone https://github.com/username/kurolist.git
cd kurolist
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Set environment variables**
```bash
# Create .env file
touch .env  # Linux/Mac
# or
echo. > .env  # Windows

# Add the following variables to .env file:
SECRET_KEY=your-super-secret-key-change-this-in-production
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=your-email@gmail.com
```

5. **Initialize database**
```bash
flask db upgrade
```

6. **Run the application**
```bash
python app.py
```

The application will run at `http://localhost:5000`.

### 📁 Project Structure

```
kurolist/
├── app.py                 # Main Flask application
├── main.py               # Main blueprint and routes
├── auth.py               # Authentication system
├── admin.py              # Admin panel
├── models.py             # Database models
├── forms.py              # Form classes
├── extensions.py         # Flask extensions
├── static/               # Static files
│   ├── css/             # Style files
│   └── js/              # JavaScript files
├── templates/            # HTML templates
├── migrations/           # Database migrations
└── translations/         # Translation files
```

### 🔧 Configuration

#### Environment Variables

```env
SECRET_KEY=your-secret-key-here
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=your-email@gmail.com
```

#### Database

The application uses SQLite by default. To use PostgreSQL or MySQL, update the `SQLALCHEMY_DATABASE_URI` in `app.py`.

### 📱 Usage

#### User Operations
1. **Register**: Create an account at `/auth/register`
2. **Login**: Sign in at `/auth/login`
3. **Profile**: View your statistics at `/profile`

#### List Management
1. **Search**: Search for anime/manga at `/search`
2. **Add to List**: Add desired items to your list from search results
3. **View My List**: Manage your list at `/my-list`
4. **Update**: Update status, episode, and rating information

#### MAL Import
1. Download XML export file from MyAnimeList
2. Click "MAL Import" button from `/my-list` page
3. Upload XML file and select options
4. Start import

### 🔌 API Endpoints

#### Search API
- `GET /api/advanced-search` - Advanced search
- `GET /api/record/<id>` - Record details

#### List API
- `POST /list/add/<id>` - Add to list
- `POST /list/update/<id>` - Update list item
- `POST /list/delete/<id>` - Delete list item

#### Import API
- `POST /import/mal` - MAL XML file import

### 🎨 Theme System

The application automatically detects system theme and provides manual theme switching option:
- 🌙 Dark theme (default)
- ☀️ Light theme

### 📊 Statistics

You can view the following statistics on the profile page:
- Total anime/manga count
- Status-based distribution (pie chart)
- Average rating
- Total watched episodes count

### 🚀 Deployment

#### Production Server
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

#### Docker (recommended)
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "app:app"]
```

### 🤝 Contributing

1. Fork the project
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### 📝 License

This project is licensed under the MIT License. See the `LICENSE` file for details.

### 📞 Contact

- **Live Site**: [https://kurolist.xyz](https://kurolist.xyz)
- **GitHub Repository**: [https://github.com/username/kurolist](https://github.com/username/kurolist)
- **Issue Reporting**: [Issues](https://github.com/username/kurolist/issues)

---

## 🌟 Star History

[![Star History Chart](https://api.star-history.com/svg?repos=username/kurolist&type=Date)](https://star-history.com/#username/kurolist&Date)

---

<div align="center">
Made with ❤️ for the anime/manga community
</div>
