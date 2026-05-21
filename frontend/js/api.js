const API_BASE = window.location.origin + '/api';

var Api = {
  getToken(role = 'user') {
    return localStorage.getItem(role === 'admin' ? 'prepzo_admin_token' : 'prepzo_token');
  },

  setToken(token, role = 'user') {
    const key = role === 'admin' ? 'prepzo_admin_token' : 'prepzo_token';
    if (token) localStorage.setItem(key, token);
    else localStorage.removeItem(key);
  },

  setUser(user, role = 'user') {
    const key = role === 'admin' ? 'prepzo_admin_user' : 'prepzo_user';
    if (user) localStorage.setItem(key, JSON.stringify(user));
    else localStorage.removeItem(key);
  },

  getUser(role = 'user') {
    const key = role === 'admin' ? 'prepzo_admin_user' : 'prepzo_user';
    const data = localStorage.getItem(key);
    return data ? JSON.parse(data) : null;
  },

  async request(endpoint, options = {}) {
    const role = options.role || 'user';
    const token = this.getToken(role);
    const headers = { 'Content-Type': 'application/json', ...options.headers };
    if (token) headers['Authorization'] = `Bearer ${token}`;

    const res = await fetch(`${API_BASE}${endpoint}`, {
      ...options,
      headers,
      body: options.body ? JSON.stringify(options.body) : undefined,
    });

    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.error || `Request failed (${res.status})`);
    return data;
  },

  async formRequest(endpoint, formData, role = 'admin') {
    const token = this.getToken(role);
    const headers = {};
    if (token) headers['Authorization'] = `Bearer ${token}`;
    const res = await fetch(`${API_BASE}${endpoint}`, {
      method: 'POST',
      headers,
      body: formData,
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.error || `Request failed (${res.status})`);
    return data;
  },

  auth: {
    register: (body) => Api.request('/auth/register', { method: 'POST', body }),
    login: (body) => Api.request('/auth/login', { method: 'POST', body }),
    adminLogin: (body) => Api.request('/auth/admin/login', { method: 'POST', body }),
  },

  companies: {
    list: (trending) => Api.request(`/companies${trending ? '?trending=true' : ''}`),
    get: (id) => Api.request(`/companies/${id}`),
  },

  questions: {
    list: (params = {}) => {
      const qs = new URLSearchParams(params).toString();
      return Api.request(`/questions?${qs}`);
    },
    get: (id) => Api.request(`/questions/${id}`),
    daily: () => Api.request('/questions/daily'),
  },

  progress: {
    save: (body) => Api.request('/progress', { method: 'POST', body }),
    list: (companyId) => Api.request(`/progress${companyId ? `?company_id=${companyId}` : ''}`),
    stats: () => Api.request('/progress/stats'),
    leaderboard: () => Api.request('/progress/leaderboard'),
    bookmarks: () => Api.request('/progress/bookmarks'),
    bookmark: (body) => Api.request('/progress/bookmarks', { method: 'POST', body }),
    unbookmark: (id) => Api.request(`/progress/bookmarks/${id}`, { method: 'DELETE' }),
  },

  evaluate: (body) => Api.request('/evaluate', { method: 'POST', body }),

  feedback: {
    submit: (body) => Api.request('/feedback', { method: 'POST', body }),
    list: () => Api.request('/feedback', { role: 'admin' }),
  },

  users: {
    me: () => Api.request('/users/me'),
    list: () => Api.request('/users', { role: 'admin' }),
    delete: (id) => Api.request(`/users/${id}`, { method: 'DELETE', role: 'admin' }),
  },

  analytics: {
    dashboard: () => Api.request('/analytics/dashboard', { role: 'admin' }),
    charts: () => Api.request('/analytics/charts', { role: 'admin' }),
  },

  admin: {
    createCompany: (formData) => Api.formRequest('/companies', formData),
    updateCompany: (id, formData) => {
      formData.append('_method', 'PUT');
      return Api.formRequest(`/companies/${id}`, formData);
    },
    deleteCompany: (id) => Api.request(`/companies/${id}`, { method: 'DELETE', role: 'admin' }),
    createQuestion: (body) => Api.request('/questions', { method: 'POST', body, role: 'admin' }),
    updateQuestion: (id, body) => Api.request(`/questions/${id}`, { method: 'PUT', body, role: 'admin' }),
    deleteQuestion: (id) => Api.request(`/questions/${id}`, { method: 'DELETE', role: 'admin' }),
    bulkUpload: (file) => {
      const fd = new FormData();
      fd.append('file', file);
      return Api.formRequest('/questions/bulk', fd, 'admin');
    },
    bulkUploadJson: (questions) => Api.request('/questions/bulk', { method: 'POST', body: { questions }, role: 'admin' }),
  },
};

function requireAuth(redirect = '/auth.html') {
  if (!Api.getToken()) {
    window.location.href = redirect;
    return false;
  }
  return true;
}

function requireAdmin() {
  if (!Api.getToken('admin')) {
    window.location.href = '/admin/login.html';
    return false;
  }
  return true;
}

if (typeof window !== 'undefined') {
  window.Api = Api;
}
