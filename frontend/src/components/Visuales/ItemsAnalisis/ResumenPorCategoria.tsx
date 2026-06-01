import React from 'react';
import type { ResumenPorCategoria as ResumenPorCategoriaType } from './types/analisisItems.types';
import styles from './styles/ItemsAnalisis.module.css';

interface ResumenPorCategoriaProps {
  resumenes: Record<string, ResumenPorCategoriaType>;
}

const ResumenPorCategoria: React.FC<ResumenPorCategoriaProps> = ({ resumenes }) => {
  const categorias = ['MEDIUM', 'PREMIUM', 'LUXURY', 'LUXURY_PLUS'];
  
  const getCategoriaClass = (cat: string) => {
    switch (cat) {
      case 'MEDIUM': return styles.categoriaMedium;
      case 'PREMIUM': return styles.categoriaPremium;
      case 'LUXURY': return styles.categoriaLuxury;
      case 'LUXURY_PLUS': return styles.categoriaLuxuryPlus;
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
      <h3 className="text-xl font-serif text-primary mb-4">Resumen por Categoría</h3>
      <div className={styles.resumenGrid}>
        {categorias.map((cat) => {
          const resumen = resumenes[cat];
          if (!resumen) return null;

          return (
            <div
              key={cat}
              className={`${styles.resumenCard} ${getCategoriaClass(cat)}`}
            >
              <div className={styles.cardHeader}>
                <h4 className="font-bold text-primary">{cat}</h4>
                <span className="text-xs bg-[#f3f4f6] px-2 py-1 rounded text-accent">
                  {resumen.cantidad_items} items
                </span>
              </div>

              <div className="space-y-1">
                <div className={styles.statRow}>
                  <span className="text-accent">Total Usuario:</span>
                  <span className="font-semibold">€{resumen.precio_total_usuario.toFixed(2)}</span>
                </div>
                <div className={styles.statRow}>
                  <span className="text-accent">Total Histórico:</span>
                  <span className="font-semibold">€{resumen.ratio_total_historico.toFixed(2)}</span>
                </div>
                <div className={styles.statRow}>
                  <span className="text-accent">Desviación:</span>
                  <span className={`font-semibold ${resumen.desviacion_pct_promedio > 0 ? styles.desviacionPositiva : styles.desviacionNegativa}`}>
                    {resumen.desviacion_pct_promedio.toFixed(1)}%
                  </span>
                </div>
                <div className={styles.statRow}>
                  <span className="text-accent">Confianza:</span>
                  <span className={`${styles.confianza} ${getConfianzaClass(resumen.confianza_global)}`}>
                    {resumen.confianza_global}
                  </span>
                </div>
                {resumen.items_sin_ratio > 0 && (
                  <div className={`${styles.statRow} ${styles.warning}`}>
                    ⚠️ {resumen.items_sin_ratio} sin ratio histórico
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default ResumenPorCategoria;
