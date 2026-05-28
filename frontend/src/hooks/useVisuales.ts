import { useEffect, useState } from 'react';

import { analizarComparativa } from '@/api/visuales';
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

        const timestamp = new Date().toISOString();
        console.log(`[${timestamp}] [useVisuales] INICIANDO FETCH`);
        console.log(`[${timestamp}] [useVisuales] URL: /api/ratios/chapters`);
        console.log(`[${timestamp}] [useVisuales] Origin: ${window.location.origin}`);

        const response = await fetch('/api/ratios/chapters', {
          method: 'GET',
          headers: {
            Accept: 'application/json',
            'Content-Type': 'application/json',
          },
        });

        console.log(`[${timestamp}] [useVisuales] RESPONSE RECIBIDA`);
        console.log(`[${timestamp}] [useVisuales] Status: ${response.status} ${response.statusText}`);
        console.log(
          `[${timestamp}] [useVisuales] Content-Type: ${response.headers.get('content-type')}`,
        );
        console.log(
          `[${timestamp}] [useVisuales] Content-Length: ${response.headers.get('content-length')}`,
        );

        const text = await response.text();
        console.log(`[${timestamp}] [useVisuales] Body length: ${text.length} bytes`);
        console.log(`[${timestamp}] [useVisuales] First 200 chars: ${text.substring(0, 200)}`);
        console.log(`[${timestamp}] [useVisuales] First char code: ${text.charCodeAt(0)}`);

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const data = JSON.parse(text) as CapituloRatioResponse[];
        console.log(`[${timestamp}] [useVisuales] JSON PARSED OK`);
        console.log(
          `[${timestamp}] [useVisuales] Items: ${Array.isArray(data) ? data.length : 'invalid'}`,
        );

        setCapitulos(data);
        setError(null);
      } catch (err) {
        const timestamp = new Date().toISOString();
        console.error(`[${timestamp}] [useVisuales] ERROR:`, err);

        const errorMsg = err instanceof Error ? err.message : String(err);
        console.error(`[${timestamp}] [useVisuales] Message: ${errorMsg}`);
        if (err instanceof Error) {
          console.error(`[${timestamp}] [useVisuales] Stack:`, err.stack);
        }

        setError(errorMsg);
        setCapitulos([]);
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
