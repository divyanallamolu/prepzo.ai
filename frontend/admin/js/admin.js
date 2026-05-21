if (typeof Api === 'undefined') {
  alert('Failed to load API scripts. Press Ctrl+F5 to refresh.');
  throw new Error('Api not loaded');
}
if (!requireAdmin()) throw new Error('admin auth');

let companies = [];
let questions = [];

function toast(msg, type = 'success') {
  Components.toast(msg, type);
}

window.toggleAdminMenu = (open) => {
  document.getElementById('admin-sidebar')?.classList.toggle('open', open);
  document.getElementById('admin-overlay')?.classList.toggle('open', open);
};

document.getElementById('logout').onclick = () => {
  Api.setToken(null, 'admin');
  Api.setUser(null, 'admin');
  location.href = '/admin/login.html';
};

document.querySelectorAll('[data-tab]').forEach(btn => {
  btn.onclick = () => {
    document.querySelectorAll('[data-tab]').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    document.querySelectorAll('.tab-panel').forEach(p => p.classList.add('hidden'));
    document.getElementById('tab-' + btn.dataset.tab).classList.remove('hidden');
    const title = document.getElementById('page-title');
    if (title) title.textContent = btn.textContent;
    toggleAdminMenu(false);
    if (btn.dataset.tab === 'companies') loadCompanies();
    if (btn.dataset.tab === 'questions') loadQuestions();
    if (btn.dataset.tab === 'users') loadUsers();
    if (btn.dataset.tab === 'feedback') loadFeedback();
  };
});

function closeModal(id) {
  document.getElementById(id).classList.add('hidden');
  document.getElementById(id).classList.remove('flex');
}
function openModal(id) {
  document.getElementById(id).classList.remove('hidden');
  document.getElementById(id).classList.add('flex');
}

async function loadOverview() {
  try {
    const stats = await Api.analytics.dashboard();
    document.getElementById('stats-cards').innerHTML = [
      ['Users', stats.users], ['Companies', stats.companies],
      ['Questions', stats.questions], ['Sessions', stats.sessions],
    ].map(([l, v]) => `<div class="glass-card p-5"><p class="text-xs text-[var(--text-muted)]">${l}</p><p class="text-3xl font-bold text-[var(--accent)]">${v}</p></div>`).join('');

    const charts = await Api.analytics.charts();
    new Chart(document.getElementById('chart-difficulty'), {
      type: 'bar',
      data: {
        labels: charts.by_difficulty.map(x => x._id || 'Unknown'),
        datasets: [{ label: 'Questions', data: charts.by_difficulty.map(x => x.count), backgroundColor: '#FF4500' }],
      },
      options: { plugins: { legend: { display: false }, title: { display: true, text: 'By Difficulty', color: '#9CA3AF' } }, scales: { y: { beginAtZero: true } } },
    });
    new Chart(document.getElementById('chart-category'), {
      type: 'doughnut',
      data: {
        labels: charts.by_category.map(x => x._id || 'Unknown'),
        datasets: [{ data: charts.by_category.map(x => x.count), backgroundColor: ['#FF4500', '#6366F1', '#06B6D4', '#22C55E'] }],
      },
      options: { plugins: { title: { display: true, text: 'By Category', color: '#9CA3AF' } } },
    });
  } catch (ex) {
    document.getElementById('stats-cards').innerHTML = `<p class="text-[var(--text-muted)]">${ex.message}</p>`;
  }
}

async function loadCompanies() {
  try {
    companies = await Api.companies.list();
    renderCompanies(companies);
  } catch (ex) {
    toast(ex.message, 'error');
  }
}

