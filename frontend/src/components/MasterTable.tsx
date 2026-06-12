import { useState, useMemo } from 'react';
import { Search, Download, Filter, AlertTriangle, CheckCircle } from 'lucide-react';
import { useFetch } from '../hooks/useFetch';
import type { MasterResponse } from '../types';
import LoadingSpinner from './LoadingSpinner';
import { formatCurrency } from '../utils/format';
import { toast } from 'react-toastify';

const MasterTable = () => {
  const { data, loading, error } = useFetch<MasterResponse>('/master');
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<'ALL' | 'VALID' | 'DUBIOUS'>('ALL');
  const [currentPage, setCurrentPage] = useState(1);
  const rowsPerPage = 50;

  const filteredRatios = useMemo(() => {
    if (!data) return [];
    
    return data.ratios.filter((ratio) => {
      const matchesSearch = 
        ratio.chapter_code.toLowerCase().includes(searchTerm.toLowerCase()) ||
        ratio.chapter_description.toLowerCase().includes(searchTerm.toLowerCase());
      
      const matchesStatus = 
        statusFilter === 'ALL' || 
        ratio.validation_status === statusFilter;
      
      return matchesSearch && matchesStatus;
    });
  }, [data, searchTerm, statusFilter]);

  const paginatedRatios = useMemo(() => {
    const startIndex = (currentPage - 1) * rowsPerPage;
    return filteredRatios.slice(startIndex, startIndex + rowsPerPage);
  }, [filteredRatios, currentPage]);

  const totalPages = Math.ceil(filteredRatios.length / rowsPerPage);

  const handleDownload = () => {
    window.open('http://localhost:8000/api/export/master.xlsx', '_blank');
    toast.info('Descargando Master Excel...');
  };

  if (loading) return <LoadingSpinner />;
  if (error) return <div className="text-center py-12 text-error">Error: {error}</div>;
  if (!data) return null;

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-3xl font-serif text-primary">Master de Ratios</h2>
          <p className="text-accent text-sm italic">
            Consolidado de {data.metadata.total_ratios} ratios de {data.metadata.total_budgets} presupuestos.
          </p>
        </div>
        <button
          onClick={handleDownload}
          className="flex items-center px-6 py-2 bg-primary text-white text-sm uppercase tracking-widest hover:bg-accent transition-all self-start"
        >
          <Download className="w-4 h-4 mr-2" />
          Exportar Excel
        </button>
      </div>

      <div className="bg-white border border-border p-6 shadow-sm">
        <div className="flex flex-col md:flex-row gap-4 mb-8">
          <div className="relative flex-grow">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-accent" />
            <input
              type="text"
              placeholder="Buscar por capítulo o descripción..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-border focus:border-accent outline-none text-sm"
            />
          </div>
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-accent" />
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value as ('ALL' | 'VALID' | 'DUBIOUS'))}
              className="border border-border py-2 px-4 text-sm focus:border-accent outline-none bg-white"
            >
              <option value="ALL">Todos los estados</option>
              <option value="VALID">Solo Confiables</option>
              <option value="DUBIOUS">Solo Dudosos</option>
            </select>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-border text-xs uppercase tracking-widest text-accent font-bold bg-secondary/30">
                <th className="px-4 py-4 font-bold">Capítulo</th>
                <th className="px-4 py-4 font-bold">Descripción</th>
                <th className="px-4 py-4 font-bold">Gama</th>
                <th className="px-4 py-4 font-bold text-right">€/m² (Mediana)</th>
                <th className="px-4 py-4 font-bold text-right">Min</th>
                <th className="px-4 py-4 font-bold text-right">Max</th>
                <th className="px-4 py-4 font-bold text-center">Nº</th>
                <th className="px-4 py-4 font-bold text-center">Estado</th>
              </tr>
            </thead>
            <tbody className="text-sm">
              {paginatedRatios.length > 0 ? (
                paginatedRatios.map((ratio, idx) => (
                  <tr 
                    key={`${ratio.chapter_code}-${idx}`}
                    className={`
                      border-b border-border/50 hover:bg-secondary/20 transition-colors
                      ${ratio.validation_status === 'DUBIOUS' ? 'bg-[#f0ede9]/40' : ''}
                    `}
                  >
                    <td className="px-4 py-4 font-medium text-primary">{ratio.chapter_code}</td>
                    <td className="px-4 py-4 text-accent italic">{ratio.chapter_description || '—'}</td>
                    <td className="px-4 py-4 text-xs">
                      {ratio.gama_asignada ? (
                        <span className="px-2 py-1 rounded bg-secondary text-primary font-bold">
                          {ratio.gama_asignada}
                        </span>
                      ) : '—'}
                    </td>
                    <td className="px-4 py-4 text-right font-bold text-primary">
                      {formatCurrency(ratio.median_ratio)}
                    </td>
                    <td className="px-4 py-4 text-right text-accent">
                      {formatCurrency(ratio.min_ratio)}
                    </td>
                    <td className="px-4 py-4 text-right text-accent">
                      {formatCurrency(ratio.max_ratio)}
                    </td>
                    <td className="px-4 py-4 text-center text-accent">{ratio.count_budgets}</td>
                    <td className="px-4 py-4 text-center">
                      {ratio.validation_status === 'VALID' ? (
                        <div className="flex justify-center" title="Validado">
                          <CheckCircle className="w-4 h-4 text-success" />
                        </div>
                      ) : (
                        <div className="flex justify-center" title="Dudoso / Revisar">
                          <AlertTriangle className="w-4 h-4 text-warning" />
                        </div>
                      )}
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={7} className="px-4 py-12 text-center text-accent italic">
                    No se encontraron ratios con los filtros actuales.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {totalPages > 1 && (
          <div className="mt-8 flex justify-center items-center space-x-4">
            <button
              disabled={currentPage === 1}
              onClick={() => setCurrentPage(prev => prev - 1)}
              className="px-4 py-2 border border-border text-xs uppercase tracking-widest disabled:opacity-30 hover:bg-secondary transition-all"
            >
              Anterior
            </button>
            <span className="text-xs text-accent">
              Página {currentPage} de {totalPages}
            </span>
            <button
              disabled={currentPage === totalPages}
              onClick={() => setCurrentPage(prev => prev + 1)}
              className="px-4 py-2 border border-border text-xs uppercase tracking-widest disabled:opacity-30 hover:bg-secondary transition-all"
            >
              Siguiente
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default MasterTable;
