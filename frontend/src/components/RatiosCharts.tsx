import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, 
  LineChart, Line, AreaChart, Area
} from 'recharts';
import { useFetch } from '../hooks/useFetch';
import type { StatsResponse } from '../types';
import LoadingSpinner from './LoadingSpinner';
import { formatCurrency } from '../utils/format';

const RatiosCharts = () => {
  const { data, loading, error } = useFetch<StatsResponse>('/ratios/stats');

  if (loading) return <LoadingSpinner />;
  if (error) return <div className="text-center py-12 text-error">Error: {error}</div>;
  if (!data) return null;

  return (
    <div className="space-y-12">
      <div>
        <h2 className="text-3xl font-serif text-primary mb-2">Análisis Visual</h2>
        <p className="text-accent italic">Distribución económica y tendencias de costes por capítulos.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Top Chapters Chart */}
        <div className="bg-white border border-border p-8 shadow-sm">
          <h3 className="text-sm font-bold uppercase tracking-widest text-primary mb-8 border-b border-border pb-4">
            Top 10 Capítulos por Importe Total
          </h3>
          <div className="h-[400px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={data.top_chapters}
                layout="vertical"
                margin={{ top: 5, right: 30, left: 40, bottom: 5 }}
              >
                <CartesianGrid strokeDasharray="3 3" horizontal={true} vertical={false} stroke="#e0dcd8" />
                <XAxis type="number" hide />
                <YAxis 
                  dataKey="chapter_code" 
                  type="category" 
                  tick={{ fill: '#333333', fontSize: 12 }}
                  width={60}
                />
                <Tooltip 
                  cursor={{ fill: '#f5f2f0' }}
                  contentStyle={{ 
                    backgroundColor: '#ffffff', 
                    border: '1px solid #e0dcd8',
                    borderRadius: '0px',
                    fontSize: '12px'
                  }}
                  formatter={(value: any) => [formatCurrency(Number(value)), 'Importe']}
                />
                <Bar 
                  dataKey="total_amount" 
                  fill="#8b7355" 
                  radius={[0, 2, 2, 0]} 
                  barSize={24}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Ratio Distribution Chart */}
        <div className="bg-white border border-border p-8 shadow-sm">
          <h3 className="text-sm font-bold uppercase tracking-widest text-primary mb-8 border-b border-border pb-4">
            Distribución de Ratios (€/m²)
          </h3>
          <div className="h-[400px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart
                data={data.ratio_distribution}
                margin={{ top: 10, right: 10, left: 0, bottom: 0 }}
              >
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e0dcd8" />
                <XAxis 
                  dataKey="range" 
                  tick={{ fill: '#333333', fontSize: 10 }}
                  interval={0}
                  angle={-45}
                  textAnchor="end"
                  height={60}
                />
                <YAxis tick={{ fill: '#333333', fontSize: 12 }} />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: '#ffffff', 
                    border: '1px solid #e0dcd8',
                    borderRadius: '0px',
                    fontSize: '12px'
                  }}
                />
                <Area 
                  type="monotone" 
                  dataKey="count" 
                  stroke="#1a1a1a" 
                  fill="#f5f2f0" 
                  strokeWidth={2}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Temporal Evolution (if data available) */}
      {data.temporal_evolution && data.temporal_evolution.length > 0 && (
        <div className="bg-white border border-border p-8 shadow-sm">
          <h3 className="text-sm font-bold uppercase tracking-widest text-primary mb-8 border-b border-border pb-4">
            Evolución Temporal de Ratios Medios
          </h3>
          <div className="h-[300px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={data.temporal_evolution}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e0dcd8" />
                <XAxis 
                  dataKey="date" 
                  tick={{ fill: '#333333', fontSize: 12 }}
                />
                <YAxis tick={{ fill: '#333333', fontSize: 12 }} />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: '#ffffff', 
                    border: '1px solid #e0dcd8',
                    borderRadius: '0px',
                    fontSize: '12px'
                  }}
                  formatter={(value: any) => [formatCurrency(Number(value)), 'Ratio Medio']}
                />
                <Line 
                  type="monotone" 
                  dataKey="avg_ratio" 
                  stroke="#8b7355" 
                  strokeWidth={3}
                  dot={{ r: 6, fill: '#8b7355', strokeWidth: 2, stroke: '#ffffff' }}
                  activeDot={{ r: 8 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}
    </div>
  );
};

export default RatiosCharts;
