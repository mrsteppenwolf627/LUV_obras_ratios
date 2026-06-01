import { useState } from 'react';
import type { AnalisisItemsResponse, ItemParaAnalisis } from '../types/analisisItems.types';

interface UseAnalisisItemsReturn {
  analisisActual: AnalisisItemsResponse | null;
  historico: AnalisisItemsResponse[];
  loading: boolean;
  error: string | null;
  analizarItems: (items: ItemParaAnalisis[]) => Promise<void>;
  cargarHistorico: () => Promise<void>;
  limpiar: () => void;
}

const useAnalisisItems = (): UseAnalisisItemsReturn => {
  const [analisisActual, setAnalisisActual] = useState<AnalisisItemsResponse | null>(null);
  const [historico, setHistorico] = useState<AnalisisItemsResponse[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const analizarItems = async (items: ItemParaAnalisis[]) => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/items/analisis', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ items }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Error ${response.status}: ${response.statusText}`);
      }

      const data: AnalisisItemsResponse = await response.json();
      setAnalisisActual(data);
      setHistorico((prev) => [data, ...prev]);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error desconocido');
    } finally {
      setLoading(false);
    }
  };

  const cargarHistorico = async () => {
    // Por ahora, el histórico es in-memory durante la sesión
    // En el futuro, se podría implementar un endpoint GET /api/items/historico
  };

  const limpiar = () => {
    setAnalisisActual(null);
    setHistorico([]);
    setError(null);
  };

  return {
    analisisActual,
    historico,
    loading,
    error,
    analizarItems,
    cargarHistorico,
    limpiar,
  };
};

export default useAnalisisItems;
