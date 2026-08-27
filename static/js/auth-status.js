function escapeHtml(text) {
    if (!text) return '';
    return text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
}

export async function renderAuthStatus(containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;

    try {
        const response = await fetch('/api/me');
        const data = await response.json();

        if (data.logged_in) {
            container.innerHTML = `
                <span>Eingeloggt als ${escapeHtml(data.user.email)}</span>
                · <a href="/garage" class="underline hover:no-underline">🏠 Meine Garage</a>
                <button id="auth-logout-btn" type="button" class="ml-2 underline hover:no-underline">Logout</button>
            `;
            document.getElementById('auth-logout-btn').addEventListener('click', async () => {
                await fetch('/api/logout', { method: 'POST' });
                window.location.reload();
            });
        } else {
            container.innerHTML = `<a href="/login" class="underline hover:no-underline">🔑 Login</a> · <a href="/register" class="underline hover:no-underline">Registrieren</a>`;
        }
    } catch (error) {
        console.error('Fehler beim Laden des Login-Status:', error);
    }
}
