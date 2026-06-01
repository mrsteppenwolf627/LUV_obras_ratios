import { useState, useRef, useEffect } from 'react';

export interface ItemOption {
  id: number;
  item_key: string;
  descripcion: string;
  categoria_asignada: string;
  muestras_count: number;
  ratio_actual?: number;
}

interface ItemComboboxProps {
  items: ItemOption[];
  value: string;
  onSelect: (item: ItemOption) => void;
  onTextChange?: (text: string) => void;
  placeholder?: string;
  loading?: boolean;
  'aria-label'?: string;
}

export function ItemCombobox({
  items,
  value,
  onSelect,
  onTextChange,
  placeholder = 'Selecciona un item...',
  loading = false,
  'aria-label': ariaLabel,
}: ItemComboboxProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [searchText, setSearchText] = useState('');
  const containerRef = useRef<HTMLDivElement>(null);

  const selectedItem = items.find((item) => item.item_key === value);

  const filteredItems = items.filter(
    (item) =>
      item.descripcion.toLowerCase().includes(searchText.toLowerCase()) ||
      item.categoria_asignada.toLowerCase().includes(searchText.toLowerCase()),
  );

  const handleSelect = (item: ItemOption) => {
    setSearchText(item.descripcion);
    onSelect(item);
    setIsOpen(false);
  };

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <div ref={containerRef} className="relative w-full">
      <input
        type="text"
        value={searchText}
        onChange={(e) => {
          setSearchText(e.target.value);
          onTextChange?.(e.target.value);
          setIsOpen(true);
        }}
        onFocus={() => setIsOpen(true)}
        placeholder={placeholder}
        className="w-full rounded-lg border border-[#D4C7B8] bg-white px-3 py-2 text-base focus:outline-none focus:ring-2 focus:ring-[#2D5016] disabled:opacity-50"
        disabled={loading}
        aria-label={ariaLabel}
        aria-autocomplete="list"
        aria-expanded={isOpen}
      />

      {loading && (
        <div className="absolute left-0 right-0 top-full z-50 mt-1 rounded-md border border-[#D4C7B8] bg-white p-2 text-sm text-[#6B5D4D] shadow-lg">
          Cargando items...
        </div>
      )}

      {isOpen && !loading && (
        <div className="absolute left-0 right-0 top-full z-50 mt-1 max-h-64 overflow-y-auto rounded-md border border-[#D4C7B8] bg-white shadow-lg">
          {filteredItems.length > 0 ? (
            filteredItems.map((item) => (
              <button
                key={item.id}
                type="button"
                onClick={() => handleSelect(item)}
                className="flex w-full items-start justify-between border-b border-[#F0EAE0] px-3 py-2 text-left last:border-b-0 hover:bg-[#F5F0EA]"
              >
                <div>
                  <div className="text-sm font-medium text-primary">{item.descripcion}</div>
                  <div className="text-xs text-[#6B5D4D]">
                    {item.categoria_asignada} &bull; N={item.muestras_count}
                    {item.ratio_actual != null && ` • €${item.ratio_actual.toFixed(0)}`}
                  </div>
                </div>
                {selectedItem?.id === item.id && (
                  <span className="ml-2 font-bold text-[#2D5016]">✓</span>
                )}
              </button>
            ))
          ) : (
            <div className="px-3 py-2 text-sm text-[#6B5D4D]">No se encontraron items</div>
          )}
        </div>
      )}
    </div>
  );
}
