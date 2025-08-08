// static/js/search.js (Nihai Sürüm - Gelişmiş Filtreleme ve Sonsuz Kaydırma ile)

document.addEventListener('DOMContentLoaded', function() {
    
    // --- ELEMENT SEÇİMLERİ ---
    const searchBox = document.getElementById('search-box');
    const resultsContainer = document.getElementById('results-container');
    const loader = document.getElementById('loader');
    const detailsModal = document.getElementById('details-modal');
    const studioFilter = document.getElementById('studio-filter');
    const sortByFilter = document.getElementById('sort-by-filter');
    
    if (!searchBox || !resultsContainer || !detailsModal) {
        console.error("Arama sayfası için gerekli elementler bulunamadı.");
        return;
    }

    const closeModalBtn = document.getElementById('close-details-modal-btn');
    let currentPage = 1;
    let isLoading = false;
    let hasNextPage = true;
    let currentQuery = '';
    let currentStudio = '';
    let currentSortBy = 'popularity';

    // --- YARDIMCI FONKSİYONLAR ---
    const openModal = (modal) => { if(modal) modal.style.display = 'block'; };
    const closeModal = (modal) => { if(modal) modal.style.display = 'none'; };

    // --- ARAMA VE FİLTRELEME MANTIĞI ---
    const fetchResults = async (page = 1, append = false) => {
        if (isLoading) return;
        isLoading = true;
        if(loader) loader.style.display = 'block';

        currentQuery = searchBox.value;
        currentStudio = studioFilter.value;
        currentSortBy = sortByFilter.value;
        
        const params = new URLSearchParams({
            q: currentQuery,
            studio: currentStudio,
            sort_by: currentSortBy,
            page: page
        });
        
        const response = await fetch(`/api/advanced-search?${params.toString()}`);
        const data = await response.json();
        
        if (!append) {
            resultsContainer.innerHTML = '';
        }

        if (data.results.length === 0 && !append) {
            resultsContainer.innerHTML = '<p style="color: var(--text-secondary); grid-column: 1 / -1; text-align: center;">Aramanızla eşleşen sonuç bulunamadı.</p>';
        }

        data.results.forEach(record => {
            const card = document.createElement('div');
            card.className = 'manhwa-card';
            card.dataset.recordId = record.id;
            
            card.innerHTML = `
                <div class="card-image-wrapper">
                    <img src="${record.image || 'https://via.placeholder.com/250x350.png?text=Yok'}" class="card-image" loading="lazy">
                </div>
                <div class="card-info">
                    <h3 class="card-title">${record.title}</h3>
                    <div class="card-bottom-info">
                        <small>${record.type || ''}</small>
                        <button class="add-to-list-btn ${record.in_list ? 'in-list' : ''}" 
                                data-id="${record.id}" 
                                title="${record.in_list ? 'Zaten Listede' : 'Listeye Ekle'}">
                            ${record.in_list ? '✓' : '+'}
                        </button>
                    </div>
                </div>
            `;
            resultsContainer.appendChild(card);
        });

        hasNextPage = data.has_next;
        isLoading = false;
        if(loader) loader.style.display = 'none';
    };
    
    const resetAndFetch = () => {
        currentPage = 1;
        hasNextPage = true;
        fetchResults(1, false);
    };

    // --- SONSUZ KAYDIRMA (INFINITE SCROLL) ---
    window.onscroll = () => {
        if (window.innerHeight + window.scrollY >= document.body.offsetHeight - 500 && !isLoading && hasNextPage) {
            currentPage++;
            fetchResults(currentPage, true);
        }
    };
    
    // --- OLAY DİNLEYİCİLERİ ---
    let searchTimeout;
    searchBox.addEventListener('keyup', () => {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(resetAndFetch, 500);
    });

    studioFilter.addEventListener('change', resetAndFetch);
    sortByFilter.addEventListener('change', resetAndFetch);
    
    // --- KARTLARA TIKLAMA MANTIĞI (LİSTEYE EKLEME & DETAY) ---
    resultsContainer.addEventListener('click', async (e) => {
        const targetButton = e.target.closest('.add-to-list-btn');
        const targetCard = e.target.closest('.manhwa-card');

        if (targetButton) {
            e.stopPropagation();
            if (targetButton.classList.contains('in-list')) return;

            const recordId = targetButton.dataset.id;
            const response = await fetch(`/list/add/${recordId}`, { method: 'POST' });
            
            if (response.ok) {
                targetButton.classList.add('in-list');
                targetButton.innerHTML = '✓';
                targetButton.title = 'Listeye Eklendi';
            } else {
                if (response.status === 401) {
                    window.location.href = '/auth/login';
                } else {
                    const data = await response.json();
                    alert(`Hata: ${data.message}`);
                }
            }
        } else if (targetCard) {
            const recordId = targetCard.dataset.recordId;
            const response = await fetch(`/admin/api/record/${recordId}`);
            if(!response.ok) return;

            const record = await response.json();
            
            detailsModal.querySelector('#details-title').textContent = record.original_title;
            detailsModal.querySelector('#details-image').src = record.image_url || 'https://via.placeholder.com/250x375.png?text=Yok';
            detailsModal.querySelector('#details-synopsis').textContent = record.synopsis || "Konu bilgisi mevcut değil.";
            detailsModal.querySelector('#details-release-year').textContent = record.release_year || 'N/A';
            detailsModal.querySelector('#details-source').textContent = record.source || 'N/A';
            detailsModal.querySelector('#details-studios').textContent = record.studios || 'N/A';
            const tagsContainer = detailsModal.querySelector('#details-tags');
            tagsContainer.innerHTML = '';
            if (record.tags) {
                record.tags.split(',').forEach(tag => {
                    const tagElement = document.createElement('span');
                    tagElement.className = 'tag';
                    tagElement.textContent = tag.trim();
                    tagsContainer.appendChild(tagElement);
                });
            } else {
                tagsContainer.textContent = 'N/A';
            }

            openModal(detailsModal);
        }
    });
    
    // Detay Modalını Kapatma
    closeModalBtn.addEventListener('click', () => closeModal(detailsModal));
    window.addEventListener('click', (e) => { if (e.target == detailsModal) closeModal(detailsModal); });

    // --- İLK YÜKLEME ---
    fetchResults();
});