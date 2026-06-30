import type {
  MasterApproveRejectBody,
  MasterImportRecord,
  MasterStatusResponse,
} from '@/types/master';

const API_BASE = '/api/master';
const DEFAULT_TIMEOUT_MS = 10000;

type RequestOptions = {
  signal?: AbortSignal;
};

const buildTimeoutSignal = (timeoutMs: number, externalSignal?: AbortSignal) => {
  const timeoutController = new AbortController();
  const timeoutId = globalThis.setTimeout(() => timeoutController.abort(), timeoutMs);

  if (externalSignal) {
    if (externalSignal.aborted) {
      timeoutController.abort(externalSignal.reason);
    } else {
      externalSignal.addEventListener('abort', () => timeoutController.abort(externalSignal.reason), {
        once: true,
      });
    }
  }

  return {
    signal: timeoutController.signal,
    cleanup: () => globalThis.clearTimeout(timeoutId),
  };
};

const parseJsonResponse = async <T>(response: Response): Promise<T> => {
  const rawBody = await response.text();

  if (!response.ok) {
    let detail = response.statusText;
    try {
      const parsed = rawBody ? (JSON.parse(rawBody) as { detail?: string }) : null;
      if (parsed?.detail) {
        detail = parsed.detail;
      }
    } catch {
      // Fallback to status text when the body is not valid JSON.
    }
    throw new Error(`HTTP ${response.status}: ${detail || 'Error de API'}`);
  }

  try {
    return JSON.parse(rawBody) as T;
  } catch {
    throw new Error('La API devolvio una respuesta no valida.');
  }
};

const requestJson = async <T>(
  url: string,
  init: RequestInit,
  options: RequestOptions = {},
): Promise<T> => {
  const { signal, cleanup } = buildTimeoutSignal(DEFAULT_TIMEOUT_MS, options.signal);
  try {
    const response = await fetch(url, {
      ...init,
      headers: {
        Accept: 'application/json',
        'Content-Type': 'application/json',
        ...(init.headers ?? {}),
      },
      signal,
    });
    return await parseJsonResponse<T>(response);
  } catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError') {
      throw new Error('La peticion ha excedido el tiempo de espera.');
    }
    throw error;
  } finally {
    cleanup();
  }
};

export const getMasterStatus = async (
  options: RequestOptions = {},
): Promise<MasterStatusResponse> => {
  return requestJson<MasterStatusResponse>(`${API_BASE}/status`, { method: 'GET' }, options);
};

export const getPendingMasterImports = async (
  options: RequestOptions = {},
): Promise<MasterImportRecord[]> => {
  return requestJson<MasterImportRecord[]>(`${API_BASE}/imports/pending`, { method: 'GET' }, options);
};

export const getMasterImportDetail = async (
  importId: number,
  options: RequestOptions = {},
): Promise<MasterImportRecord> => {
  return requestJson<MasterImportRecord>(`${API_BASE}/imports/${importId}`, { method: 'GET' }, options);
};

export const approveMasterImport = async (
  importId: number,
  body: MasterApproveRejectBody,
  options: RequestOptions = {},
): Promise<MasterImportRecord> => {
  return requestJson<MasterImportRecord>(
    `${API_BASE}/imports/${importId}/approve`,
    {
      method: 'POST',
      body: JSON.stringify(body),
    },
    options,
  );
};

export const rejectMasterImport = async (
  importId: number,
  body: MasterApproveRejectBody,
  options: RequestOptions = {},
): Promise<MasterImportRecord> => {
  return requestJson<MasterImportRecord>(
    `${API_BASE}/imports/${importId}/reject`,
    {
      method: 'POST',
      body: JSON.stringify(body),
    },
    options,
  );
};