function renderCompanies(list) {
  document.getElementById('companies-table').innerHTML = list.length ? `
    <table class="w-full text-sm">
      <thead><tr class="border-b border-[var(--border)] text-left text-[var(--text-muted)]">
        <th class="p-4">Logo</th><th class="p-4">Name</th><th class="p-4">Questions</th><th class="p-4">Trending</th><th class="p-4">Actions</th>
      </tr></thead>
      <tbody>${list.map(c => `<tr class="border-b border-[var(--border)] hover:bg-[var(--bg-secondary)]/50">
        <td class="p-4">${c.logo ? `<img src="${c.logo}" class="w-10 h-10 rounded-lg object-cover" alt="">` : `<div class="company-logo w-10 h-10 text-sm">${c.name.charAt(0)}</div>`}</td>
        <td class="p-4 font-medium">${c.name}</td>
        <td class="p-4"><span class="px-2 py-0.5 rounded-full bg-[var(--accent)]/15 text-[var(--accent)] text-xs">${c.question_count || 0}</span></td>
        <td class="p-4">${c.trending ? '<span class="text-green-400">Yes</span>' : 'No'}</td>
        <td class="p-4 whitespace-nowrap">
          <button onclick="editCompany('${c.id}')" class="text-[var(--accent)] mr-3">Edit</button>
          <button onclick="deleteCompany('${c.id}')" class="text-red-400">Delete</button>
        </td>
      </tr>`).join('')}</tbody>
    </table>` : '<p class="p-6 text-[var(--text-muted)]">No companies yet. Add your first company.</p>';
}

window.openCompanyModal = () => {
  document.getElementById('company-modal-title').textContent = 'Add Company';
  document.getElementById('company-form').reset();
  document.getElementById('company-id').value = '';
  openModal('company-modal');
};

window.editCompany = (id) => {
  const c = companies.find(x => x.id === id);
  if (!c) return;
  document.getElementById('company-modal-title').textContent = 'Edit Company';
  document.getElementById('company-id').value = id;
  document.getElementById('company-name').value = c.name;
  document.getElementById('company-desc').value = c.description || '';
  document.getElementById('company-trending').checked = c.trending;
  openModal('company-modal');
};

window.deleteCompany = async (id) => {
  if (!confirm('Delete company and all its questions?')) return;
  try {
    await Api.admin.deleteCompany(id);
    toast('Company deleted');
    loadCompanies();
  } catch (ex) { toast(ex.message, 'error'); }
};

document.getElementById('company-form').onsubmit = async (e) => {
  e.preventDefault();
  const fd = new FormData();
  fd.append('name', document.getElementById('company-name').value);
  fd.append('description', document.getElementById('company-desc').value);
  fd.append('trending', document.getElementById('company-trending').checked);
  const logo = document.getElementById('company-logo').files[0];
  if (logo) fd.append('logo', logo);
  const id = document.getElementById('company-id').value;
  try {
    if (id) {
      const res = await fetch(`/api/companies/${id}`, {
        method: 'PUT',
        headers: { Authorization: 'Bearer ' + Api.getToken('admin') },
        body: fd,
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data.error || 'Update failed');
    } else {
      await Api.admin.createCompany(fd);
    }
    closeModal('company-modal');
    toast(id ? 'Company updated' : 'Company created');
    loadCompanies();
  } catch (ex) { toast(ex.message, 'error'); }
};

function populateCompanyFilters() {
  const sel = document.getElementById('filter-company');
  const qSel = document.getElementById('q-company');
  const opts = companies.map(c => `<option value="${c.id}" data-name="${c.name}">${c.name}</option>`).join('');
  if (sel) sel.innerHTML = '<option value="">All Companies</option>' + opts;
  if (qSel) qSel.innerHTML = opts;
}

async function loadQuestions() {
  try {
    if (!companies.length) companies = await Api.companies.list();
    populateCompanyFilters();
    questions = await Api.questions.list();
    filterQuestions();
  } catch (ex) {
    toast(ex.message, 'error');
  }
}

function renderQuestions(list) {
  const countEl = document.getElementById('questions-count');
  if (countEl) countEl.textContent = `${list.length} question(s) shown`;
  document.getElementById('questions-table').innerHTML = list.length ? `
    <table class="w-full text-sm">
      <thead><tr class="border-b border-[var(--border)] text-left text-[var(--text-muted)]">
        <th class="p-3">Company</th><th class="p-3">Question</th><th class="p-3">Category</th><th class="p-3">Difficulty</th><th class="p-3">Actions</th>
      </tr></thead>
      <tbody>${list.map(q => `<tr class="border-b border-[var(--border)] hover:bg-[var(--bg-secondary)]/50">
        <td class="p-3 font-medium">${q.company_name}</td>
        <td class="p-3 max-w-xs truncate" title="${q.question.replace(/"/g, '&quot;')}">${q.question}</td>
        <td class="p-3">${Components.categoryBadge(q.category)}</td>
        <td class="p-3">${Components.difficultyBadge(q.difficulty)}</td>
        <td class="p-3 whitespace-nowrap">
          <button onclick="editQuestion('${q.id}')" class="text-[var(--accent)] mr-2">Edit</button>
          <button onclick="deleteQuestion('${q.id}')" class="text-red-400">Delete</button>
        </td>
      </tr>`).join('')}</tbody>
    </table>` : '<p class="p-6 text-[var(--text-muted)]">No questions found.</p>';
}

