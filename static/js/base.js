// static/js/base.js (Gelişmiş Header ve Dropdown Mantığı ile)
document.addEventListener('DOMContentLoaded', () => {
    // --- TEMA DEĞİŞTİRİCİ ---
    const themeBtn = document.getElementById('theme-btn');
    if (themeBtn) {
        const body = document.body;
        const themeIcon = document.getElementById('theme-icon');
        const sunIcon = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2.25a.75.75 0 01.75.75v2.25a.75.75 0 01-1.5 0V3a.75.75 0 01.75-.75zM7.5 12a4.5 4.5 0 119 0 4.5 4.5 0 01-9 0zM18.894 6.166a.75.75 0 00-1.06-1.06l-1.591 1.59a.75.75 0 101.06 1.061l1.591-1.59zM21.75 12a.75.75 0 01-.75.75h-2.25a.75.75 0 010-1.5h2.25a.75.75 0 01.75.75zM17.834 18.894a.75.75 0 001.06-1.06l-1.59-1.591a.75.75 0 10-1.061 1.06l1.59 1.591zM12 18a.75.75 0 01.75.75v2.25a.75.75 0 01-1.5 0v-2.25A.75.75 0 0112 18zM5.106 17.834a.75.75 0 001.06 1.06l1.591-1.59a.75.75 0 00-1.06-1.061l-1.591 1.59zM4.5 12a.75.75 0 01-.75.75H1.5a.75.75 0 010-1.5h2.25a.75.75 0 01.75.75zM6.166 5.106a.75.75 0 00-1.06 1.06l1.59 1.591a.75.75 0 001.061-1.06l-1.59-1.591z"></path></svg>`;
        const moonIcon = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><path fill-rule="evenodd" d="M9.528 1.718a.75.75 0 01.162.819A8.97 8.97 0 009 6a9 9 0 009 9 8.97 8.97 0 003.463-.69.75.75 0 01.981.981A10.503 10.503 0 0118 18a10.5 10.5 0 01-10.5-10.5c0-1.31.249-2.548.7-3.662a.75.75 0 01.819.162z" clip-rule="evenodd"></path></svg>`;

        const applyTheme = (theme) => {
            document.body.dataset.theme = theme;
            if (themeIcon) themeIcon.innerHTML = theme === 'light' ? sunIcon : moonIcon;
            localStorage.setItem('lystTheme', theme);
        };

        themeBtn.addEventListener('click', () => {
            const newTheme = document.body.dataset.theme === 'dark' ? 'light' : 'dark';
            applyTheme(newTheme);
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

        document.addEventListener('click', () => {
            if (userMenuDropdown.classList.contains('active')) {
                userMenuDropdown.classList.remove('active');
            }
        });
    }

    // --- MOBİL MENÜ ---
    const mobileMenuBtn = document.getElementById('mobile-menu-btn');
    const mobileNavContainer = document.getElementById('mobile-nav-container');

    if (mobileMenuBtn && mobileNavContainer) {
        // Mobil menüyü, masaüstü menülerinden klonlayarak oluştur
        const mainNav = document.querySelector('.main-nav');
        const userMenu = document.querySelector('.user-menu-dropdown');
        
        if (mainNav) mobileNavContainer.appendChild(mainNav.cloneNode(true));
        if (userMenu) mobileNavContainer.appendChild(userMenu.cloneNode(true));

        mobileMenuBtn.addEventListener('click', () => {
            mobileNavContainer.classList.toggle('active');
        });
    }
});