const API_BASE_URL = 'http://localhost:8000/api/v1';

class ApiService {
  constructor() {
    this.tokenKey = 'invoice_ocr_token';
  }

  setToken(token) {
    localStorage.setItem(this.tokenKey, token);
  }

  getToken() {
    return localStorage.getItem(this.tokenKey);
  }

  logout() {
    localStorage.removeItem(this.tokenKey);
  }

  isAuthenticated() {
    return !!this.getToken();
  }

  async request(endpoint, options = {}) {
    const token = this.getToken();
    const headers = {
      ...(options.headers || {}),
    };

    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const config = {
      ...options,
      headers,
    };

    try {
      const response = await fetch(`${API_BASE_URL}${endpoint}`, config);
      
      if (response.status === 401) {
        this.logout();
        window.dispatchEvent(new Event('auth-change'));
        throw new Error('Session expired. Please log in again.');
      }

      if (response.status === 204) {
        return null;
      }

      const data = await response.json();
      
      if (!response.ok) {
        let errorMessage = 'An unexpected error occurred.';
        
        if (data && data.detail) {
          if (typeof data.detail === 'string') {
            // Standard string error messages (e.g. HTTPException)
            errorMessage = data.detail;
          } else if (Array.isArray(data.detail)) {
            // FastAPI 422 validation array error structures
            errorMessage = data.detail
              .map(err => {
                const fieldName = err.loc ? err.loc[err.loc.length - 1] : 'value';
                return `${fieldName}: ${err.msg}`;
              })
              .join(', ');
          } else if (typeof data.detail === 'object') {
            errorMessage = JSON.stringify(data.detail);
          }
        }
        throw new Error(errorMessage);
      }
      return data;
    } catch (error) {
      console.error(`API Error on ${endpoint}:`, error);
      throw error;
    }
  }

  // --- Auth Endpoints ---
  async login(username, password) {
    const params = new URLSearchParams();
    params.append('username', username);
    params.append('password', password);

    const data = await this.request('/auth/token', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: params,
    });
    
    if (data && data.access_token) {
      this.setToken(data.access_token);
      window.dispatchEvent(new Event('auth-change'));
    }
    return data;
  }

  async register(username, password) {
    return this.request('/auth/register', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ username, password }),
    });
  }

  // --- OCR & Invoice Endpoints ---
  async uploadInvoice(file, language = 'auto') {
    const formData = new FormData();
    formData.append('invoice_image', file);
    formData.append('language', language);

    return this.request('/invoice/upload', {
      method: 'POST',
      body: formData,
    });
  }

  async getInvoices({ page = 1, pageSize = 20, search = '', sortBy = 'created_at', sortDir = 'desc' }) {
    let query = `?page=${page}&page_size=${pageSize}&sort_by=${sortBy}&sort_dir=${sortDir}`;
    if (search) {
      query += `&search=${encodeURIComponent(search)}`;
    }
    return this.request(`/invoices${query}`, { method: 'GET' });
  }

  async getInvoiceById(id) {
    return this.request(`/invoices/${id}`, { method: 'GET' });
  }

  async deleteInvoice(id) {
    return this.request(`/invoices/${id}`, { method: 'DELETE' });
  }

  async getHealth() {
    return this.request('/health', { method: 'GET' });
  }
}

export const api = new ApiService();