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

const MUESTRAS_MINIMAS_PARA_RANGO = 2;

const formatMetric = (value: number | null | undefined) =>
  value === null || value === undefined ? 'N/D' : value.toFixed(2);

const getEstadoValidacion = (cantidad: number) => {
  if (cantidad === 0) return 'SIN_DATOS';
  if (cantidad < MUESTRAS_MINIMAS_PARA_RANGO) return 'MUESTRA_INSUFICIENTE';
  return 'VALIDACION_COMPLETA';
};

const getBadgeColor = (estado: EstadoConfiabilidad) => {
  switch (estado) {
    case 'muy_solido': return 'bg-[#2D5016]';
    case 'solido':     return 'bg-[#4CAF50]';
    case 'debil':      return 'bg-[#FBC02D]';
    case 'muy_debil':  return 'bg-[#D32F2F]';
    default:           return 'bg-gray-500';
  }
};

const RangoValidacion: React.FC<RangoValidacionProps> = ({
  capitulo,
  descripcion,
  minimo,
  percentil_25,
  percentil_75,
  mediana,
  maximo,
  cantidad_datos,
  unidad,
  estado_confiabilidad,
  desviacion_std,
}) => {
  const [miValor, setMiValor] = useState<string>('');
  const [showTutorial, setShowTutorial] = useState(false);

  const estado = getEstadoValidacion(cantidad_datos);

  const miValorNumerico = miValor !== '' ? Number(miValor) : null;
  const hasMiValor = miValorNumerico !== null && !isNaN(miValorNumerico);

  const puedeValidar = estado === 'VALIDACION_COMPLETA';

  const dentroRango =
    puedeValidar &&
    hasMiValor &&
    minimo !== null &&
    maximo !== null &&
    Number.isFinite(miValorNumerico!) &&
    miValorNumerico! >= minimo &&
    miValorNumerico! <= maximo;

  const renderTutorial = () => (
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
          <h3 className="font-bold text-primary mb-3">Validar si tu precio está en rango</h3>
          <ol className="space-y-3 text-sm text-[#4A4034] list-decimal pl-5">
            <li><strong>Selecciona un capítulo</strong> en el desplegable superior (ej: AMENITIES).</li>
            <li><strong>Entra el precio unitario</strong> en EUR/m2 que quieres validar (ej: 250).</li>
            <li>El sistema compara tu precio contra todos los históricos:
              <ul className="list-disc pl-5 mt-1 space-y-1">
                <li><span className="text-green-700 font-bold">VERDE</span> = Tu precio está dentro del rango normal.</li>
                <li><span className="text-red-700 font-bold">ROJO</span> = Tu precio está fuera (muy alto o muy bajo).</li>
              </ul>
            </li>
            <li><strong>Lee la confiabilidad</strong> (badge arriba a la derecha):
              <ul className="list-disc pl-5 mt-1 space-y-1">
                <li><span className="font-bold uppercase text-red-700">MUY DÉBIL</span> = Solo 1 dato histórico (poco fiable).</li>
                <li><span className="font-bold uppercase text-green-700">SÓLIDO / MUY SÓLIDO</span> = Muchos datos (muy fiable).</li>
              </ul>
            </li>
          </ol>
          <p className="mt-4 text-xs font-semibold text-primary border-t border-[#B8D4FF] pt-2 italic">
            Cuándo usarlo: Para revisar si tus precios de construcción son razonables.
          </p>
        </div>
      )}
    </div>
  );

  // ── Estado: SIN DATOS ──────────────────────────────────────────────────────
  if (estado === 'SIN_DATOS') {
    return (
      <div className="w-full rounded-lg border border-[#E0D5C7] bg-[#F5F1EB] p-6 font-inter text-left">
        <div className="mb-4 flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
          <div>
            <h2 className="font-playfair text-xl font-bold">{capitulo}</h2>
            <p className="mt-1 text-sm text-[#6B5D4D]">{descripcion}</p>
          </div>
        </div>
        <div className="rounded-lg border border-[#D4C788] bg-gray-100 p-6 text-center">
          <p className="text-gray-600">
            No hay datos históricos para <strong>{descripcion}</strong> aún.
          </p>
          <p className="mt-2 text-sm text-gray-500">
            Importa presupuestos para ver análisis comparativos.
          </p>
        </div>
        {renderTutorial()}
      </div>
    );
  }

  // ── Estado: MUESTRA INSUFICIENTE (N=1) ────────────────────────────────────
  if (estado === 'MUESTRA_INSUFICIENTE') {
    return (
      <div className="w-full rounded-lg border border-[#E0D5C7] bg-[#F5F1EB] p-6 font-inter text-left">
        <div className="mb-4 flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
          <div>
            <h2 className="font-playfair text-xl font-bold">{capitulo}</h2>
            <p className="mt-1 text-sm text-[#6B5D4D]">{descripcion}</p>
          </div>
        </div>
        <div className="rounded-lg border border-orange-300 bg-orange-50 p-4">
          <div className="mb-2 flex items-center gap-2">
            <span className="inline-block rounded bg-orange-600 px-2 py-1 text-xs font-bold text-white">
              MUY_DÉBIL
            </span>
            <p className="text-sm font-semibold text-orange-800">
              Muestra insuficiente ({cantidad_datos}/{MUESTRAS_MINIMAS_PARA_RANGO})
            </p>
          </div>
          <p className="text-xs text-orange-700">
            Solo hay {cantidad_datos} dato. Importa más presupuestos para validar rangos confiables.
          </p>
          <label className="mt-3 flex flex-col gap-2">
            <span className="text-sm">Valor comparativo ({unidad}) (referencia):</span>
            <input
              type="number"
              value={miValor}
              onChange={(e) => setMiValor(e.target.value)}
              placeholder="Ej: 245.50"
              min="0"
              step="0.01"
              className="rounded border border-orange-300 px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-orange-300/50"
            />
          </label>
          <p className="mt-2 text-xs text-orange-700">
            Referencia: {formatMetric(mediana)} {unidad} (único dato)
          </p>
        </div>
        {renderTutorial()}
      </div>
    );
  }

  // ── Estado: VALIDACION COMPLETA (N>=2) ────────────────────────────────────
  return (
    <div className="w-full rounded-lg border border-[#E0D5C7] bg-[#F5F1EB] p-6 font-inter text-left">
      <div className="mb-4 flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
        <div>
          <h2 className="font-playfair text-xl font-bold">{capitulo}</h2>
          <p className="mt-1 text-sm text-[#6B5D4D]">{descripcion}</p>
        </div>
        <span className={`${getBadgeColor(estado_confiabilidad)} rounded px-3 py-1 text-sm uppercase text-white`}>
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

      {renderTutorial()}
    </div>
  );
};

export default RangoValidacion;
