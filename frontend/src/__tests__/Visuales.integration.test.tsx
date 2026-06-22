import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, test, vi } from 'vitest';

import Visuales from '@/pages/Visuales';

const itemsPayload = [
  {
    id: 1,
    item_key: 'vigas metalicas estructura',
    descripcion: 'Vigas Metalicas Estructura',
    categoria: 'ESTRUCTURA',
    categoria_asignada: 'ESTRUCTURA',
    gama_asignada: 'SIN_CLASIFICAR',
    muestras_count: 2,
    ratio_actual: null,
  },
  {
    id: 2,
    item_key: 'forjado hormigon estructura',
    descripcion: 'Forjado Hormigon Estructura',
    categoria: 'ESTRUCTURA',
    categoria_asignada: 'ESTRUCTURA',
    gama_asignada: 'SIN_CLASIFICAR',
    muestras_count: 2,
    ratio_actual: null,
  },
];

const chaptersPayload = [
  {
    capitulo: 'ESTRUCTURA',
    descripcion: 'Estructura',
    minimo: 280,
    percentil_25: 310,
    mediana: 334.67,
    percentil_75: 350,
    maximo: 450,
    desviacion_std: 45.3,
    cantidad_datos: 8,
    estado_confiabilidad: 'solido',
  },
];

const itemStatsPayloads: Record<number, Record<string, unknown>> = {
  1: {
    item_master_id: 1,
    item_key: 'vigas metalicas estructura',
    categoria: 'ESTRUCTURA',
    muestras_total: 2,
    min_unitario: 100,
    p25_unitario: 110,
    median_unitario: 120,
    p75_unitario: 130,
    max_unitario: 140,
    avg_unitario: 120,
  },
  2: {
    item_master_id: 2,
    item_key: 'forjado hormigon estructura',
    categoria: 'ESTRUCTURA',
    muestras_total: 2,
    min_unitario: 150,
    p25_unitario: 155,
    median_unitario: 160,
    p75_unitario: 165,
    max_unitario: 170,
    avg_unitario: 160,
  },
};

