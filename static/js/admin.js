// static/js/admin.js (Final Sürümü)

document.addEventListener('DOMContentLoaded', function() {

    // --- ELEMENT SEÇİMLERİ ---
    const listContainer = document.getElementById('admin-records-list');
    const searchBox = document.getElementById('admin-search-box');
    const addNewBtn = document.getElementById('add-new-record-btn');
    const bulkImportBtn = document.getElementById('bulk-import-btn'); // Yeni buton
    const entryModal = document.getElementById('entry-modal');
    const bulkImportModal = document.getElementById('bulk-import-modal'); // Yeni modal
    const confirmDeleteModal = document.getElementById('confirm-delete-modal');

    if (!entryModal || !listContainer || !confirmDeleteModal || !bulkImportModal) return;

    const entryForm = document.getElementById('entry-form');
    const bulkImportForm = document.getElementById('bulk-import-form'); // Yeni form
    const closeModalBtn = document.getElementById('close-entry-modal-btn');
    const closeBulkModalBtn = document.getElementById('close-bulk-modal-btn'); // Yeni kapatma butonu
    const deleteBtn = document.getElementById('delete-record-btn');
    const cancelDeleteBtn = document.getElementById('cancel-delete-btn');
    const confirmDeleteBtn = document.getElementById('confirm-delete-btn');
    let itemToDeleteId = null;

    // --- YARDIMCI FONKSİYONLAR ---
    const openModal = (modal) => { if(modal) modal.style.display = 'block'; };
    const closeModal = (modal) => { if(modal) modal.style.display = 'none'; };

    // --- KAYITLARI YÜKLEME VE GÖSTERME ---
    const loadRecords = async (query = '') => {
        const response = await fetch(`/admin/api/records?q=${query}`);
        const records = await response.json();
        listContainer.innerHTML = '';
        if (records.length === 0) {
            listContainer.innerHTML = '<p style="color: var(--text-secondary); grid-column: 1 / -1; text-align: center;">Sonuç bulunamadı veya hiç kayıt yok.</p>';
            return;
        }
        records.forEach(record => {
            const card = document.createElement('div');
            card.className = 'manhwa-card';
            card.dataset.id = record.id;
            card.innerHTML = `
                <div class="card-image-wrapper">
                    <img src="${record.image || 'https://via.placeholder.com/250x350.png?text=Yok'}" class="card-image" loading="lazy">
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
        deleteBtn.style.display = 'none';
        openModal(entryModal);
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
            entryForm.querySelector('#synopsis').value = record.synopsis || '';
            
            entryModal.querySelector('h2').textContent = 'Kaydı Düzenle';
            deleteBtn.style.display = 'inline-flex';
            openModal(entryModal);
        }
    });

    // --- MODAL KAPATMA ---
    closeModalBtn.addEventListener('click', () => closeModal(entryModal));
    window.addEventListener('click', (e) => {
        if (e.target == entryModal || e.target == confirmDeleteModal) {
            closeModal(entryModal);
            closeModal(confirmDeleteModal);
        }
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
            closeModal(entryModal);
            loadRecords(searchBox.value);
        } else {
            const data = await response.json();
            alert(`Hata: ${data.message}`);
        }
    });

    // --- KAYIT SİLME (MODERN MODAL) ---
    deleteBtn.addEventListener('click', () => {
        itemToDeleteId = document.getElementById('record-id-input').value;
        if(itemToDeleteId){
            closeModal(entryModal);
            const confirmText = confirmDeleteModal.querySelector('#confirm-text');
            confirmText.textContent = "Bu kayıt kütüphaneden kalıcı olarak silinecektir. Bu işlem geri alınamaz.";
            openModal(confirmDeleteModal);
        }
    });

    cancelDeleteBtn.addEventListener('click', () => {
        closeModal(confirmDeleteModal);
        itemToDeleteId = null;
    });

    confirmDeleteBtn.addEventListener('click', async () => {
        if (itemToDeleteId) {
            const response = await fetch(`/admin/api/record/delete/${itemToDeleteId}`, { method: 'POST' });
            if (response.ok) {
                closeModal(confirmDeleteModal);
                loadRecords(searchBox.value);
                itemToDeleteId = null;
            } else {
                alert('Silme işlemi sırasında bir hata oluştu.');
            }
        }
    });

    // --- YENİ: Toplu Ekleme Modalı Mantığı ---
    bulkImportBtn.addEventListener('click', () => {
        bulkImportForm.reset();
        openModal(bulkImportModal);
    });

    closeBulkModalBtn.addEventListener('click', () => closeModal(bulkImportModal));

    bulkImportForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData(bulkImportForm);
        const submitButton = bulkImportForm.querySelector('button[type="submit"]');
        submitButton.disabled = true;
        submitButton.textContent = 'İşleniyor...';

        try {
            const response = await fetch('/admin/api/bulk-import', {
                method: 'POST',
                body: formData,
            });
            const data = await response.json();
            alert(data.message); // Sonucu kullanıcıya göster
            if (response.ok) {
                closeModal(bulkImportModal);
                loadRecords(); // Listeyi yenile
            }
        } catch (error) {
            alert('Dosya yüklenirken bir hata oluştu.');
        } finally {
            submitButton.disabled = false;
            submitButton.textContent = 'İçe Aktar';
        }
    });

    // --- BAŞLANGIÇ ---
    loadRecords();
});