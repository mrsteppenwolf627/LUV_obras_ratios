import { render, screen } from '@testing-library/react';
import { describe, test, expect } from 'vitest';
import ResumenPorCategoria from '../ResumenPorCategoria';
import type { ResumenPorCategoria as ResumenPorCategoriaType } from '../types/analisisItems.types';

const mockResumenes: Record<string, ResumenPorCategoriaType> = {
  MEDIUM: {
    categoria: 'MEDIUM',
    cantidad_items: 5,
    precio_total_usuario: 1000,
    ratio_total_historico: 1100,
    desviacion_pct_promedio: -9.1,
    confianza_global: 'MUY_SÓLIDO',
    items_sin_ratio: 0
  },
  PREMIUM: {
    categoria: 'PREMIUM',
    cantidad_items: 2,
    precio_total_usuario: 2000,
    ratio_total_historico: 1800,
    desviacion_pct_promedio: 11.1,
    confianza_global: 'DÉBIL',
    items_sin_ratio: 1
  }
};

describe('ResumenPorCategoria', () => {
  test('renderiza categorías presentes', () => {
    render(<ResumenPorCategoria resumenes={mockResumenes} />);
    expect(screen.getByText('MEDIUM')).toBeInTheDocument();
    expect(screen.getByText('PREMIUM')).toBeInTheDocument();
    expect(screen.queryByText('LUXURY')).not.toBeInTheDocument();
  });

  test('calcula totales correctos', () => {
    render(<ResumenPorCategoria resumenes={mockResumenes} />);
    expect(screen.getByText('€1000.00')).toBeInTheDocument();
    expect(screen.getByText('€1800.00')).toBeInTheDocument();
  });

  test('advierte items sin ratio', () => {
    render(<ResumenPorCategoria resumenes={mockResumenes} />);
    expect(screen.getByText(/1 sin ratio histórico/)).toBeInTheDocument();
  });

  test('muestra badge de confianza con clase correcta', () => {
    render(<ResumenPorCategoria resumenes={mockResumenes} />);
    const confianzaBadge = screen.getByText('MUY_SÓLIDO');
    expect(confianzaBadge.className).toMatch(/confianzaMuySolido/);
  });

  test('no renderiza nada si no hay resumenes', () => {
    const { container } = render(<ResumenPorCategoria resumenes={{}} />);
    // Debería tener el título pero el grid estar vacío (buscamos por clase que contiene resumenGrid)
    const grid = container.querySelector('[class*="resumenGrid"]');
    expect(grid).toBeEmptyDOMElement();
  });
});
