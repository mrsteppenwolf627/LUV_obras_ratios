import { render, screen, fireEvent } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import RangoValidacion from '@/components/Visuales/RangoValidacion';

describe('RangoValidacion', () => {
  const defaultProps = {
    capitulo: 'ESTRUCTURA',
    cantidad_datos: 8,
    descripcion: 'Estructura de hormigón',
    desviacion_std: 45.3,
    estado_confiabilidad: 'solido' as const,
    maximo: 450,
    mediana: 334.67,
    minimo: 280,
    percentil_25: 310,
    percentil_75: 350,
    unidad: 'EUR/m2',
  };

  it('renders initial state without value', () => {
    render(<RangoValidacion {...defaultProps} />);

    expect(screen.getByText(/ESTRUCTURA/)).toBeInTheDocument();
    expect(screen.getByText(/Introduce tu valor/)).toBeInTheDocument();
    expect(screen.getByLabelText(/Mi valor/i)).toBeInTheDocument();
  });

  it('updates validation when entering a value within range', () => {
    render(<RangoValidacion {...defaultProps} />);

    const input = screen.getByLabelText(/Mi valor/i);
    fireEvent.change(input, { target: { value: '340' } });

    expect(screen.getByText(/Mi valor: 340\.00/)).toBeInTheDocument();
    expect(screen.getByText(/Dentro de rango/i)).toBeInTheDocument();
    // Check for green text class
    const resultDiv = screen.getByText(/Dentro de rango/i).closest('div');
    expect(resultDiv).toHaveClass('text-green-700');
  });

  it('updates validation when entering a value outside range', () => {
    render(<RangoValidacion {...defaultProps} />);

    const input = screen.getByLabelText(/Mi valor/i);
    fireEvent.change(input, { target: { value: '500' } });

    expect(screen.getByText(/Mi valor: 500\.00/)).toBeInTheDocument();
    expect(screen.getByText(/Fuera de rango/i)).toBeInTheDocument();
    // Check for red text class
    const resultDiv = screen.getByText(/Fuera de rango/i).closest('div');
    expect(resultDiv).toHaveClass('text-red-700');
  });

  it('handles decimal values correctly', () => {
    render(<RangoValidacion {...defaultProps} />);

    const input = screen.getByLabelText(/Mi valor/i);
    fireEvent.change(input, { target: { value: '280.50' } });

    expect(screen.getByText(/Mi valor: 280\.50/)).toBeInTheDocument();
    expect(screen.getByText(/Dentro de rango/i)).toBeInTheDocument();
  });
});
