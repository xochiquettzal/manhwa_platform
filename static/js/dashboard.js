// static/js/dashboard.js (Nihai Sürüm - Çeviri ve Sıralama ile)
document.addEventListener('DOMContentLoaded', function() {
    // --- ELEMENT SEÇİMLERİ ---
    const searchBox = document.getElementById('my-list-search-box');
    const clearBtn = document.getElementById('my-list-clear-btn');
    const filterContainer = document.getElementById('my-list-status-container');
    const yearFilter = document.getElementById('my-list-year-filter');
    const studioFilter = document.getElementById('my-list-studio-filter');
    const sortByFilter = document.getElementById('my-list-sort-by');
    const tagPanel = document.getElementById('my-list-tag-panel');
    const tagToggle = document.getElementById('my-list-tag-toggle');
    const tagApply = document.getElementById('my-list-apply-tags');
    const tagClear = document.getElementById('my-list-clear-tags');
    const selectedBar = document.getElementById('my-list-selected-bar');
    const listContainer = document.getElementById('results-container');
    const updateModal = document.getElementById('update-item-modal');
    const confirmDeleteModal = document.getElementById('confirm-delete-modal');
    
    // Toplu işlem elementleri
    const selectAllBtn = document.getElementById('select-all-btn');
    const bulkDeleteBtn = document.getElementById('bulk-delete-btn');
    
    if (!listContainer) return;
    
    const updateForm = document.getElementById('update-item-form');
    const closeModalBtn = document.getElementById('close-update-modal-btn');
    const listItems = Array.from(listContainer.querySelectorAll('.manhwa-card'));
    
    const updateCardProgress = (card) => {
        if (!card) return;
        const total = parseInt(card.dataset.totalEpisodes || '0', 10) || 0;
        const current = parseInt(card.dataset.chapter || '0', 10) || 0;
        if (total > 0) {
            const pct = Math.floor((current * 100) / total);
            const progress = card.querySelector('.progress');
            if (progress) progress.style.width = `${pct}%`;
        }
    };
    const cancelDeleteBtn = document.getElementById('cancel-delete-btn');
    const confirmDeleteBtn = document.getElementById('confirm-delete-btn');
    let itemToDeleteId = null;
    const openModal = (modal) => { if(modal) modal.style.display = 'block'; };
    const closeModal = (modal) => { if(modal) modal.style.display = 'none'; };

    // --- SIRALAMA MANTIĞI ---
    const sortAndReorder = () => {
        const sortValue = sortByFilter ? sortByFilter.value : 'default';
        if (sortValue === 'default') {
            listItems.sort((a, b) => parseInt(a.dataset.userListId) - parseInt(b.dataset.userListId));
        } else {
            const [key, direction] = sortValue.split('-');
            listItems.sort((a, b) => {
                let valA, valB;
                if (key === 'title') {
                    valA = a.dataset.recordTitle.toLowerCase();
                    valB = b.dataset.recordTitle.toLowerCase();
                    return direction === 'asc' ? valA.localeCompare(valB) : valB.localeCompare(valA);
                }
                if (key === 'score') {
                    valA = parseInt(a.dataset.userScore || '0');
                    valB = parseInt(b.dataset.userScore || '0');
                }
                if (key === 'year') {
                    valA = parseInt(a.dataset.releaseYear || '0');
                    valB = parseInt(b.dataset.releaseYear || '0');
                }
                return direction === 'asc' ? valA - valB : valB - valA;
            });
        }
        listItems.forEach(item => listContainer.appendChild(item));
    };

    // --- FİLTRELEME VE ARAMA MANTIĞI ---
    const applyFilters = () => {
        const activeFilterButton = filterContainer ? filterContainer.querySelector('.filter-btn.active') : null;
        if (!activeFilterButton) return;
        const statusToFilter = activeFilterButton.dataset.status;
        const searchQuery = searchBox ? searchBox.value.toLowerCase() : '';
        const selectedYear = yearFilter ? yearFilter.value : '';
        const selectedStudio = studioFilter ? studioFilter.value : '';
        const selectedTags = Array.from(tagPanel ? tagPanel.querySelectorAll('input[data-kind="genre"]:checked') : []).map(c => c.value.toLowerCase());
        const selectedThemes = Array.from(tagPanel ? tagPanel.querySelectorAll('input[data-kind="theme"]:checked') : []).map(c => c.value.toLowerCase());
        const selectedDemos = Array.from(tagPanel ? tagPanel.querySelectorAll('input[data-kind="demographic"]:checked') : []).map(c => c.value.toLowerCase());
        
        listItems.forEach(item => {
            const title = (item.dataset.recordTitle || '').toLowerCase();
            const englishTitle = (item.dataset.recordEnglishTitle || '').toLowerCase();
            const status = item.dataset.status;
            const releaseYear = (item.dataset.releaseYear || '').toString();
            const studios = (item.dataset.studios || '').toLowerCase();
            const tags = (item.dataset.tags || '').toLowerCase();
            const themes = (item.dataset.themes || '').toLowerCase();
            const demographics = (item.dataset.demographics || '').toLowerCase();
            
            const statusMatch = (statusToFilter === 'all' || status === statusToFilter);
            const searchMatch = (title.includes(searchQuery) || englishTitle.includes(searchQuery));
            const yearMatch = (!selectedYear || releaseYear === selectedYear);
            const studioMatch = (!selectedStudio || studios.includes(selectedStudio.toLowerCase()));
            const tagsMatch = (selectedTags.length === 0 || selectedTags.every(t => tags.includes(t)));
            const themesMatch = (selectedThemes.length === 0 || selectedThemes.every(t => themes.includes(t)));
            const demosMatch = (selectedDemos.length === 0 || selectedDemos.every(d => demographics.includes(d)));

            item.style.display = (statusMatch && searchMatch && yearMatch && studioMatch && tagsMatch && themesMatch && demosMatch) ? 'block' : 'none';
        });
        sortAndReorder();
    };

    // --- OLAY DİNLEYİCİLERİ ---
    if (sortByFilter) {
        sortByFilter.addEventListener('change', sortAndReorder);
    }
    
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
        const toggleClear = () => { if (clearBtn) clearBtn.classList.toggle('hidden', !searchBox.value); };
        searchBox.addEventListener('input', () => { toggleClear(); applyFilters(); });
        toggleClear();
    }

    if (clearBtn) {
        clearBtn.addEventListener('click', (e) => {
            e.preventDefault();
            searchBox.value = '';
            clearBtn.classList.add('hidden');
            applyFilters();
            searchBox.focus();
        });
    }

    if (yearFilter) yearFilter.addEventListener('change', applyFilters);
    if (studioFilter) studioFilter.addEventListener('change', applyFilters);
    
    // --- TAG MULTISELECT ---
    const refreshChips = () => {
        if (!selectedBar || !tagPanel) return;
        selectedBar.innerHTML = '';
        const activeBtn = filterContainer ? filterContainer.querySelector('.filter-btn.active') : null;
        if (activeBtn && activeBtn.dataset.status !== 'all') {
            const chip = document.createElement('span'); chip.className = 'chip';
            chip.textContent = activeBtn.textContent.trim();
            selectedBar.appendChild(chip);
        }
        if (yearFilter && yearFilter.value) {
            const chip = document.createElement('span'); chip.className = 'chip';
            chip.innerHTML = `${yearFilter.value}<button class="remove" aria-label="Sil">&times;</button>`;
            chip.querySelector('.remove').addEventListener('click', () => { yearFilter.value=''; applyFilters(); refreshChips(); });
            selectedBar.appendChild(chip);
        }
        if (studioFilter && studioFilter.value) {
            const chip = document.createElement('span'); chip.className = 'chip';
            chip.innerHTML = `${studioFilter.value}<button class="remove" aria-label="Sil">&times;</button>`;
            chip.querySelector('.remove').addEventListener('click', () => { studioFilter.value=''; applyFilters(); refreshChips(); });
            selectedBar.appendChild(chip);
        }
        const checked = Array.from(tagPanel.querySelectorAll('input[type="checkbox"]:checked'));
        checked.forEach(cb => {
            const chip = document.createElement('span'); chip.className = 'chip';
            chip.innerHTML = `${cb.value}<button class="remove" aria-label="Sil">&times;</button>`;
            chip.querySelector('.remove').addEventListener('click', () => {
                cb.checked = false; refreshChips(); applyFilters();
            });
            selectedBar.appendChild(chip);
        });
    };
    if (tagToggle && tagPanel) {
        tagToggle.addEventListener('click', () => {
            tagPanel.classList.toggle('open');
        });
        document.addEventListener('click', (e) => {
            if (!tagPanel.contains(e.target) && e.target !== tagToggle) {
                tagPanel.classList.remove('open');
            }
        });
        tagPanel.addEventListener('change', () => {
            refreshChips();
        });
    }
    if (tagApply) tagApply.addEventListener('click', () => { tagPanel.classList.remove('open'); applyFilters(); });
    if (tagClear) tagClear.addEventListener('click', () => {
        if (!tagPanel) return;
        tagPanel.querySelectorAll('input[type="checkbox"]').forEach(cb => cb.checked = false);
        refreshChips();
        applyFilters();
    });
    refreshChips();

    // --- KARTTA +1 BÖLÜM ---
    listContainer.addEventListener('click', async (e) => {
        const incBtn = e.target.closest('.inc-chapter-btn');
        const card = e.target.closest('.manhwa-card');
        if (incBtn && card) {
            e.stopPropagation();
            const userListId = card.dataset.userListId;
            const total = parseInt(card.dataset.totalEpisodes || '0', 10) || 0;
            const current = parseInt(card.dataset.chapter || '0', 10) || 0;
            const next = total > 0 ? Math.min(current + 1, total) : current + 1;
            if (next === current) return;
            const payload = { current_chapter: next, silent: true };
            const response = await fetch(`/list/update/${userListId}`, {
                method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload)
            });
            if (response.ok) {
                card.dataset.chapter = String(next);
                const counter = card.querySelector('.card-bottom-info span');
                if (counter) {
                    const totalText = total ? ` / ${total}` : '';
                    // DEĞİŞİKLİK BURADA: Sabit metin yerine 'translations' değişkeni kullanıldı.
                    counter.textContent = `${translations.progress_label} ${next}${totalText}`;
                }
                updateCardProgress(card);
            } else {
                alert('Güncelleme sırasında bir hata oluştu.');
            }
        }
    });

    // --- GÜNCELLEME MODALI'NI AÇMA ---
    listItems.forEach(item => {
        item.addEventListener('click', (e) => {
            // Checkbox'a tıklandıysa modal açma
            if (e.target.closest('.card-checkbox') || e.target.closest('.card-select-checkbox')) {
                e.stopPropagation();
                return;
            }
            
            if (e.target.closest('.inc-chapter-btn')) return;
            
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
            const themes = item.dataset.themes;
            const demographics = item.dataset.demographics;
            updateModal.querySelector('#user-list-id-input').value = item.dataset.userListId;
            updateModal.querySelector('#update-modal-title').textContent = item.dataset.recordTitle;
            updateModal.querySelector('#details-image').src = item.dataset.recordImage || 'https://via.placeholder.com/250x375.png?text=Yok';
            updateModal.querySelector('#details-synopsis').textContent = item.dataset.synopsis || "Konu bilgisi mevcut değil.";
            updateModal.querySelector('#details-release-year').textContent = releaseYear || 'N/A';
            updateModal.querySelector('#details-source').textContent = source || 'N/A';
            updateModal.querySelector('#details-studios').textContent = studios || 'N/A';
            const demEl = updateModal.querySelector('#details-demographics'); if (demEl) demEl.textContent = demographics || 'N/A';
            const thEl = updateModal.querySelector('#details-themes'); if (thEl) thEl.textContent = themes || 'N/A';
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
            const totalEpisodes = parseInt(item.dataset.totalEpisodes || '0', 10) || 0;
            const chapterInput = updateForm.querySelector('#chapter-input');
            chapterInput.value = item.dataset.chapter;
            if (totalEpisodes > 0) { chapterInput.setAttribute('max', String(totalEpisodes)); }
            updateCardProgress(item);
            updateForm.querySelector('#user-score-input').value = item.dataset.userScore;
            updateForm.querySelector('#notes-input').value = item.dataset.notes;
            openModal(updateModal);
        });
    });
    listItems.forEach(updateCardProgress);

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
            method: 'POST', headers: { 'Content-Type': 'application/json' },
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
    
    // --- MYANIMELIST İÇE AKTARIM ---
    const importMalBtn = document.getElementById('import-mal-btn');
    const importMalModal = document.getElementById('import-mal-modal');
    const closeImportModalBtn = document.getElementById('close-import-modal-btn');
    const cancelImportBtn = document.getElementById('cancel-import-btn');
    const importMalForm = document.getElementById('import-mal-form');
    const importProgress = document.getElementById('import-progress');
    const importProgressBar = document.getElementById('import-progress-bar');
    const importStatusText = document.getElementById('import-status-text');
    const submitImportBtn = document.getElementById('submit-import-btn');
    
    if (importMalBtn && importMalModal) {
        // Import modalını aç
        importMalBtn.addEventListener('click', () => {
            openModal(importMalModal);
        });
        
        // Import modalını kapat
        if (closeImportModalBtn) {
            closeImportModalBtn.addEventListener('click', () => closeModal(importMalModal));
        }
        if (cancelImportBtn) {
            cancelImportBtn.addEventListener('click', () => closeModal(importMalModal));
        }
        
        // Import formunu gönder
        if (importMalForm) {
            importMalForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                
                const formData = new FormData(importMalForm);
                const fileInput = document.getElementById('mal-file');
                
                // Checkbox değerlerini manuel olarak ekle
                const importScores = document.getElementById('import-scores').checked;
                const importNotes = document.getElementById('import-notes').checked;
                const importDates = document.getElementById('import-dates').checked;
                
                // FormData'ya checkbox değerlerini ekle
                formData.set('import_scores', importScores.toString());
                formData.set('import_notes', importNotes.toString());
                formData.set('import_dates', importDates.toString());
                
                if (!fileInput.files[0]) {
                    alert('Lütfen bir XML dosyası seçin.');
                    return;
                }
                
                // Progress bar'ı göster ve detaylı bilgi ver
                importProgress.style.display = 'block';
                submitImportBtn.disabled = true;
                submitImportBtn.textContent = 'İçe Aktarılıyor...';
                
                // Progress mesajlarını güncelle
                if (importStatusText) {
                    importStatusText.textContent = 'XML dosyası analiz ediliyor...';
                }
                if (importProgressBar) {
                    importProgressBar.style.width = '10%';
                }
                
                // Progress bar animasyonu
                let progress = 10;
                const progressInterval = setInterval(() => {
                    if (progress < 90) {
                        progress += Math.random() * 5;
                        if (importProgressBar) {
                            importProgressBar.style.width = progress + '%';
                        }
                    }
                }, 500);
                
                try {
                    const response = await fetch('/import/mal', {
                        method: 'POST',
                        body: formData
                    });
                    
                    const data = await response.json();
                    
                    if (data.success) {
                        // Progress bar'ı tamamla
                        if (importProgressBar) {
                            importProgressBar.style.width = '100%';
                        }
                        if (importStatusText) {
                            importStatusText.textContent = 'İçe aktarım tamamlandı!';
                        }
                        
                        // Başarı mesajını göster
                        setTimeout(() => {
                            alert(data.message);
                            closeModal(importMalModal);
                            // Sayfayı yenile
                            window.location.reload();
                        }, 1000);
                    } else {
                        // Hata
                        if (importStatusText) {
                            importStatusText.textContent = 'Hata oluştu!';
                        }
                        alert(`Hata: ${data.message}`);
                    }
                } catch (error) {
                    if (importStatusText) {
                        importStatusText.textContent = 'Bağlantı hatası!';
                    }
                    alert('İçe aktarım sırasında bir hata oluştu: ' + error.message);
                } finally {
                    // Progress interval'i temizle
                    clearInterval(progressInterval);
                    
                    // Progress bar'ı gizle
                    setTimeout(() => {
                        importProgress.style.display = 'none';
                        submitImportBtn.disabled = false;
                        submitImportBtn.textContent = 'İçe Aktar';
                    }, 2000);
                }
            });
        }
    }
    
    // Import modalını dışarı tıklayınca kapat
    window.addEventListener('click', (e) => {
        if (e.target == importMalModal) {
            closeModal(importMalModal);
        }
    });
    
    // --- TOPLU İŞLEM FONKSİYONLARI ---
    
    // Checkbox değişikliklerini dinle
    listContainer.addEventListener('change', (e) => {
        if (e.target.classList.contains('card-select-checkbox')) {
            const card = e.target.closest('.manhwa-card');
            if (e.target.checked) {
                card.classList.add('selected');
            } else {
                card.classList.remove('selected');
            }
            updateBulkDeleteButton();
        }
    });
    
    // Tümünü seç/kaldır
    if (selectAllBtn) {
        selectAllBtn.addEventListener('click', () => {
            const checkboxes = listContainer.querySelectorAll('.card-select-checkbox');
            const allChecked = Array.from(checkboxes).every(cb => cb.checked);
            
            checkboxes.forEach(cb => {
                cb.checked = !allChecked;
                const card = cb.closest('.manhwa-card');
                if (!allChecked) {
                    card.classList.add('selected');
                } else {
                    card.classList.remove('selected');
                }
            });
            
            updateBulkDeleteButton();
            selectAllBtn.textContent = allChecked ? translations.select_all : translations.clear_selection;
        });
    }
    
    // Toplu silme butonunu güncelle
    function updateBulkDeleteButton() {
        const selectedCheckboxes = listContainer.querySelectorAll('.card-select-checkbox:checked');
        if (bulkDeleteBtn) {
            if (selectedCheckboxes.length > 0) {
                bulkDeleteBtn.style.display = 'inline-flex';
                bulkDeleteBtn.textContent = `${translations.delete_selected} (${selectedCheckboxes.length})`;
            } else {
                bulkDeleteBtn.style.display = 'none';
            }
        }
    }
    
    // Toplu silme işlemi
    if (bulkDeleteBtn) {
        bulkDeleteBtn.addEventListener('click', async () => {
            const selectedCheckboxes = listContainer.querySelectorAll('.card-select-checkbox:checked');
            if (selectedCheckboxes.length === 0) return;
            
            const confirmMessage = `${translations.selected} ${selectedCheckboxes.length} ${translations.entries_will_be_deleted}`;
            
            if (!confirm(confirmMessage)) return;
            
            const selectedIds = Array.from(selectedCheckboxes).map(cb => cb.dataset.userListId);
            
            try {
                // Her bir kaydı tek tek sil
                for (const id of selectedIds) {
                    const response = await fetch(`/list/delete/${id}`, { method: 'POST' });
                    if (!response.ok) {
                        console.error(`Kayıt ${id} silinirken hata oluştu`);
                    }
                }
                
                // Sayfayı yenile
                window.location.reload();
            } catch (error) {
                alert('Toplu silme işlemi sırasında bir hata oluştu: ' + error.message);
            }
        });
    }
});