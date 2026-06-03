import React, { useState } from 'react';

import type { CapituloRatioResponse } from '@/types/visuales';

interface TablaConfiabilidadProps {
  capitulos: CapituloRatioResponse[];
}

const TablaConfiabilidad: React.FC<TablaConfiabilidadProps> = ({ capitulos }) => {
  const [showTutorial, setShowTutorial] = useState(false);
  const sortedCapitulos = [...capitulos].sort((a, b) => b.cantidad_datos - a.cantidad_datos);

  const getSolidezBarColor = (estado: string) => {
    switch (estado) {
      case 'muy_solido':
        return 'bg-[#2D5016]';
      case 'solido':
        return 'bg-[#4CAF50]';
      case 'debil':
        return 'bg-[#FBC02D]';
      case 'muy_debil':
        return 'bg-[#D32F2F]';
      default:
        return 'bg-gray-500';
    }
  };

  return (
    <div className="overflow-x-auto rounded-lg border border-[#E0D5C7] bg-white p-4 font-inter">
      <h2 className="mb-4 text-lg font-bold text-[#2D5016]">Solidez por capitulo</h2>
      {sortedCapitulos.length === 0 && (
        <p className="rounded-lg border border-dashed border-[#D4C7B8] bg-[#FAF7F2] px-4 py-6 text-sm text-[#6B5D4D]">
          No hay capitulos disponibles para evaluar la solidez.
        </p>
      )}
      {sortedCapitulos.length > 0 && <table className="w-full text-left">
        <thead>
          <tr className="bg-[#2D5016] text-white">
            <th className="p-3">Capitulo</th>
            <th className="p-3">Datos</th>
            <th className="p-3">Solidez</th>
          </tr>
        </thead>
        <tbody>
          {sortedCapitulos.map((c, idx) => (
            <tr key={c.capitulo} className={idx % 2 === 0 ? 'bg-white' : 'bg-[#FAF7F2]'}>
              <td className="p-3 font-medium">{c.capitulo}</td>
              <td className="p-3">{c.cantidad_datos}</td>
              <td className="flex items-center gap-2 p-3">
                <div className="h-4 w-24 overflow-hidden rounded bg-gray-200">
                  <div
                    className={`h-full ${getSolidezBarColor(c.estado_confiabilidad)}`}
                    style={{ width: `${Math.min((c.cantidad_datos / 12) * 100, 100)}%` }}
                  />
                </div>
                <span className="text-xs font-bold uppercase">{c.estado_confiabilidad.replace('_', ' ')}</span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>}

      <div className="mt-8 border-t border-[#D4C788] pt-4">
        <button
          onClick={() => setShowTutorial(!showTutorial)}
          className="flex items-center gap-2 text-sm font-medium text-primary hover:text-[#2D5016] transition-colors"
        >
          {showTutorial ? '📖 Cerrar guía' : '📖 Cómo usar esta herramienta'}
          <span className="text-xs">{showTutorial ? '▼' : '▶'}</span>
        </button>

        {showTutorial && (
          <div className="mt-3 bg-[#E8F1FF] p-5 rounded-lg border border-[#B8D4FF] shadow-sm animate-in fade-in slide-in-from-top-1 duration-200">
            <h3 className="font-bold text-primary mb-3">Ver la confiabilidad de cada capítulo</h3>
            <ol className="space-y-3 text-sm text-[#4A4034] list-decimal pl-5">
              <li><strong>Mira la tabla</strong>: cada fila es un capítulo (AMENITIES, CARPINTERÍA, etc).</li>
              <li><strong>Lee las columnas</strong>:
                <ul className="list-disc pl-5 mt-1 space-y-1">
                  <li><strong>Capítulo</strong>: nombre de la partida.</li>
                  <li><strong>Datos</strong>: cuántos presupuestos tenemos de esta partida.</li>
                  <li><strong>Solidez</strong>: barra de color (rojo/naranja/verde). Más datos = más verde.</li>
                </ul>
              </li>
              <li>Haz clic en <strong>"Ver detalle"</strong> (si está disponible) para expandir estadísticas (mediana, rango, etc).</li>
              <li>Un capítulo con <strong>muchas muestras (>10)</strong> es más fiable que uno con pocas (<3).</li>
            </ol>
            <p className="mt-4 text-xs font-semibold text-primary border-t border-[#B8D4FF] pt-2 italic">
              Cuándo usarlo: Para saber qué capítulos tienen datos buenos vs pobres.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default TablaConfiabilidad;
