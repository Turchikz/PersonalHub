(() => {
    const panel = document.getElementById("monitor-panel");
    if (!panel) return;
    const initial = JSON.parse(document.getElementById("monitor-initial-notifications").textContent);
    const toast = document.getElementById("monitor-toast");
    const toastText = document.getElementById("monitor-toast-text");
    let lastSeen = initial;
    let toastTimer;
    let inFlight = false;
    // Remember notifications in this browser; storage may be disabled.
    try {
        const saved = localStorage.getItem("monitorLastNotification");
        if (saved !== null && Number.isSafeInteger(Number(saved))) lastSeen = Number(saved);
    } catch (_) { /* Session memory still prevents repeat notifications. */ }

    document.getElementById("monitor-toast-close").addEventListener("click", () => { toast.hidden = true; });

    async function refresh() {
        if (inFlight || document.hidden) return;
        inFlight = true;
        try {
            const response = await fetch(panel.dataset.statusUrl, {
                cache: "no-store", signal: AbortSignal.timeout(10000),
            });
            if (!response.ok) throw new Error("Status unavailable");
            const data = await response.json();
            const opened = [...panel.querySelectorAll("details[open]")].map(item => item.dataset.monitorDetails);
            // This fragment is escaped by Django, rather than interpolated from URLs in JS.
            panel.innerHTML = data.html;
            panel.querySelectorAll("details").forEach(item => {
                item.open = opened.includes(item.dataset.monitorDetails);
            });
            document.getElementById("monitor-refresh-error").hidden = true;
            const latest = data.notifications[0]?.id ?? 0;
            const fresh = data.notifications.filter(item => item.id > lastSeen);
            if (fresh.length) {
                toastText.textContent = fresh.reverse().map(item => item.message).join("\n");
                toast.hidden = false;
                clearTimeout(toastTimer);
                toastTimer = setTimeout(() => { toast.hidden = true; }, 15000);
            }
            lastSeen = latest;
            try { localStorage.setItem("monitorLastNotification", String(lastSeen)); } catch (_) {}
        } catch (_) {
            document.getElementById("monitor-refresh-error").hidden = false;
        } finally {
            inFlight = false;
        }
    }
    refresh();
    setInterval(refresh, 30000);
    document.addEventListener("visibilitychange", () => { if (!document.hidden) refresh(); });
})();
