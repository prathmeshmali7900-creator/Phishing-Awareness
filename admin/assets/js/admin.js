// Shared admin JS: auth guard, sidebar, fetch wrapper, logout
const API = '';

function getToken(){ return localStorage.getItem('token'); }
function getRole(){ return localStorage.getItem('role'); }

// Auth guard
if(getRole() !== 'admin'){
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

// Sidebar template
const SIDEBAR_TEMPLATE = `
<div class="brand">
    <div class="brand-logo"><i class="bi bi-shield-lock-fill"></i></div>
    <div class="brand-text">
        <h1>CyberSec Admin</h1>
        <small>Security Console</small>
    </div>
</div>
<nav class="nav">
    <div class="nav-label">Main</div>
    <a class="nav-item" data-nav="dashboard" href="dashboard.html"><i class="bi bi-grid-1x2"></i><span>Dashboard</span></a>
    <a class="nav-item" data-nav="users" href="users.html"><i class="bi bi-people"></i><span>Users</span></a>
<a class="nav-item" data-nav="campaigns" href="campaigns.html"><i class="bi bi-bullseye"></i><span>Campaigns</span></a>
    <a class="nav-item" data-nav="quizzes" href="quizzes.html"><i class="bi bi-patch-question"></i><span>Quiz Management</span></a>
    <a class="nav-item" data-nav="templates" href="templates.html"><i class="bi bi-envelope-paper"></i><span>Templates</span></a>
    <div class="nav-label">Insights</div>
    <a class="nav-item" data-nav="responses" href="responses.html"><i class="bi bi-activity"></i><span>Responses</span></a>
    <a class="nav-item" data-nav="analytics" href="analytics.html"><i class="bi bi-graph-up-arrow"></i><span>Analytics</span></a>
    <a class="nav-item" data-nav="reports" href="reports.html"><i class="bi bi-file-earmark-bar-graph"></i><span>Reports</span></a>
    <div class="nav-label">System</div>
    <a class="nav-item" data-nav="settings" href="settings.html"><i class="bi bi-gear"></i><span>Settings</span></a>
</nav>
<div class="sidebar-footer">
    <div class="profile-card">
        <div class="profile-avatar" id="sidebarAvatar">A</div>
        <div class="profile-info">
            <strong id="sidebarAdminName">Administrator</strong>
            <span id="sidebarAdminEmail">admin@cybersec.com</span>
        </div>
    </div>
</div>
`;

function initSidebar(active){
    const sb = document.getElementById('sidebar');
    if(sb){
        sb.innerHTML = SIDEBAR_TEMPLATE;
        const name = localStorage.getItem('name') || 'Administrator';
        const emailEl = document.getElementById('sidebarAdminEmail');
        const nameEl = document.getElementById('sidebarAdminName');
        const avatarEl = document.getElementById('sidebarAvatar');
        if(nameEl) nameEl.textContent = name;
        if(emailEl) emailEl.textContent = name;
        if(avatarEl) avatarEl.textContent = name.split(' ').map(w=>w[0]).slice(0,2).join('').toUpperCase();
        const item = sb.querySelector(`[data-nav="${active}"]`);
        if(item) item.classList.add('active');
    }
}

function initTopbar(){
    const topbar = document.getElementById('topbar');
    if(!topbar) return;
    topbar.innerHTML = `
        <div class="topbar-left">
            <button class="hamburger" onclick="toggleSidebar()"><i class="bi bi-list"></i></button>
            <div class="topbar-title">
                <h2 id="pageTitle">Dashboard</h2>
                <small id="pageSubtitle">Security overview</small>
            </div>
        </div>
        <div class="topbar-actions">
            <button class="btn-logout" onclick="logout()"><i class="bi bi-box-arrow-right"></i>Logout</button>
        </div>
    `;
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

// escape helper
function esc(s){ return (s||'').toString().replace(/[&<>"']/g, m=>({'&':'&amp;','<':'<','>':'>','"':'"',"'":'&#39;'}[m])); }

// risk badge helper
function riskBadge(level){
    const map = {Low:'risk-low', Medium:'risk-medium', High:'risk-high'};
    return `<span class="badge-risk ${map[level]||'risk-medium'}">${esc(level)}</span>`;
}

// status badge helper
function statusBadge(status){
    const map = {active:'status-active', inactive:'status-inactive', scheduled:'status-scheduled', pending:'status-pending'};
    return `<span class="badge-risk ${map[status]||'status-inactive'}">${esc(status)}</span>`;
}
