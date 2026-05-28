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
    const fetchCapitulos = async () => {
      try {
        setLoading(true);
        const data = await getCapitulosRatios();
        setCapitulos(data);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Error desconocido');
      } finally {
        setLoading(false);
      }
    };

    void fetchCapitulos();
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
