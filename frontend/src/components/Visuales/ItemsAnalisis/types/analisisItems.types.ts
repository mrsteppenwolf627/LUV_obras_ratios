// Input
export interface ItemParaAnalisis {
  descripcion: string;
  precio_unitario: number;
  cantidad?: number;
  unidad?: string;
}

// Output
export interface ItemAnalisisResultado {
  descripcion: string;
  categoria: string; // MEDIUM|PREMIUM|LUXURY|LUXURY_PLUS
  precio_usuario: number;
  ratio_historico: number | null;
  desviacion_pct: number | null;
  confianza: string; // MUY_DÉBIL|DÉBIL|SÓLIDO|MUY_SÓLIDO
  impacto_monetario: number | null;
  ratio_encontrado: boolean;
}

export interface ResumenPorCategoria {
  categoria: string;
  cantidad_items: number;
  precio_total_usuario: number;
  ratio_total_historico: number;
  desviacion_pct_promedio: number;
  confianza_global: string;
  items_sin_ratio: number;
}

export interface AnalisisItemsResponse {
  items: ItemAnalisisResultado[];
  resumenes_por_categoria: Record<string, ResumenPorCategoria>;
  resumen_general: {
    total_usuario: number;
    total_ratio: number;
    diferencia_pct: number;
    items_con_ratio: number;
    items_sin_ratio: number;
  };
}
