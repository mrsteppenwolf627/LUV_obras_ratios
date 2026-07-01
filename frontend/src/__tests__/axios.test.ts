import { afterEach, describe, expect, test, vi } from 'vitest';

afterEach(() => {
  vi.unstubAllEnvs();
  vi.resetModules();
});

describe('resolveApiBaseUrl', () => {
  test('usa /api cuando VITE_API_URL no existe', async () => {
    vi.unstubAllEnvs();
    vi.resetModules();

    const { resolveApiBaseUrl } = await import('../utils/axios');

    expect(resolveApiBaseUrl()).toBe('/api');
  });

  test('usa /api cuando VITE_API_URL llega vacio', async () => {
    vi.stubEnv('VITE_API_URL', '');
    vi.resetModules();

    const { resolveApiBaseUrl } = await import('../utils/axios');

    expect(resolveApiBaseUrl()).toBe('/api');
  });

  test('anade /api cuando la URL configurada apunta solo al host', async () => {
    vi.stubEnv('VITE_API_URL', 'http://localhost:8000');
    vi.resetModules();

    const { resolveApiBaseUrl } = await import('../utils/axios');

    expect(resolveApiBaseUrl()).toBe('http://localhost:8000/api');
  });

  test('no duplica /api cuando la URL ya lo incluye', async () => {
    vi.stubEnv('VITE_API_URL', 'http://localhost:8000/api');
    vi.resetModules();

    const { resolveApiBaseUrl } = await import('../utils/axios');

    expect(resolveApiBaseUrl()).toBe('http://localhost:8000/api');
  });
});
