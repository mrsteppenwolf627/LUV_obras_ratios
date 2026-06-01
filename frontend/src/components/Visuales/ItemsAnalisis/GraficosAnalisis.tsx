import React from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ScatterChart,
  Scatter,
  ComposedChart,
} from 'recharts';
import type { ItemAnalisisResultado } from './types/analisisItems.types';
import styles from './styles/ItemsAnalisis.module.css';

interface GraficosAnalisisProps {
  items: ItemAnalisisResultado[];
}

const COLORS = ['#8B9DC3', '#D4A574', '#C9A876', '#2C2C2C'];
const CATEGORIAS = ['MEDIUM', 'PREMIUM', 'LUXURY', 'LUXURY_PLUS'];

const GraficosAnalisis: React.FC<GraficosAnalisisProps> = ({ items }) => {
  // Data para barchart
  const dataBarChart = CATEGORIAS.map(cat => ({
    categoria: cat,
    cantidad: items.filter(i => i.categoria === cat).length,
  })).filter(d => d.cantidad > 0);

  // Helper para preparar datos boxplot (simplificado para BarChart en este caso)
  const prepararBoxplotData = () => {
    return CATEGORIAS.map(cat => {
      const desviaciones = items
        .filter(i => i.categoria === cat && i.desviacion_pct !== null)
        .map(i => i.desviacion_pct!);
      
      if (desviaciones.length === 0) return { categoria: cat, desviacion_pct: 0 };
      
      const sum = desviaciones.reduce((a, b) => a + b, 0);
      const avg = sum / desviaciones.length;
      return {
        categoria: cat,
        desviacion_pct: parseFloat(avg.toFixed(1)),
      };
    });
  };

  return (
    <div className={styles.graficosSection}>
      <div className={styles.graficoContainer}>
        <h4 className="font-bold text-primary mb-4">Items por Categoría</h4>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={dataBarChart}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="categoria" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Bar dataKey="cantidad" fill="#2D5016" name="Cantidad de Items" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className={styles.graficoContainer}>
        <h4 className="font-bold text-primary mb-4">Precio Usuario vs Ratio Histórico</h4>
        <ResponsiveContainer width="100%" height={300}>
          <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis type="number" dataKey="precio_usuario" name="Precio Usuario" unit="€" />
            <YAxis type="number" dataKey="ratio_historico" name="Ratio Histórico" unit="€" />
            <Tooltip cursor={{ strokeDasharray: '3 3' }} />
            <Legend />
            {CATEGORIAS.map((cat, idx) => (
              <Scatter
                key={cat}
                name={cat}
                data={items.filter(i => i.categoria === cat && i.ratio_encontrado)}
                fill={COLORS[idx]}
              />
            ))}
          </ScatterChart>
        </ResponsiveContainer>
      </div>

      <div className={styles.graficoContainer}>
        <h4 className="font-bold text-primary mb-4">Desviación Promedio % por Categoría</h4>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={prepararBoxplotData()}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="categoria" />
            <YAxis label={{ value: 'Desviación %', angle: -90, position: 'insideLeft' }} />
            <Tooltip />
            <Legend />
            <Bar dataKey="desviacion_pct" fill="#8884d8" name="Desviación Promedio %" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default GraficosAnalisis;
