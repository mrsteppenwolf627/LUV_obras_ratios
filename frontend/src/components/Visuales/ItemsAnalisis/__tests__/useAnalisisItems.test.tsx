import { renderHook, act } from '@testing-library/react';
import { describe, test, expect, vi, beforeEach } from 'vitest';
import useAnalisisItems from '../hooks/useAnalisisItems';

describe('useAnalisisItems', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', vi.fn());
  });

  test('llamada inicial retorna valores vacíos', () => {
    const { result } = renderHook(() => useAnalisisItems());
    expect(result.current.analisisActual).toBeNull();
    expect(result.current.historico).toHaveLength(0);
    expect(result.current.loading).toBe(false);
  });

  test('analizarItems actualiza estado al éxito', async () => {
    const mockResponse = {
      items: [{ descripcion: 'Item 1', categoria: 'MEDIUM' }],
      resumenes_por_categoria: {},
      resumen_general: { total_usuario: 100, total_ratio: 90, diff_pct: 11.1 }
    };

    (fetch as any).mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockResponse)
    });

    const { result } = renderHook(() => useAnalisisItems());

    await act(async () => {
      await result.current.analizarItems([{ descripcion: 'Item 1', precio_unitario: 100 }]);
    });

    expect(result.current.analisisActual).toEqual(mockResponse);
    expect(result.current.historico).toHaveLength(1);
    expect(result.current.historico[0]).toEqual(mockResponse);
    expect(result.current.loading).toBe(false);
  });

  test('maneja error de API', async () => {
    (fetch as any).mockResolvedValue({
      ok: false,
      status: 500,
      statusText: 'Internal Server Error',
      json: () => Promise.resolve({ detail: 'Error en servidor' })
    });

    const { result } = renderHook(() => useAnalisisItems());

    await act(async () => {
      await result.current.analizarItems([{ descripcion: 'Item 1', precio_unitario: 100 }]);
    });

    expect(result.current.error).toBe('Error en servidor');
    expect(result.current.loading).toBe(false);
  });

  test('limpiar resetea estado', async () => {
    const { result } = renderHook(() => useAnalisisItems());
    
    act(() => {
      result.current.limpiar();
    });

    expect(result.current.analisisActual).toBeNull();
    expect(result.current.historico).toHaveLength(0);
  });

  test('acumula análisis en el histórico', async () => {
    const mockResponse1 = { items: [], resumenes_por_categoria: {}, resumen_general: { total_usuario: 100, diff_pct: 0 } };
    const mockResponse2 = { items: [], resumenes_por_categoria: {}, resumen_general: { total_usuario: 200, diff_pct: 0 } };

    (fetch as any)
      .mockResolvedValueOnce({ ok: true, json: () => Promise.resolve(mockResponse1) })
      .mockResolvedValueOnce({ ok: true, json: () => Promise.resolve(mockResponse2) });

    const { result } = renderHook(() => useAnalisisItems());

    await act(async () => {
      await result.current.analizarItems([]);
    });
    await act(async () => {
      await result.current.analizarItems([]);
    });

    expect(result.current.historico).toHaveLength(2);
    expect(result.current.historico[0]).toEqual(mockResponse2);
    expect(result.current.historico[1]).toEqual(mockResponse1);
  });

  test('maneja error de red (fetch failure)', async () => {
    (fetch as any).mockRejectedValue(new Error('Network error'));

    const { result } = renderHook(() => useAnalisisItems());

    await act(async () => {
      await result.current.analizarItems([]);
    });

    expect(result.current.error).toBe('Network error');
  });
});
