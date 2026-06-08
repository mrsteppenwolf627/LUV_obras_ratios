import React, { useState } from 'react';

import type { ComparativaCapitulo, ResumenComparativa } from '@/types/visuales';

interface ComparativaDesviacionProps {
  capitulos: ComparativaCapitulo[];
  resumen: ResumenComparativa;
}

const ComparativaDesviacion: React.FC<ComparativaDesviacionProps> = ({ capitulos, resumen }) => {
  const [showTutorial, setShowTutorial] = useState(false);
  return (
    <div className="space-y-6 font-inter">
      <div className="overflow-x-auto rounded-lg border border-[#E0D5C7] bg-white p-4">
        <h2 className="mb-4 text-lg font-bold">
          Desviacion: Mi presupuesto vs ratios ({resumen.area_total} m2)
        </h2>
        {capitulos.length === 0 && (
          <p className="rounded-lg border border-dashed border-[#D4C7B8] bg-[#FAF7F2] px-4 py-6 text-sm text-[#6B5D4D]">
            No hay capitulos comparables para mostrar.
          </p>
        )}
        {capitulos.length > 0 && <table className="w-full text-left">
          <thead>
            <tr className="bg-[#2D5016] text-white">
              <th className="p-3">CAP</th>
              <th className="p-3">MIO</th>
              <th className="p-3">RATIO</th>
              <th className="p-3">DESV%</th>
              <th className="p-3">IMPACTO</th>
            </tr>
          </thead>
          <tbody>
            {capitulos.map((c, idx) => (
              <tr key={c.capitulo} className={idx % 2 === 0 ? 'bg-white' : 'bg-[#FAF7F2]'}>
                <td className="p-3 font-medium">{c.capitulo}</td>
                <td className="p-3">{c.valor_mio.toFixed(2)}</td>
                <td className="p-3">{c.valor_ratio.toFixed(2)}</td>
                <td className={`p-3 font-bold ${c.desviacion_pct >= 0 ? 'text-[#D32F2F]' : 'text-[#4CAF50]'}`}>
                  {c.desviacion_pct > 0 ? '+' : ''}
                  {c.desviacion_pct}%
                </td>
                <td className={c.impacto_monetario >= 0 ? 'p-3 text-[#D32F2F]' : 'p-3 text-[#4CAF50]'}>
                  {c.impacto_monetario.toFixed(2)} EUR
                </td>
              </tr>
            ))}
          </tbody>
        </table>}
      </div>

      <div className="rounded-lg border-4 border-gray-300 bg-[#F0F0F0] p-6">
        <h3 className="mb-4 text-xl font-bold">Resumen</h3>
        <div className="grid grid-cols-1 gap-4 text-lg md:grid-cols-2">
          <p>Total presupuesto: EUR {resumen.total_presupuesto.toLocaleString()}</p>
          <p>Total ratios: EUR {resumen.total_ratio.toLocaleString()}</p>
          <p className="font-bold">
            Diferencia: {resumen.diferencia_monetaria.toLocaleString()} EUR ({resumen.diferencia_pct}%)
          </p>
          <p>Confiabilidad: {resumen.confiabilidad_global.toUpperCase()}</p>
        </div>
      </div>

      <div className="mt-6 border-t border-[#D4C788] pt-4">
        <button
          onClick={() => setShowTutorial(!showTutorial)}
          className="flex items-center gap-2 text-sm font-medium text-primary hover:text-secondary transition-colors"
        >
          📖 Cómo usar esta herramienta
          <span>{showTutorial ? '▼' : '▶'}</span>
        </button>

        {showTutorial && (
          <div className="mt-3 bg-blue-50 p-4 rounded-lg border border-blue-200 shadow-sm animate-in fade-in slide-in-from-top-1 duration-200">
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
};

export default ComparativaDesviacion;
