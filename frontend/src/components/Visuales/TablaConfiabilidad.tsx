import React from 'react';

import type { CapituloRatioResponse } from '@/types/visuales';

interface TablaConfiabilidadProps {
  capitulos: CapituloRatioResponse[];
}

const TablaConfiabilidad: React.FC<TablaConfiabilidadProps> = ({ capitulos }) => {
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
      <table className="w-full text-left">
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
      </table>
    </div>
  );
};

export default TablaConfiabilidad;
