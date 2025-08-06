// static/js/admin.js (Yeni Dosya)

document.addEventListener('DOMContentLoaded', function() {

    // --- ELEMENT SEÇİMLERİ ---
    const listContainer = document.getElementById('admin-records-list');
    const searchBox = document.getElementById('admin-search-box');
    const addNewBtn = document.getElementById('add-new-record-btn');
    const entryModal = document.getElementById('entry-modal');
    
    if (!entryModal) return;

    const entryForm = document.getElementById('entry-form');
    const closeModalBtn = document.getElementById('close-entry-modal-btn');
    const deleteBtn = document.getElementById('delete-record-btn');
    
    // --- YARDIMCI FONKSİYONLAR ---
    const openModal = () => entryModal.style.display = 'block';
    const closeModal = () => entryModal.style.display = 'none';

    // --- KAYITLARI YÜKLEME VE GÖSTERME ---
    const loadRecords = async (query = '') => {
        const response = await fetch(`/admin/api/records?q=${query}`);
        const records = await response.json();
        listContainer.innerHTML = '';
        if (records.length === 0) {
            listContainer.innerHTML = '<p>Sonuç bulunamadı veya hiç kayıt yok.</p>';
            return;
        }
        records.forEach(record => {
            const card = document.createElement('div');
            card.className = 'manhwa-card';
            card.dataset.id = record.id;
            card.innerHTML = `
                <div class="card-image-wrapper">
                    <img src="${record.image || 'https://via.placeholder.com/250x350.png?text=Yok'}" class="card-image">
                </div>
                <div class="card-title">${record.title}</div>
            `;
            listContainer.appendChild(card);
        });
    };

    // --- ARAMA MANTIĞI ---
    let searchTimeout;
    searchBox.addEventListener('keyup', () => {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            loadRecords(searchBox.value);
        }, 300);
    });

    // --- MODAL AÇMA (YENİ EKLEME & DÜZENLEME) ---
    addNewBtn.addEventListener('click', () => {
        entryForm.reset();
        entryForm.querySelector('#record-id-input').value = '';
        entryModal.querySelector('h2').textContent = 'Yeni Kütüphane Kaydı';
        deleteBtn.style.display = 'none'; // Yeni kayıtta silme butonu olmaz
        openModal();
    });

    listContainer.addEventListener('click', async (e) => {
        const card = e.target.closest('.manhwa-card');
        if (card) {
            const recordId = card.dataset.id;
            const response = await fetch(`/admin/api/record/${recordId}`);
            const record = await response.json();
            
            entryForm.reset();
            entryForm.querySelector('#record-id-input').value = record.id;
            entryForm.querySelector('#original_title').value = record.original_title;
            entryForm.querySelector('#english_title').value = record.english_title || '';
            entryForm.querySelector('#record_type').value = record.record_type;
            entryForm.querySelector('#image_url').value = record.image_url || '';
            
            entryModal.querySelector('h2').textContent = 'Kaydı Düzenle';
            deleteBtn.style.display = 'inline-flex';
            openModal();
        }
    });

    // --- MODAL KAPATMA ---
    closeModalBtn.addEventListener('click', closeModal);
    window.addEventListener('click', (e) => {
        if (e.target == entryModal) closeModal();
    });

    // --- FORM GÖNDERME (YENİ EKLEME & DÜZENLEME) ---
    entryForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const id = document.getElementById('record-id-input').value;
        const formData = new FormData(entryForm);
        const url = id ? `/admin/api/record/update/${id}` : '/admin/api/record/add';
        const response = await fetch(url, {
            method: 'POST',
            body: formData
        });
        
        if (response.ok) {
            closeModal();
            loadRecords(searchBox.value);
        } else {
            const data = await response.json();
            alert(`Hata: ${data.message}`);
        }
    });

    // --- KAYIT SİLME ---
    deleteBtn.addEventListener('click', async () => {
        const id = document.getElementById('record-id-input').value;
        if (id && confirm('Bu kaydı kütüphaneden kalıcı olarak silmek istediğinizden emin misiniz? Bu işlem geri alınamaz.')) {
            const response = await fetch(`/admin/api/record/delete/${id}`, { method: 'POST' });
            if (response.ok) {
                closeModal();
                loadRecords(searchBox.value);
            } else {
                alert('Silme işlemi sırasında bir hata oluştu.');
            }
        }
    });

    // --- BAŞLANGIÇ ---
    loadRecords();
});