window.openQuestionModal = () => {
  if (!companies.length) { toast('Add a company first', 'error'); return; }
  document.getElementById('question-modal-title').textContent = 'Add Question';
  document.getElementById('question-form').reset();
  document.getElementById('question-id').value = '';
  populateCompanyFilters();
  openModal('question-modal');
};

window.editQuestion = (id) => {
  const q = questions.find(x => x.id === id);
  if (!q) return;
  document.getElementById('question-modal-title').textContent = 'Edit Question';
  document.getElementById('question-id').value = id;
  document.getElementById('q-company').value = q.company_id;
  document.getElementById('q-text').value = q.question;
  document.getElementById('q-answer').value = q.answer || '';
  document.getElementById('q-explanation').value = q.explanation || '';
  document.getElementById('q-year').value = q.year_asked || '';
  document.getElementById('q-difficulty').value = q.difficulty;
  document.getElementById('q-category').value = q.category;
  document.getElementById('q-tags').value = (q.tags || []).join(', ');
  openModal('question-modal');
};

window.deleteQuestion = async (id) => {
  if (!confirm('Delete this question?')) return;
  try {
    await Api.admin.deleteQuestion(id);
    toast('Question deleted');
    loadQuestions();
  } catch (ex) { toast(ex.message, 'error'); }
};

document.getElementById('question-form').onsubmit = async (e) => {
  e.preventDefault();
  const sel = document.getElementById('q-company');
  const explanation = document.getElementById('q-explanation').value.trim();
  const answer = document.getElementById('q-answer').value;
  const body = {
    company_id: sel.value,
    company_name: sel.options[sel.selectedIndex].dataset.name,
    question: document.getElementById('q-text').value,
    answer,
    explanation: explanation || answer,
    year_asked: document.getElementById('q-year').value,
    difficulty: document.getElementById('q-difficulty').value,
    category: document.getElementById('q-category').value,
    tags: document.getElementById('q-tags').value.split(',').map(t => t.trim()).filter(Boolean),
  };
  const id = document.getElementById('question-id').value;
  try {
    if (id) await Api.admin.updateQuestion(id, body);
    else await Api.admin.createQuestion(body);
    closeModal('question-modal');
    toast(id ? 'Question updated' : 'Question added');
    loadQuestions();
  } catch (ex) { toast(ex.message, 'error'); }
};

document.getElementById('search-companies')?.addEventListener('input', (e) => {
  const q = e.target.value.toLowerCase();
  renderCompanies(companies.filter(c => c.name.toLowerCase().includes(q)));
});

document.getElementById('search-questions')?.addEventListener('input', filterQuestions);
document.getElementById('filter-category')?.addEventListener('change', filterQuestions);
document.getElementById('filter-difficulty')?.addEventListener('change', filterQuestions);
document.getElementById('filter-company')?.addEventListener('change', filterQuestions);

function filterQuestions() {
  const q = (document.getElementById('search-questions')?.value || '').toLowerCase();
  const cat = document.getElementById('filter-category')?.value || '';
  const diff = document.getElementById('filter-difficulty')?.value || '';
  const companyId = document.getElementById('filter-company')?.value || '';
  renderQuestions(questions.filter(x =>
    (!companyId || x.company_id === companyId) &&
    (!cat || x.category === cat) &&
    (!diff || x.difficulty === diff) &&
    (x.question.toLowerCase().includes(q) || x.company_name.toLowerCase().includes(q))
  ));
}

window.downloadBulkTemplate = async () => {
  try {
    const res = await fetch('/api/questions/bulk/template', {
      headers: { Authorization: 'Bearer ' + Api.getToken('admin') },
    });
    if (!res.ok) throw new Error('Could not download template');
    const blob = await res.blob();
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'prepzo-questions-template.csv';
    a.click();
    URL.revokeObjectURL(a.href);
  } catch (ex) { toast(ex.message, 'error'); }
};

