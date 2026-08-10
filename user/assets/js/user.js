// Shared user JS: auth guard, sidebar, fetch wrapper, logout, helpers
const API = '';

function getToken(){ return localStorage.getItem('token'); }
function getRole(){ return localStorage.getItem('role'); }

// Auth guard - users only
if(getRole() !== 'user'){
    window.location.href = '/login.html';
}

async function apiFetch(url, options={}){
    const headers = Object.assign({'Content-Type':'application/json'}, options.headers||{});
    if(getToken()) headers['Authorization'] = 'Bearer ' + getToken();
    const res = await fetch(url, Object.assign({}, options, {headers}));
    const data = await res.json().catch(()=>({}));
    if(res.status === 401 || res.status === 403){
        logout();
        throw new Error(data.error || 'Unauthorized');
    }
    if(!res.ok) throw new Error(data.error || 'Request failed');
    return data;
}

function logout(){
    localStorage.removeItem('token');
    localStorage.removeItem('role');
    localStorage.removeItem('name');
    window.location.href = '/login.html';
}

function toggleSidebar(){
    document.querySelector('.sidebar').classList.toggle('open');
}

const SIDEBAR_TEMPLATE = `
<div class="brand">
    <div class="brand-logo"><i class="bi bi-shield-lock-fill"></i></div>
    <div class="brand-text">
        <h1>CyberSec Learn</h1>
        <small>Awareness Portal</small>
    </div>
</div>
<nav class="nav">
    <div class="nav-label">Learn</div>
    <a class="nav-item" data-nav="dashboard" href="dashboard.html"><i class="bi bi-grid-1x2"></i> Dashboard</a>
    <a class="nav-item" data-nav="simulations" href="simulations.html"><i class="bi bi-envelope-at"></i> Simulations</a>
    <a class="nav-item" data-nav="training" href="training.html"><i class="bi bi-book"></i> Training</a>
    <a class="nav-item" data-nav="quiz" href="quiz.html"><i class="bi bi-patch-question"></i> Quiz</a>
    <div class="nav-label">Progress</div>
    <a class="nav-item" data-nav="results" href="results.html"><i class="bi bi-bar-chart"></i> Results</a>
    <a class="nav-item" data-nav="profile" href="profile.html"><i class="bi bi-person-circle"></i> Profile</a>
</nav>
<div class="sidebar-footer">
    <div class="profile-card">
        <div class="profile-avatar" id="sidebarAvatar">${avatarInitials()}</div>
        <div class="profile-info">
            <strong id="sidebarUserName">Learner</strong>
            <span id="sidebarUserEmail">Learner</span>
        </div>
    </div>
</div>
`;

function initSidebar(active){
    const sb = document.getElementById('sidebar');
    if(sb){
        sb.innerHTML = SIDEBAR_TEMPLATE;
        const name = localStorage.getItem('name') || 'Learner';
        const emailEl = document.getElementById('sidebarUserEmail');
        if(emailEl) emailEl.textContent = name;
        const item = sb.querySelector(`[data-nav="${active}"]`);
        if(item) item.classList.add('active');
    }
}

function initTopbar(){
    const topbar = document.getElementById('topbar');
    if(!topbar) return;
    topbar.innerHTML = `
        <div class="hamburger" onclick="toggleSidebar()"><i class="bi bi-list"></i></div>
        <div class="title">
            <h2 id="pageTitle">Dashboard</h2>
            <small id="pageSubtitle">Your awareness overview</small>
        </div>
        <div class="ms-auto d-flex align-items-center gap-2">
            <div class="avatar-user" id="avatarUser">${avatarInitials()}</div>
            <button class="btn-logout" onclick="logout()"><i class="bi bi-box-arrow-right me-1"></i>Logout</button>
        </div>
    `;
}

function avatarInitials(){
    const name = localStorage.getItem('name') || 'User';
    return name.split(' ').map(w=>w[0]).slice(0,2).join('').toUpperCase();
}

function setPageTitle(title, sub){
    const t = document.getElementById('pageTitle');
    const s = document.getElementById('pageSubtitle');
    if(t) t.textContent = title;
    if(s) s.textContent = sub;
}

function toast(msg, type='success'){
    let container = document.getElementById('toastContainer');
    if(!container){
        container = document.createElement('div');
        container.id = 'toastContainer';
        container.style.cssText = 'position:fixed;top:20px;right:20px;z-index:2000;display:flex;flex-direction:column;gap:10px;';
        document.body.appendChild(container);
    }
const colors = {success:'#2ed573', danger:'#ff6b6b', warning:'#ffc048', info:'#00b4ff'};
    const el = document.createElement('div');
el.style.cssText = `background:#131c2d;border:1px solid ${colors[type]||'#1e2d44'};color:#FFFFFF;padding:12px 18px;border-radius:10px;font-size:.85rem;box-shadow:0 8px 24px rgba(0,0,0,.4);min-width:220px;`;
el.innerHTML = `<span style="color:${colors[type]||'#2ed573'}">●</span> ${msg}`;
    container.appendChild(el);
    setTimeout(()=>el.remove(), 3000);
}

function esc(s){ return (s||'').toString().replace(/[&<>"']/g, m=>({'&':'&amp;','<':'<','>':'>','"':'"',"'":'&#39;'}[m])); }

function riskBadge(level){
    const map = {Low:'risk-low', Medium:'risk-medium', High:'risk-high'};
    return `<span class="badge-risk ${map[level]||'risk-medium'}">${esc(level)}</span>`;
}

function scoreRing(selector, score, color='#00ffb4'){
    const el = document.querySelector(selector);
    if(!el) return;
    const r = 63;
    const circ = 2 * Math.PI * r;
    const filled = circ * (score/100);
    el.innerHTML = `
        <div class="score-ring">
            <svg viewBox="0 0 150 150" width="150" height="150">
                <circle class="ring-bg" cx="75" cy="75" r="${r}"></circle>
                <circle class="ring-val" cx="75" cy="75" r="${r}" stroke="${color}"
                    stroke-dasharray="${circ}" stroke-dashoffset="${circ - filled}"></circle>
            </svg>
            <div class="ring-text">
                <div class="num">${score}%</div>
                <div class="lbl">Awareness</div>
            </div>
        </div>
    `;
}
