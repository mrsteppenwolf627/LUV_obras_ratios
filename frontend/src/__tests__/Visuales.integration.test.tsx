import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, test, vi } from 'vitest';

import * as visualesAPI from '@/api/visuales';
import Visuales from '@/pages/Visuales';

vi.mock('@/api/visuales', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/api/visuales')>();
  return {
    ...actual,
    analizarComparativa: vi.fn(),
  };
});

describe('Visuales Integration', () => {
  const fetchMock = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    fetchMock.mockResolvedValue({
      ok: true,
      status: 200,
      statusText: 'OK',
      headers: {
        get: (name: string) =>
          name === 'content-type' ? 'application/json' : name === 'content-length' ? '233' : null,
      },
      text: async () =>
        JSON.stringify([
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
        ]),
    });
    vi.stubGlobal('fetch', fetchMock);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  test('carga capitulos al montar', async () => {
    render(<Visuales />);

    await waitFor(() => {
      expect(screen.getByLabelText(/Selecciona un capitulo/i)).toBeInTheDocument();
    });

    expect(fetchMock).toHaveBeenCalledWith('/api/ratios/chapters', {
      method: 'GET',
      headers: {
        Accept: 'application/json',
        'Content-Type': 'application/json',
      },
      signal: expect.any(AbortSignal),
    });
  });

  test('muestra Tab 0 (Rango) por defecto', async () => {
    render(<Visuales />);

    await waitFor(() => {
      expect(screen.getByRole('tab', { name: /Rango/i })).toHaveAttribute('aria-selected', 'true');
    });
  });

  test('cambia a Tab 1 (Solidez) al hacer click', async () => {
    render(<Visuales />);
    const user = userEvent.setup();

    await waitFor(() => {
      expect(screen.getByRole('tab', { name: /Solidez/i })).toBeInTheDocument();
    });

    await user.click(screen.getByRole('tab', { name: /Solidez/i }));

    expect(screen.getByRole('tab', { name: /Solidez/i })).toHaveAttribute('aria-selected', 'true');
  });

  test('llama a analizarComparativa con datos correctos', async () => {
    vi.mocked(visualesAPI.analizarComparativa).mockResolvedValue({
      capitulos: [],
      capitulos_sin_ratio: [],
      resumen: {
        total_presupuesto: 58500,
        total_ratio: 59480,
        diferencia_pct: -1.7,
        diferencia_monetaria: -980,
        area_total: 250,
        confiabilidad_global: 'solido',
      },
    });

    render(<Visuales />);
    const user = userEvent.setup();

    await waitFor(() => {
      expect(screen.getByRole('tab', { name: /Comparativa/i })).toBeInTheDocument();
    });

    await user.click(screen.getByRole('tab', { name: /Comparativa/i }));
    await user.type(screen.getByPlaceholderText(/Area total/i), '250');
    await user.type(screen.getByLabelText(/Valor unitario 1/i), '334.67');
    await user.click(screen.getByRole('button', { name: /Analizar comparativa/i }));

    await waitFor(() => {
      expect(visualesAPI.analizarComparativa).toHaveBeenCalledWith({
        area_total: 250,
        items: [
          {
            capitulo: 'ESTRUCTURA',
            valor_unitario: 334.67,
            cantidad: 1,
            unidad: 'm2',
          },
        ],
      });
    });
  });

  test('muestra error si API falla', async () => {
    fetchMock.mockResolvedValue({
      ok: false,
      status: 404,
      statusText: 'Not Found',
      headers: {
        get: () => 'text/html',
      },
      text: async () => '<!doctype html><html></html>',
    });

    render(<Visuales />);

    await waitFor(() => {
      expect(screen.getByText(/HTTP 404: Not Found/i)).toBeInTheDocument();
    });
  });

  test('muestra mensaje amigable en timeout de API', async () => {
    fetchMock.mockRejectedValue(new Error('La peticion ha excedido el tiempo de espera.'));

    render(<Visuales />);

    await waitFor(() => {
      expect(screen.getByText(/La API ha tardado demasiado en responder/i)).toBeInTheDocument();
    });
  });

  test('valida area total negativa sin llamar a la API de comparativa', async () => {
    render(<Visuales />);
    const user = userEvent.setup();

    await waitFor(() => {
      expect(screen.getByRole('tab', { name: /Comparativa/i })).toBeInTheDocument();
    });

    await user.click(screen.getByRole('tab', { name: /Comparativa/i }));
    await user.type(screen.getByPlaceholderText(/Area total/i), '-5');
    await user.type(screen.getByLabelText(/Valor unitario 1/i), '334.67');
    await user.click(screen.getByRole('button', { name: /Analizar comparativa/i }));

    expect(visualesAPI.analizarComparativa).not.toHaveBeenCalled();
    expect(screen.getByText(/Introduce un area total mayor que 0/i)).toBeInTheDocument();
  });

  test('muestra estados vacios cuando la API devuelve cero capitulos', async () => {
    fetchMock.mockResolvedValue({
      ok: true,
      status: 200,
      statusText: 'OK',
      headers: {
        get: () => 'application/json',
      },
      text: async () => JSON.stringify([]),
    });

    render(<Visuales />);
    const user = userEvent.setup();

    await waitFor(() => {
      expect(screen.getByText(/No hay capitulos disponibles para mostrar el rango/i)).toBeInTheDocument();
    });

    await user.click(screen.getByRole('tab', { name: /Solidez/i }));
    expect(screen.getByText(/No hay capitulos disponibles para evaluar la solidez/i)).toBeInTheDocument();
  });
});