window.runBulkUpload = async () => {
  const fileInput = document.getElementById('bulk-file');
  const file = fileInput?.files[0];
  if (!file) { toast('Select a CSV or JSON file', 'error'); return; }

  const progressWrap = document.getElementById('upload-progress-wrap');
  const progressBar = document.getElementById('upload-progress-bar');
  const resultEl = document.getElementById('bulk-result');
  const btn = document.getElementById('bulk-upload-btn');

  progressWrap?.classList.remove('hidden');
  if (progressBar) progressBar.style.width = '30%';
  btn.disabled = true;

  try {
    if (progressBar) progressBar.style.width = '60%';
    const res = await Api.admin.bulkUpload(file);
    if (progressBar) progressBar.style.width = '100%';
    resultEl.classList.remove('hidden');
    resultEl.innerHTML = `
      <p class="text-green-400 font-medium">${res.message}</p>
      <ul class="mt-2 text-[var(--text-muted)] space-y-1">
        <li>Inserted: ${res.inserted}</li>
        <li>Skipped duplicates: ${res.skipped_duplicates}</li>
        <li>Total rows: ${res.total_rows}</li>
      </ul>
      ${res.errors?.length ? `<p class="mt-2 text-amber-400">Warnings:</p><ul class="text-xs text-[var(--text-muted)]">${res.errors.map(e => `<li>${e}</li>`).join('')}</ul>` : ''}`;
    toast(`Imported ${res.inserted} questions`);
    fileInput.value = '';
    loadQuestions();
    loadCompanies();
  } catch (ex) {
    toast(ex.message, 'error');
    resultEl.classList.remove('hidden');
    resultEl.innerHTML = `<p class="text-red-400">${ex.message}</p>`;
  } finally {
    btn.disabled = false;
    setTimeout(() => {
      progressWrap?.classList.add('hidden');
      if (progressBar) progressBar.style.width = '0%';
    }, 800);
  }
};

async function loadUsers() {
  try {
    const users = await Api.users.list();
    document.getElementById('users-table').innerHTML = users.length ? `
      <table class="w-full text-sm">
        <thead><tr class="border-b border-[var(--border)] text-left text-[var(--text-muted)]">
          <th class="p-4">Name</th><th class="p-4">Email</th><th class="p-4">Streak</th><th class="p-4">Actions</th>
        </tr></thead>
        <tbody>${users.map(u => `<tr class="border-b border-[var(--border)]">
          <td class="p-4">${u.name}</td><td class="p-4">${u.email}</td><td class="p-4">${u.streak}</td>
          <td class="p-4"><button onclick="deleteUser('${u.id}')" class="text-red-400">Delete</button></td>
        </tr>`).join('')}</tbody>
      </table>` : '<p class="p-6 text-[var(--text-muted)]">No users yet.</p>';
  } catch (ex) { toast(ex.message, 'error'); }
}

window.deleteUser = async (id) => {
  if (!confirm('Delete user?')) return;
  try {
    await Api.users.delete(id);
    toast('User deleted');
    loadUsers();
  } catch (ex) { toast(ex.message, 'error'); }
};

async function loadFeedback() {
  try {
    const items = await Api.feedback.list();
    document.getElementById('feedback-list').innerHTML = items.length ? items.map(f => `
      <div class="glass-card p-4">
        <div class="flex justify-between text-sm mb-2">
          <span class="font-medium">${f.user_name}</span>
          <span class="text-[var(--text-muted)]">${(f.created_at || '').slice(0, 10)}</span>
        </div>
        <span class="text-xs px-2 py-0.5 rounded bg-[var(--accent)]/20 text-[var(--accent)]">${f.type}</span>
        ${f.rating ? `<span class="text-xs ml-2 text-amber-400">${'★'.repeat(f.rating)}</span>` : ''}
        <p class="mt-2 text-sm text-[var(--text-muted)]">${f.message}</p>
      </div>
    `).join('') : '<p class="text-[var(--text-muted)]">No feedback yet</p>';
  } catch (ex) { toast(ex.message, 'error'); }
}

loadOverview();
