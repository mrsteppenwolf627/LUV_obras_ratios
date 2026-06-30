import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, test, vi } from 'vitest';

import MasterReviewPage from '@/pages/MasterReviewPage';

const statusPayload = {
  phase: 'FASE_MASTER',
  approval_flow_enabled: true,
  message: 'Flujo de aprobacion activo.',
};

const makeImport = (id: number, filename: string) => ({
  id,
  filename,
  file_hash: `hash-${id}`,
  status: 'success',
  approval_status: 'PENDING_REVIEW',
  building_type: 'residencial',
  import_date: '2026-06-30T10:00:00Z',
  items_count: 12,
  reviewed_by: null,
  reviewed_at: null,
  review_notes: null,
});

describe('MasterReviewPage', () => {
  const fetchMock = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    vi.stubGlobal('fetch', fetchMock);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  test('renderiza la lista de importaciones pendientes', async () => {
    const pendingImports = [makeImport(1, 'presupuesto_a.xlsx'), makeImport(2, 'presupuesto_b.xlsx')];

    fetchMock.mockImplementation(async (input: RequestInfo | URL) => {
      const url = String(input);

      if (url.includes('/api/master/status')) {
        return okJson(statusPayload);
      }
      if (url.includes('/api/master/imports/pending')) {
        return okJson(pendingImports);
      }

      return notFound();
    });

    render(<MasterReviewPage />);

    await waitFor(() => {
      expect(screen.getByText(/presupuesto_a.xlsx/i)).toBeInTheDocument();
    });

    expect(screen.getByText(/presupuesto_b.xlsx/i)).toBeInTheDocument();
    expect(screen.getByText(/2 pendientes de revision/i)).toBeInTheDocument();
  });

  test('aprueba una importacion y refresca la lista', async () => {
    const user = userEvent.setup();
    let pendingImports = [makeImport(1, 'presupuesto_a.xlsx')];

    fetchMock.mockImplementation(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);

      if (url.includes('/api/master/status')) {
        return okJson(statusPayload);
      }
      if (url.includes('/api/master/imports/pending')) {
        return okJson(pendingImports);
      }
      if (url.includes('/api/master/imports/1/approve')) {
        expect(init?.method).toBe('POST');
        expect(init?.body).toBe(
          JSON.stringify({ reviewed_by: 'Aitor', notes: 'Validado para master' }),
        );
        pendingImports = [];
        return okJson({ ...makeImport(1, 'presupuesto_a.xlsx'), approval_status: 'APPROVED' });
      }

      return notFound();
    });

    render(<MasterReviewPage />);

    await waitFor(() => {
      expect(screen.getByText(/presupuesto_a.xlsx/i)).toBeInTheDocument();
    });

    await user.click(screen.getByRole('button', { name: /Aprobar/i }));
    await user.type(screen.getByPlaceholderText(/Nombre o iniciales/i), 'Aitor');
    await user.type(screen.getByPlaceholderText(/Observaciones de aprobacion/i), 'Validado para master');
    await user.click(screen.getByRole('button', { name: /Confirmar aprobacion/i }));

    await waitFor(() => {
      expect(screen.getByText(/Importacion aprobada/i)).toBeInTheDocument();
    });

    await waitFor(() => {
      expect(screen.getByText(/No hay importaciones pendientes de revision/i)).toBeInTheDocument();
    });
  });

  test('exige notes al rechazar', async () => {
    const user = userEvent.setup();
    const pendingImports = [makeImport(1, 'presupuesto_a.xlsx')];

    fetchMock.mockImplementation(async (input: RequestInfo | URL) => {
      const url = String(input);

      if (url.includes('/api/master/status')) {
        return okJson(statusPayload);
      }
      if (url.includes('/api/master/imports/pending')) {
        return okJson(pendingImports);
      }
      if (url.includes('/api/master/imports/1/reject')) {
        throw new Error('No deberia llamarse reject sin notes');
      }

      return notFound();
    });

    render(<MasterReviewPage />);

    await waitFor(() => {
      expect(screen.getByText(/presupuesto_a.xlsx/i)).toBeInTheDocument();
    });

    await user.click(screen.getByRole('button', { name: /Rechazar/i }));
    await user.type(screen.getByPlaceholderText(/Nombre o iniciales/i), 'Aitor');
    await user.click(screen.getByRole('button', { name: /Confirmar rechazo/i }));

    await waitFor(() => {
      expect(
        screen.getByText(/Debes indicar un motivo al rechazar la importacion/i),
      ).toBeInTheDocument();
    });
  });

  test('refresca la lista tras rechazar una importacion', async () => {
    const user = userEvent.setup();
    let pendingImports = [makeImport(1, 'presupuesto_a.xlsx')];

    fetchMock.mockImplementation(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);

      if (url.includes('/api/master/status')) {
        return okJson(statusPayload);
      }
      if (url.includes('/api/master/imports/pending')) {
        return okJson(pendingImports);
      }
      if (url.includes('/api/master/imports/1/reject')) {
        expect(init?.method).toBe('POST');
        expect(init?.body).toBe(
          JSON.stringify({ reviewed_by: 'Aitor', notes: 'Faltan datos de origen' }),
        );
        pendingImports = [];
        return okJson({ ...makeImport(1, 'presupuesto_a.xlsx'), approval_status: 'REJECTED' });
      }

      return notFound();
    });

    render(<MasterReviewPage />);

    await waitFor(() => {
      expect(screen.getByText(/presupuesto_a.xlsx/i)).toBeInTheDocument();
    });

    await user.click(screen.getByRole('button', { name: /Rechazar/i }));
    await user.type(screen.getByPlaceholderText(/Nombre o iniciales/i), 'Aitor');
    await user.type(
      screen.getByPlaceholderText(/Explica por que se rechaza esta importacion/i),
      'Faltan datos de origen',
    );
    await user.click(screen.getByRole('button', { name: /Confirmar rechazo/i }));

    await waitFor(() => {
      expect(screen.getByText(/Importacion rechazada/i)).toBeInTheDocument();
    });

    await waitFor(() => {
      expect(screen.getByText(/No hay importaciones pendientes de revision/i)).toBeInTheDocument();
    });
  });
});

const okJson = (payload: unknown) =>
  ({
    ok: true,
    status: 200,
    statusText: 'OK',
    headers: {
      get: (name: string) => (name === 'content-type' ? 'application/json' : null),
    },
    text: async () => JSON.stringify(payload),
  }) as unknown as Response;

const notFound = () =>
  ({
    ok: false,
    status: 404,
    statusText: 'Not Found',
    headers: {
      get: () => 'application/json',
    },
    text: async () => JSON.stringify({ detail: 'Not Found' }),
  }) as unknown as Response;
