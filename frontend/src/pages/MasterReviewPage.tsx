import { useEffect, useState } from 'react';

import {
  approveMasterImport,
  getMasterImportDetail,
  getMasterStatus,
  getPendingMasterImports,
  rejectMasterImport,
} from '@/api/master';
import type { MasterImportRecord, MasterStatusResponse } from '@/types/master';

type ActionMode = 'approve' | 'reject' | null;

const formatDate = (value?: string | null) => {
  if (!value) {
    return 'Sin fecha';
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleString('es-ES', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
};

const statusTone = (status: string) => {
  switch (status) {
    case 'success':
    case 'APPROVED':
      return 'bg-[#E8F5E9] text-[#1B5E20] border-[#A5D6A7]';
    case 'partial':
    case 'PENDING_REVIEW':
      return 'bg-[#FFF8E1] text-[#8D6E63] border-[#E6D5AE]';
    case 'error':
    case 'REJECTED':
      return 'bg-[#FDECEC] text-[#8B1E1E] border-[#F2B8B5]';
    default:
      return 'bg-[#F5F1EA] text-accent border-[#E0D5C7]';
  }
};

const MasterReviewPage = () => {
  const [status, setStatus] = useState<MasterStatusResponse | null>(null);
  const [imports, setImports] = useState<MasterImportRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeImportId, setActiveImportId] = useState<number | null>(null);
  const [actionMode, setActionMode] = useState<ActionMode>(null);
  const [reviewedBy, setReviewedBy] = useState('');
  const [notes, setNotes] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [detailLoadingId, setDetailLoadingId] = useState<number | null>(null);
  const [detailsById, setDetailsById] = useState<Record<number, MasterImportRecord>>({});
  const [flashMessage, setFlashMessage] = useState<string | null>(null);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [statusPayload, pendingPayload] = await Promise.all([
        getMasterStatus(),
        getPendingMasterImports(),
      ]);
      setStatus(statusPayload);
      setImports(pendingPayload);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : 'Error al cargar revision master');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadData();
  }, []);

  const resetActionForm = () => {
    setActionMode(null);
    setActiveImportId(null);
    setReviewedBy('');
    setNotes('');
  };

  const handleViewDetail = async (importId: number) => {
    if (detailsById[importId]) {
      setActiveImportId(importId);
      setActionMode(null);
      return;
    }

    setDetailLoadingId(importId);
    setFlashMessage(null);
    try {
      const detail = await getMasterImportDetail(importId);
      setDetailsById((current) => ({ ...current, [importId]: detail }));
      setActiveImportId(importId);
      setActionMode(null);
    } catch (detailError) {
      setFlashMessage(
        detailError instanceof Error ? detailError.message : 'No se pudo cargar el detalle',
      );
    } finally {
      setDetailLoadingId(null);
    }
  };

  const openAction = (importId: number, mode: ActionMode) => {
    setActiveImportId(importId);
    setActionMode(mode);
    setReviewedBy('');
    setNotes('');
    setFlashMessage(null);
  };

  const submitAction = async () => {
    if (!activeImportId || !actionMode) {
      return;
    }
    if (!reviewedBy.trim()) {
      setFlashMessage('Debes indicar quien revisa la importacion.');
      return;
    }
    if (actionMode === 'reject' && !notes.trim()) {
      setFlashMessage('Debes indicar un motivo al rechazar la importacion.');
      return;
    }

    setSubmitting(true);
    setFlashMessage(null);
    try {
      if (actionMode === 'approve') {
        await approveMasterImport(activeImportId, {
          reviewed_by: reviewedBy.trim(),
          notes: notes.trim() || undefined,
        });
        setFlashMessage('Importacion aprobada. Se han recalculado los ratios oficiales.');
      } else {
        await rejectMasterImport(activeImportId, {
          reviewed_by: reviewedBy.trim(),
          notes: notes.trim(),
        });
        setFlashMessage('Importacion rechazada. Queda fuera del master oficial.');
      }

      resetActionForm();
      await loadData();
    } catch (submitError) {
      setFlashMessage(
        submitError instanceof Error ? submitError.message : 'No se pudo completar la accion',
      );
    } finally {
      setSubmitting(false);
    }
  };

  const selectedDetail = activeImportId ? detailsById[activeImportId] : null;

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <div className="space-y-2">
        <h1 className="text-3xl font-serif text-primary">Revision master</h1>
        <p className="max-w-3xl text-sm text-accent">
          Revisa importaciones pendientes antes de alimentar el master oficial.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <div className="rounded-lg border border-[#E0D5C7] bg-white p-4">
          <p className="text-sm font-semibold text-primary">Aprobacion canonica</p>
          <p className="mt-2 text-sm text-accent">
            Aprobar una importacion recalcula ratios oficiales y actualiza
            {' '}
            <strong>LUV_RATIOS_MASTER.xlsx</strong>.
          </p>
        </div>
        <div className="rounded-lg border border-[#E0D5C7] bg-white p-4">
          <p className="text-sm font-semibold text-primary">Exclusion controlada</p>
          <p className="mt-2 text-sm text-accent">
            Rechazar una importacion la excluye del master oficial.
          </p>
        </div>
      </div>

      {status && (
        <div className="rounded-lg border border-[#E0D5C7] bg-[#F7F2EA] p-4 text-sm text-accent">
          <p className="font-medium text-primary">{status.phase}</p>
          <p className="mt-1">{status.message}</p>
        </div>
      )}

      {flashMessage && (
        <div className="rounded-lg border border-[#E0D5C7] bg-white px-4 py-3 text-sm text-primary">
          {flashMessage}
        </div>
      )}

      {error && (
        <div className="rounded-lg border border-[#D32F2F] bg-[#FDECEC] px-4 py-3 text-sm text-[#8B1E1E]">
          {error}
        </div>
      )}

      <div className="rounded-lg border border-[#E0D5C7] bg-white">
        <div className="border-b border-[#EEE4D8] px-5 py-4">
          <h2 className="text-lg font-semibold text-primary">Importaciones pendientes</h2>
          <p className="mt-1 text-sm text-accent">
            {loading ? 'Cargando pendientes...' : `${imports.length} pendientes de revision`}
          </p>
        </div>

        {loading ? (
          <div className="px-5 py-8 text-sm text-accent">Cargando importaciones pendientes...</div>
        ) : imports.length === 0 ? (
          <div className="px-5 py-8 text-sm text-accent">
            No hay importaciones pendientes de revision.
          </div>
        ) : (
          <div className="divide-y divide-[#EEE4D8]">
            {imports.map((record) => (
              <div key={record.id} className="space-y-4 px-5 py-4">
                <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                  <div className="space-y-2">
                    <div className="flex flex-wrap items-center gap-2">
                      <h3 className="text-base font-semibold text-primary">{record.filename}</h3>
                      <span
                        className={`rounded-full border px-2.5 py-1 text-xs font-medium ${statusTone(
                          record.status,
                        )}`}
                      >
                        tecnico: {record.status}
                      </span>
                      <span
                        className={`rounded-full border px-2.5 py-1 text-xs font-medium ${statusTone(
                          record.approval_status,
                        )}`}
                      >
                        {record.approval_status}
                      </span>
                    </div>
                    <div className="grid gap-1 text-sm text-accent sm:grid-cols-2">
                      <p>Fecha: {formatDate(record.import_date)}</p>
                      <p>Items: {record.items_count ?? 'N/D'}</p>
                      <p>Tipo: {record.building_type || 'sin_especificar'}</p>
                      <p>ID: {record.id}</p>
                    </div>
                  </div>

                  <div className="flex flex-wrap gap-2">
                    <button
                      className="rounded-lg border border-[#D4C7B8] px-3 py-2 text-sm text-primary transition-colors hover:bg-[#F6F1E8]"
                      type="button"
                      onClick={() => void handleViewDetail(record.id)}
                    >
                      {detailLoadingId === record.id ? 'Cargando...' : 'Ver detalle'}
                    </button>
                    <button
                      className="rounded-lg bg-[#2D5016] px-3 py-2 text-sm font-medium text-white transition-opacity hover:opacity-90"
                      type="button"
                      onClick={() => openAction(record.id, 'approve')}
                    >
                      Aprobar
                    </button>
                    <button
                      className="rounded-lg bg-[#8B1E1E] px-3 py-2 text-sm font-medium text-white transition-opacity hover:opacity-90"
                      type="button"
                      onClick={() => openAction(record.id, 'reject')}
                    >
                      Rechazar
                    </button>
                  </div>
                </div>

                {selectedDetail && activeImportId === record.id && actionMode === null && (
                  <div className="rounded-lg border border-[#EEE4D8] bg-[#FAF7F2] p-4 text-sm text-accent">
                    <p><strong className="text-primary">Hash:</strong> {selectedDetail.file_hash}</p>
                    <p><strong className="text-primary">Reviewed by:</strong> {selectedDetail.reviewed_by || 'sin revisar'}</p>
                    <p><strong className="text-primary">Review notes:</strong> {selectedDetail.review_notes || 'sin notas'}</p>
                  </div>
                )}

                {activeImportId === record.id && actionMode && (
                  <div className="rounded-lg border border-[#EEE4D8] bg-[#FAF7F2] p-4">
                    <div className="space-y-4">
                      <div>
                        <p className="text-sm font-semibold text-primary">
                          {actionMode === 'approve' ? 'Aprobar importacion' : 'Rechazar importacion'}
                        </p>
                        <p className="mt-1 text-sm text-accent">
                          {actionMode === 'approve'
                            ? 'La aprobacion dispara el recalculo oficial approved-only.'
                            : 'El rechazo requiere una nota y deja esta importacion fuera del master oficial.'}
                        </p>
                      </div>

                      <label className="block text-sm font-medium text-primary">
                        Revisado por
                        <input
                          className="mt-2 w-full rounded-lg border border-[#D4C7B8] px-3 py-2 text-sm"
                          value={reviewedBy}
                          onChange={(event) => setReviewedBy(event.target.value)}
                          placeholder="Nombre o iniciales"
                        />
                      </label>

                      <label className="block text-sm font-medium text-primary">
                        Notas {actionMode === 'reject' ? '(obligatorio)' : '(opcional)'}
                        <textarea
                          className="mt-2 min-h-24 w-full rounded-lg border border-[#D4C7B8] px-3 py-2 text-sm"
                          value={notes}
                          onChange={(event) => setNotes(event.target.value)}
                          placeholder={
                            actionMode === 'reject'
                              ? 'Explica por que se rechaza esta importacion'
                              : 'Observaciones de aprobacion'
                          }
                        />
                      </label>

                      <div className="flex flex-wrap gap-2">
                        <button
                          className={`rounded-lg px-3 py-2 text-sm font-medium text-white ${
                            actionMode === 'approve' ? 'bg-[#2D5016]' : 'bg-[#8B1E1E]'
                          }`}
                          type="button"
                          onClick={() => void submitAction()}
                          disabled={submitting}
                        >
                          {submitting
                            ? 'Guardando...'
                            : actionMode === 'approve'
                              ? 'Confirmar aprobacion'
                              : 'Confirmar rechazo'}
                        </button>
                        <button
                          className="rounded-lg border border-[#D4C7B8] px-3 py-2 text-sm text-primary"
                          type="button"
                          onClick={resetActionForm}
                          disabled={submitting}
                        >
                          Cancelar
                        </button>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default MasterReviewPage;
