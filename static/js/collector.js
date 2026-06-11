// ── Clock ──────────────────────────────────────
function updateClock() {
    const now = new Date();
    const h = String(now.getHours()).padStart(2, '0');
    const m = String(now.getMinutes()).padStart(2, '0');
    const s = String(now.getSeconds()).padStart(2, '0');
    const timeStr = h + ':' + m + ':' + s;
    ['clock', 'clock2'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.textContent = h + ':' + m;
    });
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

// ── Unit Statuses ──────────────────────────────
const unitStatuses = {};
for (let i = 1; i <= 30; i++) {
    if (i <= 18) {
        unitStatuses[i] = i % 6 === 4 ? 'violation' : 'collected';
    } else {
        unitStatuses[i] = 'pending';
    }
}

const stops = [
    { lat: 31.6285, lng: -8.0089, name: 'Dar 1',  resident: 'Karima Fahim',    addr: 'Massira I' },
    { lat: 31.6278, lng: -8.0075, name: 'Dar 2',  resident: 'Ahmed Benali',    addr: 'Massira I' },
    { lat: 31.6271, lng: -8.0062, name: 'Dar 3',  resident: 'Fatima Ouali',    addr: 'Massira I' },
    { lat: 31.6264, lng: -8.0050, name: 'Dar 4',  resident: 'Hassan Tazi',     addr: 'Massira I' },
    { lat: 31.6258, lng: -8.0038, name: 'Dar 5',  resident: 'Nadia Chraibi',   addr: 'Massira II' },
    { lat: 31.6250, lng: -8.0025, name: 'Dar 6',  resident: 'Omar Bakkali',    addr: 'Massira II' },
    { lat: 31.6243, lng: -8.0010, name: 'Dar 7',  resident: 'Zineb Mansouri',  addr: 'Massira II' },
    { lat: 31.6235, lng: -7.9998, name: 'Dar 8',  resident: 'Rachid Idrissi',  addr: 'Massira II' },
    { lat: 31.6228, lng: -7.9985, name: 'Dar 9',  resident: 'Samira Bensouda', addr: 'Massira II' },
    { lat: 31.6220, lng: -7.9972, name: 'Dar 10', resident: 'Karim Ouazzani',  addr: "M'hamid 6" },
    { lat: 31.6213, lng: -7.9960, name: 'Dar 11', resident: 'Laila Berrada',   addr: "M'hamid 6" },
    { lat: 31.6205, lng: -7.9948, name: 'Dar 12', resident: 'Yassine Alami',   addr: "M'hamid 6" },
    { lat: 31.6198, lng: -7.9935, name: 'Dar 13', resident: 'Houda El Fassi',  addr: "M'hamid 6" },
    { lat: 31.6191, lng: -7.9923, name: 'Dar 14', resident: 'Mehdi Chraibi',   addr: "M'hamid 7" },
    { lat: 31.6184, lng: -7.9910, name: 'Dar 15', resident: 'Amina Touri',     addr: "M'hamid 7" },
    { lat: 31.6177, lng: -7.9898, name: 'Dar 16', resident: 'Hamza Benkirane', addr: "M'hamid 7" },
    { lat: 31.6170, lng: -7.9886, name: 'Dar 17', resident: 'Sara Kadiri',     addr: "M'hamid 7" },
    { lat: 31.6163, lng: -7.9874, name: 'Dar 18', resident: 'Mouad Filali',    addr: 'Daoudiate' },
    { lat: 31.6156, lng: -7.9862, name: 'Dar 19', resident: 'Khadija Amine',   addr: 'Daoudiate' },
    { lat: 31.6149, lng: -7.9850, name: 'Dar 20', resident: 'Tarik Sebti',     addr: 'Daoudiate' },
    { lat: 31.6142, lng: -7.9838, name: 'Dar 21', resident: 'Imane Bensaid',   addr: 'Daoudiate' },
    { lat: 31.6135, lng: -7.9826, name: 'Dar 22', resident: 'Younes Alaoui',   addr: 'Hay Hassani' },
    { lat: 31.6128, lng: -7.9814, name: 'Dar 23', resident: 'Hiba Squalli',    addr: 'Hay Hassani' },
    { lat: 31.6121, lng: -7.9802, name: 'Dar 24', resident: 'Anas Berrada',    addr: 'Hay Hassani' },
    { lat: 31.6114, lng: -7.9790, name: 'Dar 25', resident: 'Loubna Bennis',   addr: 'Hay Hassani' },
    { lat: 31.6107, lng: -7.9778, name: 'Dar 26', resident: 'Othmane Fassi',   addr: 'Sidi Youssef' },
    { lat: 31.6100, lng: -7.9766, name: 'Dar 27', resident: 'Widad Chakir',    addr: 'Sidi Youssef' },
    { lat: 31.6093, lng: -7.9754, name: 'Dar 28', resident: 'Soufiane Lahlou', addr: 'Sidi Youssef' },
    { lat: 31.6086, lng: -7.9742, name: 'Dar 29', resident: 'Meryem Tazi',     addr: 'Sidi Youssef' },
    { lat: 31.6079, lng: -7.9730, name: 'Dar 30', resident: 'Driss Bennani',   addr: 'Sidi Youssef' },
];

