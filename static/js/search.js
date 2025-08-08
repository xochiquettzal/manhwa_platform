// static/js/search.js (Nihai Sürüm - Gelişmiş Filtreleme ve Sonsuz Kaydırma ile)

document.addEventListener('DOMContentLoaded', function() {
    
    // --- ELEMENT SEÇİMLERİ ---
    const searchBox = document.getElementById('search-box');
    const resultsContainer = document.getElementById('results-container');
    const loader = document.getElementById('loader');
    const detailsModal = document.getElementById('details-modal');
    const studioFilter = document.getElementById('studio-filter');
    const yearFilter = document.getElementById('year-filter');
    // tag multiselect controls for search
    const tagPanel = document.getElementById('search-tag-panel');
    const tagToggle = document.getElementById('search-tag-toggle');
    const tagApply = document.getElementById('search-apply-tags');
    const tagClear = document.getElementById('search-clear-tags');
    const selectedBar = document.getElementById('search-selected-bar');
    const sortByFilter = document.getElementById('sort-by-filter');
    const clearBtn = document.getElementById('search-clear-btn');
    
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
    let currentYear = '';
    let currentTags = [];
    let currentThemes = [];
    let currentDemos = [];
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
        currentYear = yearFilter ? yearFilter.value : '';
        const checked = Array.from(tagPanel ? tagPanel.querySelectorAll('input[type="checkbox"]:checked') : []);
        currentTags = checked.filter(cb => cb.dataset.kind === 'genre').map(cb => cb.value);
        currentThemes = checked.filter(cb => cb.dataset.kind === 'theme').map(cb => cb.value);
        currentDemos = checked.filter(cb => cb.dataset.kind === 'demographic').map(cb => cb.value);
        
        const params = new URLSearchParams({
            q: currentQuery,
            studio: currentStudio,
            year: currentYear,
            tags: currentTags.join(','),
            themes: currentThemes.join(','),
            demographics: currentDemos.join(','),
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
                        <small>${record.type || ''} ${record.release_year ? '• ' + record.release_year : ''}</small>
                        <button class="add-to-list-btn ${record.in_list ? 'in-list' : ''}" 
                                data-id="${record.id}" 
                                title="${record.in_list ? 'Zaten Listede' : 'Listeye Ekle'}">
                            ${record.in_list ? '✓' : '+'}
                        </button>
                    </div>
                    <div class="card-bottom-info" style="margin-top: .25rem;">
                        <div class="badges-row">
                            ${record.status ? `<span class="badge ${record.status && record.status.toLowerCase().includes('airing') ? 'status-airing' : 'status-finished'}">${record.status}</span>` : ''}
                            ${record.total_episodes ? `<span class="badge episodes">${record.total_episodes} bölüm</span>` : ''}
                        </div>
                        ${record.score ? `<small style="color: var(--accent-primary); font-weight: 700;">⭐ ${record.score.toFixed ? record.score.toFixed(2) : record.score}</small>` : ''}
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
    const toggleClear = () => {
        if (!clearBtn) return;
        if (searchBox.value && searchBox.value.length > 0) clearBtn.classList.remove('hidden');
        else clearBtn.classList.add('hidden');
    };
    searchBox.addEventListener('keyup', () => {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(resetAndFetch, 500);
        toggleClear();
    });
    toggleClear();
    if (clearBtn) {
        clearBtn.addEventListener('click', (e) => {
            e.preventDefault();
            searchBox.value = '';
            toggleClear();
            resetAndFetch();
            searchBox.focus();
        });
    }

    studioFilter.addEventListener('change', resetAndFetch);
    if (yearFilter) yearFilter.addEventListener('change', resetAndFetch);
    // --- TAG MULTISELECT (SEARCH) ---
    const refreshChips = () => {
        if (!selectedBar) return;
        selectedBar.innerHTML = '';
        // year
        if (yearFilter && yearFilter.value) {
            const chip = document.createElement('span'); chip.className = 'chip';
            chip.innerHTML = `${yearFilter.value}<button class="remove" aria-label="Sil">&times;</button>`;
            chip.querySelector('.remove').addEventListener('click', () => { yearFilter.value=''; resetAndFetch(); refreshChips(); });
            selectedBar.appendChild(chip);
        }
        // studio
        if (studioFilter && studioFilter.value) {
            const chip = document.createElement('span'); chip.className = 'chip';
            chip.innerHTML = `${studioFilter.value}<button class="remove" aria-label="Sil">&times;</button>`;
            chip.querySelector('.remove').addEventListener('click', () => { studioFilter.value=''; resetAndFetch(); refreshChips(); });
            selectedBar.appendChild(chip);
        }
        // tags
        if (tagPanel) {
            const checked = Array.from(tagPanel.querySelectorAll('input[type="checkbox"]:checked'));
            checked.forEach(cb => {
                const label = cb.dataset.kind === 'theme' ? 'Theme' : (cb.dataset.kind === 'demographic' ? 'Demo' : 'Genre');
                const chip = document.createElement('span'); chip.className = 'chip';
                chip.innerHTML = `${label}: ${cb.value}<button class="remove" aria-label="Sil">&times;</button>`;
                chip.querySelector('.remove').addEventListener('click', () => { cb.checked = false; refreshChips(); resetAndFetch(); });
                selectedBar.appendChild(chip);
            });
        }
    };
    if (tagToggle && tagPanel) {
        tagToggle.addEventListener('click', () => tagPanel.classList.toggle('open'));
        document.addEventListener('click', (e) => {
            if (!tagPanel.contains(e.target) && e.target !== tagToggle) tagPanel.classList.remove('open');
        });
        tagPanel.addEventListener('change', () => { refreshChips(); resetAndFetch(); });
        const filterText = document.getElementById('filter-text-search');
        if (filterText) {
            filterText.addEventListener('input', () => {
                const q = filterText.value.toLowerCase();
                tagPanel.querySelectorAll('.tag-item').forEach(el => {
                    const name = (el.textContent || '').toLowerCase();
                    el.style.display = name.includes(q) ? 'flex' : 'none';
                });
            });
        }
    }
    if (tagApply) tagApply.addEventListener('click', () => { tagPanel.classList.remove('open'); resetAndFetch(); });
    if (tagClear) tagClear.addEventListener('click', () => {
        if (!tagPanel) return;
        tagPanel.querySelectorAll('input[type="checkbox"]').forEach(cb => cb.checked = false);
        refreshChips();
        resetAndFetch();
    });
    refreshChips();
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
            const demEl = detailsModal.querySelector('#details-demographics'); if (demEl) demEl.textContent = record.demographics || 'N/A';
            const thEl = detailsModal.querySelector('#details-themes'); if (thEl) thEl.textContent = record.themes || 'N/A';
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