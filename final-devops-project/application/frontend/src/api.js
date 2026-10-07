// All calls are relative (/api/...). nginx in the frontend container, or the
// Kubernetes Ingress, forwards them to the FastAPI backend.

export class ApiError extends Error {
  constructor(status, message) {
    super(message);
    this.status = status;
  }
}

function describe(detail) {
  if (!detail) return null;
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((d) => `${(d.loc || []).filter((p) => p !== 'body').join('.')}: ${d.msg}`.replace(/^: /, ''))
      .join('; ');
  }
  return JSON.stringify(detail);
}

async function request(path, options = {}) {
  let response;
  try {
    response = await fetch(`/api${path}`, {
      headers: { 'Content-Type': 'application/json' },
      ...options,
    });
  } catch {
    throw new ApiError(0, 'Can’t reach the ClinicDesk API. Check that the backend is running.');
  }
  if (response.status === 204) return null;
  const body = await response.json().catch(() => null);
  if (!response.ok) {
    throw new ApiError(response.status, describe(body?.detail) || `Request failed with HTTP ${response.status}`);
  }
  return body;
}

const qs = (params) => {
  const s = new URLSearchParams(Object.entries(params).filter(([, v]) => v !== undefined && v !== null && v !== ''));
  const str = s.toString();
  return str ? `?${str}` : '';
};

export const api = {
  doctors: () => request('/doctors'),
  patients: (q) => request(`/patients${qs({ q })}`),
  appointments: (on) => request(`/appointments${qs({ on })}`),
  stats: (on) => request(`/stats${qs({ on })}`),
  book: (payload) => request('/appointments', { method: 'POST', body: JSON.stringify(payload) }),
  update: (id, payload) => request(`/appointments/${id}`, { method: 'PUT', body: JSON.stringify(payload) }),
  cancel: (id) => request(`/appointments/${id}/cancel`, { method: 'POST' }),
};
