import React, { useEffect, useState, useMemo } from 'react';
import LoadingSpinner from '@/components/LoadingSpinner';

interface ItemWithGama {
  id: number;
  item_key: string;
  categoria: string | null;
  mediana_unitario: number | null;
  min_unitario: number | null;
  max_unitario: number | null;
  muestras_count: number;
  gama_asignada: string;
}

interface GamaStats {
  gama: string;
  count: number;
  min: number;
  max: number;
  median: number;
}

const GAMAS = ['MEDIUM', 'PREMIUM', 'LUXURY', 'LUXURY_PLUS'];

const GamaComparativa: React.FC = () => {
  const [items, setItems] = useState<ItemWithGama[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchItems = async () => {
      try {
        setLoading(true);
        const res = await fetch('/api/items/with_gamas?limit=1000');
        if (!res.ok) throw new Error(`Error ${res.status}`);
        const data = await res.json();
        setItems(data.items);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Error cargando items');
      } finally {
        setLoading(false);
      }
    };
    fetchItems();
  }, []);

  const gamaStats = useMemo(() => {
    const stats: Record<string, GamaStats> = {};
    
    GAMAS.forEach(gama => {
      stats[gama] = { gama, count: 0, min: Infinity, max: -Infinity, median: 0 };
    });

    const pricesByGama: Record<string, number[]> = {};

    items.forEach(item => {
      const gama = item.gama_asignada;
      if (stats[gama] && item.mediana_unitario != null) {
        stats[gama].count++;
        if (item.mediana_unitario < stats[gama].min) stats[gama].min = item.mediana_unitario;
        if (item.mediana_unitario > stats[gama].max) stats[gama].max = item.mediana_unitario;
        
        if (!pricesByGama[gama]) pricesByGama[gama] = [];
        pricesByGama[gama].push(item.mediana_unitario);
      }
    });

    GAMAS.forEach(gama => {
      if (stats[gama].count > 0) {
        const prices = pricesByGama[gama].sort((a, b) => a - b);
        const mid = Math.floor(prices.length / 2);
        stats[gama].median = prices.length % 2 !== 0 ? prices[mid] : (prices[mid - 1] + prices[mid]) / 2;
      } else {
        stats[gama].min = 0;
        stats[gama].max = 0;
      }
    });

    return GAMAS.map(gama => stats[gama]);
  }, [items]);

  if (loading) return <div className="flex justify-center p-12"><LoadingSpinner /></div>;
  if (error) return <div className="p-4 bg-red-50 text-red-700 rounded-lg">{error}</div>;

  return (
    <div className="space-y-6">
      <div className="space-y-1">
        <h2 className="text-2xl font-serif text-primary">Items × Gama</h2>
        <p className="text-sm text-accent">Distribución de items y precios según la gama asignada automáticamente.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {gamaStats.map(stat => (
          <div key={stat.gama} className="bg-white p-6 rounded-lg border border-[#E0D5C7] shadow-sm hover:border-[#2D5016] transition-colors">
            <h3 className="text-lg font-bold text-primary mb-4 border-b border-[#F0EAE0] pb-2">{stat.gama}</h3>
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-xs text-accent uppercase font-bold tracking-wider">Items</span>
                <span className="text-xl font-serif text-primary">{stat.count}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-xs text-accent uppercase font-bold tracking-wider">Mediana</span>
                <span className="text-xl font-serif text-[#2D5016]">€{stat.median.toLocaleString(undefined, { maximumFractionDigits: 0 })}</span>
              </div>
              <div className="pt-2 border-t border-[#F0EAE0] flex justify-between text-xs text-accent">
                <span>Min: €{stat.min.toLocaleString(undefined, { maximumFractionDigits: 0 })}</span>
                <span>Max: €{stat.max.toLocaleString(undefined, { maximumFractionDigits: 0 })}</span>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="bg-[#FAF7F2] p-6 rounded-lg border border-[#D4C7B8]">
        <h3 className="font-bold text-primary mb-4">Detalle de Items por Gama</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-[#D4C7B8] text-accent font-bold">
                <th className="py-2">Item</th>
                <th className="py-2">Gama</th>
                <th className="py-2 text-right">Precio Mediana</th>
                <th className="py-2 text-center">Muestras</th>
              </tr>
            </thead>
            <tbody>
              {items.slice(0, 20).map(item => (
                <tr key={item.id} className="border-b border-[#F0EAE0] hover:bg-[#F5F0EA]">
                  <td className="py-2 font-medium">{item.item_key.replace(/_/g, ' ')}</td>
                  <td className="py-2">
                    <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                      item.gama_asignada === 'MEDIUM' ? 'bg-gray-100 text-gray-600' :
                      item.gama_asignada === 'PREMIUM' ? 'bg-blue-100 text-blue-600' :
                      item.gama_asignada === 'LUXURY' ? 'bg-purple-100 text-purple-600' :
                      item.gama_asignada === 'LUXURY_PLUS' ? 'bg-amber-100 text-amber-600' :
                      'bg-gray-100 text-gray-600'
                    }`}>
                      {item.gama_asignada}
                    </span>
                  </td>
                  <td className="py-2 text-right">€{item.mediana_unitario?.toLocaleString()}</td>
                  <td className="py-2 text-center text-accent">{item.muestras_count}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="mt-4 text-xs text-accent italic">Mostrando los primeros 20 items con más muestras.</p>
        </div>
      </div>
    </div>
  );
};

export default GamaComparativa;