describe('Visuales Integration', () => {
  const fetchMock = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    fetchMock.mockImplementation(async (input: RequestInfo | URL) => {
      const url = String(input);

      if (url.includes('/api/items/list')) {
        return {
          ok: true,
          status: 200,
          statusText: 'OK',
          headers: {
            get: (name: string) => (name === 'content-type' ? 'application/json' : null),
          },
          text: async () => JSON.stringify({ items: itemsPayload }),
        } as unknown as Response;
      }

      if (url.includes('/api/ratios/chapters')) {
        return {
          ok: true,
          status: 200,
          statusText: 'OK',
          headers: {
            get: (name: string) => (name === 'content-type' ? 'application/json' : null),
          },
          text: async () => JSON.stringify(chaptersPayload),
        } as unknown as Response;
      }

      if (url.includes('/api/ratios/item/1')) {
        return {
          ok: true,
          status: 200,
          statusText: 'OK',
          headers: {
            get: (name: string) => (name === 'content-type' ? 'application/json' : null),
          },
          text: async () => JSON.stringify(itemStatsPayloads[1]),
        } as unknown as Response;
      }

      if (url.includes('/api/ratios/item/2')) {
        return {
          ok: true,
          status: 200,
          statusText: 'OK',
          headers: {
            get: (name: string) => (name === 'content-type' ? 'application/json' : null),
          },
          text: async () => JSON.stringify(itemStatsPayloads[2]),
        } as unknown as Response;
      }

      return {
        ok: false,
        status: 404,
        statusText: 'Not Found',
        headers: {
          get: () => 'text/html',
        },
        text: async () => '<!doctype html><html></html>',
      } as unknown as Response;
    });
    vi.stubGlobal('fetch', fetchMock);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  test('carga items y capitulos al montar', async () => {
    render(<Visuales />);

    await waitFor(() => {
      expect(screen.getByLabelText(/Selecciona una partida o item/i)).toBeInTheDocument();
    });

    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining('/api/items/list'),
      expect.objectContaining({
        method: 'GET',
        headers: {
          Accept: 'application/json',
          'Content-Type': 'application/json',
        },
        signal: expect.any(AbortSignal),
      }),
    );
    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining('/api/ratios/chapters'),
      expect.objectContaining({
        method: 'GET',
        headers: {
          Accept: 'application/json',
          'Content-Type': 'application/json',
        },
        signal: expect.any(AbortSignal),
      }),
    );
    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining('/api/ratios/item/1'),
      expect.objectContaining({
        method: 'GET',
        headers: {
          Accept: 'application/json',
          'Content-Type': 'application/json',
        },
        signal: expect.any(AbortSignal),
      }),
    );
  });

  test('muestra Tab Rango por defecto y carga el primer item', async () => {
    render(<Visuales />);

    await waitFor(() => {
      expect(screen.getByRole('tab', { name: /Rango/i })).toHaveAttribute('aria-selected', 'true');
    });
    await waitFor(() => {
      expect(screen.getByText(/Item 1: ESTRUCTURA - vigas metalicas estructura/i)).toBeInTheDocument();
    });
  });

  test('cambia el item y pide stats distintos', async () => {
    render(<Visuales />);
    const user = userEvent.setup();

    await waitFor(() => {
      expect(screen.getByLabelText(/Selecciona una partida o item/i)).toBeInTheDocument();
    });

    await user.selectOptions(screen.getByLabelText(/Selecciona una partida o item/i), '2');

    await waitFor(() => {
      expect(screen.getByText(/Item 2: ESTRUCTURA - forjado hormigon estructura/i)).toBeInTheDocument();
    });
    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining('/api/ratios/item/2'),
      expect.objectContaining({
        method: 'GET',
        headers: {
          Accept: 'application/json',
          'Content-Type': 'application/json',
        },
        signal: expect.any(AbortSignal),
      }),
    );
  });

  test('cambia a Tab Solidez al hacer click', async () => {
    render(<Visuales />);
    const user = userEvent.setup();

    await waitFor(() => {
      expect(screen.getByRole('tab', { name: /Solidez/i })).toBeInTheDocument();
    });

    await user.click(screen.getByRole('tab', { name: /Solidez/i }));

    expect(screen.getByRole('tab', { name: /Solidez/i })).toHaveAttribute('aria-selected', 'true');
  });

  test('muestra error si la API de items falla', async () => {
    fetchMock.mockImplementation(async (input: RequestInfo | URL) => {
      const url = String(input);

      if (url.includes('/api/items/list')) {
        return {
          ok: false,
          status: 404,
          statusText: 'Not Found',
          headers: {
            get: () => 'text/html',
          },
          text: async () => '<!doctype html><html></html>',
        } as unknown as Response;
      }

      if (url.includes('/api/ratios/chapters')) {
        return {
          ok: true,
          status: 200,
          statusText: 'OK',
          headers: {
            get: () => 'application/json',
          },
          text: async () => JSON.stringify(chaptersPayload),
        } as unknown as Response;
      }

      return {
        ok: true,
        status: 200,
        statusText: 'OK',
        headers: {
          get: () => 'application/json',
        },
        text: async () => JSON.stringify(itemStatsPayloads[1]),
      } as unknown as Response;
    });

    render(<Visuales />);

    await waitFor(() => {
      expect(screen.getAllByText(/HTTP 404: Not Found/i).length).toBeGreaterThan(0);
    });
  });

  test('muestra estados vacios cuando no hay datos', async () => {
    fetchMock.mockImplementation(async (input: RequestInfo | URL) => {
      const url = String(input);

      if (url.includes('/api/items/list')) {
        return {
          ok: true,
          status: 200,
          statusText: 'OK',
          headers: {
            get: () => 'application/json',
          },
          text: async () => JSON.stringify({ items: [] }),
        } as unknown as Response;
      }

      if (url.includes('/api/ratios/chapters')) {
        return {
          ok: true,
          status: 200,
          statusText: 'OK',
          headers: {
            get: () => 'application/json',
          },
          text: async () => JSON.stringify([]),
        } as unknown as Response;
      }

      return {
        ok: false,
        status: 404,
        statusText: 'Not Found',
        headers: {
          get: () => 'text/html',
        },
        text: async () => '<!doctype html><html></html>',
      } as unknown as Response;
    });

    render(<Visuales />);

    await waitFor(() => {
      expect(screen.getByText(/No hay items disponibles para mostrar el rango/i)).toBeInTheDocument();
    });

    await userEvent.click(screen.getByRole('tab', { name: /Solidez/i }));
    expect(screen.getByText(/No hay capitulos disponibles para evaluar la solidez/i)).toBeInTheDocument();
  });
});
