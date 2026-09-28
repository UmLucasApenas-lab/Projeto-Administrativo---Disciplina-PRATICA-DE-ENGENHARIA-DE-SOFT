/**
 * Gerenciador de Tema (Modo Noturno / Claro)
 * UniRV - Prática de Engenharia de Software
 */
(function () {
    // 1. Aplica o tema imediatamente para evitar FOUC (flash de tela branca)
    function getPreferredTheme() {
        const savedTheme = localStorage.getItem('THEME_PREFERENCE');
        if (savedTheme) {
            return savedTheme;
        }
        const systemPrefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
        return systemPrefersDark ? 'dark' : 'light';
    }

    const currentTheme = getPreferredTheme();
    document.documentElement.setAttribute('data-theme', currentTheme);

    // 2. Quando o DOM carregar, inicializa o botão e ícone
    document.addEventListener('DOMContentLoaded', () => {
        const btnToggle = document.getElementById('btnThemeToggle');
        const themeIcon = document.getElementById('themeIcon');

        function updateIcon(theme) {
            if (!themeIcon) return;
            if (theme === 'dark') {
                themeIcon.className = 'fa-solid fa-sun';
                if (btnToggle) btnToggle.title = 'Alternar para Modo Claro';
            } else {
                themeIcon.className = 'fa-solid fa-moon';
                if (btnToggle) btnToggle.title = 'Alternar para Modo Noturno';
            }
        }

        updateIcon(document.documentElement.getAttribute('data-theme') || 'light');

        if (btnToggle) {
            btnToggle.addEventListener('click', () => {
                const current = document.documentElement.getAttribute('data-theme') === 'dark' ? 'dark' : 'light';
                const next = current === 'dark' ? 'light' : 'dark';
                document.documentElement.setAttribute('data-theme', next);
                localStorage.setItem('THEME_PREFERENCE', next);
                updateIcon(next);
            });
        }
    });
})();
