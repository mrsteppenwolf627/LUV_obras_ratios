import { useEffect, useMemo, useState } from 'react';

import LoadingSpinner from '@/components/LoadingSpinner';
import ComparativaDesviacion from '@/components/Visuales/ComparativaDesviacion';
import RangoValidacion from '@/components/Visuales/RangoValidacion';
import TablaConfiabilidad from '@/components/Visuales/TablaConfiabilidad';
import ItemsAnalisisTab from '@/components/Visuales/ItemsAnalisis/ItemsAnalisisTab';
import GamaComparativa from '@/components/GamaComparativa';
import { useVisuales } from '@/hooks/useVisuales';
import type {
  CapituloRatioResponse,
  ComparativaResponse,
  ItemPresupuesto,
  PresupuestoAnalisis,
  RangoResponse,
} from '@/types/visuales';

type ComparativaDraftItem = {
  id: string;
  capitulo: string;
  valor_unitario: string;
  cantidad: string;
  unidad: string;
};

const TABS = ['Rango', 'Solidez', 'Comparativa', 'Items × Categorías', 'Items × Gama'];

const createDraftItem = (capitulo = ''): ComparativaDraftItem => ({
  id: globalThis.crypto?.randomUUID?.() ?? `${Date.now()}-${Math.random()}`,
  capitulo,
  valor_unitario: '',
  cantidad: '1',
  unidad: 'm2',
});

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

const isPositiveNumber = (value: string) => {
  const parsed = Number(value);
  return Number.isFinite(parsed) && parsed > 0;
};

