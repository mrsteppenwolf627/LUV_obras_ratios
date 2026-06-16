import { render, screen, fireEvent } from '@testing-library/react';
import { describe, test, expect, vi } from 'vitest';
import ItemsTable from '../ItemsTable';
import type { ItemAnalisisResultado } from '../types/analisisItems.types';

const mockItems: ItemAnalisisResultado[] = [
  {
    descripcion: 'Carpintería Aluminio',
    categoria: 'PREMIUM',
    gama_asignada: 'MEDIUM',
    precio_usuario: 500,
    ratio_historico: 450,
    desviacion_pct: 11.1,
    confianza: 'SÓLIDO',
    impacto_monetario: 50,
    ratio_encontrado: true,
  },
  {
    descripcion: 'Pintura Blanca',
    categoria: 'MEDIUM',
    gama_asignada: 'MEDIUM',
    precio_usuario: 10,
    ratio_historico: 12,
    desviacion_pct: -16.7,
    confianza: 'MUY_SÓLIDO',
    impacto_monetario: -2,
    ratio_encontrado: true,
  }
];

describe('ItemsTable', () => {
  const onItemClick = vi.fn();

  test('renderiza todas las filas', () => {
    render(<ItemsTable items={mockItems} filtroCategoria={null} onItemClick={onItemClick} />);
    expect(screen.getByText('Carpintería Aluminio')).toBeInTheDocument();
    expect(screen.getByText('Pintura Blanca')).toBeInTheDocument();
  });

  test('filtra por categoría', () => {
    render(<ItemsTable items={mockItems} filtroCategoria="MEDIUM" onItemClick={onItemClick} />);
    expect(screen.queryByText('Carpintería Aluminio')).not.toBeInTheDocument();
    expect(screen.getByText('Pintura Blanca')).toBeInTheDocument();
  });

  test('colores de desviación correctos', () => {
    render(<ItemsTable items={mockItems} filtroCategoria={null} onItemClick={onItemClick} />);
    
    // Buscar por texto y verificar que tenga una clase que contenga el nombre (CSS Modules)
    const posDesv = screen.getByText('11.1%');
    const negDesv = screen.getByText('-16.7%');
    
    expect(posDesv.className).toMatch(/desviacionPositiva/);
    expect(negDesv.className).toMatch(/desviacionNegativa/);
  });

  test('abre detalle al click "Ver detalles"', () => {
    render(<ItemsTable items={mockItems} filtroCategoria={null} onItemClick={onItemClick} />);
    
    // Por defecto se ordena por categoría ASC: MEDIUM (Pintura) antes que PREMIUM (Carpintería)
    const buttons = screen.getAllByText('Ver detalles');
    fireEvent.click(buttons[1]); // Clic en Carpintería (segunda fila)
    expect(onItemClick).toHaveBeenCalledWith(mockItems.find(i => i.descripcion === 'Carpintería Aluminio'));
  });

  test('ordena por descripción al click en header', () => {
    render(<ItemsTable items={mockItems} filtroCategoria={null} onItemClick={onItemClick} />);
    const header = screen.getByText(/Descripción/);
    
    // Primero ASC: Carpintería antes que Pintura
    fireEvent.click(header);
    const cells = screen.getAllByRole('cell');
    expect(cells[0]).toHaveTextContent('Carpintería Aluminio');
    
    // Luego DESC: Pintura antes que Carpintería
    fireEvent.click(header);
    const cellsDesc = screen.getAllByRole('cell');
    expect(cellsDesc[0]).toHaveTextContent('Pintura Blanca');
  });

  test('maneja items sin ratio (N/A en celdas)', () => {
    const itemsSinRatio = [{ ...mockItems[0], ratio_encontrado: false, ratio_historico: null, desviacion_pct: null }];
    render(<ItemsTable items={itemsSinRatio} filtroCategoria={null} onItemClick={onItemClick} />);
    expect(screen.getAllByText('N/A').length).toBe(2); // Ratio histórico y Desviación %
  });
});
