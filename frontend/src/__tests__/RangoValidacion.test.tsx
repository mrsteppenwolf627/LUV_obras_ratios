import { render, screen } from '@testing-library/react';

import RangoValidacion from '@/components/Visuales/RangoValidacion';

test('renders with correct props', () => {
  const props = {
    capitulo: 'ESTRUCTURA',
    cantidad_datos: 8,
    descripcion: 'Estructura',
    desviacion_std: 45.3,
    estado_confiabilidad: 'solido' as const,
    maximo: 450,
    mediana: 334.67,
    mi_valor: 340,
    minimo: 280,
    percentil_25: 310,
    percentil_75: 350,
    unidad: 'EUR/m2',
  };

  render(<RangoValidacion {...props} />);

  expect(screen.getByText(/ESTRUCTURA/)).toBeInTheDocument();
  expect(screen.getByText(/340/)).toBeInTheDocument();
  expect(screen.getByText(/solido/i)).toBeInTheDocument();
});