const Visuales = () => {
  const { capitulos, loading, analyzing, error, setError, analizarPresupuesto } = useVisuales();
  const [indiceTab, setIndiceTab] = useState(0);
  const [capituloSeleccionado, setCapituloSeleccionado] = useState('');
  const [areaTotal, setAreaTotal] = useState('');
  const [comparativaItems, setComparativaItems] = useState<ComparativaDraftItem[]>([createDraftItem()]);
  const [comparativaData, setComparativaData] = useState<ComparativaResponse | null>(null);
  const [formError, setFormError] = useState<string | null>(null);
  const [rangoData, setRangoData] = useState<RangoResponse | null>(null);
  const [loadingRango, setLoadingRango] = useState(false);

  useEffect(() => {
    if (!capituloSeleccionado && capitulos.length > 0) {
      setCapituloSeleccionado(capitulos[0].capitulo);
      setComparativaItems([createDraftItem(capitulos[0].capitulo)]);
    }
  }, [capituloSeleccionado, capitulos]);

  const selectedCapitulo = useMemo(
    () => capitulos.find((capitulo) => capitulo.capitulo === capituloSeleccionado) ?? null,
    [capituloSeleccionado, capitulos],
  );

  const displayError = humanizeError(formError ?? error);

  const updateComparativaItem = (
    id: string,
    field: keyof Omit<ComparativaDraftItem, 'id'>,
    value: string,
  ) => {
    setComparativaItems((current) =>
      current.map((item) => (item.id === id ? { ...item, [field]: value } : item)),
    );
  };

  const addComparativaItem = () => {
    setComparativaItems((current) => [...current, createDraftItem(capitulos[0]?.capitulo ?? '')]);
  };

  const removeComparativaItem = (id: string) => {
    setComparativaItems((current) => (current.length > 1 ? current.filter((item) => item.id !== id) : current));
  };

  const handleCapituloChange = async (chapter: string) => {
    setCapituloSeleccionado(chapter);
    setLoadingRango(true);
    try {
      const res = await fetch(`/api/ratios/rango?chapter=${encodeURIComponent(chapter)}`);
      if (!res.ok) {
        throw new Error(`Error ${res.status}`);
      }
      const data = await res.json() as RangoResponse;
      setRangoData(data);
    } catch (error) {
      console.error('Error cargando rango:', error);
      setRangoData(null);
    } finally {
      setLoadingRango(false);
    }
  };

  const buildPresupuesto = (): PresupuestoAnalisis | null => {
    if (!isPositiveNumber(areaTotal)) {
      setFormError('Introduce un area total mayor que 0.');
      return null;
    }

    const items: ItemPresupuesto[] = comparativaItems
      .filter((item) => item.capitulo && isPositiveNumber(item.valor_unitario))
      .map((item) => ({
        capitulo: item.capitulo,
        valor_unitario: Number(item.valor_unitario),
        cantidad: isPositiveNumber(item.cantidad) ? Math.round(Number(item.cantidad)) : 1,
        unidad: item.unidad.trim() || 'm2',
      }));

    if (items.length === 0) {
      setFormError('Anade al menos un capitulo con valor unitario mayor que 0.');
      return null;
    }

    return {
      items,
      area_total: Number(areaTotal),
    };
  };

  const handleAnalizarComparativa = async () => {
    const presupuesto = buildPresupuesto();
    if (!presupuesto) {
      setComparativaData(null);
      return;
    }

    setFormError(null);
    setError(null);
    const response = await analizarPresupuesto(presupuesto);
    setComparativaData(response);
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
              <option key={item.capitulo} value={item.capitulo}>
                {item.capitulo} - {item.descripcion ?? 'Sin descripcion'}
              </option>
            ))}
          </select>
        </label>
      </div>

      {loadingRango && (
        <div className="rounded-lg border border-[#E0D5C7] bg-white px-4 py-6 text-sm text-accent text-center">
          Cargando estadísticas...
        </div>
      )}

      {!loadingRango && rangoData && (
        <>
          <div className="rounded-lg border border-[#E0D5C7] bg-white p-4 space-y-2">
            <h3 className="font-semibold text-primary">{rangoData.chapter}</h3>
            <p className="text-sm text-accent">Muestras totales: {rangoData.muestras_total}</p>
            <p className="text-sm text-accent">Items únicos: {rangoData.items_count}</p>
          </div>

          <RangoValidacion
            capitulo={rangoData.chapter}
            cantidad_datos={rangoData.muestras_total}
            descripcion={`${rangoData.items_count} items únicos`}
            desviacion_std={null}
            estado_confiabilidad={rangoData.muestras_total >= 5 ? 'solido' : rangoData.muestras_total >= 2 ? 'debil' : 'muy_debil'}
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

  const [showTutorialComparativa, setShowTutorialComparativa] = useState(false);

  const renderComparativaForm = () => (
    <div className="space-y-6">
      <div className="grid grid-cols-1 items-end gap-4 md:grid-cols-[220px_auto]">
        <label className="flex flex-col gap-2 text-sm font-medium text-primary">
          Area total (m2)
          <input
            aria-label="Area total"
            className="rounded-lg border border-[#D4C7B8] bg-white px-4 py-3 text-base"
            min="0"
            placeholder="Area total"
            step="0.01"
            type="number"
            value={areaTotal}
            onChange={(event) => setAreaTotal(event.target.value)}
          />
        </label>

        <div className="rounded-lg border border-dashed border-[#D4C7B8] bg-[#FAF7F2] px-4 py-3 text-sm text-[#6B5D4D]">
          Simula la carga del presupuesto introduciendo capitulos y valores unitarios manualmente.
        </div>
      </div>

      <div className="space-y-4">
        {comparativaItems.map((item, index) => (
          <div
            key={item.id}
            className="grid grid-cols-1 gap-3 rounded-lg border border-[#E0D5C7] bg-white p-4 xl:grid-cols-[minmax(0,1.5fr)_180px_120px_120px_auto]"
          >
            <label className="flex flex-col gap-2 text-sm font-medium text-primary">
              Capitulo
              <select
                aria-label={`Capitulo ${index + 1}`}
                className="rounded-lg border border-[#D4C7B8] bg-white px-3 py-2"
                value={item.capitulo}
                onChange={(event) => updateComparativaItem(item.id, 'capitulo', event.target.value)}
              >
                <option value="">Selecciona capitulo</option>
                {capitulos.map((capitulo) => (
                  <option key={capitulo.capitulo} value={capitulo.capitulo}>
                    {capitulo.capitulo} - {capitulo.descripcion ?? 'Sin descripcion'}
                  </option>
                ))}
              </select>
            </label>

            <label className="flex flex-col gap-2 text-sm font-medium text-primary">
              Valor unitario
              <input
                aria-label={`Valor unitario ${index + 1}`}
                className="rounded-lg border border-[#D4C7B8] bg-white px-3 py-2"
                min="0"
                placeholder="EUR/m2"
                step="0.01"
                type="number"
                value={item.valor_unitario}
                onChange={(event) => updateComparativaItem(item.id, 'valor_unitario', event.target.value)}
              />
            </label>

            <label className="flex flex-col gap-2 text-sm font-medium text-primary">
              Cantidad
              <input
                aria-label={`Cantidad ${index + 1}`}
                className="rounded-lg border border-[#D4C7B8] bg-white px-3 py-2"
                min="1"
                step="1"
                type="number"
                value={item.cantidad}
                onChange={(event) => updateComparativaItem(item.id, 'cantidad', event.target.value)}
              />
            </label>

            <label className="flex flex-col gap-2 text-sm font-medium text-primary">
              Unidad
              <input
                aria-label={`Unidad ${index + 1}`}
                className="rounded-lg border border-[#D4C7B8] bg-white px-3 py-2"
                value={item.unidad}
                onChange={(event) => updateComparativaItem(item.id, 'unidad', event.target.value)}
              />
            </label>

            <div className="flex items-end justify-end">
              <button
                aria-label={`Eliminar fila ${index + 1}`}
                className="rounded-lg border border-[#D4C7B8] px-4 py-2 text-sm text-primary disabled:opacity-40"
                disabled={comparativaItems.length === 1}
                type="button"
                onClick={() => removeComparativaItem(item.id)}
              >
                Eliminar
              </button>
            </div>
          </div>
        ))}
      </div>

      <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
        <button
          className="rounded-lg border border-[#2D5016] px-4 py-3 text-sm font-semibold text-[#2D5016]"
          type="button"
          onClick={addComparativaItem}
        >
          Anadir capitulo
        </button>
        <button
          className="rounded-lg bg-[#2D5016] px-5 py-3 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:bg-[#9AAF92]"
          disabled={analyzing || capitulos.length === 0}
          type="button"
          onClick={() => void handleAnalizarComparativa()}
        >
          {analyzing ? 'Analizando...' : 'Analizar comparativa'}
        </button>
      </div>

      {comparativaData && (
        <div className="space-y-4">
          <ComparativaDesviacion capitulos={comparativaData.capitulos} resumen={comparativaData.resumen} />
          {comparativaData.capitulos_sin_ratio.length > 0 && (
            <div className="rounded-lg border border-[#FBC02D] bg-[#FFF8DE] px-4 py-3 text-sm text-[#7A5A00]">
              Capitulos sin ratio: {comparativaData.capitulos_sin_ratio.join(', ')}
            </div>
          )}
        </div>
      )}

      <div className="mt-6 border-t border-[#D4C788] pt-4">
        <button
          onClick={() => setShowTutorialComparativa(!showTutorialComparativa)}
          className="flex items-center gap-2 text-sm font-medium text-primary hover:text-secondary transition-colors"
        >
          📖 Cómo usar esta herramienta
          <span>{showTutorialComparativa ? '▼' : '▶'}</span>
        </button>

        {showTutorialComparativa && (
          <div className="mt-3 bg-blue-50 p-4 rounded-lg border border-blue-200 shadow-sm animate-in fade-in slide-in-from-top-1 duration-200 text-left">
            <h3 className="font-bold text-gray-800 mb-2">Simular presupuesto vs ratios históricos</h3>
            <ol className="space-y-2 text-sm text-gray-700 list-decimal pl-5">
              <li><strong>Introduce el área total</strong> de tu proyecto en m2.</li>
              <li><strong>Añade capítulos</strong>: selecciona el nombre de la partida (ej: ESTRUCTURA).</li>
              <li><strong>Introduce valores</strong>: pon el valor unitario (EUR/m2) y la cantidad de ese capítulo.</li>
              <li>Haz clic en <strong>"Analizar comparativa"</strong> para ver los resultados:
                <ul className="list-disc pl-5 mt-1 space-y-1">
                  <li><strong>MIO</strong>: Coste total calculado para tu presupuesto.</li>
                  <li><strong>RATIO</strong>: Coste esperado según la mediana histórica.</li>
                  <li><strong>DESV%</strong>: Porcentaje de desviación (<span className="text-red-700 font-bold">rojo</span> = caro, <span className="text-green-700 font-bold">verde</span> = barato).</li>
                  <li><strong>IMPACTO</strong>: Diferencia monetaria total en euros.</li>
                </ul>
              </li>
              <li>Revisa el <strong>Resumen final</strong> para ver si tu obra global está en precio.</li>
            </ol>
            <p className="mt-3 text-xs font-semibold text-gray-600 border-t border-blue-200 pt-2 italic">
              Cuándo usarlo: Para validar si un presupuesto completo es competitivo vs el mercado histórico.
            </p>
          </div>
        )}
      </div>
    </div>
  );

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <div className="space-y-2">
        <h1 className="text-3xl font-serif text-primary">Visuales de ratios</h1>
        <p className="max-w-3xl text-sm text-accent">
          Valida rangos por capitulo, revisa la solidez estadistica y compara un presupuesto propio contra los ratios historicos.
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
          {indiceTab === 2 && renderComparativaForm()}
          {indiceTab === 3 && <ItemsAnalisisTab />}
          {indiceTab === 4 && <GamaComparativa />}
        </>
      )}
    </div>
  );
};

export default Visuales;
