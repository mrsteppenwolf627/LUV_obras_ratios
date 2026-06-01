import { render, screen, fireEvent } from '@testing-library/react';
import { describe, test, expect, vi } from 'vitest';
import DetalleItemModal from '../DetalleItemModal';
import type { ItemAnalisisResultado } from '../types/analisisItems.types';

const mockItem: ItemAnalisisResultado = {
  descripcion: 'Carpintería Aluminio',
  categoria: 'PREMIUM',
  precio_usuario: 500,
  ratio_historico: 450,
  desviacion_pct: 11.1,
  confianza: 'SÓLIDO',
  impacto_monetario: 50,
  ratio_encontrado: true,
};

describe('DetalleItemModal', () => {
  const onClose = vi.fn();

  test('renderiza detalles del item', () => {
    render(<DetalleItemModal item={mockItem} onClose={onClose} />);
    expect(screen.getByText('Carpintería Aluminio')).toBeInTheDocument();
    expect(screen.getByText('PREMIUM')).toBeInTheDocument();
    expect(screen.getByText('€500.00')).toBeInTheDocument();
    expect(screen.getByText('€450.00')).toBeInTheDocument();
    expect(screen.getByText('11.1%')).toBeInTheDocument();
    expect(screen.getByText('SÓLIDO')).toBeInTheDocument();
  });

  test('muestra interpretación correcta para sobre precio', () => {
    render(<DetalleItemModal item={mockItem} onClose={onClose} />);
    expect(screen.getByText(/SOBRE precio/)).toBeInTheDocument();
  });

  test('muestra mensaje cuando no hay ratio encontrado', () => {
    const itemSinRatio = { ...mockItem, ratio_encontrado: false, ratio_historico: null, desviacion_pct: null };
    render(<DetalleItemModal item={itemSinRatio} onClose={onClose} />);
    expect(screen.getByText(/No se han encontrado ratios históricos/)).toBeInTheDocument();
  });

  test('llama a onClose al click "Cerrar"', () => {
    render(<DetalleItemModal item={mockItem} onClose={onClose} />);
    fireEvent.click(screen.getByText('Cerrar'));
    expect(onClose).toHaveBeenCalled();
  });

  test('llama a onClose al click "✕"', () => {
    render(<DetalleItemModal item={mockItem} onClose={onClose} />);
    fireEvent.click(screen.getByText('✕'));
    expect(onClose).toHaveBeenCalled();
  });
});
