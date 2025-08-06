// static/js/dashboard.js (Yeni Tasarıma Uyumlu Son Hali)

document.addEventListener('DOMContentLoaded', function() {

    const searchBox = document.getElementById('search-box');
    const searchResults = document.getElementById('search-results');
    const filterContainer = document.getElementById('filter-container');
    const listContainer = document.getElementById('user-list-container');
    const updateModal = document.getElementById('update-item-modal');
    if (!updateModal) return; 
    
    const updateForm = document.getElementById('update-item-form');
    const closeModalBtn = document.getElementById('close-update-modal-btn');
    const listItems = listContainer.querySelectorAll('.manhwa-card'); // Sınıf adı değişti

    // --- ARAMA MANTIĞI ---
    let searchTimeout;
    searchBox.addEventListener('keyup', (e) => {
        clearTimeout(searchTimeout);
        const query = e.target.value;
        if (query.length < 2) { searchResults.style.display = 'none'; return; }
        
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
                    itemDiv.innerHTML = `<img src="${record.image || 'https://via.placeholder.com/40x60.png?text=N/A'}"><span>${record.title}</span>`;
                    searchResults.appendChild(itemDiv);
                });
            } else { searchResults.style.display = 'none'; }
        }, 300);
    });
    document.addEventListener('click', (e) => { if (e.target.id !== 'search-box') searchResults.style.display = 'none'; });
    searchResults.addEventListener('click', async (e) => {
        const targetItem = e.target.closest('.search-item');
        if (targetItem) {
            const recordId = targetItem.dataset.id;
            const response = await fetch(`/list/add/${recordId}`, { method: 'POST' });
            if (response.ok) { window.location.reload(); } 
            else { const data = await response.json(); alert(`Hata: ${data.message}`); }
        }
    });

    // --- FİLTRELEME MANTIĞI ---
    filterContainer.addEventListener('click', (e) => {
        if (e.target.tagName === 'BUTTON') {
            filterContainer.querySelector('.active').classList.remove('active');
            e.target.classList.add('active');
            const statusToFilter = e.target.dataset.status;
            listItems.forEach(item => {
                item.style.display = (statusToFilter === 'all' || item.dataset.status === statusToFilter) ? 'block' : 'none';
            });
        }
    });

    // --- GÜNCELLEME MODALI'NI AÇMA ---
    listItems.forEach(item => {
        item.addEventListener('click', () => {
            updateForm.querySelector('#user-list-id-input').value = item.dataset.userListId;
            updateModal.querySelector('#update-modal-title').textContent = item.dataset.recordTitle;
            updateForm.querySelector('#status-input').value = item.dataset.status;
            updateForm.querySelector('#chapter-input').value = item.dataset.chapter;
            updateForm.querySelector('#notes-input').value = item.dataset.notes; // Notları doldur
            updateModal.style.display = 'block';
        });
    });

    // --- MODALI KAPATMA ---
    closeModalBtn.addEventListener('click', () => updateModal.style.display = 'none');
    window.addEventListener('click', (e) => { if (e.target == updateModal) updateModal.style.display = 'none'; });

    // --- GÜNCELLEME FORMUNU GÖNDERME ---
    updateForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const userListId = document.getElementById('user-list-id-input').value;
        const data = {
            status: document.getElementById('status-input').value,
            current_chapter: document.getElementById('chapter-input').value,
            notes: document.getElementById('notes-input').value // Notları data'ya ekle
        };
        const response = await fetch(`/list/update/${userListId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        if (response.ok) { window.location.reload(); } 
        else { alert('Güncelleme sırasında bir hata oluştu.'); }
    });
});