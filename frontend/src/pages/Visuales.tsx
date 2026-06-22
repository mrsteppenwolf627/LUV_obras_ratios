import { useEffect, useState } from 'react';

import LoadingSpinner from '@/components/LoadingSpinner';
import RangoValidacion from '@/components/Visuales/RangoValidacion';
import TablaConfiabilidad from '@/components/Visuales/TablaConfiabilidad';
import { getItemRatio, getItemsList } from '@/api/visuales';
import { useVisuales } from '@/hooks/useVisuales';
import type { Item, ItemRatioResponse } from '@/types/visuales';

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
  const [items, setItems] = useState<Item[]>([]);
  const [loadingItems, setLoadingItems] = useState(true);
  const [itemsError, setItemsError] = useState<string | null>(null);
  const [itemSeleccionadoId, setItemSeleccionadoId] = useState<number | null>(null);
  const [rangoData, setRangoData] = useState<ItemRatioResponse | null>(null);
  const [loadingRango, setLoadingRango] = useState(false);
  const [rangoError, setRangoError] = useState<string | null>(null);

  useEffect(() => {
    const abortController = new AbortController();

    const fetchItems = async () => {
      try {
        setLoadingItems(true);
        const data = await getItemsList({ signal: abortController.signal });
        setItems(data);
        setItemsError(null);
      } catch (fetchError) {
        if (abortController.signal.aborted) {
          return;
        }
        console.error('Error cargando items:', fetchError);
        setItems([]);
        setItemsError(fetchError instanceof Error ? fetchError.message : 'Error al cargar items');
      } finally {
        if (!abortController.signal.aborted) {
          setLoadingItems(false);
        }
      }
    };

    void fetchItems();

    return () => abortController.abort();
  }, []);

  const cargarRango = async (itemMasterId: number) => {
    setLoadingRango(true);
    setRangoError(null);
    try {
      const data = await getItemRatio(itemMasterId);
      setRangoData(data);
    } catch (fetchError) {
      console.error('Error cargando rango:', fetchError);
      setRangoData(null);
      setRangoError(fetchError instanceof Error ? fetchError.message : 'Error al cargar rango');
    } finally {
      setLoadingRango(false);
    }
  };

  useEffect(() => {
    if (itemSeleccionadoId === null && items.length > 0) {
      const primerItem = items[0];
      setItemSeleccionadoId(primerItem.id);
      void cargarRango(primerItem.id);
    }
  }, [itemSeleccionadoId, items]);

  const displayError = humanizeError(error);

  const handleItemChange = async (itemMasterId: number) => {
    setItemSeleccionadoId(itemMasterId);
    await cargarRango(itemMasterId);
  };

  const itemSeleccionado = items.find((item) => item.id === itemSeleccionadoId) ?? null;
  const itemLabel = itemSeleccionado
    ? `${itemSeleccionado.categoria ?? itemSeleccionado.categoria_asignada} - ${itemSeleccionado.item_key}`
    : '';

  const renderRango = () => (
    <div className="space-y-6">
      <div className="flex flex-col gap-4">
        <label className="flex flex-col gap-2 text-sm font-medium text-primary">
          Selecciona una partida o item
          <select
            aria-label="Selecciona una partida o item"
            className="rounded-lg border border-[#D4C7B8] bg-white px-4 py-3 text-base"
            value={itemSeleccionadoId ?? ''}
            onChange={(event) => void handleItemChange(Number(event.target.value))}
            disabled={loadingItems || items.length === 0}
          >
            {items.map((item) => (
              <option key={item.id} value={item.id}>
                {(item.categoria ?? item.categoria_asignada ?? 'SIN_CATEGORIA') + ' - ' + item.item_key}
              </option>
            ))}
          </select>
        </label>
      </div>

      {loadingItems && (
        <div className="rounded-lg border border-[#E0D5C7] bg-white px-4 py-6 text-center text-sm text-accent">
          Cargando items desde la API...
        </div>
      )}

      {itemsError && (
        <div className="rounded-lg border border-[#D32F2F] bg-[#FDECEC] px-4 py-3 text-sm text-[#8B1E1E]">
          {itemsError}
        </div>
      )}

      {loadingRango && (
        <div className="rounded-lg border border-[#E0D5C7] bg-white px-4 py-6 text-center text-sm text-accent">
          Cargando estadisticas del item...
        </div>
      )}

      {!loadingRango && rangoError && (
        <div className="rounded-lg border border-[#D32F2F] bg-[#FDECEC] px-4 py-3 text-sm text-[#8B1E1E]">
          No se pudo cargar datos para {itemLabel || `item ${itemSeleccionadoId}`}
        </div>
      )}

      {!loadingRango && rangoData && (
        <>
          <div className="space-y-2 rounded-lg border border-[#E0D5C7] bg-white p-4">
            <h3 className="font-semibold text-primary">
              Item {rangoData.item_master_id}: {rangoData.categoria} - {rangoData.item_key}
            </h3>
            <p className="text-sm text-accent">Muestras totales: {rangoData.muestras_total}</p>
            <p className="text-sm text-accent">Promedio: {rangoData.avg_unitario.toFixed(2)}</p>
            <p className="text-sm text-accent">Items unicos: 1</p>
          </div>

          <RangoValidacion
            capitulo={`${rangoData.categoria} - ${rangoData.item_key}`}
            cantidad_datos={rangoData.muestras_total}
            descripcion={`${rangoData.item_key} (${rangoData.categoria})`}
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

      {!loadingRango && !rangoData && !rangoError && itemSeleccionadoId && (
        <div className="rounded-lg border border-[#D32F2F] bg-[#FDECEC] px-4 py-3 text-sm text-[#8B1E1E]">
          No se pudo cargar datos para {itemLabel || `item ${itemSeleccionadoId}`}
        </div>
      )}

      {!loadingItems && items.length === 0 && !itemsError && (
        <div className="rounded-lg border border-[#E0D5C7] bg-white px-4 py-6 text-sm text-accent">
          No hay items disponibles para mostrar el rango.
        </div>
      )}
    </div>
  );

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <div className="space-y-2">
        <h1 className="text-3xl font-serif text-primary">Visuales de ratios</h1>
        <p className="max-w-3xl text-sm text-accent">
          Demo de lectura sobre datos reales en produccion: valida rango por item y revisa la
          solidez estadistica de los datos disponibles.
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
          <p className="text-center text-sm text-accent">Cargando datos desde la API...</p>
        </div>
      ) : (
        <>
          {indiceTab === 0 && renderRango()}
          {indiceTab === 1 && <TablaConfiabilidad capitulos={capitulos} />}
        </>
      )}
    </div>
  );
};

export default Visuales;
