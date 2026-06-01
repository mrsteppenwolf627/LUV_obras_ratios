import React, { useState, useEffect } from 'react';
import type { ItemParaAnalisis } from './types/analisisItems.types';
import styles from './styles/ItemsAnalisis.module.css';
import { ItemCombobox, type ItemOption } from '@/components/ItemCombobox';

interface ItemInputRow {
  id: string;
  descripcion: string;
  precio_unitario: string;
  cantidad: string;
  unidad: string;
}

interface AnalisisFormProps {
  onAnalizar: (items: ItemParaAnalisis[]) => void;
  onClose: () => void;
}

const AnalisisForm: React.FC<AnalisisFormProps> = ({ onAnalizar, onClose }) => {
  const [items, setItems] = useState<ItemInputRow[]>([
    { id: crypto.randomUUID(), descripcion: '', precio_unitario: '', cantidad: '1', unidad: 'm2' }
  ]);
  const [availableItems, setAvailableItems] = useState<ItemOption[]>([]);
  const [loadingItems, setLoadingItems] = useState(false);
  const [errores, setErrores] = useState<Record<string, string>>({});

  // Cargar items al montar
  useEffect(() => {
    const cargarItems = async () => {
      setLoadingItems(true);
      try {
        const res = await fetch('/api/items/list');
        if (res.ok) {
          const data = await res.json();
          setAvailableItems(data.items);
        }
      } catch (err) {
        console.error('Error cargando items:', err);
      } finally {
        setLoadingItems(false);
      }
    };
    cargarItems();
  }, []);

  const seleccionarItem = (itemIndex: number, selectedItem: ItemOption) => {
    setItems(
      items.map((item, idx) =>
        idx === itemIndex
          ? {
              ...item,
              descripcion: selectedItem.descripcion,
              // Pre-llenar precio si está disponible
              precio_unitario: selectedItem.ratio_actual
                ? selectedItem.ratio_actual.toString()
                : item.precio_unitario,
            }
          : item
      )
    );
  };

  const agregarItem = () => {
    setItems([
      ...items,
      { id: crypto.randomUUID(), descripcion: '', precio_unitario: '', cantidad: '1', unidad: 'm2' }
    ]);
  };

  const eliminarItem = (id: string) => {
    setItems(items.filter(item => item.id !== id));
  };

  const actualizarItem = (id: string, campo: keyof ItemInputRow, valor: string) => {
    setItems(items.map(item => 
      item.id === id ? { ...item, [campo]: valor } : item
    ));
  };

  const validar = (): boolean => {
    const nuevosErrores: Record<string, string> = {};
    
    items.forEach((item, idx) => {
      if (!item.descripcion.trim()) {
        nuevosErrores[`desc_${idx}`] = 'Descripción requerida';
      }
      const precio = Number(item.precio_unitario);
      if (isNaN(precio) || precio <= 0) {
        nuevosErrores[`precio_${idx}`] = 'Precio debe ser > 0';
      }
      const cantidad = Number(item.cantidad);
      if (isNaN(cantidad) || cantidad <= 0) {
        nuevosErrores[`cant_${idx}`] = 'Cantidad debe ser > 0';
      }
    });

    setErrores(nuevosErrores);
    return Object.keys(nuevosErrores).length === 0;
  };

  const handleAnalizar = () => {
    if (!validar()) return;

    const itemsParaAnalizar: ItemParaAnalisis[] = items.map(item => ({
      descripcion: item.descripcion.trim(),
      precio_unitario: Number(item.precio_unitario),
      cantidad: Number(item.cantidad) || 1,
      unidad: item.unidad || 'm2'
    }));

    onAnalizar(itemsParaAnalizar);
  };

  return (
    <div className={styles.modalOverlay} onClick={onClose} role="dialog" aria-modal="true">
      <div className={styles.modalContent} onClick={(e) => e.stopPropagation()}>
        <div className={styles.modalHeader}>
          <h3 className="text-xl font-serif text-primary">Analizar Presupuesto Nuevo</h3>
          <button className={styles.closeBtn} onClick={onClose} aria-label="Cerrar">✕</button>
        </div>

        <div className={styles.modalBody}>
          <div className="space-y-4">
            <h4 className="font-medium text-primary">Items</h4>
            {items.map((item, idx) => (
              <div key={item.id} className={styles.itemRow}>
                <ItemCombobox
                  items={availableItems}
                  value={item.descripcion}
                  onSelect={(selectedItem) => seleccionarItem(idx, selectedItem)}
                  onTextChange={(text) => actualizarItem(item.id, 'descripcion', text)}
                  placeholder="Selecciona un item..."
                  loading={loadingItems}
                  aria-label={`Descripción item ${idx + 1}`}
                />
                {errores[`desc_${idx}`] && <span className="text-[10px] text-red-500 absolute -bottom-4 left-0">{errores[`desc_${idx}`]}</span>}
                
                <input
                  type="number"
                  placeholder="Precio (€)"
                  value={item.precio_unitario}
                  onChange={(e) => actualizarItem(item.id, 'precio_unitario', e.target.value)}
                  className={errores[`precio_${idx}`] ? styles.error : ''}
                  step="0.01"
                  min="0"
                  aria-label={`Precio unitario item ${idx + 1}`}
                />
                {errores[`precio_${idx}`] && <span className="text-[10px] text-red-500 absolute -bottom-4 left-[calc(100%+0.5rem)] w-24">{errores[`precio_${idx}`]}</span>}

                <input
                  type="number"
                  placeholder="Cantidad"
                  value={item.cantidad}
                  onChange={(e) => actualizarItem(item.id, 'cantidad', e.target.value)}
                  className={errores[`cant_${idx}`] ? styles.error : ''}
                  step="0.01"
                  min="0"
                  aria-label={`Cantidad item ${idx + 1}`}
                />
                <select
                  value={item.unidad}
                  onChange={(e) => actualizarItem(item.id, 'unidad', e.target.value)}
                  aria-label={`Unidad item ${idx + 1}`}
                >
                  <option value="m2">m2</option>
                  <option value="ml">ml</option>
                  <option value="ud">ud</option>
                  <option value="kg">kg</option>
                </select>
                <button 
                  className={styles.deleteBtn} 
                  onClick={() => eliminarItem(item.id)}
                  disabled={items.length === 1}
                  aria-label={`Eliminar item ${idx + 1}`}
                >
                  🗑️
                </button>
              </div>
            ))}
            <button className={styles.addItemBtn} onClick={agregarItem}>
              + Agregar otro item
            </button>
          </div>
        </div>

        <div className={styles.modalFooter}>
          <button className={styles.btnSecondary} onClick={onClose}>Cancelar</button>
          <button className={styles.btnPrimary} onClick={handleAnalizar}>Analizar</button>
        </div>
      </div>
    </div>
  );
};

export default AnalisisForm;
