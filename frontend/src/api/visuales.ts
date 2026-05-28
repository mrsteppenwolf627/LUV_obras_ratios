import type {
  CapituloRatioResponse,
  ComparativaResponse,
  PresupuestoAnalisis,
} from '@/types/visuales';

const API_BASE = '/api';

export const getCapitulosRatios = async (): Promise<CapituloRatioResponse[]> => {
  const response = await fetch(`${API_BASE}/ratios/chapters`);
  if (!response.ok) {
    throw new Error(`Error fetching ratios: ${response.statusText}`);
  }
  return response.json();
};

export const analizarComparativa = async (
  presupuesto: PresupuestoAnalisis,
): Promise<ComparativaResponse> => {
  const response = await fetch(`${API_BASE}/analyze/comparativa`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(presupuesto),
  });
  if (!response.ok) {
    throw new Error(`Error analyzing comparativa: ${response.statusText}`);
  }
  return response.json();
};
