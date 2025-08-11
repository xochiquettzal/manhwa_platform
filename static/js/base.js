// static/js/base.js (Nihai, En Basit ve En Sağlam Hali)
document.addEventListener('DOMContentLoaded', () => {
    // --- TEMA DEĞİŞTİRİCİ ---
    const themeButtons = document.querySelectorAll('.theme-btn');
    if (themeButtons.length > 0) {
        const body = document.body;
        const sunIcon = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2.25a.75.75 0 01.75.75v2.25a.75.75 0 01-1.5 0V3a.75.75 0 01.75-.75zM7.5 12a4.5 4.5 0 119 0 4.5 4.5 0 01-9 0zM18.894 6.166a.75.75 0 00-1.06-1.06l-1.591 1.59a.75.75 0 101.06 1.061l1.591-1.59zM21.75 12a.75.75 0 01-.75.75h-2.25a.75.75 0 010-1.5h2.25a.75.75 0 01.75.75zM17.834 18.894a.75.75 0 001.06-1.06l-1.59-1.591a.75.75 0 10-1.061 1.06l1.59 1.591zM12 18a.75.75 0 01.75.75v2.25a.75.75 0 01-1.5 0v-2.25A.75.75 0 0112 18zM5.106 17.834a.75.75 0 001.06 1.06l1.591-1.59a.75.75 0 00-1.06-1.061l-1.591 1.59zM4.5 12a.75.75 0 01-.75.75H1.5a.75.75 0 010-1.5h2.25a.75.75 0 01.75.75zM6.166 5.106a.75.75 0 00-1.06 1.06l1.59 1.591a.75.75 0 001.061-1.06l-1.59-1.591z"></path></svg>`;
        const moonIcon = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><path fill-rule="evenodd" d="M9.528 1.718a.75.75 0 01.162.819A8.97 8.97 0 009 6a9 9 0 009 9 8.97 8.97 0 003.463-.69.75.75 0 01.981.981A10.503 10.503 0 0118 18a10.5 10.5 0 01-10.5-10.5c0-1.31.249-2.548.7-3.662a.75.75 0 01.819.162z" clip-rule="evenodd"></path></svg>`;

        const applyTheme = (theme) => {
            body.dataset.theme = theme;
            themeButtons.forEach(btn => {
                const iconContainer = btn.querySelector('svg');
                if (iconContainer) {
                   iconContainer.outerHTML = theme === 'light' ? sunIcon : moonIcon;
                }
            });
            localStorage.setItem('lystTheme', theme);
        };

        themeButtons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const newTheme = body.dataset.theme === 'dark' ? 'light' : 'dark';
                applyTheme(newTheme);
            });
        });
        
        applyTheme(localStorage.getItem('lystTheme') || 'dark');
    }

    // --- KULLANICI DROPDOWN MENÜSÜ ---
    const userMenuBtn = document.getElementById('user-menu-btn');
    const userMenuDropdown = document.getElementById('user-menu-dropdown');

    if (userMenuBtn && userMenuDropdown) {
        userMenuBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            userMenuDropdown.classList.toggle('active');
        });
    }

    // --- MOBİL MENÜ ---
    const mobileMenuBtn = document.getElementById('mobile-menu-btn');
    const mobileNavPanel = document.getElementById('mobile-nav-panel');

    if (mobileMenuBtn && mobileNavPanel) {
        mobileMenuBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            mobileNavPanel.classList.toggle('active');
        });
    }

    // Dropdown ve mobil menüyü dışarı tıklayınca kapat
    document.addEventListener('click', (e) => {
        if (userMenuDropdown && userMenuDropdown.classList.contains('active') && !userMenuBtn.contains(e.target)) {
            userMenuDropdown.classList.remove('active');
        }

        if (mobileNavPanel && mobileNavPanel.classList.contains('active') && !mobileNavPanel.contains(e.target) && !mobileMenuBtn.contains(e.target)) {
            mobileNavPanel.classList.remove('active');
        }
    });
});