import React, { useState } from 'react';
import type { ItemAnalisisResultado } from './types/analisisItems.types';
import styles from './styles/ItemsAnalisis.module.css';

interface ItemsTableProps {
  items: ItemAnalisisResultado[];
  filtroCategoria: string | null;
  onItemClick: (item: ItemAnalisisResultado) => void;
}

type OrderBy = 'descripcion' | 'categoria' | 'precio_usuario' | 'desviacion_pct' | 'confianza';

const ItemsTable: React.FC<ItemsTableProps> = ({ items, filtroCategoria, onItemClick }) => {
  const [orderBy, setOrderBy] = useState<OrderBy>('categoria');
  const [orderDir, setOrderDir] = useState<'asc' | 'desc'>('asc');

  const itemsFiltrados = filtroCategoria
    ? items.filter(item => item.categoria === filtroCategoria)
    : items;

  const itemsOrdenados = [...itemsFiltrados].sort((a, b) => {
    let aVal: any = a[orderBy];
    let bVal: any = b[orderBy];

    if (typeof aVal === 'string') {
      aVal = aVal.toLowerCase();
      bVal = (b[orderBy] as string || '').toLowerCase();
    }
    
    if (aVal === null) return 1;
    if (bVal === null) return -1;

    const comparison = aVal < bVal ? -1 : aVal > bVal ? 1 : 0;
    return orderDir === 'asc' ? comparison : -comparison;
  });

  const handleSort = (col: OrderBy) => {
    if (orderBy === col) {
      setOrderDir(orderDir === 'asc' ? 'desc' : 'asc');
    } else {
      setOrderBy(col);
      setOrderDir('asc');
    }
  };

  const getCategoriaClass = (cat: string) => {
    switch (cat) {
      case 'MEDIUM': return styles.badgeMedium;
      case 'PREMIUM': return styles.badgePremium;
      case 'LUXURY': return styles.badgeLuxury;
      case 'LUXURY_PLUS': return styles.badgeLuxuryPlus;
      default: return '';
    }
  };

  const getConfianzaClass = (conf: string) => {
    switch (conf) {
      case 'MUY_DÉBIL': return styles.confianzaMuyDebil;
      case 'DÉBIL': return styles.confianzaDebil;
      case 'SÓLIDO': return styles.confianzaSolido;
      case 'MUY_SÓLIDO': return styles.confianzaMuySolido;
      default: return '';
    }
  };

  return (
    <div className="mt-8">
      <h3 className="text-xl font-serif text-primary mb-4">Items Analizados ({itemsOrdenados.length})</h3>
      <div className="overflow-x-auto rounded-lg border border-[#E0D5C7]">
        <table className={styles.itemsTable}>
          <thead>
            <tr>
              <th onClick={() => handleSort('descripcion')}>
                Descripción {orderBy === 'descripcion' && (orderDir === 'asc' ? '↑' : '↓')}
              </th>
              <th onClick={() => handleSort('categoria')}>
                Categoría {orderBy === 'categoria' && (orderDir === 'asc' ? '↑' : '↓')}
              </th>
              <th onClick={() => handleSort('precio_usuario')}>
                Precio Usuario {orderBy === 'precio_usuario' && (orderDir === 'asc' ? '↑' : '↓')}
              </th>
              <th>Ratio Histórico</th>
              <th onClick={() => handleSort('desviacion_pct')}>
                Desviación % {orderBy === 'desviacion_pct' && (orderDir === 'asc' ? '↑' : '↓')}
              </th>
              <th onClick={() => handleSort('confianza')}>
                Confianza {orderBy === 'confianza' && (orderDir === 'asc' ? '↑' : '↓')}
              </th>
              <th>Acción</th>
            </tr>
          </thead>
          <tbody>
            {itemsOrdenados.map((item, idx) => (
              <tr key={idx}>
                <td title={item.descripcion}>{truncate(item.descripcion, 40)}</td>
                <td>
                  <span className={`${styles.badge} ${getCategoriaClass(item.categoria)}`}>
                    {item.categoria}
                  </span>
                </td>
                <td>€{item.precio_usuario.toFixed(2)}</td>
                <td>{item.ratio_encontrado ? `€${item.ratio_historico?.toFixed(2)}` : 'N/A'}</td>
                <td className={item.desviacion_pct !== null ? (item.desviacion_pct > 0 ? styles.desviacionPositiva : styles.desviacionNegativa) : ''}>
                  {item.desviacion_pct !== null ? `${item.desviacion_pct.toFixed(1)}%` : 'N/A'}
                </td>
                <td>
                  <span className={`${styles.confianza} ${getConfianzaClass(item.confianza)}`}>
                    {item.confianza}
                  </span>
                </td>
                <td>
                  <button className={styles.detailBtn} onClick={() => onItemClick(item)}>
                    Ver detalles
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

const truncate = (str: string, length: number) => 
  str.length > length ? str.substring(0, length) + '...' : str;

export default ItemsTable;
