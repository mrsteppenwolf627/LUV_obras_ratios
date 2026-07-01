import axios from 'axios';

const resolveApiBaseUrl = (): string => {
  const rawBaseUrl = (import.meta.env.VITE_API_URL as string | undefined)?.trim();

  if (!rawBaseUrl) {
    return '/api';
  }

  const normalizedBaseUrl = rawBaseUrl.replace(/\/+$/, '');
  return normalizedBaseUrl.endsWith('/api')
    ? normalizedBaseUrl
    : `${normalizedBaseUrl}/api`;
};

const api = axios.create({
  baseURL: resolveApiBaseUrl(),
  headers: {
    'Content-Type': 'application/json',
  },
});

export default api;
export { resolveApiBaseUrl };
