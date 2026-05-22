/**
 * Prepzo API client
 * - Development: http://localhost:5000/api
 * - Production (Vercel): relative /api on same origin
 */
(function () {
  function getApiBase() {
    const { hostname, port, protocol } = window.location;
    const isLocal =
      hostname === 'localhost' ||
      hostname === '127.0.0.1' ||
      hostname === '[::1]' ||
      port === '5000' ||
      port === '5500';

    if (isLocal && port !== '' && port !== '80' && port !== '443') {
      // Flask dev server serves API on same origin when using python app.py
      if (port === '5000') return `${protocol}//${hostname}:${port}/api`;
      // Live Server / other static ports → point to Flask
      return `${protocol}//${hostname}:5000/api`;
    }
    // Vercel production: same-origin /api
    return '/api';
  }

  const API_BASE = getApiBase();
  const API_BASE_URL = API_BASE;
  console.log('API BASE:', API_BASE_URL);

  const DEBUG = localStorage.getItem('prepzo_debug') === '1' || getApiBase().includes('localhost');

  function log(...args) {
    if (DEBUG) console.log('[Prepzo API]', ...args);
  }

  function logError(endpoint, err, res) {
    console.error('[Prepzo API Error]', {
      endpoint,
      base: API_BASE,
      message: err?.message || err,
      status: res?.status,
      url: `${API_BASE}${endpoint}`,
    });
  }

  var Api = {
    baseUrl: API_BASE,
    baseUrlFull: API_BASE_URL,

    async health() {
      return this.request('/health');
    },

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

      const url = `${API_BASE}${endpoint}`;
      log(options.method || 'GET', url);

      let res;
      try {
        res = await fetch(url, {
          method: options.method || 'GET',
          headers,
          body: options.body ? JSON.stringify(options.body) : undefined,
        });
      } catch (networkErr) {
        logError(endpoint, networkErr);
        throw new Error(
          `Cannot reach API at ${API_BASE}. ${networkErr.message}. ` +
            (API_BASE.startsWith('/')
              ? 'Check Vercel env vars (MONGO_URI) and redeploy.'
              : 'Start backend: cd backend && python app.py')
        );
      }

      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        logError(endpoint, new Error(data.error || res.statusText), res);
        if (res.status === 404) {
          throw new Error(`API not found (404): ${url}. Check Vercel api/index.py deployment.`);
        }
        throw new Error(data.error || `Request failed (${res.status})`);
      }
      return data;
    },

    async formRequest(endpoint, formData, role = 'admin') {
      const token = this.getToken(role);
      const headers = {};
      if (token) headers['Authorization'] = `Bearer ${token}`;
      const url = `${API_BASE}${endpoint}`;
      const res = await fetch(url, { method: 'POST', headers, body: formData });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        logError(endpoint, new Error(data.error), res);
        throw new Error(data.error || `Request failed (${res.status})`);
      }
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
        return Api.request(`/questions${qs ? `?${qs}` : ''}`);
      },
      get: (id) => Api.request(`/questions/${id}`),
      daily: () => Api.request('/questions/daily'),
      mixed: (limit = 20) => Api.request(`/questions/mixed?limit=${limit}`),
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

    timer: {
      get: (query = '') => Api.request(`/timer/settings${query}`),
      getAdmin: () => Api.request('/timer/settings/admin', { role: 'admin' }),
      saveAdmin: (body) => Api.request('/timer/settings/admin', { method: 'PUT', body, role: 'admin' }),
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
      bulkUploadJson: (questions) =>
        Api.request('/questions/bulk', { method: 'POST', body: { questions }, role: 'admin' }),
    },
  };

  function requireAuth(redirect = '/auth.html') {
    if (!Api.getToken()) {
      window.location.href = redirect;
      return false;
    }
    return true;
  }

  function requireAdmin(redirect = '/admin/login.html') {
    if (!Api.getToken('admin')) {
      window.location.replace(redirect);
      return false;
    }
    return true;
  }

  window.Api = Api;
  window.requireAuth = requireAuth;
  window.requireAdmin = requireAdmin;

  // Ping API on load (non-blocking)
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
      Api.health().then((h) => log('health', h)).catch((e) => log('health skip', e.message));
    });
  }
})();
