// static/js/dashboard.js (Nihai Sürüm - ID Düzeltmeleriyle)

document.addEventListener('DOMContentLoaded', function() {

    // --- ELEMENT SEÇİMLERİ (Spesifik ID'ler ile) ---
    const searchBox = document.getElementById('my-list-search-box');
    const filterContainer = document.getElementById('my-list-filter-container');
    const listContainer = document.getElementById('results-container');
    const updateModal = document.getElementById('update-item-modal');
    const confirmDeleteModal = document.getElementById('confirm-delete-modal');
    
    if (!updateModal || !confirmDeleteModal || !listContainer) {
        return; 
    }
    
    const updateForm = document.getElementById('update-item-form');
    const closeModalBtn = document.getElementById('close-update-modal-btn');
    const listItems = listContainer.querySelectorAll('.manhwa-card');
    const cancelDeleteBtn = document.getElementById('cancel-delete-btn');
    const confirmDeleteBtn = document.getElementById('confirm-delete-btn');
    let itemToDeleteId = null;

    // --- YARDIMCI FONKSİYONLAR ---
    const openModal = (modal) => { if(modal) modal.style.display = 'block'; };
    const closeModal = (modal) => { if(modal) modal.style.display = 'none'; };

    // --- FİLTRELEME VE ARAMA MANTIĞI ---
    const applyFilters = () => {
        // null kontrolleri eklendi
        const activeFilterButton = filterContainer ? filterContainer.querySelector('.filter-btn.active') : null;
        if (!activeFilterButton) return;

        const statusToFilter = activeFilterButton.dataset.status;
        const searchQuery = searchBox ? searchBox.value.toLowerCase() : '';

        listItems.forEach(item => {
            const title = (item.dataset.recordTitle || '').toLowerCase();
            const englishTitle = (item.dataset.recordEnglishTitle || '').toLowerCase();
            const status = item.dataset.status;

            const statusMatch = (statusToFilter === 'all' || status === statusToFilter);
            const searchMatch = (title.includes(searchQuery) || englishTitle.includes(searchQuery));

            if (statusMatch && searchMatch) {
                item.style.display = 'block';
            } else {
                item.style.display = 'none';
            }
        });
    };

    if (filterContainer) {
        filterContainer.addEventListener('click', (e) => {
            if (e.target.tagName === 'BUTTON') {
                if(filterContainer.querySelector('.active')) {
                    filterContainer.querySelector('.active').classList.remove('active');
                }
                e.target.classList.add('active');
                applyFilters();
            }
        });
    }

    if (searchBox) {
        searchBox.addEventListener('keyup', applyFilters);
    }
    
    // --- GÜNCELLEME MODALI'NI AÇMA ---
    listItems.forEach(item => {
        item.addEventListener('click', () => {
            const recordType = item.dataset.recordType;
            const statusSelect = updateForm.querySelector('#status-input');
            
            Array.from(statusSelect.options).forEach(opt => opt.style.display = 'block');
            
            if (recordType === 'Anime') {
                statusSelect.querySelector('option[value="Okunuyor"]').style.display = 'none';
                statusSelect.querySelector('option[value="İzleniyor"]').style.display = 'block';
                statusSelect.value = (item.dataset.status === 'Okunuyor' || !item.dataset.status) ? 'İzleniyor' : item.dataset.status;
            } else {
                statusSelect.querySelector('option[value="Okunuyor"]').style.display = 'block';
                statusSelect.querySelector('option[value="İzleniyor"]').style.display = 'none';
                 statusSelect.value = (item.dataset.status === 'İzleniyor' || !item.dataset.status) ? 'Okunuyor' : item.dataset.status;
            }
            
            const releaseYear = item.dataset.releaseYear;
            const source = item.dataset.source;
            const studios = item.dataset.studios;
            const tags = item.dataset.tags;

            updateModal.querySelector('#user-list-id-input').value = item.dataset.userListId;
            updateModal.querySelector('#update-modal-title').textContent = item.dataset.recordTitle;
            updateModal.querySelector('#details-image').src = item.dataset.recordImage || 'https://via.placeholder.com/250x375.png?text=Yok';
            updateModal.querySelector('#details-synopsis').textContent = item.dataset.synopsis || "Konu bilgisi mevcut değil.";
            
            updateModal.querySelector('#details-release-year').textContent = releaseYear || 'N/A';
            updateModal.querySelector('#details-source').textContent = source || 'N/A';
            updateModal.querySelector('#details-studios').textContent = studios || 'N/A';

            const tagsContainer = updateModal.querySelector('#details-tags');
            tagsContainer.innerHTML = '';
            if (tags) {
                tags.split(',').forEach(tag => {
                    const tagElement = document.createElement('span');
                    tagElement.className = 'tag';
                    tagElement.textContent = tag.trim();
                    tagsContainer.appendChild(tagElement);
                });
            } else {
                tagsContainer.textContent = 'N/A';
            }
            
            updateForm.querySelector('#chapter-input').value = item.dataset.chapter;
            updateForm.querySelector('#user-score-input').value = item.dataset.userScore;
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
            user_score: document.getElementById('user-score-input').value,
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

    // --- LİSTEDEN SİLME MANTIĞI ---
    const deleteBtn = document.getElementById('delete-item-btn');
    if(deleteBtn) {
        deleteBtn.addEventListener('click', () => {
            itemToDeleteId = document.getElementById('user-list-id-input').value;
            closeModal(updateModal);
            openModal(confirmDeleteModal);
        });
    }

    cancelDeleteBtn.addEventListener('click', () => closeModal(confirmDeleteModal));
    confirmDeleteBtn.addEventListener('click', async () => {
        if (itemToDeleteId) {
            const response = await fetch(`/list/delete/${itemToDeleteId}`, { method: 'POST' });
            if (response.ok) {
                window.location.reload();
            } else {
                alert('Silme işlemi sırasında bir hata oluştu.');
            }
        }
    });
});