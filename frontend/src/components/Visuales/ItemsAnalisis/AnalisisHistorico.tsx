import React, { useState } from 'react';
import type { AnalisisItemsResponse } from './types/analisisItems.types';
import ItemsTable from './ItemsTable';
import ResumenPorCategoria from './ResumenPorCategoria';
import styles from './styles/ItemsAnalisis.module.css';

interface AnalisisHistoricoProps {
  historico: AnalisisItemsResponse[];
}

const AnalisisHistorico: React.FC<AnalisisHistoricoProps> = ({ historico }) => {
  const [analisisSeleccionado, setAnalisisSeleccionado] = useState<AnalisisItemsResponse | null>(null);

  if (historico.length === 0) {
    return (
      <div className={styles.sinAnalisis}>
        <p className="text-accent">No hay análisis históricos en esta sesión.</p>
      </div>
    );
  }

  if (analisisSeleccionado) {
    return (
      <div className="space-y-6">
        <button 
          className="flex items-center gap-2 text-[#2D5016] font-semibold hover:underline"
          onClick={() => setAnalisisSeleccionado(null)}
        >
          ← Volver al listado
        </button>
        <div className="bg-white p-6 rounded-lg border border-[#E0D5C7]">
          <h3 className="text-2xl font-serif text-primary mb-6">Detalles del Análisis</h3>
          <ResumenPorCategoria resumenes={analisisSeleccionado.resumenes_por_categoria} />
          <ItemsTable items={analisisSeleccionado.items} filtroCategoria={null} onItemClick={() => {}} />
        </div>
      </div>
    );
  }

  return (
    <div className="mt-8">
      <h3 className="text-xl font-serif text-primary mb-4">Histórico de Análisis (Sesión Actual)</h3>
      <div className="overflow-x-auto rounded-lg border border-[#E0D5C7]">
        <table className={styles.itemsTable}>
          <thead>
            <tr>
              <th>#</th>
              <th>Cantidad Items</th>
              <th>Total Usuario</th>
              <th>Desviación General</th>
              <th>Acción</th>
            </tr>
          </thead>
          <tbody>
            {historico.map((analisis, idx) => (
              <tr key={idx}>
                <td>{historico.length - idx}</td>
                <td>{analisis.items.length} items</td>
                <td>€{analisis.resumen_general.total_usuario.toLocaleString()}</td>
                <td className={analisis.resumen_general.diferencia_pct > 0 ? styles.desviacionPositiva : styles.desviacionNegativa}>
                  {analisis.resumen_general.diferencia_pct.toFixed(1)}%
                </td>
                <td>
                  <button className={styles.detailBtn} onClick={() => setAnalisisSeleccionado(analisis)}>
                    Ver detalles
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default AnalisisHistorico;
