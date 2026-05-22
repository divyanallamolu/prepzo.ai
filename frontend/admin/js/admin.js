/**
 * Prepzo Admin Dashboard
 * Runs after DOM is ready. Uses demo data if API is unavailable.
 */
const AdminApp = {
  companies: [],
  questions: [],
  timerConfig: null,
  useDemo: false,
  charts: { difficulty: null, category: null },

  DEMO_STATS: { users: 12, companies: 5, questions: 48, sessions: 156, feedback: 8 },
  DEMO_CHARTS: {
    by_difficulty: [{ _id: 'Easy', count: 12 }, { _id: 'Medium', count: 22 }, { _id: 'Hard', count: 14 }],
    by_category: [{ _id: 'Technical', count: 28 }, { _id: 'Behavioral', count: 12 }, { _id: 'HR', count: 8 }],
  },
  DEMO_COMPANIES: [
    { id: 'demo-1', name: 'Google', description: 'Search & cloud', question_count: 15, trending: true, logo: '' },
    { id: 'demo-2', name: 'Amazon', description: 'E-commerce & AWS', question_count: 12, trending: true, logo: '' },
    { id: 'demo-3', name: 'Microsoft', description: 'Software & Azure', question_count: 10, trending: false, logo: '' },
  ],
  DEMO_QUESTIONS: [
    { id: 'dq-1', company_id: 'demo-1', company_name: 'Google', question: 'Explain time complexity of binary search.', answer: 'O(log n)...', explanation: 'Divide and conquer.', category: 'Technical', difficulty: 'Medium' },
    { id: 'dq-2', company_id: 'demo-2', company_name: 'Amazon', question: 'Tell me about a conflict you resolved.', answer: 'STAR format...', explanation: 'Focus on outcome.', category: 'Behavioral', difficulty: 'Easy' },
  ],
  DEMO_USERS: [
    { id: 'du-1', name: 'Demo User', email: 'user@demo.com', streak: 3 },
  ],

  init() {
    if (typeof Api === 'undefined') {
      this.showAlert('API script failed to load. Check /js/api.js path.', 'error');
      return;
    }
    if (!this.checkAuth()) return;

    const user = Api.getUser('admin');
    const label = document.getElementById('admin-user-label');
    if (label && user) label.textContent = user.email || user.name || 'Admin';

    this.bindTabs();
    this.bindForms();
    this.bindFilters();

    document.getElementById('logout-btn')?.addEventListener('click', () => {
      Api.setToken(null, 'admin');
      Api.setUser(null, 'admin');
      window.location.href = '/admin/login.html';
    });

    this.loadOverview();
  },

  checkAuth() {
    if (!Api.getToken('admin')) {
      window.location.href = '/admin/login.html';
      return false;
    }
    return true;
  },

  showAlert(msg, type = 'error') {
    const el = document.getElementById('admin-alert');
    if (!el) return;
    el.textContent = msg;
    el.classList.remove('hidden', 'info');
    if (type === 'info') el.classList.add('info');
    else el.classList.remove('info');
  },

  hideAlert() {
    document.getElementById('admin-alert')?.classList.add('hidden');
  },

  toast(msg, type = 'success') {
    if (typeof Components !== 'undefined' && Components.toast) {
      Components.toast(msg, type);
    } else {
      console.log('[Admin]', type, msg);
    }
  },

  toggleMenu(open) {
    document.getElementById('admin-sidebar')?.classList.toggle('open', open);
    document.getElementById('admin-overlay')?.classList.toggle('open', open);
  },

  closeModal(id) {
    document.getElementById(id)?.classList.remove('open');
  },

  openModal(id) {
    document.getElementById(id)?.classList.add('open');
  },

  bindTabs() {
    document.querySelectorAll('[data-tab]').forEach((btn) => {
      btn.addEventListener('click', () => {
        const tab = btn.dataset.tab;
        document.querySelectorAll('[data-tab]').forEach((b) => b.classList.remove('active'));
        btn.classList.add('active');
        document.querySelectorAll('.tab-panel').forEach((p) => p.classList.remove('active'));
        const panel = document.getElementById('tab-' + tab);
        if (panel) panel.classList.add('active');
        const title = document.getElementById('page-title');
        if (title) title.textContent = btn.textContent.trim();
        this.toggleMenu(false);
        if (tab === 'companies') this.loadCompanies();
        if (tab === 'questions') this.loadQuestions();
        if (tab === 'timers') this.loadTimerSettings();
        if (tab === 'users') this.loadUsers();
        if (tab === 'feedback') this.loadFeedback();
        if (tab === 'overview') this.loadOverview();
      });
    });
  },

  bindForms() {
    document.getElementById('company-form')?.addEventListener('submit', (e) => {
      e.preventDefault();
      this.saveCompany();
    });
    document.getElementById('question-form')?.addEventListener('submit', (e) => {
      e.preventDefault();
      this.saveQuestion();
    });
  },

  bindFilters() {
    document.getElementById('search-companies')?.addEventListener('input', (e) => {
      const q = e.target.value.toLowerCase();
      this.renderCompanies(this.companies.filter((c) => c.name.toLowerCase().includes(q)));
    });
    let searchTimer;
    document.getElementById('search-questions')?.addEventListener('input', () => {
      clearTimeout(searchTimer);
      searchTimer = setTimeout(() => this.loadQuestions(), 350);
    });
    ['filter-category', 'filter-difficulty', 'filter-company'].forEach((id) => {
      document.getElementById(id)?.addEventListener('change', () => this.loadQuestions());
    });
  },

  renderStatCards(stats, demo = false) {
    const el = document.getElementById('stats-cards');
    if (!el) return;
    const badge = demo ? '<span class="demo-badge">DEMO</span>' : '';
    const items = [
      ['Users', stats.users ?? 0],
      ['Companies', stats.companies ?? 0],
      ['Questions', stats.questions ?? 0],
      ['Sessions', stats.sessions ?? 0],
    ];
    el.innerHTML = items
      .map(
        ([label, value]) =>
          `<div class="admin-stat-card glass-card">
            <p class="label">${label}${badge}</p>
            <p class="value">${value}</p>
          </div>`
      )
      .join('');
  },

  renderCharts(chartData, demo = false) {
    if (typeof Chart === 'undefined') {
      console.warn('Chart.js not loaded');
      return;
    }
    const diff = chartData.by_difficulty || [];
    const cat = chartData.by_category || [];
    const diffLabels = diff.length ? diff.map((x) => x._id || 'Unknown') : ['No data'];
    const diffCounts = diff.length ? diff.map((x) => x.count) : [0];
    const catLabels = cat.length ? cat.map((x) => x._id || 'Unknown') : ['No data'];
    const catCounts = cat.length ? cat.map((x) => x.count) : [0];

    const diffCanvas = document.getElementById('chart-difficulty');
    const catCanvas = document.getElementById('chart-category');
    if (!diffCanvas || !catCanvas) return;

    if (this.charts.difficulty) this.charts.difficulty.destroy();
    if (this.charts.category) this.charts.category.destroy();

    const titleSuffix = demo ? ' (demo)' : '';
    this.charts.difficulty = new Chart(diffCanvas, {
      type: 'bar',
      data: {
        labels: diffLabels,
        datasets: [{ label: 'Questions', data: diffCounts, backgroundColor: '#ff4500' }],
      },
      options: {
        responsive: true,
        plugins: { legend: { display: false }, title: { display: true, text: 'By Difficulty' + titleSuffix, color: '#94a3b8' } },
        scales: { y: { beginAtZero: true, ticks: { color: '#94a3b8' } }, x: { ticks: { color: '#94a3b8' } } },
      },
    });

    this.charts.category = new Chart(catCanvas, {
      type: 'doughnut',
      data: {
        labels: catLabels,
        datasets: [{ data: catCounts, backgroundColor: ['#ff4500', '#6366f1', '#06b6d4', '#22c55e'] }],
      },
      options: {
        responsive: true,
        plugins: { title: { display: true, text: 'By Category' + titleSuffix, color: '#94a3b8' }, legend: { labels: { color: '#94a3b8' } } },
      },
    });
  },

  async loadOverview() {
    const el = document.getElementById('stats-cards');
    if (el) el.innerHTML = '<div class="admin-loading">Loading stats...</div>';

    try {
      const stats = await Api.analytics.dashboard();
      const charts = await Api.analytics.charts();
      this.useDemo = false;
      this.hideAlert();
      this.renderStatCards(stats);
      this.renderCharts(charts);
    } catch (ex) {
      console.warn('Admin overview API failed, using demo data:', ex.message);
      this.useDemo = true;
      this.showAlert('API unavailable — showing demo data. Start backend: python backend/app.py', 'info');
      this.renderStatCards(this.DEMO_STATS, true);
      this.renderCharts(this.DEMO_CHARTS, true);
    }
  },

  async loadCompanies() {
    const wrap = document.getElementById('companies-table');
    if (wrap) wrap.innerHTML = '<div class="admin-loading">Loading companies...</div>';

    try {
      this.companies = await Api.companies.list();
      this.hideAlert();
      this.renderCompanies(this.companies);
    } catch (ex) {
      this.companies = this.DEMO_COMPANIES;
      this.renderCompanies(this.companies, true);
      this.toast('Using demo companies — ' + ex.message, 'error');
    }
  },

  renderCompanies(list, demo = false) {
    const el = document.getElementById('companies-table');
    if (!el) return;

    if (!list.length) {
      el.innerHTML = '<div class="empty-state">No companies yet. Click <strong>+ Add Company</strong> to create one.</div>';
      return;
    }

    const demoNote = demo ? ' <span class="demo-badge">DEMO</span>' : '';
    el.innerHTML = `
      <table class="table">
        <thead>
          <tr>
            <th>Logo</th><th>Name</th><th>Questions</th><th>Trending</th><th>Actions</th>
          </tr>
        </thead>
        <tbody>
          ${list
            .map((c) => {
              const logo = c.logo
                ? `<img src="${this.escapeAttr(c.logo)}" alt="" style="width:40px;height:40px;border-radius:10px;object-fit:cover">`
                : `<div class="company-logo" style="width:40px;height:40px;font-size:0.9rem">${this.escapeHtml(c.name.charAt(0))}</div>`;
              const id = this.escapeAttr(c.id);
              return `<tr>
                <td>${logo}</td>
                <td><strong>${this.escapeHtml(c.name)}</strong>${demoNote}</td>
                <td><span class="badge-cat">${c.question_count || 0}</span></td>
                <td>${c.trending ? '<span style="color:#22c55e">Yes</span>' : 'No'}</td>
                <td>
                  <button type="button" class="btn-ghost btn-sm" onclick="AdminApp.editCompany('${id}')">Edit</button>
                  <button type="button" class="btn-ghost btn-sm" style="color:#f87171" onclick="AdminApp.deleteCompany('${id}')">Delete</button>
                </td>
              </tr>`;
            })
            .join('')}
        </tbody>
      </table>`;
  },

  openCompanyModal() {
    document.getElementById('company-modal-title').textContent = 'Add Company';
    document.getElementById('company-form')?.reset();
    const idEl = document.getElementById('company-id');
    if (idEl) idEl.value = '';
    this.openModal('company-modal');
  },

  editCompany(id) {
    const c = this.companies.find((x) => x.id === id);
    if (!c) return;
    document.getElementById('company-modal-title').textContent = 'Edit Company';
    document.getElementById('company-id').value = id;
    document.getElementById('company-name').value = c.name;
    document.getElementById('company-desc').value = c.description || '';
    document.getElementById('company-trending').checked = !!c.trending;
    this.openModal('company-modal');
  },

  async deleteCompany(id) {
    if (id.startsWith('demo-')) {
      this.toast('Demo data cannot be deleted', 'error');
      return;
    }
    if (!confirm('Delete this company and its questions?')) return;
    try {
      await Api.admin.deleteCompany(id);
      this.toast('Company deleted');
      this.loadCompanies();
    } catch (ex) {
      this.toast(ex.message, 'error');
    }
  },

  async saveCompany() {
    if (this.useDemo && !Api.getToken('admin')) {
      this.toast('Connect to backend to save', 'error');
      return;
    }
    const fd = new FormData();
    fd.append('name', document.getElementById('company-name').value);
    fd.append('description', document.getElementById('company-desc').value);
    fd.append('trending', document.getElementById('company-trending').checked);
    const logo = document.getElementById('company-logo').files[0];
    if (logo) fd.append('logo', logo);
    const id = document.getElementById('company-id').value;

    try {
      if (id && !id.startsWith('demo-')) {
        const res = await fetch(`${window.location.origin}/api/companies/${id}`, {
          method: 'PUT',
          headers: { Authorization: 'Bearer ' + Api.getToken('admin') },
          body: fd,
        });
        const data = await res.json().catch(() => ({}));
        if (!res.ok) throw new Error(data.error || 'Update failed');
      } else if (!id) {
        await Api.admin.createCompany(fd);
      } else {
        this.toast('Demo company — start backend to save', 'error');
        return;
      }
      this.closeModal('company-modal');
      this.toast(id ? 'Company updated' : 'Company created');
      this.loadCompanies();
    } catch (ex) {
      this.toast(ex.message, 'error');
    }
  },

  populateCompanyFilters() {
    const opts = this.companies
      .map((c) => `<option value="${this.escapeAttr(c.id)}" data-name="${this.escapeAttr(c.name)}">${this.escapeHtml(c.name)}</option>`)
      .join('');
    const filter = document.getElementById('filter-company');
    const qSel = document.getElementById('q-company');
    if (filter) filter.innerHTML = '<option value="">All Companies</option>' + opts;
    if (qSel) qSel.innerHTML = opts || '<option value="">No companies</option>';
  },

  async loadQuestions() {
    const wrap = document.getElementById('questions-table');
    if (wrap) wrap.innerHTML = '<div class="admin-loading">Loading questions...</div>';

    try {
      if (!this.companies.length) {
        try {
          this.companies = await Api.companies.list();
        } catch {
          this.companies = this.DEMO_COMPANIES;
        }
      }
      this.populateCompanyFilters();
      const search = document.getElementById('search-questions')?.value?.trim() || '';
      const companyId = document.getElementById('filter-company')?.value || '';
      const category = document.getElementById('filter-category')?.value || '';
      const difficulty = document.getElementById('filter-difficulty')?.value || '';
      const params = {};
      if (companyId) params.company_id = companyId;
      if (category) params.category = category;
      if (difficulty) params.difficulty = difficulty;
      if (search) params.search = search;
      this.questions = await Api.questions.list(params);
      this.filterQuestions();
    } catch (ex) {
      this.questions = this.DEMO_QUESTIONS;
      if (!this.companies.length) this.companies = this.DEMO_COMPANIES;
      this.populateCompanyFilters();
      this.filterQuestions(true);
      this.toast('Using demo questions — ' + ex.message, 'error');
    }
  },

  filterQuestions(demo = false) {
    const q = (document.getElementById('search-questions')?.value || '').toLowerCase();
    const cat = document.getElementById('filter-category')?.value || '';
    const diff = document.getElementById('filter-difficulty')?.value || '';
    const companyId = document.getElementById('filter-company')?.value || '';
    const filtered = this.questions.filter(
      (x) =>
        (!companyId || x.company_id === companyId) &&
        (!cat || x.category === cat) &&
        (!diff || x.difficulty === diff) &&
        (x.question.toLowerCase().includes(q) || (x.company_name || '').toLowerCase().includes(q))
    );
    this.renderQuestions(filtered, demo);
  },

  renderQuestions(list, demo = false) {
    const el = document.getElementById('questions-table');
    const countEl = document.getElementById('questions-count');
    if (countEl) countEl.textContent = `${list.length} question(s) shown`;
    if (!el) return;

    if (!list.length) {
      el.innerHTML = '<div class="empty-state">No questions match your filters.</div>';
      return;
    }

    const badge = (cat, diff) => {
      const catB = typeof Components !== 'undefined' ? Components.categoryBadge(cat) : cat;
      const diffB = typeof Components !== 'undefined' ? Components.difficultyBadge(diff) : diff;
      return catB + ' ' + diffB;
    };

    el.innerHTML = `
      <table class="table">
        <thead>
          <tr><th>Company</th><th>Question</th><th>Tags</th><th>Actions</th></tr>
        </thead>
        <tbody>
          ${list
            .map((q) => {
              const id = this.escapeAttr(q.id);
              const text = this.escapeHtml(q.question.length > 80 ? q.question.slice(0, 80) + '…' : q.question);
              return `<tr>
                <td><strong>${this.escapeHtml(q.company_name)}</strong></td>
                <td title="${this.escapeAttr(q.question)}">${text}</td>
                <td>${badge(q.category, q.difficulty)}</td>
                <td>
                  <button type="button" class="btn-ghost btn-sm" onclick="AdminApp.editQuestion('${id}')">Edit</button>
                  <button type="button" class="btn-ghost btn-sm" style="color:#f87171" onclick="AdminApp.deleteQuestion('${id}')">Delete</button>
                </td>
              </tr>`;
            })
            .join('')}
        </tbody>
      </table>${demo ? '<p class="empty-state" style="padding-top:0"><span class="demo-badge">DEMO DATA</span></p>' : ''}`;
  },

  openQuestionModal() {
    if (!this.companies.length) {
      this.toast('Add a company first', 'error');
      return;
    }
    document.getElementById('question-modal-title').textContent = 'Add Question';
    document.getElementById('question-form')?.reset();
    document.getElementById('question-id').value = '';
    this.populateCompanyFilters();
    this.openModal('question-modal');
  },

  editQuestion(id) {
    const q = this.questions.find((x) => x.id === id);
    if (!q) return;
    document.getElementById('question-modal-title').textContent = 'Edit Question';
    document.getElementById('question-id').value = id;
    document.getElementById('q-company').value = q.company_id;
    document.getElementById('q-text').value = q.question;
    document.getElementById('q-answer').value = q.answer || '';
    document.getElementById('q-explanation').value = q.explanation || '';
    document.getElementById('q-year').value = q.year_asked || '';
    document.getElementById('q-difficulty').value = q.difficulty || 'Medium';
    document.getElementById('q-category').value = q.category || 'Technical';
    document.getElementById('q-tags').value = (q.tags || []).join(', ');
    this.openModal('question-modal');
  },

  async deleteQuestion(id) {
    if (id.startsWith('dq-')) {
      this.toast('Demo data cannot be deleted', 'error');
      return;
    }
    if (!confirm('Delete this question?')) return;
    try {
      await Api.admin.deleteQuestion(id);
      this.toast('Question deleted');
      this.loadQuestions();
    } catch (ex) {
      this.toast(ex.message, 'error');
    }
  },

  async saveQuestion() {
    const sel = document.getElementById('q-company');
    const explanation = document.getElementById('q-explanation').value.trim();
    const answer = document.getElementById('q-answer').value;
    const body = {
      company_id: sel.value,
      company_name: sel.options[sel.selectedIndex]?.dataset?.name || '',
      question: document.getElementById('q-text').value,
      answer,
      explanation: explanation || answer,
      year_asked: document.getElementById('q-year').value,
      difficulty: document.getElementById('q-difficulty').value,
      category: document.getElementById('q-category').value,
      tags: document.getElementById('q-tags').value.split(',').map((t) => t.trim()).filter(Boolean),
    };
    const id = document.getElementById('question-id').value;

    try {
      if (id && !id.startsWith('dq-')) await Api.admin.updateQuestion(id, body);
      else if (!id) await Api.admin.createQuestion(body);
      else {
        this.toast('Demo question — start backend to save', 'error');
        return;
      }
      this.closeModal('question-modal');
      this.toast(id ? 'Question updated' : 'Question added');
      this.loadQuestions();
    } catch (ex) {
      this.toast(ex.message, 'error');
    }
  },

  async downloadBulkTemplate() {
    try {
      const res = await fetch(window.location.origin + '/api/questions/bulk/template', {
        headers: { Authorization: 'Bearer ' + Api.getToken('admin') },
      });
      if (!res.ok) throw new Error('Could not download template');
      const blob = await res.blob();
      const a = document.createElement('a');
      a.href = URL.createObjectURL(blob);
      a.download = 'prepzo-questions-template.csv';
      a.click();
      URL.revokeObjectURL(a.href);
    } catch (ex) {
      const csv = 'company_name,difficulty,category,question,answer,explanation\nGoogle,Easy,Technical,"What is OOP?","Classes and objects","Explain encapsulation."\n';
      const blob = new Blob([csv], { type: 'text/csv' });
      const a = document.createElement('a');
      a.href = URL.createObjectURL(blob);
      a.download = 'prepzo-questions-template.csv';
      a.click();
      this.toast('Downloaded local demo template (API offline)', 'info');
    }
  },

  async runBulkUpload() {
    const fileInput = document.getElementById('bulk-file');
    const file = fileInput?.files[0];
    if (!file) {
      this.toast('Select a CSV or JSON file', 'error');
      return;
    }

    const progressWrap = document.getElementById('upload-progress-wrap');
    const progressBar = document.getElementById('upload-progress-bar');
    const resultEl = document.getElementById('bulk-result');
    const btn = document.getElementById('bulk-upload-btn');

    progressWrap?.classList.remove('hidden');
    if (progressBar) progressBar.style.width = '30%';
    if (btn) btn.disabled = true;

    try {
      if (progressBar) progressBar.style.width = '60%';
      const res = await Api.admin.bulkUpload(file);
      if (progressBar) progressBar.style.width = '100%';
      resultEl?.classList.remove('hidden');
      if (resultEl) {
        resultEl.innerHTML = `
          <p style="color:#22c55e;font-weight:600">${this.escapeHtml(res.message)}</p>
          <ul class="text-muted mt-2">
            <li>Inserted: ${res.inserted}</li>
            <li>Skipped duplicates: ${res.skipped_duplicates}</li>
            <li>Total rows: ${res.total_rows}</li>
          </ul>
          ${res.errors?.length ? `<p class="mt-2">Warnings:</p><ul class="text-xs text-muted">${res.errors.map((e) => '<li>' + this.escapeHtml(e) + '</li>').join('')}</ul>` : ''}`;
      }
      this.toast('Imported ' + res.inserted + ' questions');
      fileInput.value = '';
      this.loadQuestions();
      this.loadCompanies();
      this.loadOverview();
    } catch (ex) {
      this.toast(ex.message, 'error');
      resultEl?.classList.remove('hidden');
      if (resultEl) resultEl.innerHTML = `<p style="color:#f87171">${this.escapeHtml(ex.message)}</p>`;
    } finally {
      if (btn) btn.disabled = false;
      setTimeout(() => {
        progressWrap?.classList.add('hidden');
        if (progressBar) progressBar.style.width = '0%';
      }, 800);
    }
  },

  async loadUsers() {
    const el = document.getElementById('users-table');
    if (el) el.innerHTML = '<div class="admin-loading">Loading users...</div>';

    try {
      const users = await Api.users.list();
      this.renderUsers(users);
    } catch (ex) {
      this.renderUsers(this.DEMO_USERS, true);
      this.toast('Using demo users — ' + ex.message, 'error');
    }
  },

  renderUsers(users, demo = false) {
    const el = document.getElementById('users-table');
    if (!el) return;
    if (!users.length) {
      el.innerHTML = '<div class="empty-state">No registered users yet.</div>';
      return;
    }
    el.innerHTML = `
      <table class="table">
        <thead><tr><th>Name</th><th>Email</th><th>Streak</th><th>Actions</th></tr></thead>
        <tbody>
          ${users
            .map((u) => {
              const id = this.escapeAttr(u.id);
              return `<tr>
                <td>${this.escapeHtml(u.name)}${demo ? ' <span class="demo-badge">DEMO</span>' : ''}</td>
                <td>${this.escapeHtml(u.email)}</td>
                <td>${u.streak ?? 0}</td>
                <td><button type="button" class="btn-ghost btn-sm" style="color:#f87171" onclick="AdminApp.deleteUser('${id}')">Delete</button></td>
              </tr>`;
            })
            .join('')}
        </tbody>
      </table>`;
  },

  async deleteUser(id) {
    if (id.startsWith('du-')) {
      this.toast('Demo user cannot be deleted', 'error');
      return;
    }
    if (!confirm('Delete this user?')) return;
    try {
      await Api.users.delete(id);
      this.toast('User deleted');
      this.loadUsers();
    } catch (ex) {
      this.toast(ex.message, 'error');
    }
  },

  async loadFeedback() {
    const el = document.getElementById('feedback-list');
    if (el) el.innerHTML = '<div class="admin-loading">Loading feedback...</div>';

    try {
      const items = await Api.feedback.list();
      this.renderFeedback(items);
    } catch (ex) {
      this.renderFeedback([], false);
      if (el) el.innerHTML = '<div class="empty-state">No feedback loaded. ' + this.escapeHtml(ex.message) + '</div>';
    }
  },

  renderFeedback(items) {
    const el = document.getElementById('feedback-list');
    if (!el) return;
    if (!items.length) {
      el.innerHTML = '<div class="empty-state">No feedback submissions yet.</div>';
      return;
    }
    el.innerHTML = items
      .map(
        (f) => `
      <div class="glass-card">
        <div class="flex justify-between text-sm mb-2">
          <span class="font-semibold">${this.escapeHtml(f.user_name || 'Anonymous')}</span>
          <span class="text-muted">${(f.created_at || '').slice(0, 10)}</span>
        </div>
        <span class="badge-cat">${this.escapeHtml(f.type || 'general')}</span>
        ${f.rating ? `<span class="text-muted ml-2">${'★'.repeat(f.rating)}</span>` : ''}
        <p class="text-sm text-muted mt-2">${this.escapeHtml(f.message)}</p>
      </div>`
      )
      .join('');
  },

  async loadTimerSettings() {
    const list = document.getElementById('company-timers-list');
    if (list) list.innerHTML = '<div class="admin-loading">Loading timer settings...</div>';
    try {
      const cfg = await Api.timer.getAdmin();
      this.timerConfig = cfg;
      if (!this.companies.length) this.companies = cfg.companies || await Api.companies.list();

      const d = cfg.defaults || {};
      document.getElementById('def-thinking').value = d.thinking_seconds ?? 180;
      document.getElementById('def-interview').value = d.interview_duration_seconds ?? 1200;
      document.getElementById('def-reveal-delay').value = d.reveal_delay_seconds ?? 0;
      document.getElementById('def-auto-reveal').checked = d.auto_reveal !== false;

      const bd = cfg.by_difficulty || {};
      document.getElementById('diff-easy').value = bd.Easy?.thinking_seconds ?? 120;
      document.getElementById('diff-medium').value = bd.Medium?.thinking_seconds ?? 240;
      document.getElementById('diff-hard').value = bd.Hard?.thinking_seconds ?? 360;

      this.renderCompanyTimerRows(cfg.by_company || {}, cfg.companies || this.companies);
      document.getElementById('timer-save-status').textContent =
        cfg.updated_at ? `Last saved: ${cfg.updated_at.slice(0, 19)}` : '';
    } catch (ex) {
      if (list) list.innerHTML = `<p class="text-muted">${this.escapeHtml(ex.message)}</p>`;
      this.toast(ex.message, 'error');
    }
  },

  renderCompanyTimerRows(byCompany, companies) {
    const list = document.getElementById('company-timers-list');
    if (!list) return;
    const ids = Object.keys(byCompany);
    if (!ids.length) {
      list.innerHTML = '<p class="text-sm text-muted">No company overrides yet.</p>';
      return;
    }
    list.innerHTML = ids
      .map((cid) => this.companyTimerRowHtml(cid, byCompany[cid], companies))
      .join('');
  },

  companyTimerRowHtml(companyId, cfg, companies) {
    const name =
      companies.find((c) => c.id === companyId)?.name || companyId;
    return `<div class="flex flex-wrap gap-3 items-end mb-4 p-4 rounded-xl" style="border:1px solid var(--border)" data-cid="${this.escapeAttr(companyId)}">
      <div style="flex:1;min-width:140px">
        <label class="label">Company</label>
        <select class="select company-timer-select">${companies
          .map(
            (c) =>
              `<option value="${this.escapeAttr(c.id)}" ${c.id === companyId ? 'selected' : ''}>${this.escapeHtml(c.name)}</option>`
          )
          .join('')}</select>
      </div>
      <div><label class="label">Thinking (sec)</label><input type="number" class="input ct-thinking" min="30" value="${cfg.thinking_seconds ?? ''}"></div>
      <div><label class="label">Session (sec)</label><input type="number" class="input ct-session" min="300" value="${cfg.interview_duration_seconds ?? ''}"></div>
      <div><label class="label">Reveal delay</label><input type="number" class="input ct-delay" min="0" value="${cfg.reveal_delay_seconds ?? 0}"></div>
      <div><label class="label">Auto reveal</label><input type="checkbox" class="ct-auto" ${cfg.auto_reveal !== false ? 'checked' : ''}></div>
      <button type="button" class="btn-ghost btn-sm" style="color:#f87171" onclick="AdminApp.removeCompanyTimerRow(this)">Remove</button>
    </div>`;
  },

  addCompanyTimerRow() {
    const list = document.getElementById('company-timers-list');
    if (!list) return;
    const companies = this.timerConfig?.companies || this.companies;
    if (!companies.length) {
      this.toast('Load companies first', 'error');
      return;
    }
    const first = companies[0];
    const row = document.createElement('div');
    row.innerHTML = this.companyTimerRowHtml(first.id, { thinking_seconds: 180, auto_reveal: true }, companies);
    list.appendChild(row.firstElementChild);
    if (list.querySelector('.text-muted')) list.querySelector('.text-muted')?.remove();
  },

  removeCompanyTimerRow(btn) {
    btn.closest('[data-cid]')?.remove();
  },

  collectCompanyTimers() {
    const byCompany = {};
    document.querySelectorAll('#company-timers-list [data-cid]').forEach((row) => {
      const cid = row.querySelector('.company-timer-select')?.value;
      if (!cid) return;
      const thinking = parseInt(row.querySelector('.ct-thinking')?.value, 10);
      const session = parseInt(row.querySelector('.ct-session')?.value, 10);
      const delay = parseInt(row.querySelector('.ct-delay')?.value, 10);
      const auto = row.querySelector('.ct-auto')?.checked;
      byCompany[cid] = {};
      if (!isNaN(thinking)) byCompany[cid].thinking_seconds = thinking;
      if (!isNaN(session)) byCompany[cid].interview_duration_seconds = session;
      if (!isNaN(delay)) byCompany[cid].reveal_delay_seconds = delay;
      byCompany[cid].auto_reveal = auto;
    });
    return byCompany;
  },

  async saveTimerSettings() {
    const body = {
      defaults: {
        thinking_seconds: parseInt(document.getElementById('def-thinking').value, 10) || 180,
        interview_duration_seconds: parseInt(document.getElementById('def-interview').value, 10) || 1200,
        reveal_delay_seconds: parseInt(document.getElementById('def-reveal-delay').value, 10) || 0,
        auto_reveal: document.getElementById('def-auto-reveal').checked,
      },
      by_difficulty: {
        Easy: { thinking_seconds: parseInt(document.getElementById('diff-easy').value, 10) || 120 },
        Medium: { thinking_seconds: parseInt(document.getElementById('diff-medium').value, 10) || 240 },
        Hard: { thinking_seconds: parseInt(document.getElementById('diff-hard').value, 10) || 360 },
      },
      by_company: this.collectCompanyTimers(),
    };
    try {
      const res = await Api.timer.saveAdmin(body);
      this.timerConfig = { ...this.timerConfig, ...body };
      document.getElementById('timer-save-status').textContent = `Saved at ${res.updated_at?.slice(0, 19) || 'now'}`;
      this.toast('Timer settings saved');
    } catch (ex) {
      this.toast(ex.message, 'error');
    }
  },

  escapeHtml(s) {
    if (s == null) return '';
    return String(s)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  },

  escapeAttr(s) {
    return this.escapeHtml(s).replace(/'/g, '&#39;');
  },
};

document.addEventListener('DOMContentLoaded', () => AdminApp.init());
