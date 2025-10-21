import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Products API
export const productsApi = {
  getAll: (params) => api.get('/products/', { params }),
  getOne: (barcode) => api.get(`/products/${barcode}`),
  create: (data) => api.post('/products/', data),
  update: (barcode, data) => api.patch(`/products/${barcode}`, data),
  delete: (barcode) => api.delete(`/products/${barcode}`),
  getBrands: () => api.get('/products/filters/brands'),
  getCategories: () => api.get('/products/filters/categories'),
};

// Imports API
export const importsApi = {
  import1C: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/imports/1c', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  importWBBarcodes: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/imports/wb/barcodes', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  importWBPrices: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/imports/wb/prices', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  importWBMinPrices: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/imports/wb/min-prices', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  importOzonBarcodes: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/imports/ozon/barcodes', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  importOzonPrices: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/imports/ozon/prices', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  getLogs: (limit = 50) => api.get('/imports/logs', { params: { limit } }),
};

// Exports API
export const exportsApi = {
  exportToWB: () => api.get('/exports/wb', { responseType: 'blob' }),
  exportToOzon: () => api.get('/exports/ozon', { responseType: 'blob' }),
  exportFull: () => api.get('/exports/full', { responseType: 'blob' }),
};

export default api;