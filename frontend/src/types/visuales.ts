export type EstadoConfiabilidad =
  | 'muy_solido'
  | 'solido'
  | 'debil'
  | 'muy_debil';

export interface CapituloRatioResponse {
  capitulo: string;
  descripcion?: string | null;
  minimo?: number | null;
  percentil_25?: number | null;
  mediana?: number | null;
  percentil_75?: number | null;
  maximo?: number | null;
  desviacion_std?: number | null;
  cantidad_datos: number;
  estado_confiabilidad: EstadoConfiabilidad;
  building_type?: string | null;
}

export interface ItemPresupuesto {
  capitulo: string;
  valor_unitario: number;
  cantidad: number;
  unidad: string;
}

export interface PresupuestoAnalisis {
  items: ItemPresupuesto[];
  area_total: number;
  building_type?: string | null;
}

export interface ComparativaCapitulo {
  capitulo: string;
  descripcion?: string | null;
  valor_mio: number;
  valor_ratio: number;
  desviacion_pct: number;
  impacto_monetario: number;
  estado_confiabilidad: EstadoConfiabilidad;
  ratio_encontrado: boolean;
}

export interface ResumenComparativa {
  total_presupuesto: number;
  total_ratio: number;
  diferencia_pct: number;
  diferencia_monetaria: number;
  area_total: number;
  confiabilidad_global: EstadoConfiabilidad;
}

export interface ComparativaResponse {
  capitulos: ComparativaCapitulo[];
  capitulos_sin_ratio: string[];
  resumen: ResumenComparativa;
}