// ── Map ────────────────────────────────────────
let collectorMap = null;
let vanMarker = null;
let markers = [];
let routeLine = null;
let doneRouteLine = null;
let vanAnimTimer = null;

function initCollectorMap() {
    const mapEl = document.getElementById('collector-map');
    if (!mapEl) return;

    collectorMap = L.map('collector-map', {
        zoomControl: true,
        scrollWheelZoom: true,
        tap: true
    }).setView([31.6200, -7.9970], 14);

    // Smooth tile layer
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap',
        maxZoom: 19,
        className: 'map-tiles'
    }).addTo(collectorMap);

    drawMapMarkers();
    startVanAnimation();
}

function getMarkerIcon(status, num) {
    const bg = status === 'collected' ? '#2E7D32' : status === 'violation' ? '#C62828' : '#90A4AE';
    const border = status === 'collected' ? '#1B5E20' : status === 'violation' ? '#7F0000' : '#607D8B';
    const label = status === 'collected' ? '✓' : status === 'violation' ? '!' : num;
    const size = status === 'violation' ? 28 : status === 'collected' ? 24 : 22;
    const fontSize = status === 'violation' ? 14 : 10;
    return L.divIcon({
        html: `<div style="
            background:${bg};
            width:${size}px;height:${size}px;
            border-radius:50%;
            display:flex;align-items:center;justify-content:center;
            font-size:${fontSize}px;font-weight:800;color:white;
            border:2.5px solid ${border};
            box-shadow:0 3px 8px rgba(0,0,0,.3);
            transition:transform .2s;
        ">${label}</div>`,
        iconSize: [size, size],
        iconAnchor: [size / 2, size / 2],
        className: ''
    });
}

function drawMapMarkers() {
    if (!collectorMap) return;

    markers.forEach(m => collectorMap.removeLayer(m));
    markers = [];
    if (routeLine) collectorMap.removeLayer(routeLine);
    if (doneRouteLine) collectorMap.removeLayer(doneRouteLine);
    if (vanMarker) collectorMap.removeLayer(vanMarker);

    const allLatLngs = stops.map(s => [s.lat, s.lng]);
    const collectedCount = Object.values(unitStatuses).filter(s => s === 'collected').length;

    // Full route (dashed)
    routeLine = L.polyline(allLatLngs, {
        color: '#B0BEC5',
        weight: 2.5,
        opacity: 0.5,
        dashArray: '8,5'
    }).addTo(collectorMap);

    // Completed route (solid green)
    if (collectedCount > 0) {
        doneRouteLine = L.polyline(allLatLngs.slice(0, collectedCount + 1), {
            color: '#2E7D32',
            weight: 4,
            opacity: 0.85,
            lineCap: 'round',
            lineJoin: 'round'
        }).addTo(collectorMap);
    }

    // Unit markers with click popups
    stops.forEach((stop, i) => {
        const status = unitStatuses[i + 1] || 'pending';
        const icon = getMarkerIcon(status, i + 1);
        const timeStr = status === 'collected' ? `21:${String(10 + i).padStart(2,'0')}` : '—';
        const m = L.marker([stop.lat, stop.lng], { icon })
            .addTo(collectorMap)
            .bindPopup(`
                <div style="font-family:-apple-system,sans-serif;min-width:160px">
                    <div style="font-weight:800;font-size:14px;color:#1A2332;margin-bottom:4px">${stop.name}</div>
                    <div style="font-size:12px;color:#607D8B;margin-bottom:2px">👤 ${stop.resident}</div>
                    <div style="font-size:12px;color:#607D8B;margin-bottom:6px">📍 ${stop.addr}</div>
                    <div style="display:inline-flex;align-items:center;gap:4px;background:${status === 'collected' ? '#E8F5E9' : status === 'violation' ? '#FFEBEE' : '#F5F5F5'};
                        color:${status === 'collected' ? '#2E7D32' : status === 'violation' ? '#C62828' : '#607D8B'};
                        padding:3px 10px;border-radius:20px;font-size:11px;font-weight:700">
                        ${status === 'collected' ? '✓ Collecté · ' + timeStr : status === 'violation' ? '⚠ Violation' : '⏳ En attente'}
                    </div>
                </div>
            `, { maxWidth: 220 });
        markers.push(m);
    });

    // Van marker — animated pulse
    const vanIdx = Math.min(collectedCount, stops.length - 1);
    const vp = stops[vanIdx];
    const vanIcon = L.divIcon({
        html: `
            <div style="position:relative;width:44px;height:44px;display:flex;align-items:center;justify-content:center">
                <div style="position:absolute;width:44px;height:44px;border-radius:50%;background:#00695C;opacity:0.25;animation:mapPulse 1.5s infinite"></div>
                <div style="position:absolute;width:34px;height:34px;border-radius:50%;background:#00695C;border:3px solid white;display:flex;align-items:center;justify-content:center;font-size:17px;box-shadow:0 3px 12px rgba(0,0,0,.4);z-index:10">🚛</div>
            </div>
            <style>@keyframes mapPulse{0%,100%{transform:scale(1);opacity:.25}50%{transform:scale(1.5);opacity:0}}</style>
        `,
        iconSize: [44, 44],
        iconAnchor: [22, 22],
        className: ''
    });

    vanMarker = L.marker([vp.lat, vp.lng], { icon: vanIcon, zIndexOffset: 1000 })
        .addTo(collectorMap)
        .bindPopup(`
            <div style="font-family:-apple-system,sans-serif">
                <div style="font-weight:800;font-size:14px;color:#1A2332">🚛 Youssef Benaissa</div>
                <div style="font-size:12px;color:#607D8B;margin-top:3px">Position actuelle</div>
                <div style="font-size:12px;color:#00695C;font-weight:700;margin-top:3px">📍 ${vp.addr}</div>
                <div style="font-size:11px;color:#607D8B;margin-top:2px">🕐 Mis à jour il y a 30s</div>
            </div>
        `);
}

