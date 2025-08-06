// static/js/dashboard.js (Final Sürümü)

document.addEventListener('DOMContentLoaded', function() {

    // --- ELEMENT SEÇİMLERİ ---
    const searchBox = document.getElementById('search-box');
    const searchResults = document.getElementById('search-results');
    const filterContainer = document.getElementById('filter-container');
    const listContainer = document.getElementById('user-list-container');
    const updateModal = document.getElementById('update-item-modal');
    const confirmDeleteModal = document.getElementById('confirm-delete-modal');
    
    if (!updateModal || !confirmDeleteModal) return; 
    
    const updateForm = document.getElementById('update-item-form');
    const closeModalBtn = document.getElementById('close-update-modal-btn');
    const listItems = listContainer.querySelectorAll('.manhwa-card');
    const cancelDeleteBtn = document.getElementById('cancel-delete-btn');
    const confirmDeleteBtn = document.getElementById('confirm-delete-btn');
    let itemToDeleteId = null;

    // --- YARDIMCI FONKSİYONLAR ---
    const openModal = (modal) => { if(modal) modal.style.display = 'block'; };
    const closeModal = (modal) => { if(modal) modal.style.display = 'none'; };

    // --- CANLI ARAMA MANTIĞI ---
    let searchTimeout;
    searchBox.addEventListener('keyup', (e) => {
        clearTimeout(searchTimeout);
        const query = e.target.value;
        if (query.length < 2) {
            searchResults.style.display = 'none';
            return;
        }
        
        searchTimeout = setTimeout(async () => {
            const response = await fetch(`/api/search?q=${query}`);
            const results = await response.json();
            searchResults.innerHTML = '';
            if (results.length > 0) {
                searchResults.style.display = 'block';
                results.forEach(record => {
                    const itemDiv = document.createElement('div');
                    itemDiv.className = 'search-item';
                    itemDiv.dataset.id = record.id;
                    itemDiv.innerHTML = `
                        <img src="${record.image || 'https://via.placeholder.com/40x60.png?text=N/A'}" alt="${record.title}">
                        <div class="search-item-info">
                            <span>${record.title}</span>
                            <small>${record.type}</small>
                        </div>
                    `;
                    searchResults.appendChild(itemDiv);
                });
            } else {
                searchResults.style.display = 'none';
            }
        }, 300);
    });
    document.addEventListener('click', (e) => {
        if (!e.target.closest('#search-container')) {
            searchResults.style.display = 'none';
        }
    });

    // --- LİSTEYE EKLEME MANTIĞI (Tıklayarak) ---
    searchResults.addEventListener('click', async (e) => {
        const targetItem = e.target.closest('.search-item');
        if (targetItem) {
            const recordId = targetItem.dataset.id;
            const response = await fetch(`/list/add/${recordId}`, { method: 'POST' });
            if (response.ok) {
                window.location.reload();
            } else {
                const data = await response.json();
                alert(`Hata: ${data.message}`);
            }
        }
    });

    // --- FİLTRELEME MANTIĞI ---
    if (filterContainer) {
        filterContainer.addEventListener('click', (e) => {
            if (e.target.tagName === 'BUTTON') {
                if(filterContainer.querySelector('.active')) {
                    filterContainer.querySelector('.active').classList.remove('active');
                }
                e.target.classList.add('active');
                const statusToFilter = e.target.dataset.status;
                listItems.forEach(item => {
                    item.style.display = (statusToFilter === 'all' || item.dataset.status === statusToFilter) ? 'block' : 'none';
                });
            }
        });
    }

    // --- GÜNCELLEME MODALI'NI AÇMA (Akıllı Durum Mantığı) ---
    listItems.forEach(item => {
        item.addEventListener('click', () => {
            const recordType = item.dataset.recordType;
            const statusSelect = updateForm.querySelector('#status-input');
            
            Array.from(statusSelect.options).forEach(opt => opt.style.display = 'block');
            
            if (recordType === 'Anime') {
                statusSelect.querySelector('option[value="Okunuyor"]').style.display = 'none';
                statusSelect.querySelector('option[value="İzleniyor"]').style.display = 'block';
                // Eğer mevcut durum Okunuyor ise, İzleniyor'a çevir
                if (item.dataset.status === 'Okunuyor') {
                    statusSelect.value = 'İzleniyor';
                } else {
                    statusSelect.value = item.dataset.status;
                }
            } else { // Manhwa, Manga, etc.
                statusSelect.querySelector('option[value="Okunuyor"]').style.display = 'block';
                statusSelect.querySelector('option[value="İzleniyor"]').style.display = 'none';
                 // Eğer mevcut durum İzleniyor ise, Okunuyor'a çevir
                 if (item.dataset.status === 'İzleniyor') {
                    statusSelect.value = 'Okunuyor';
                } else {
                    statusSelect.value = item.dataset.status;
                }
            }
            
            updateModal.querySelector('#user-list-id-input').value = item.dataset.userListId;
            updateModal.querySelector('#update-modal-title').textContent = item.dataset.recordTitle;
            updateModal.querySelector('#details-image').src = item.dataset.recordImage || 'https://via.placeholder.com/250x360.png?text=Yok';
            updateForm.querySelector('#chapter-input').value = item.dataset.chapter;
            updateForm.querySelector('#notes-input').value = item.dataset.notes;
            openModal(updateModal);
        });
    });

    // --- MODAL KAPATMA ---
    closeModalBtn.addEventListener('click', () => closeModal(updateModal));
    window.addEventListener('click', (e) => {
        if (e.target == updateModal || e.target == confirmDeleteModal) {
            closeModal(updateModal);
            closeModal(confirmDeleteModal);
        }
    });

    // --- GÜNCELLEME FORMUNU GÖNDERME ---
    updateForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const userListId = document.getElementById('user-list-id-input').value;
        const data = {
            status: document.getElementById('status-input').value,
            current_chapter: document.getElementById('chapter-input').value,
            notes: document.getElementById('notes-input').value
        };
        const response = await fetch(`/list/update/${userListId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        if (response.ok) {
            window.location.reload();
        } else {
            alert('Güncelleme sırasında bir hata oluştu.');
        }
    });

    // --- MODERN LİSTEDEN SİLME MANTIĞI ---
    const deleteBtn = document.getElementById('delete-item-btn');
    if(deleteBtn) {
        deleteBtn.addEventListener('click', () => {
            itemToDeleteId = document.getElementById('user-list-id-input').value;
            closeModal(updateModal); // Önceki modalı kapat
            openModal(confirmDeleteModal); // Onay modalını aç
        });
    }

    cancelDeleteBtn.addEventListener('click', () => {
        closeModal(confirmDeleteModal);
        itemToDeleteId = null;
    });

    confirmDeleteBtn.addEventListener('click', async () => {
        if (itemToDeleteId) {
            const response = await fetch(`/list/delete/${itemToDeleteId}`, {
                method: 'POST',
            });
            if (response.ok) {
                window.location.reload();
            } else {
                alert('Silme işlemi sırasında bir hata oluştu.');
            }
        }
    });
});