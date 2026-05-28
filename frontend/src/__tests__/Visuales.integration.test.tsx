import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import * as visualesAPI from '@/api/visuales';
import Visuales from '@/pages/Visuales';

vi.mock('@/api/visuales', () => ({
  analizarComparativa: vi.fn(),
  getCapitulosRatios: vi.fn(),
}));

describe('Visuales Integration', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(visualesAPI.getCapitulosRatios).mockResolvedValue([
      {
        capitulo: 'ESTRUCTURA',
        descripcion: 'Estructura',
        minimo: 280,
        percentil_25: 310,
        mediana: 334.67,
        percentil_75: 350,
        maximo: 450,
        desviacion_std: 45.3,
        cantidad_datos: 8,
        estado_confiabilidad: 'solido',
      },
    ]);
  });

  test('carga capitulos al montar', async () => {
    render(<Visuales />);
    expect(screen.getByText(/Cargando/i)).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByLabelText(/Selecciona un capitulo/i)).toBeInTheDocument();
    });
  });

  test('muestra Tab 0 (Rango) por defecto', async () => {
    render(<Visuales />);

    await waitFor(() => {
      expect(screen.getByRole('tab', { name: /Rango/i })).toHaveAttribute('aria-selected', 'true');
    });
  });

  test('cambia a Tab 1 (Solidez) al hacer click', async () => {
    render(<Visuales />);
    const user = userEvent.setup();

    await waitFor(() => {
      expect(screen.getByRole('tab', { name: /Solidez/i })).toBeInTheDocument();
    });

    await user.click(screen.getByRole('tab', { name: /Solidez/i }));

    expect(screen.getByRole('tab', { name: /Solidez/i })).toHaveAttribute('aria-selected', 'true');
  });

  test('llama a analizarComparativa con datos correctos', async () => {
    vi.mocked(visualesAPI.analizarComparativa).mockResolvedValue({
      capitulos: [],
      capitulos_sin_ratio: [],
      resumen: {
        total_presupuesto: 58500,
        total_ratio: 59480,
        diferencia_pct: -1.7,
        diferencia_monetaria: -980,
        area_total: 250,
        confiabilidad_global: 'solido',
      },
    });

    render(<Visuales />);
    const user = userEvent.setup();

    await waitFor(() => {
      expect(screen.getByRole('tab', { name: /Comparativa/i })).toBeInTheDocument();
    });

    await user.click(screen.getByRole('tab', { name: /Comparativa/i }));
    await user.type(screen.getByPlaceholderText(/Area total/i), '250');
    await user.type(screen.getByLabelText(/Valor unitario 1/i), '334.67');
    await user.click(screen.getByRole('button', { name: /Analizar comparativa/i }));

    await waitFor(() => {
      expect(visualesAPI.analizarComparativa).toHaveBeenCalledWith({
        area_total: 250,
        items: [
          {
            capitulo: 'ESTRUCTURA',
            valor_unitario: 334.67,
            cantidad: 1,
            unidad: 'm2',
          },
        ],
      });
    });
  });

  test('muestra error si API falla', async () => {
    vi.mocked(visualesAPI.getCapitulosRatios).mockRejectedValue(new Error('Network error'));

    render(<Visuales />);

    await waitFor(() => {
      expect(screen.getByText(/conexion con la API/i)).toBeInTheDocument();
    });
  });
});
