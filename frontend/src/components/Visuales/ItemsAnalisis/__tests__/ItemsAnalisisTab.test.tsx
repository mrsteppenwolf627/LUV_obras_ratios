import { render, screen, fireEvent } from '@testing-library/react';
import { describe, test, expect, vi, beforeEach } from 'vitest';
import ItemsAnalisisTab from '../ItemsAnalisisTab';
import useAnalisisItems from '../hooks/useAnalisisItems';

// Mock the hook
vi.mock('../hooks/useAnalisisItems');

// Mock child components to simplify
vi.mock('../AnalisisForm', () => ({
  default: ({ onAnalizar }: any) => (
    <div data-testid="mock-form">
      <button onClick={() => onAnalizar([{ descripcion: 'test', precio_unitario: 100 }])}>
        Submit Mock
      </button>
    </div>
  ),
}));

describe('ItemsAnalisisTab', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  test('renders initial empty state', () => {
    vi.mocked(useAnalisisItems).mockReturnValue({
      analisisActual: null,
      historico: [],
      loading: false,
      error: null,
      analizarItems: vi.fn(),
      cargarHistorico: vi.fn(),
      limpiar: vi.fn(),
    });

    render(<ItemsAnalisisTab />);
    expect(screen.getByText('Items × Categorías')).toBeInTheDocument();
    expect(screen.getByText('No hay un análisis activo')).toBeInTheDocument();
  });

  test('abre modal al click "Analizar Presupuesto"', () => {
    vi.mocked(useAnalisisItems).mockReturnValue({
      analisisActual: null,
      historico: [],
      loading: false,
      error: null,
      analizarItems: vi.fn(),
      cargarHistorico: vi.fn(),
      limpiar: vi.fn(),
    });

    render(<ItemsAnalisisTab />);
    const btn = screen.getByText('+ Analizar Presupuesto');
    fireEvent.click(btn);
    expect(screen.getByTestId('mock-form')).toBeInTheDocument();
  });

  test('muestra estado de carga cuando loading es true', () => {
    vi.mocked(useAnalisisItems).mockReturnValue({
      analisisActual: null,
      historico: [],
      loading: true,
      error: null,
      analizarItems: vi.fn(),
      cargarHistorico: vi.fn(),
      limpiar: vi.fn(),
    });

    render(<ItemsAnalisisTab />);
    expect(screen.getByText(/Analizando items/)).toBeInTheDocument();
  });

  test('muestra mensaje de error cuando error existe', () => {
    vi.mocked(useAnalisisItems).mockReturnValue({
      analisisActual: null,
      historico: [],
      loading: false,
      error: 'API Error',
      analizarItems: vi.fn(),
      cargarHistorico: vi.fn(),
      limpiar: vi.fn(),
    });

    render(<ItemsAnalisisTab />);
    expect(screen.getByText('API Error')).toBeInTheDocument();
  });

  test('muestra botón de histórico solo si hay datos', () => {
    vi.mocked(useAnalisisItems).mockReturnValue({
      analisisActual: null,
      historico: [{ 
        items: [], 
        resumenes_por_categoria: {}, 
        resumen_general: { total_usuario: 0, total_ratio: 0, diferencia_pct: 0, items_con_ratio: 0, items_sin_ratio: 0 } 
      }],
      loading: false,
      error: null,
      analizarItems: vi.fn(),
      cargarHistorico: vi.fn(),
      limpiar: vi.fn(),
    });

    render(<ItemsAnalisisTab />);
    expect(screen.getByText(/Ver Histórico \(1\)/)).toBeInTheDocument();
  });

  test('cambia vista a histórico al click en botón', () => {
    vi.mocked(useAnalisisItems).mockReturnValue({
      analisisActual: null,
      historico: [{ 
        items: [], 
        resumenes_por_categoria: {}, 
        resumen_general: { total_usuario: 0, total_ratio: 0, diferencia_pct: 0, items_con_ratio: 0, items_sin_ratio: 0 } 
      }],
      loading: false,
      error: null,
      analizarItems: vi.fn(),
      cargarHistorico: vi.fn(),
      limpiar: vi.fn(),
    });

    render(<ItemsAnalisisTab />);
    const btn = screen.getByText(/Ver Histórico/);
    fireEvent.click(btn);
    expect(screen.getByText('Histórico de Análisis (Sesión Actual)')).toBeInTheDocument();
  });
});