// Van moves automatically every 8 seconds
function startVanAnimation() {
    if (vanAnimTimer) clearInterval(vanAnimTimer);
    vanAnimTimer = setInterval(() => {
        const pending = Object.keys(unitStatuses).filter(k => unitStatuses[k] === 'pending');
        if (pending.length === 0) {
            clearInterval(vanAnimTimer);
            return;
        }
        // Simulate van moving to next stop
        const collectedCount = Object.values(unitStatuses).filter(s => s === 'collected').length;
        if (collectedCount < stops.length && vanMarker) {
            const nextStop = stops[Math.min(collectedCount, stops.length - 1)];
            vanMarker.setLatLng([nextStop.lat, nextStop.lng]);
        }
    }, 8000);
}

// ── Unit Grid ──────────────────────────────────
function renderUnitGrid() {
    const grid = document.getElementById('unit-grid');
    if (!grid) return;
    let html = '';
    for (let i = 1; i <= 30; i++) {
        const s = unitStatuses[i];
        const cls = s === 'collected' ? 'unit-collected' : s === 'violation' ? 'unit-violation' : 'unit-pending';
        const icon = s === 'collected' ? '✓' : s === 'violation' ? '!' : i;
        html += `<div class="unit-cell ${cls}" title="Dar ${i} · ${s}">${icon}</div>`;
    }
    grid.innerHTML = html;
}

// ── Stats ──────────────────────────────────────
function updateStats() {
    const collected = Object.values(unitStatuses).filter(s => s === 'collected').length;
    const violations = Object.values(unitStatuses).filter(s => s === 'violation').length;
    const pending = Object.values(unitStatuses).filter(s => s === 'pending').length;
    const pct = Math.round(collected / 30 * 100);

    animateNumber('stat-collected', collected);
    animateNumber('stat-violations', violations);
    animateNumber('stat-pending', pending);

    document.getElementById('points-display').textContent = collected * 45;
    document.getElementById('progress-text').textContent = collected + ' / 30';
    document.getElementById('progress-pct').textContent = pct + '%';
    document.getElementById('progress-fill').style.width = pct + '%';

    if (pending === 0) {
        document.getElementById('completion-badge').textContent = '+20 DH';
        document.getElementById('completion-badge').className = 'badge badge-green';
        document.getElementById('bonus-total').textContent = '+45 DH';
        showToast('🎉 Toutes les dyor collectées! Bonus débloqué!', '#2E7D32');
    }
}

function animateNumber(id, target) {
    const el = document.getElementById(id);
    if (!el) return;
    const current = parseInt(el.textContent) || 0;
    if (current === target) return;
    const step = target > current ? 1 : -1;
    let val = current;
    const timer = setInterval(() => {
        val += step;
        el.textContent = val;
        if (val === target) clearInterval(timer);
    }, 50);
}

