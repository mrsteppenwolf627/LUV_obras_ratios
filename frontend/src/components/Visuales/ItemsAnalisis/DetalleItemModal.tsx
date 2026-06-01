import React from 'react';
import type { ItemAnalisisResultado } from './types/analisisItems.types';
import styles from './styles/ItemsAnalisis.module.css';

interface DetalleItemModalProps {
  item: ItemAnalisisResultado;
  onClose: () => void;
}

const DetalleItemModal: React.FC<DetalleItemModalProps> = ({ item, onClose }) => {
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
    <div className={styles.modalOverlay} onClick={onClose} role="dialog" aria-modal="true">
      <div className={styles.modalContent} onClick={(e) => e.stopPropagation()}>
        <div className={styles.modalHeader}>
          <h3 className="text-xl font-serif text-primary">{item.descripcion}</h3>
          <button className={styles.closeBtn} onClick={onClose} aria-label="Cerrar">✕</button>
        </div>

        <div className={styles.modalBody}>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div className="space-y-4">
              <h4 className="font-bold text-primary border-b pb-2">Información del Análisis</h4>
              <dl className="space-y-2">
                <div className="flex justify-between">
                  <dt className="text-accent">Categoría:</dt>
                  <dd><span className={`${styles.badge} ${getCategoriaClass(item.categoria)}`}>{item.categoria}</span></dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-accent">Precio Usuario:</dt>
                  <dd className="font-semibold">€{item.precio_usuario.toFixed(2)}</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-accent">Ratio Histórico:</dt>
                  <dd className="font-semibold">{item.ratio_encontrado ? `€${item.ratio_historico?.toFixed(2)}` : 'Sin histórico'}</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-accent">Desviación:</dt>
                  <dd className={`font-semibold ${item.desviacion_pct !== null && item.desviacion_pct > 0 ? styles.desviacionPositiva : styles.desviacionNegativa}`}>
                    {item.desviacion_pct !== null ? `${item.desviacion_pct.toFixed(1)}%` : 'N/A'}
                  </dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-accent">Confianza:</dt>
                  <dd><span className={`${styles.confianza} ${getConfianzaClass(item.confianza)}`}>{item.confianza}</span></dd>
                </div>
              </dl>
            </div>

            <div className="space-y-4">
              <h4 className="font-bold text-primary border-b pb-2">Interpretación</h4>
              <div className="bg-[#f9f9f9] p-4 rounded-lg space-y-3 text-sm text-accent">
                {item.ratio_encontrado ? (
                  <>
                    <p>
                      {item.desviacion_pct !== null && Math.abs(item.desviacion_pct) > 5
                        ? `Este item está ${(item.desviacion_pct > 0 ? 'SOBRE' : 'BAJO')} precio respecto al histórico (${Math.abs(item.desviacion_pct).toFixed(1)}% de diferencia).`
                        : `Este item está en línea con el histórico (desviación menor al 5%).`}
                    </p>
                    <p>
                      {item.confianza === 'MUY_SÓLIDO'
                        ? 'Contamos con un alto número de muestras para este tipo de item, por lo que la estimación es altamente confiable.'
                        : item.confianza === 'SÓLIDO'
                        ? 'Contamos con un número adecuado de muestras, la estimación es confiable para toma de decisiones.'
                        : 'Existen pocas muestras históricas para este item. Toma esta referencia con cautela.'}
                    </p>
                  </>
                ) : (
                  <p>No se han encontrado ratios históricos que coincidan suficientemente con la descripción de este item para realizar una comparativa fiable.</p>
                )}
              </div>
            </div>
          </div>
        </div>

        <div className={styles.modalFooter}>
          <button className={styles.btnPrimary} onClick={onClose}>Cerrar</button>
        </div>
      </div>
    </div>
  );
};

export default DetalleItemModal;
