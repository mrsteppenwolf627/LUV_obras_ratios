import { render, screen } from '@testing-library/react';
import { describe, test, expect, vi } from 'vitest';
import GraficosAnalisis from '../GraficosAnalisis';
import type { ItemAnalisisResultado } from '../types/analisisItems.types';

// Mock ResponsiveContainer and other Recharts components to avoid issues in JSDOM
vi.mock('recharts', async () => {
  const OriginalModule = await vi.importActual('recharts');
  return {
    ...OriginalModule,
    ResponsiveContainer: ({ children }: any) => <div>{children}</div>,
  };
});

const mockItems: ItemAnalisisResultado[] = [
  {
    descripcion: 'Item 1',
    categoria: 'MEDIUM',
    gama_asignada: 'MEDIUM',
    precio_usuario: 100,
    ratio_historico: 90,
    desviacion_pct: 11.1,
    confianza: 'SÓLIDO',
    impacto_monetario: 10,
    ratio_encontrado: true,
  },
  {
    descripcion: 'Item 2',
    categoria: 'PREMIUM',
    gama_asignada: 'MEDIUM',
    precio_usuario: 200,
    ratio_historico: 180,
    desviacion_pct: 11.1,
    confianza: 'SÓLIDO',
    impacto_monetario: 20,
    ratio_encontrado: true,
  }
];

describe('GraficosAnalisis', () => {
  test('renderiza títulos de gráficos', () => {
    render(<GraficosAnalisis items={mockItems} />);
    expect(screen.getByText('Items por Categoría')).toBeInTheDocument();
    expect(screen.getByText('Precio Usuario vs Ratio Histórico')).toBeInTheDocument();
    expect(screen.getByText('Desviación Promedio % por Categoría')).toBeInTheDocument();
  });
});
