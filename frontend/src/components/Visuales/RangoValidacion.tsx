import React, { useState } from 'react';

import type { EstadoConfiabilidad } from '@/types/visuales';

interface RangoValidacionProps {
  capitulo: string;
  descripcion: string;
  minimo: number | null;
  percentil_25: number | null;
  mediana: number | null;
  percentil_75: number | null;
  maximo: number | null;
  cantidad_datos: number;
  unidad: string;
  estado_confiabilidad: EstadoConfiabilidad;
  desviacion_std?: number | null;
}

const formatMetric = (value: number | null | undefined) =>
  value === null || value === undefined ? 'N/D' : value.toFixed(2);

const RangoValidacion: React.FC<RangoValidacionProps> = ({
  capitulo,
  descripcion,
  minimo,
  percentil_25,
  mediana,
  percentil_75,
  maximo,
  cantidad_datos,
  unidad,
  estado_confiabilidad,
  desviacion_std,
}) => {
  const [miValor, setMiValor] = useState<string>('');

  const getBadgeColor = () => {
    switch (estado_confiabilidad) {
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

  const miValorNumerico = miValor !== '' ? Number(miValor) : null;
  const hasMiValor = miValorNumerico !== null && !isNaN(miValorNumerico);

  const dentroRango =
    hasMiValor &&
    minimo !== null &&
    maximo !== null &&
    miValorNumerico >= minimo &&
    miValorNumerico <= maximo;

  return (
    <div className="w-full rounded-lg border border-[#E0D5C7] bg-[#F5F1EB] p-6 font-inter">
      <div className="mb-4 flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
        <div>
          <h2 className="font-playfair text-xl font-bold">{capitulo}</h2>
          <p className="mt-1 text-sm text-[#6B5D4D]">{descripcion}</p>
        </div>
        <span className={`${getBadgeColor()} rounded px-3 py-1 text-sm uppercase text-white`}>
          {estado_confiabilidad.replace('_', ' ')}
        </span>
      </div>

      <div className="mb-6">
        <label className="flex flex-col gap-2 text-sm font-medium text-[#4A4034]">
          Mi valor ({unidad})
          <input
            type="number"
            value={miValor}
            onChange={(e) => setMiValor(e.target.value)}
            placeholder="Ej: 245.50"
            min="0"
            step="0.01"
            className="rounded-lg border border-[#D4C788] bg-white px-4 py-2 text-base outline-none focus:ring-2 focus:ring-[#D4C788]/50"
          />
        </label>
      </div>

      <div className="my-6">
        <p className="mb-2 text-sm">Escala ({unidad})</p>
        <div className="relative h-6 rounded bg-gray-200">
          <div className="absolute left-0 top-0 h-full w-[10%] rounded-l bg-red-500" />
          <div className="absolute left-[30%] top-0 h-full w-[40%] bg-blue-500" />
          <div className="absolute right-0 top-0 h-full w-[10%] rounded-r bg-red-500" />
        </div>
        <div className="mt-1 flex justify-between text-xs">
          <span>{formatMetric(minimo)}</span>
          <span>{formatMetric(mediana)}</span>
          <span>{formatMetric(maximo)}</span>
        </div>
      </div>

      <div className="mb-5 grid grid-cols-2 gap-3 text-sm text-[#4A4034] md:grid-cols-4">
        <p>P25: {formatMetric(percentil_25)}</p>
        <p>P75: {formatMetric(percentil_75)}</p>
        <p>Desv.: {formatMetric(desviacion_std)}</p>
        <p>Muestras: {cantidad_datos}</p>
      </div>

      <div className={`text-lg font-bold ${hasMiValor ? (dentroRango ? 'text-green-700' : 'text-red-700') : 'text-[#6B5D4D]'}`}>
        {hasMiValor ? (
          <>
            Mi valor: {miValorNumerico?.toFixed(2)} {unidad} — {dentroRango ? '✅ Dentro de rango' : '❌ Fuera de rango'}
          </>
        ) : (
          'Introduce tu valor para validar el rango.'
        )}
      </div>
    </div>
  );
};

export default RangoValidacion;
