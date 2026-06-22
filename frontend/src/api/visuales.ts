import type {
  CapituloRatioResponse,
  ComparativaResponse,
  Item,
  ItemRatioResponse,
  PresupuestoAnalisis,
} from '@/types/visuales';

const API_BASE = '/api';
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

export const getCapitulosRatios = async (
  options: RequestOptions = {},
): Promise<CapituloRatioResponse[]> => {
  const { signal, cleanup } = buildTimeoutSignal(DEFAULT_TIMEOUT_MS, options.signal);
  try {
    const response = await fetch(`${API_BASE}/ratios/chapters`, {
      method: 'GET',
      headers: {
        Accept: 'application/json',
        'Content-Type': 'application/json',
      },
      signal,
    });
    return await parseJsonResponse<CapituloRatioResponse[]>(response);
  } catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError') {
      throw new Error('La peticion ha excedido el tiempo de espera.');
    }
    throw error;
  } finally {
    cleanup();
  }
};

export const getItemsList = async (options: RequestOptions = {}): Promise<Item[]> => {
  const { signal, cleanup } = buildTimeoutSignal(DEFAULT_TIMEOUT_MS, options.signal);
  try {
    const response = await fetch(`${API_BASE}/items/list`, {
      method: 'GET',
      headers: {
        Accept: 'application/json',
        'Content-Type': 'application/json',
      },
      signal,
    });
    const payload = await parseJsonResponse<{ items: Item[] }>(response);
    return payload.items;
  } catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError') {
      throw new Error('La peticion ha excedido el tiempo de espera.');
    }
    throw error;
  } finally {
    cleanup();
  }
};

export const getItemRatio = async (
  itemMasterId: number,
  options: RequestOptions = {},
): Promise<ItemRatioResponse> => {
  const { signal, cleanup } = buildTimeoutSignal(DEFAULT_TIMEOUT_MS, options.signal);
  try {
    const response = await fetch(`${API_BASE}/ratios/item/${itemMasterId}`, {
      method: 'GET',
      headers: {
        Accept: 'application/json',
        'Content-Type': 'application/json',
      },
      signal,
    });
    return await parseJsonResponse<ItemRatioResponse>(response);
  } catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError') {
      throw new Error('La peticion ha excedido el tiempo de espera.');
    }
    throw error;
  } finally {
    cleanup();
  }
};

export const analizarComparativa = async (
  presupuesto: PresupuestoAnalisis,
  options: RequestOptions = {},
): Promise<ComparativaResponse> => {
  const { signal, cleanup } = buildTimeoutSignal(DEFAULT_TIMEOUT_MS, options.signal);
  try {
    const response = await fetch(`${API_BASE}/analyze/comparativa`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(presupuesto),
      signal,
    });
    return await parseJsonResponse<ComparativaResponse>(response);
  } catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError') {
      throw new Error('La peticion ha excedido el tiempo de espera.');
    }
    throw error;
  } finally {
    cleanup();
  }
};
