const Components = {
  logo(size = 'md', href = '/') {
    const heights = { sm: 'h-7', md: 'h-9', lg: 'h-12', xl: 'h-16' };
    const h = heights[size] || heights.md;
    return `<a href="${href}" class="brand-logo inline-flex items-center shrink-0 mt-1">
      <img src="/assets/logo.png" alt="Prepzo" class="${h} w-auto max-w-[200px] object-contain object-left" />
    </a>`;
  },

  navbar(links = []) {
    const user = Api.getUser();
    return `
    <nav class="fixed top-0 left-0 right-0 z-50 border-b border-[var(--border)] bg-[var(--bg-primary)]/80 backdrop-blur-xl">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        <a href="/" class="brand-logo inline-flex items-center shrink-0">
          <img src="/assets/logo.png" alt="Prepzo" class="h-9 w-auto max-w-[180px] object-contain object-left" />
        </a>
        <div class="hidden md:flex items-center gap-8">
          ${links.map(l => `<a href="${l.href}" class="text-sm text-[var(--text-muted)] hover:text-[var(--accent)] transition">${l.label}</a>`).join('')}
        </div>
        <div class="flex items-center gap-4">
          <div class="theme-toggle" data-theme-toggle title="Toggle theme">
            <div class="theme-toggle-knob"></div>
          </div>
          ${user ? `
            <a href="/dashboard.html" class="text-sm font-medium hover:text-[var(--accent)] transition">${user.name}</a>
          ` : `
            <a href="/auth.html" class="btn-ghost text-sm">Log in</a>
            <a href="/auth.html?mode=register" class="btn-primary text-sm">Get Started</a>
          `}
        </div>
      </div>
    </nav>`;
  },

  footer() {
    return `
    <footer class="border-t border-[var(--border)] py-16 mt-24">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="grid md:grid-cols-4 gap-12">
          <div>
            ${Components.logo('lg', '/')}
            <p class="font-mono text-sm text-[var(--text-muted)]">Prepare. Practice. Perform.</p>
          </div>
          <div>
            <h4 class="font-semibold mb-4">Product</h4>
            <ul class="space-y-2 text-sm text-[var(--text-muted)]">
              <li><a href="/dashboard.html" class="hover:text-[var(--accent)]">Dashboard</a></li>
              <li><a href="#features" class="hover:text-[var(--accent)]">Features</a></li>
              <li><a href="#faq" class="hover:text-[var(--accent)]">FAQ</a></li>
            </ul>
          </div>
          <div>
            <h4 class="font-semibold mb-4">Companies</h4>
            <ul class="space-y-2 text-sm text-[var(--text-muted)]">
              <li>Google · Amazon · Microsoft</li>
              <li>Meta · Apple · Netflix</li>
            </ul>
          </div>
          <div>
            <h4 class="font-semibold mb-4">Admin</h4>
            <a href="/admin/login.html" class="text-sm text-[var(--text-muted)] hover:text-[var(--accent)]">Admin Portal</a>
          </div>
        </div>
        <div class="mt-12 pt-8 border-t border-[var(--border)] text-center text-sm text-[var(--text-muted)]">
          © ${new Date().getFullYear()} Prepzo. All rights reserved.
        </div>
      </div>
    </footer>`;
  },

  difficultyBadge(level) {
    const cls = { Easy: 'badge-easy', Medium: 'badge-medium', Hard: 'badge-hard' }[level] || 'badge-medium';
    return `<span class="px-2.5 py-0.5 rounded-full text-xs font-medium ${cls}">${level}</span>`;
  },

  categoryBadge(cat) {
    return `<span class="px-2.5 py-0.5 rounded-full text-xs font-medium bg-indigo-500/15 text-indigo-400">${cat}</span>`;
  },

  companyCard(company, onClick = '') {
    const initial = company.name.charAt(0);
    return `
    <div class="glass-card p-6 cursor-pointer group" ${onClick ? `onclick="${onClick}"` : ''}>
      <div class="flex items-center gap-4 mb-4">
        ${company.logo
          ? `<img src="${company.logo}" alt="${company.name}" class="w-12 h-12 rounded-xl object-cover">`
          : `<div class="company-logo">${initial}</div>`}
        <div>
          <h3 class="font-semibold group-hover:text-[var(--accent)] transition">${company.name}</h3>
          <p class="text-xs text-[var(--text-muted)]">${company.question_count || 0} questions</p>
        </div>
      </div>
      <p class="text-sm text-[var(--text-muted)] line-clamp-2">${company.description || ''}</p>
    </div>`;
  },

  loading() {
    return `<div class="flex justify-center py-20"><div class="spinner"></div></div>`;
  },

  toast(message, type = 'success') {
    const el = document.createElement('div');
    el.className = `fixed bottom-6 right-6 z-[100] px-6 py-3 rounded-xl text-sm font-medium fade-in ${
      type === 'error' ? 'bg-red-500/90 text-white' : 'bg-[var(--accent)] text-white'
    }`;
    el.textContent = message;
    document.body.appendChild(el);
    setTimeout(() => el.remove(), 3000);
  },
};
