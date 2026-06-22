import { useEffect, useState } from 'react';

import LoadingSpinner from '@/components/LoadingSpinner';
import RangoValidacion from '@/components/Visuales/RangoValidacion';
import TablaConfiabilidad from '@/components/Visuales/TablaConfiabilidad';
import { useVisuales } from '@/hooks/useVisuales';
import type { RangoResponse } from '@/types/visuales';

const TABS = ['Rango', 'Solidez'];

const humanizeError = (error: string | null) => {
  if (!error) {
    return null;
  }
  if (error.includes('Failed to fetch')) {
    return 'No se pudo conectar con la API. Comprueba que el backend este levantado.';
  }
  if (error.includes('Network')) {
    return 'La conexion con la API ha fallado. Reintenta en unos segundos.';
  }
  if (error.includes('tiempo de espera')) {
    return 'La API ha tardado demasiado en responder. Reintenta en unos segundos.';
  }
  return error;
};

const Visuales = () => {
  const { capitulos, loading, error } = useVisuales();
  const [indiceTab, setIndiceTab] = useState(0);
  const [capituloSeleccionado, setCapituloSeleccionado] = useState('');
  const [rangoData, setRangoData] = useState<RangoResponse | null>(null);
  const [loadingRango, setLoadingRango] = useState(false);

  const cargarRango = async (chapter: string) => {
    setLoadingRango(true);
    try {
      const res = await fetch(`/api/ratios/rango?chapter=${encodeURIComponent(chapter)}`);
      if (!res.ok) {
        throw new Error(`Error ${res.status}`);
      }
      const data = (await res.json()) as RangoResponse;
      setRangoData(data);
    } catch (fetchError) {
      console.error('Error cargando rango:', fetchError);
      setRangoData(null);
    } finally {
      setLoadingRango(false);
    }
  };

  useEffect(() => {
    if (!capituloSeleccionado && capitulos.length > 0) {
      const primerCapitulo = capitulos[0].capitulo;
      setCapituloSeleccionado(primerCapitulo);
      void cargarRango(primerCapitulo);
    }
  }, [capituloSeleccionado, capitulos]);

  const displayError = humanizeError(error);

  const handleCapituloChange = async (chapter: string) => {
    setCapituloSeleccionado(chapter);
    await cargarRango(chapter);
  };

  const renderRango = () => (
    <div className="space-y-6">
      <div className="flex flex-col gap-4">
        <label className="flex flex-col gap-2 text-sm font-medium text-primary">
          Selecciona un capitulo
          <select
            aria-label="Selecciona un capitulo"
            className="rounded-lg border border-[#D4C7B8] bg-white px-4 py-3 text-base"
            value={capituloSeleccionado}
            onChange={(event) => void handleCapituloChange(event.target.value)}
          >
            {capitulos.map((item) => (
              <option key={`${item.capitulo}-${item.descripcion ?? ''}`} value={item.capitulo}>
                {item.capitulo} - {item.descripcion ?? 'Sin descripcion'}
              </option>
            ))}
          </select>
        </label>
      </div>

      {loadingRango && (
        <div className="rounded-lg border border-[#E0D5C7] bg-white px-4 py-6 text-center text-sm text-accent">
          Cargando estadisticas...
        </div>
      )}

      {!loadingRango && rangoData && (
        <>
          <div className="space-y-2 rounded-lg border border-[#E0D5C7] bg-white p-4">
            <h3 className="font-semibold text-primary">{rangoData.chapter}</h3>
            <p className="text-sm text-accent">Muestras totales: {rangoData.muestras_total}</p>
            <p className="text-sm text-accent">Items unicos: {rangoData.items_count}</p>
          </div>

          <RangoValidacion
            capitulo={rangoData.chapter}
            cantidad_datos={rangoData.muestras_total}
            descripcion={`${rangoData.items_count} items unicos`}
            desviacion_std={null}
            estado_confiabilidad={
              rangoData.muestras_total >= 5
                ? 'solido'
                : rangoData.muestras_total >= 2
                  ? 'debil'
                  : 'muy_debil'
            }
            maximo={rangoData.max_unitario}
            mediana={rangoData.median_unitario}
            minimo={rangoData.min_unitario}
            percentil_25={rangoData.p25_unitario}
            percentil_75={rangoData.p75_unitario}
            unidad="EUR/m2"
          />
        </>
      )}

      {!loadingRango && !rangoData && capituloSeleccionado && (
        <div className="rounded-lg border border-[#D32F2F] bg-[#FDECEC] px-4 py-3 text-sm text-[#8B1E1E]">
          No se pudo cargar datos para {capituloSeleccionado}
        </div>
      )}
    </div>
  );

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <div className="space-y-2">
        <h1 className="text-3xl font-serif text-primary">Visuales de ratios</h1>
        <p className="max-w-3xl text-sm text-accent">
          Demo de lectura sobre datos reales en produccion: valida rangos y revisa la solidez
          estadistica de los ratios disponibles.
        </p>
      </div>

      <div aria-label="Visuales tabs" className="flex flex-wrap gap-3" role="tablist">
        {TABS.map((tab, idx) => (
          <button
            key={tab}
            aria-selected={indiceTab === idx}
            className={`rounded-lg px-4 py-2 text-sm font-medium ${
              indiceTab === idx ? 'bg-[#2D5016] text-white' : 'bg-[#E8E0D5] text-primary'
            }`}
            role="tab"
            type="button"
            onClick={() => setIndiceTab(idx)}
          >
            {tab}
          </button>
        ))}
      </div>

      {displayError && (
        <div className="rounded-lg border border-[#D32F2F] bg-[#FDECEC] px-4 py-3 text-sm text-[#8B1E1E]">
          {displayError}
        </div>
      )}

      {loading ? (
        <div className="space-y-3 rounded-lg border border-[#E0D5C7] bg-white p-6">
          <LoadingSpinner />
          <p className="text-center text-sm text-accent">Cargando capitulos desde la API...</p>
        </div>
      ) : (
        <>
          {indiceTab === 0 && renderRango()}
          {indiceTab === 0 && capitulos.length === 0 && (
            <div className="rounded-lg border border-[#E0D5C7] bg-white px-4 py-6 text-sm text-accent">
              No hay capitulos disponibles para mostrar el rango.
            </div>
          )}
          {indiceTab === 1 && <TablaConfiabilidad capitulos={capitulos} />}
        </>
      )}
    </div>
  );
};

export default Visuales;
