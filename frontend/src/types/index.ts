export interface Ratio {
  chapter_code: string;
  chapter_description: string;
  building_type: string;
  median_ratio: number;
  min_ratio: number;
  max_ratio: number;
  count_budgets: number;
  validation_status: 'VALID' | 'DUBIOUS';
}

export interface MasterResponse {
  metadata: {
    total_budgets: number;
    total_ratios: number;
    last_import: string;
  };
  ratios: Ratio[];
}

export interface ArchivedBudget {
  budget_id: number;
  filename: string;
  import_date: string;
  total_amount: number;
  chapter_count: number;
  file_hash: string;
}

export interface ArchivedResponse {
  archived: ArchivedBudget[];
}

export interface ImportResponse {
  message: string;
  budget_id: number;
  file_hash: string;
}

export interface StatsResponse {
  top_chapters: {
    chapter_code: string;
    total_amount: number;
  }[];
  ratio_distribution: {
    range: string;
    count: number;
  }[];
  temporal_evolution?: {
    date: string;
    avg_ratio: number;
  }[];
}
