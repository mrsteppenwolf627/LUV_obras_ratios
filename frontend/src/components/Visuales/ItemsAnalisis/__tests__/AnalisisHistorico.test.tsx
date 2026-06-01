import { render, screen, fireEvent } from '@testing-library/react';
import { describe, test, expect, vi } from 'vitest';
import AnalisisHistorico from '../AnalisisHistorico';
import type { AnalisisItemsResponse } from '../types/analisisItems.types';

const mockHistorico: AnalisisItemsResponse[] = [
  {
    items: [],
    resumenes_por_categoria: {},
    resumen_general: { total_usuario: 10000, total_ratio: 9000, diferencia_pct: 11.1, items_con_ratio: 0, items_sin_ratio: 0 }
  },
  {
    items: [],
    resumenes_por_categoria: {},
    resumen_general: { total_usuario: 5000, total_ratio: 5500, diferencia_pct: -9.1, items_con_ratio: 0, items_sin_ratio: 0 }
  }
];

describe('AnalisisHistorico', () => {
  test('renderiza mensaje cuando no hay histórico', () => {
    render(<AnalisisHistorico historico={[]} />);
    expect(screen.getByText(/No hay análisis históricos/)).toBeInTheDocument();
  });

  test('renderiza tabla con histórico', () => {
    render(<AnalisisHistorico historico={mockHistorico} />);
    expect(screen.getByText(/10[.,]?000/)).toBeInTheDocument();
    expect(screen.getByText(/5[.,]?000/)).toBeInTheDocument();
    expect(screen.getByText('11.1%')).toBeInTheDocument();
    expect(screen.getByText('-9.1%')).toBeInTheDocument();
  });

  test('muestra detalles al click "Ver detalles"', () => {
    render(<AnalisisHistorico historico={mockHistorico} />);
    const buttons = screen.getAllByText('Ver detalles');
    fireEvent.click(buttons[0]);
    expect(screen.getByText('Detalles del Análisis')).toBeInTheDocument();
    expect(screen.getByText('← Volver al listado')).toBeInTheDocument();
  });

  test('vuelve al listado al click "← Volver al listado"', () => {
    render(<AnalisisHistorico historico={mockHistorico} />);
    fireEvent.click(screen.getAllByText('Ver detalles')[0]);
    fireEvent.click(screen.getByText('← Volver al listado'));
    expect(screen.queryByText('Detalles del Análisis')).not.toBeInTheDocument();
    expect(screen.getByText(/10[.,]?000/)).toBeInTheDocument();
  });
});
