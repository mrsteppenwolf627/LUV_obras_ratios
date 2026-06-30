export interface MasterStatusResponse {
  phase: string;
  approval_flow_enabled: boolean;
  message: string;
}

export interface MasterImportRecord {
  id: number;
  filename: string;
  file_hash: string;
  status: string;
  approval_status: string;
  building_type?: string | null;
  import_date?: string | null;
  items_count?: number | null;
  reviewed_by?: string | null;
  reviewed_at?: string | null;
  review_notes?: string | null;
}

export interface MasterApproveRejectBody {
  reviewed_by: string;
  notes?: string;
}
