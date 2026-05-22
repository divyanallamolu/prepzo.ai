/**
 * Prepzo — reusable HTML components
 */
const Components = {
  logo(size = 'md', href = '/') {
    const heights = { sm: '32px', md: '40px', lg: '56px', xl: '72px' };
    const h = heights[size] || heights.md;
    return `<a href="${href}" class="brand-logo" style="line-height:0">
      <img src="/assets/logo.png" alt="Prepzo" style="height:${h};width:auto;max-width:220px;object-fit:contain" />
    </a>`;
  },

  pageLoader() {
    return `<div id="page-loader"><div class="spinner"></div><p class="text-sm text-muted">Loading Prepzo...</p></div>`;
  },

  navbar(links = [], opts = {}) {
    const user = typeof Api !== 'undefined' ? Api.getUser() : null;
    const linkHtml = links
      .map((l) => `<a href="${l.href}">${l.label}</a>`)
      .join('');
    const authHtml = user
      ? `<a href="/dashboard.html" class="btn-ghost btn-sm">${user.name}</a>`
      : `<a href="/auth.html" class="btn-ghost btn-sm">Log in</a>
         <a href="/auth.html?mode=register" class="btn-primary btn-sm">Get Started</a>`;

    return `
    <header class="navbar">
      <div class="navbar-inner">
        ${Components.logo('md', '/')}
        <nav class="nav-links">${linkHtml}</nav>
        <div class="nav-actions">
          <div class="theme-toggle" data-theme-toggle title="Toggle theme"><div class="theme-toggle-knob"></div></div>
          ${authHtml}
          <button type="button" class="mobile-menu-btn" id="mobile-menu-btn" aria-label="Menu">☰</button>
        </div>
      </div>
      <nav class="mobile-nav" id="mobile-nav">${linkHtml}${authHtml}</nav>
    </header>`;
  },

  footer() {
    const y = new Date().getFullYear();
    return `
    <footer class="footer">
      <div class="container">
        <div class="footer-grid">
          <div>
            ${Components.logo('lg', '/')}
            <p class="brand-tagline mt-4">Prepare. Practice. Perform.</p>
            <p class="text-sm text-muted mt-4">AI-powered interview prep for top tech companies.</p>
          </div>
          <div>
            <h4 class="font-semibold mb-4">Product</h4>
            <ul class="text-sm text-muted" style="list-style:none;display:flex;flex-direction:column;gap:0.5rem">
              <li><a href="/dashboard.html">Dashboard</a></li>
              <li><a href="/#features">Features</a></li>
              <li><a href="/auth.html">Sign In</a></li>
            </ul>
          </div>
          <div>
            <h4 class="font-semibold mb-4">Practice</h4>
            <ul class="text-sm text-muted" style="list-style:none;display:flex;flex-direction:column;gap:0.5rem">
              <li>Google · Amazon · Microsoft</li>
              <li>Meta · Apple · Netflix</li>
            </ul>
          </div>
          <div>
            <h4 class="font-semibold mb-4">Admin</h4>
            <a href="/admin/login.html" class="text-sm text-muted">Admin Portal →</a>
          </div>
        </div>
        <p class="text-center text-sm text-muted" style="padding-top:2rem;border-top:1px solid var(--border)">
          © ${y} Prepzo. All rights reserved.
        </p>
      </div>
    </footer>`;
  },

  difficultyBadge(level) {
    const cls = { Easy: 'badge-easy', Medium: 'badge-medium', Hard: 'badge-hard' }[level] || 'badge-medium';
    return `<span class="${cls}">${level}</span>`;
  },

  categoryBadge(cat) {
    const styles = {
      HR: 'badge-cat',
      Technical: 'badge-cat',
      Behavioral: 'badge-cat',
      DSA: 'badge-dsa',
      'System Design': 'badge-sys',
      Communication: 'badge-comm',
    };
    const cls = styles[cat] || 'badge-cat';
    return `<span class="${cls}">${cat}</span>`;
  },

  companyCard(company, onClick = '') {
    const initial = (company.name || '?').charAt(0);
    const logo = company.logo
      ? `<img src="${company.logo}" alt="" class="company-logo-img" onerror="this.style.display='none';this.nextElementSibling.style.display='flex'"><div class="company-logo-fallback" style="display:none">${initial}</div>`
      : `<div class="company-logo-fallback">${initial}</div>`;
    const trending = company.trending ? '<span class="trending-pill">Trending</span>' : '';
    const diff = company.difficulty ? Components.difficultyBadge(company.difficulty) : '';
    return `
    <div class="company-card-premium" ${onClick ? `onclick="${onClick}"` : ''} role="button" tabindex="0">
      <div class="company-card-header">
        ${logo}
        <div style="flex:1;min-width:0">
          <div class="flex items-center gap-2 flex-wrap">
            <h3 style="font-size:1.15rem;font-weight:700;margin:0">${company.name}</h3>
            ${trending}
          </div>
          <p class="text-sm text-muted" style="margin-top:0.25rem">${company.question_count || 0} questions · ${company.hiring_status || 'Hiring'}</p>
        </div>
      </div>
      <p class="text-sm text-muted" style="line-height:1.5;margin-bottom:0.75rem">${(company.description || '').slice(0, 120)}${(company.description || '').length > 120 ? '…' : ''}</p>
      <div class="company-meta-row">${diff}<span class="badge-cat">${company.category || 'Tech'}</span></div>
      <div class="flex justify-between items-center mt-2 flex-wrap gap-2">
        <span class="company-salary">${company.estimated_salary || ''}</span>
        <span class="company-prep-time">⏱ ${company.preparation_time || '4–6 weeks'}</span>
      </div>
    </div>`;
  },

  appSidebar(active = 'dashboard') {
    const items = [
      { id: 'dashboard', label: 'Dashboard', icon: '◆', href: '/dashboard.html' },
      { id: 'analytics', label: 'Analytics', icon: '▣', href: '/analytics.html' },
      { id: 'results', label: 'Results', icon: '◎', href: '/results.html' },
    ];
    return `
    <aside class="sidebar" id="app-sidebar">
      <a href="/" style="display:block;margin-bottom:2rem"><img src="/assets/logo.png" alt="Prepzo" style="height:44px;width:auto"></a>
      <nav style="flex:1;display:flex;flex-direction:column;gap:0.35rem">
        ${items.map((i) => `<a href="${i.href}" class="sidebar-link ${active === i.id ? 'active' : ''}"><span class="sidebar-icon">${i.icon}</span>${i.label}</a>`).join('')}
        <button type="button" id="nav-leaderboard" class="sidebar-link"><span class="sidebar-icon">★</span>Leaderboard</button>
      </nav>
      <button type="button" id="logout-btn" class="sidebar-link" style="color:#f87171;margin-top:1rem"><span class="sidebar-icon">⎋</span>Logout</button>
    </aside>
    <div class="sidebar-overlay" id="sidebar-overlay" onclick="AppUI.toggleSidebar(false)"></div>`;
  },

  loading() {
    return `<div class="flex justify-center" style="padding:4rem 0"><div class="spinner"></div></div>`;
  },

  toast(message, type = 'success') {
    const el = document.createElement('div');
    el.className = `toast toast-${type}`;
    el.textContent = message;
    document.body.appendChild(el);
    setTimeout(() => el.remove(), 3200);
  },

  dashboardSidebar(active = 'dashboard') {
    const items = [
      { id: 'dashboard', label: 'Dashboard', href: '/dashboard.html' },
      { id: 'results', label: 'Results', href: '/results.html' },
    ];
    return `
    <aside class="sidebar" id="app-sidebar">
      <a href="/" class="brand-logo" style="margin-bottom:2rem;display:block">${Components.logo('md', '/').replace(/<a[^>]*>|<\/a>/g, '')}</a>
      <nav style="flex:1;display:flex;flex-direction:column;gap:0.25rem">
        ${items.map((i) => `<a href="${i.href}" class="sidebar-link ${active === i.id ? 'active' : ''}">${i.label}</a>`).join('')}
      </nav>
      <button type="button" id="logout-btn" class="sidebar-link" style="color:#f87171">Logout</button>
    </aside>
    <div class="sidebar-overlay" id="sidebar-overlay" onclick="AppUI.toggleSidebar(false)"></div>`;
  },
};
