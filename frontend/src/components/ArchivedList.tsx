import { FileText, Calendar, Euro, Hash, Download } from 'lucide-react';
import { useFetch } from '../hooks/useFetch';
import type { ArchivedResponse } from '../types';
import LoadingSpinner from './LoadingSpinner';
import { formatCurrency, formatDate, truncateHash } from '../utils/format';

const ArchivedList = () => {
  const { data, loading, error } = useFetch<ArchivedResponse>('/archived');

  if (loading) return <LoadingSpinner />;
  if (error) return <div className="text-center py-12 text-error">Error: {error}</div>;
  if (!data) return null;

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-3xl font-serif text-primary mb-2">Historial de Importaciones</h2>
        <p className="text-accent italic">Registro cronológico de presupuestos analizados y su trazabilidad.</p>
      </div>

      <div className="grid grid-cols-1 gap-6">
        {data.archived.length > 0 ? (
          data.archived.map((budget) => (
            <div 
              key={budget.budget_id}
              className="bg-white border border-border p-6 hover:shadow-md transition-shadow group flex flex-col md:flex-row md:items-center justify-between gap-6"
            >
              <div className="flex items-start space-x-4">
                <div className="p-3 bg-secondary text-accent group-hover:bg-accent group-hover:text-white transition-colors">
                  <FileText className="w-6 h-6" />
                </div>
                <div>
                  <h3 className="text-lg font-serif text-primary mb-1">{budget.filename}</h3>
                  <div className="flex flex-wrap gap-x-6 gap-y-2 text-xs text-accent uppercase tracking-widest font-medium">
                    <span className="flex items-center">
                      <Calendar className="w-3 h-3 mr-1" />
                      {formatDate(budget.import_date)}
                    </span>
                    <span className="flex items-center">
                      <Hash className="w-3 h-3 mr-1" />
                      {budget.chapter_count} capítulos
                    </span>
                    <span className="flex items-center">
                      <Euro className="w-3 h-3 mr-1" />
                      {formatCurrency(budget.total_amount)}
                    </span>
                  </div>
                </div>
              </div>

              <div className="flex items-center space-x-8">
                <div className="text-right hidden sm:block">
                  <p className="text-[10px] text-accent uppercase tracking-[0.2em] mb-1">Trazabilidad</p>
                  <code className="text-xs text-primary bg-secondary px-2 py-1">
                    {truncateHash(budget.file_hash)}...
                  </code>
                </div>
                
                <button 
                  title="Descargar Original"
                  className="p-2 border border-border hover:bg-secondary transition-colors text-accent hover:text-primary"
                >
                  <Download className="w-5 h-5" />
                </button>
              </div>
            </div>
          ))
        ) : (
          <div className="bg-white border border-border p-12 text-center text-accent italic">
            No hay importaciones registradas todavía.
          </div>
        )}
      </div>
    </div>
  );
};

export default ArchivedList;
