// ── Clock ──────────────────────────────────────
function updateClock() {
    const now = new Date();
    const h = String(now.getHours()).padStart(2, '0');
    const m = String(now.getMinutes()).padStart(2, '0');
    const el = document.getElementById('clock');
    if (el) el.textContent = h + ':' + m;
}
setInterval(updateClock, 1000);
updateClock();

// ── Toast ──────────────────────────────────────
function showToast(msg, color) {
    const toast = document.getElementById('toast');
    toast.textContent = msg;
    toast.style.background = color || '#1A2332';
    toast.classList.add('show');
    setTimeout(() => toast.classList.remove('show'), 3000);
}

// ── Status Wheel ───────────────────────────────
let currentStep = 0;
const steps = [
    {
        color: '#607D8B',
        emoji: '🕐',
        title: 'Zbel mazal ma wdach',
        desc: 'Wdi s-sac barra qbel 21h. / Mettez votre sac avant 21h.',
        btnText: '🗑️ Zbel Wajd! — Marquer Prêt',
        btnClass: 'btn-green',
        offset: 217.8
    },
    {
        color: '#FF8F00',
        emoji: '🗑️',
        title: 'Zbel wajd / Prêt',
        desc: 'Collecteur ghi yjii — ~20 dqiqa. / Le collecteur arrive bientôt.',
        btnText: '🔄 Simuler collecte',
        btnClass: 'btn-teal',
        offset: 108.9
    },
    {
        color: '#2E7D32',
        emoji: '✅',
        title: 'Mjmoa / Collecté ✓',
        desc: 'Collecté à 21h15 par Youssef B. — شكرًا بزاف!',
        btnText: null,
        offset: 0
    }
];

function advanceStep() {
    if (currentStep >= 2) return;
    currentStep++;
    updateWheel();
    const msgs = [
        '🗑️ Zbel wajd! Collecteur en route — شكرًا!',
        '✅ Collecté à 21h15 — Shukran bezzaf!'
    ];
    showToast(msgs[currentStep - 1], currentStep === 2 ? '#2E7D32' : '#FF8F00');
    fetch('/api/trash_ready/1', { method: 'POST' });
}

function resetClientStep() {
    currentStep = 0;
    updateWheel();
    showToast('↺ Réinitialisé / تم الإعادة', '#607D8B');
}

function updateWheel() {
    const step = steps[currentStep];
    const circle = document.getElementById('wheel-circle');
    circle.setAttribute('stroke', step.color);
    circle.setAttribute('stroke-das