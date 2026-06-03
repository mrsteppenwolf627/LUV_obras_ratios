import React, { useState } from 'react';
import useAnalisisItems from './hooks/useAnalisisItems';
import AnalisisForm from './AnalisisForm';
import ItemsTable from './ItemsTable';
import ResumenPorCategoria from './ResumenPorCategoria';
import GraficosAnalisis from './GraficosAnalisis';
import DetalleItemModal from './DetalleItemModal';
import AnalisisHistorico from './AnalisisHistorico';
import type { ItemAnalisisResultado } from './types/analisisItems.types';
import LoadingSpinner from '@/components/LoadingSpinner';
import styles from './styles/ItemsAnalisis.module.css';

const ItemsAnalisisTab: React.FC = () => {
  const { 
    analisisActual,
    historico,
    loading,
    error,
    analizarItems,
  } = useAnalisisItems();

  const [mostrandoForm, setMostrandoForm] = useState(false);
  const [filtroCategoria, setFiltroCategoria] = useState<string | null>(null);
  const [vistaHistorico, setVistaHistorico] = useState(false);
  const [itemParaDetalle, setItemParaDetalle] = useState<ItemAnalisisResultado | null>(null);
  const [showTutorial, setShowTutorial] = useState(false);

  return (
    <div className="space-y-6">
      <div className={styles.header}>
        <div className="space-y-1">
          <h2 className="text-2xl font-serif text-primary">Items × Categorías</h2>
          <p className="text-sm text-accent">Análisis de items con clasificación automática y comparación histórica.</p>
        </div>
        <div className={styles.botones}>
          <button 
            className={`${styles.btnSecondary} flex items-center gap-2`}
            onClick={() => setVistaHistorico(!vistaHistorico)}
            disabled={historico.length === 0}
          >
            {vistaHistorico ? 'Volver al Análisis' : `Ver Histórico (${historico.length})`}
          </button>
          <button 
            className={`${styles.btnPrimary} flex items-center gap-2`}
            onClick={() => setMostrandoForm(true)}
          >
            + Analizar Presupuesto
          </button>
        </div>
      </div>

      {mostrandoForm && (
        <AnalisisForm
          onAnalizar={(items) => {
            analizarItems(items);
            setMostrandoForm(false);
            setVistaHistorico(false);
          }}
          onClose={() => setMostrandoForm(false)}
        />
      )}

      {itemParaDetalle && (
        <DetalleItemModal
          item={itemParaDetalle}
          onClose={() => setItemParaDetalle(null)}
        />
      )}

      {error && (
        <div className="rounded-lg border border-[#D32F2F] bg-[#FDECEC] px-4 py-3 text-sm text-[#8B1E1E]">
          {error}
        </div>
      )}

      {loading && (
        <div className="flex flex-col items-center justify-center p-12 bg-white rounded-lg border border-[#E0D5C7]">
          <LoadingSpinner />
          <p className="mt-4 text-accent">Analizando items y consultando históricos...</p>
        </div>
      )}

      {!loading && (
        <>
          {vistaHistorico ? (
            <AnalisisHistorico historico={historico} />
          ) : (
            <>
              {analisisActual ? (
                <div className="space-y-8">
                  <div className="bg-[#FAF7F2] p-6 rounded-lg border border-[#D4C7B8] flex flex-wrap gap-8 justify-between items-center">
                    <div className="flex gap-12">
                      <div className="flex flex-col">
                        <span className="text-xs text-accent uppercase font-bold tracking-wider">Total Presupuesto</span>
                        <span className="text-2xl font-serif text-primary">€{analisisActual.resumen_general.total_usuario.toLocaleString()}</span>
                      </div>
                      <div className="flex flex-col">
                        <span className="text-xs text-accent uppercase font-bold tracking-wider">Desviación vs Histórico</span>
                        <span className={`text-2xl font-serif ${analisisActual.resumen_general.diferencia_pct > 0 ? styles.desviacionPositiva : styles.desviacionNegativa}`}>
                          {analisisActual.resumen_general.diferencia_pct > 0 ? '+' : ''}{analisisActual.resumen_general.diferencia_pct.toFixed(1)}%
                        </span>
                      </div>
                    </div>
                    
                    <div className={styles.filtros}>
                      <label className="text-sm font-medium text-primary">Filtrar por categoría:</label>
                      <select 
                        value={filtroCategoria || ''} 
                        onChange={(e) => setFiltroCategoria(e.target.value || null)}
                      >
                        <option value="">Todas las categorías</option>
                        <option value="MEDIUM">MEDIUM</option>
                        <option value="PREMIUM">PREMIUM</option>
                        <option value="LUXURY">LUXURY</option>
                        <option value="LUXURY_PLUS">LUXURY_PLUS</option>
                      </select>
                    </div>
                  </div>

                  <ResumenPorCategoria resumenes={analisisActual.resumenes_por_categoria} />
                  
                  <ItemsTable
                    items={analisisActual.items}
                    filtroCategoria={filtroCategoria}
                    onItemClick={(item) => setItemParaDetalle(item)}
                  />

                  <GraficosAnalisis items={analisisActual.items} />
                </div>
              ) : (
                !loading && !error && (
                  <div className={styles.sinAnalisis}>
                    <div className="max-w-md mx-auto space-y-4">
                      <div className="text-4xl">📊</div>
                      <h3 className="text-xl font-serif text-primary">No hay un análisis activo</h3>
                      <p className="text-accent">
                        Utiliza el botón <strong>"Analizar Presupuesto"</strong> para ingresar los items de tu obra y compararlos con nuestros ratios históricos.
                      </p>
                      <button 
                        className={styles.btnPrimary}
                        onClick={() => setMostrandoForm(true)}
                      >
                        Comenzar primer análisis
                      </button>
                    </div>
                  </div>
                )
              )}
            </>
          )}
        </>
      )}

      <div className="mt-6 border-t border-[#D4C788] pt-4">
        <button
          onClick={() => setShowTutorial(!showTutorial)}
          className="flex items-center gap-2 text-sm font-medium text-primary hover:text-secondary transition-colors"
        >
          📖 Cómo usar esta herramienta
          <span>{showTutorial ? '▼' : '▶'}</span>
        </button>

        {showTutorial && (
          <div className="mt-3 bg-blue-50 p-4 rounded border border-blue-200 shadow-sm">
            <h3 className="font-bold text-gray-800 mb-2">Analizar partidas por categoría</h3>
            <ol className="space-y-2 text-sm text-gray-700 list-decimal pl-5">
              <li>Haz clic en <strong>"Analizar Presupuesto Nuevo"</strong> (botón verde).</li>
              <li>Se abre un formulario con campos:
                <ul className="list-disc pl-5 mt-1 space-y-1">
                  <li><strong>Busca un item</strong> en el dropdown (empieza a escribir "Carpintería").</li>
                  <li>El precio se pre-rellena automáticamente.</li>
                  <li>Puedes cambiar el precio si lo necesitas.</li>
                </ul>
              </li>
              <li>Haz clic <strong>"Añadir"</strong> → el item aparece en la lista debajo.</li>
              <li>Repite pasos 1-3 con más items de tu presupuesto.</li>
              <li>Haz clic <strong>"Analizar"</strong> → ves resultados:
                <ul className="list-disc pl-5 mt-1 space-y-1">
                  <li>Tabla por categoría (MEDIUM, PREMIUM, LUXURY, etc).</li>
                  <li>Tu total vs Ratio histórico por cada categoría.</li>
                  <li>Diferencia % (<span className="text-red-700 font-bold">rojo</span> = caro, <span className="text-green-700 font-bold">verde</span> = barato).</li>
                  <li>Confiabilidad de cada categoría.</li>
                </ul>
              </li>
              <li>Haz clic en <strong>un item de la tabla</strong> para ver detalle completo (rango, gráficos).</li>
            </ol>
            <p className="mt-3 text-xs font-semibold text-gray-600 border-t border-blue-200 pt-2 italic">
              Cuándo usarlo: Para desglosar y validar cada partida individual de tu presupuesto.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default ItemsAnalisisTab;