// ── Scanner ────────────────────────────────────
let scanning = false;
let scanDone = false;
let lastScanned = null;
let scanAnimId = null;
let scanPos = 20;
let scanDir = 1;

function startScan() {
    if (scanning) return;
    const pending = Object.keys(unitStatuses).filter(k => unitStatuses[k] === 'pending');
    if (pending.length === 0) {
        showToast('🎉 Toutes les dyor sont collectées!', '#2E7D32');
        return;
    }

    scanning = true;
    scanDone = false;
    const btn = document.getElementById('scan-btn');
    btn.disabled = true;
    btn.innerHTML = '<span class="spinning">⟳</span> Scan en cours…';
    document.getElementById('scan-content').innerHTML = '';

    const line = document.getElementById('scan-line');
    line.style.display = 'block';

    function animate() {
        scanPos += scanDir * 2.5;
        if (scanPos >= 88 || scanPos <= 10) scanDir *= -1;
        line.style.top = scanPos + '%';
        scanAnimId = requestAnimationFrame(animate);
    }
    scanAnimId = requestAnimationFrame(animate);

    setTimeout(() => {
        cancelAnimationFrame(scanAnimId);
        line.style.display = 'none';

        const pendingKeys = Object.keys(unitStatuses).filter(k => unitStatuses[k] === 'pending');
        const idx = parseInt(pendingKeys[Math.floor(Math.random() * pendingKeys.length)]);
        lastScanned = { id: idx, ...stops[idx - 1] };

        document.getElementById('scan-content').innerHTML = `
            <div style="display:flex;flex-direction:column;align-items:center;gap:6px">
                <div style="font-size:48px">✅</div>
                <div style="color:#2E7D32;font-size:12px;font-weight:700">QR Validé!</div>
            </div>`;
        document.getElementById('scan-label').textContent = `✓ ${lastScanned.name} · ${lastScanned.resident}`;
        document.getElementById('viol-unit-name').textContent = `${lastScanned.name} · ${lastScanned.resident}`;

        scanning = false;
        scanDone = true;

        document.getElementById('scan-btn-area').style.display = 'none';
        document.getElementById('action-buttons').style.display = 'block';

        showToast(`📱 ${lastScanned.name} détecté — ${lastScanned.addr}`, '#00695C');
    }, 2300);
}

function markCollected() {
    if (!lastScanned) return;
    unitStatuses[lastScanned.id] = 'collected';

    fetch(`/api/collect/${lastScanned.id}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ collector: 'Youssef Benaissa' })
    });

    const name = lastScanned.name;
    resetScanner();
    updateStats();
    renderUnitGrid();
    drawMapMarkers();
    showToast(`✅ ${name} — Mjmoa! +45 pts`, '#2E7D32');
}

function resetScanner() {
    scanDone = false;
    lastScanned = null;
    document.getElementById('scan-content').innerHTML = `
        <div class="scan-idle">
            <div class="scan-idle-icon">▦</div>
            <div>Pointer vers l'autocollant</div>
        </div>`;
    document.getElementById('scan-label').textContent = '';
    const btn = document.getElementById('scan-btn');
    btn.disabled = false;
    btn.innerHTML = '📷 Simuler Scan / محاكاة الكاميرا';
    document.getElementById('scan-btn-area').style.display = 'block';
    document.getElementById('action-buttons').style.display = 'none';
}

// ── Violation Modal ────────────────────────────
let selectedViol = null;

function openViolModal() {
    document.getElementById('viol-modal').style.display = 'flex';
}

function closeViolModal() {
    document.getElementById('viol-modal').style.display = 'none';
    selectedViol = null;
    document.querySelectorAll('.viol-option').forEach(b => b.classList.remove('selected'));
    const btn = document.getElementById('submit-viol-btn');
    btn.disabled = true;
    btn.style.opacity = '0.4';
}

function selectViol(btn, reason) {
    document.querySelectorAll('.viol-option').forEach(b => b.classList.remove('selected'));
    btn.classList.add('selected');
    selectedViol = reason;
    const submitBtn = document.getElementById('submit-viol-btn');
    submitBtn.disabled = false;
    submitBtn.style.opacity = '1';
}

function submitViol() {
    if (!selectedViol || !lastScanned) return;
    unitStatuses[lastScanned.id] = 'violation';

    fetch(`/api/violation/${lastScanned.id}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ collector: 'Youssef Benaissa', reason: selectedViol })
    });

    const name = lastScanned.name;
    closeViolModal();
    resetScanner();
    updateStats();
    renderUnitGrid();
    drawMapMarkers();
    showToast(`⚠️ Violation signalée — ${name}`, '#C62828');
}

// ── Init ───────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    renderUnitGrid();
    updateStats();
    initCollectorMap();
});