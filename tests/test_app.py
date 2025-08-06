# tests/test_app.py (Final Hali)

from flask import get_flashed_messages
from models import db, User, MasterRecord, UserList
import pytest

# --- KİMLİK DOĞRULAMA TESTLERİ ---

def test_register_and_login(client):
    """Test A1 & A4: Yeni kullanıcı kaydı ve giriş yapma."""
    response = client.post('/auth/register', data={
        'username': 'newuser', 'email': 'new@example.com',
        'password': 'password123', 'confirm_password': 'password123'
    }, follow_redirects=True)
    assert response.status_code == 200
    # Flash mesajını session'dan kontrol et
    with client.session_transaction() as session:
        flashes = session.get('_flashes', [])
        assert any('Onay linki' in message[1] for message in flashes)

    user = User.query.filter_by(email='new@example.com').first()
    assert user is not None
    user.confirmed = True
    db.session.commit()

    response = client.post('/auth/login', data={
        'login': 'newuser', 'password': 'password123'
    }, follow_redirects=True)
    assert response.status_code == 200
    # response.data'yı string'e çevirerek kontrol et
    assert 'Panelim' in response.get_data(as_text=True)
    assert 'Merhaba, newuser!' in response.get_data(as_text=True)

def test_duplicate_registration(client, new_user):
    """Test A3: Mevcut bilgilerle kayıt olmaya çalışma."""
    db.session.add(new_user)
    db.session.commit()

    response = client.post('/auth/register', data={
        'username': 'anotheruser', 'email': 'test@example.com',
        'password': 'password123', 'confirm_password': 'password123'
    }) # follow_redirects=False, çünkü hata aynı sayfada gösterilir
    assert response.status_code == 200
    assert 'Bu e-posta adresi zaten kullanılıyor.' in response.get_data(as_text=True)

# --- ERİŞİM KONTROLÜ TESTLERİ ---

def test_admin_access(client, new_user, new_admin):
    """Test A5 & B: Admin ve normal kullanıcı erişim kontrolü."""
    db.session.add(new_user)
    db.session.add(new_admin)
    db.session.commit()

    client.post('/auth/login', data={'login': 'testuser', 'password': 'password123'})
    response = client.get('/admin/dashboard', follow_redirects=True)
    assert response.status_code == 200
    assert 'Bu sayfaya erişim yetkiniz yok.' in response.get_data(as_text=True)
    client.get('/auth/logout')

    client.post('/auth/login', data={'login': 'adminuser', 'password': 'password123'})
    response = client.get('/admin/dashboard', follow_redirects=True)
    assert response.status_code == 200
    assert 'Admin Paneli' in response.get_data(as_text=True)

# --- ANA FONKSİYONLAR TESTLERİ ---

@pytest.fixture()
def setup_data(client, new_admin, new_user):
    """Her test için admin, kullanıcı ve master kayıt oluşturan yardımcı fixture."""
    db.session.add(new_admin)
    db.session.add(new_user)
    db.session.commit()

    client.post('/auth/login', data={'login': 'adminuser', 'password': 'password123'})
    client.post('/admin/api/record/add', data={
        'original_title': 'Solo Leveling', 'english_title': 'Only I Level Up',
        'record_type': 'Manhwa'
    })
    client.get('/auth/logout')
    client.post('/auth/login', data={'login': 'testuser', 'password': 'password123'})

def test_user_list_flow(client, setup_data):
    """Test C1, C2, C3: Arama, ekleme, güncelleme ve silme."""
    
    response = client.get('/api/search?q=solo')
    assert response.status_code == 200
    record_id = response.get_json()[0]['id']

    client.post(f'/list/add/{record_id}')
    list_item = UserList.query.first()
    assert list_item is not None and list_item.status == 'Planlandı'

    update_data = {'status': 'Okunuyor', 'current_chapter': 120, 'notes': 'Test notu'}
    client.post(f'/list/update/{list_item.id}', json=update_data)
    updated_item = UserList.query.get(list_item.id)
    assert updated_item.status == 'Okunuyor' and updated_item.notes == 'Test notu'

    client.post(f'/list/delete/{list_item.id}')
    deleted_item = UserList.query.get(list_item.id)
    assert deleted_item is None