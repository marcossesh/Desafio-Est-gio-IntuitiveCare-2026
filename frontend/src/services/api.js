import axios from 'axios';

const api = axios.create({
    baseURL: 'http://localhost:8000/api'
});

export const getOperadoras = (page, limit, search = '') => api.get(`/operadoras?page=${page}&limit=${limit}&q=${search}`);
export const getStatsUF = () => api.get('/estatisticas/uf');
export const getOperadoraDetails = (cnpj) => api.get(`/operadoras/${cnpj}`);
export const getOperadoraDespesas = (cnpj) => api.get(`/operadoras/${cnpj}/despesas`);
