import { useEffect, useState } from 'react';

import { analizarComparativa, getCapitulosRatios } from '@/api/visuales';
import type {
  CapituloRatioResponse,
  ComparativaResponse,
  PresupuestoAnalisis,
} from '@/types/visuales';

export const useVisuales = () => {
  const [capitulos, setCapitulos] = useState<CapituloRatioResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const abortController = new AbortController();

    const fetchCapitulos = async () => {
      try {
        setLoading(true);
        const data = await getCapitulosRatios({ signal: abortController.signal });
        setCapitulos(data);
        setError(null);
      } catch (err) {
        if (abortController.signal.aborted) {
          return;
        }
        setError(err instanceof Error ? err.message : 'Error al cargar capitulos');
        setCapitulos([]);
      } finally {
        if (!abortController.signal.aborted) {
          setLoading(false);
        }
      }
    };

    void fetchCapitulos();

    return () => abortController.abort();
  }, []);

  const analizarPresupuesto = async (
    presupuesto: PresupuestoAnalisis,
  ): Promise<ComparativaResponse | null> => {
    try {
      setAnalyzing(true);
      const data = await analizarComparativa(presupuesto);
      setError(null);
      return data;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error en el analisis');
      return null;
    } finally {
      setAnalyzing(false);
    }
  };

  return {
    capitulos,
    loading,
    analyzing,
    error,
    setError,
    analizarPresupuesto,
  };
};
