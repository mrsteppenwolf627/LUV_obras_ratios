import { render, screen, fireEvent } from '@testing-library/react';
import { describe, test, expect, vi, beforeEach } from 'vitest';
import AnalisisForm from '../AnalisisForm';

describe('AnalisisForm', () => {
  const onAnalizar = vi.fn();
  const onClose = vi.fn();

  beforeEach(() => {
    onAnalizar.mockClear();
    onClose.mockClear();
  });

  test('valida descripción vacía', () => {
    render(<AnalisisForm onAnalizar={onAnalizar} onClose={onClose} />);
    fireEvent.click(screen.getByText('Analizar'));
    expect(onAnalizar).not.toHaveBeenCalled();
  });

  test('valida precio <= 0', () => {
    render(<AnalisisForm onAnalizar={onAnalizar} onClose={onClose} />);
    const descInput = screen.getByLabelText('Descripción item 1');
    const precioInput = screen.getByLabelText('Precio unitario item 1');
    
    fireEvent.change(descInput, { target: { value: 'Test Item' } });
    fireEvent.change(precioInput, { target: { value: '0' } });
    
    fireEvent.click(screen.getByText('Analizar'));
    expect(onAnalizar).not.toHaveBeenCalled();
  });

  test('agrega nuevo item', () => {
    render(<AnalisisForm onAnalizar={onAnalizar} onClose={onClose} />);
    fireEvent.click(screen.getByText('+ Agregar otro item'));
    expect(screen.getByLabelText('Descripción item 2')).toBeInTheDocument();
  });

  test('elimina item', () => {
    render(<AnalisisForm onAnalizar={onAnalizar} onClose={onClose} />);
    fireEvent.click(screen.getByText('+ Agregar otro item'));
    expect(screen.getAllByLabelText(/Descripción item/).length).toBe(2);
    
    fireEvent.click(screen.getByLabelText('Eliminar item 2'));
    expect(screen.getAllByLabelText(/Descripción item/).length).toBe(1);
  });

  test('envía datos correctos al callback', () => {
    render(<AnalisisForm onAnalizar={onAnalizar} onClose={onClose} />);
    fireEvent.change(screen.getByLabelText('Descripción item 1'), { target: { value: 'Test Item' } });
    fireEvent.change(screen.getByLabelText('Precio unitario item 1'), { target: { value: '100.50' } });
    fireEvent.change(screen.getByLabelText('Cantidad item 1'), { target: { value: '2' } });
    
    fireEvent.click(screen.getByText('Analizar'));
    
    expect(onAnalizar).toHaveBeenCalledWith([{
      descripcion: 'Test Item',
      precio_unitario: 100.50,
      cantidad: 2,
      unidad: 'm2'
    }]);
  });

  test('cierra modal al cancelar', () => {
    render(<AnalisisForm onAnalizar={onAnalizar} onClose={onClose} />);
    fireEvent.click(screen.getByText('Cancelar'));
    expect(onClose).toHaveBeenCalled();
  });

  test('limpia errores al corregir input y re-enviar', () => {
    render(<AnalisisForm onAnalizar={onAnalizar} onClose={onClose} />);
    const submitBtn = screen.getByText('Analizar');
    
    // Provocar error
    fireEvent.click(submitBtn);
    expect(screen.getByText('Descripción requerida')).toBeInTheDocument();
    
    // Corregir
    fireEvent.change(screen.getByLabelText('Descripción item 1'), { target: { value: 'Valid Item' } });
    fireEvent.change(screen.getByLabelText('Precio unitario item 1'), { target: { value: '10' } });
    fireEvent.change(screen.getByLabelText('Cantidad item 1'), { target: { value: '1' } });
    
    fireEvent.click(submitBtn);
    expect(onAnalizar).toHaveBeenCalled();
    expect(screen.queryByText('Descripción requerida')).not.toBeInTheDocument();
  });

  test('no permite eliminar el único item', () => {
    render(<AnalisisForm onAnalizar={onAnalizar} onClose={onClose} />);
    const deleteBtn = screen.getByLabelText('Eliminar item 1');
    expect(deleteBtn).toBeDisabled();
  });
});
