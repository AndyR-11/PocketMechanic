const API_URL = 'http://localhost:8000';

export type Vehicle = {
  id: number;
  user_id: number;
  make: string;
  model: string;
  year: number;
  mileage: number;
  vin: string | null;
  license_plate: string | null;
  created_at: string;
};

export type Maintenance = {
  id: number;
  vehicle_id: number;
  service_type: string;
  service_date: string;
  mileage: number;
  cost: string | number | null;
  notes: string | null;
  created_at: string;
};

export type User = {
  id: number;
  name: string;
  email: string;
};

export async function apiRequest<T = unknown>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_URL}${endpoint}`, {
    ...options,
    credentials: 'include',
    headers: { 'Content-Type': 'application/json', ...options.headers }
  });
  if (!response.ok) {
    const data = await response.json().catch(() => null);
    const detail = data?.detail;
    throw new Error(typeof detail === 'string' ? detail : Array.isArray(detail) ? detail.map((e: { msg?: string }) => e.msg).join(', ') : `Request failed (${response.status})`);
  }
  if (response.status === 204) return undefined as T;
  const text = await response.text();
  return text ? JSON.parse(text) as T : undefined as T;
}

export const todayIso = () => {
  const now = new Date();
  return new Date(now.getTime() - now.getTimezoneOffset() * 60000).toISOString().slice(0, 10);
};
export const fmtMileage = (value: number) => `${value.toLocaleString()} mi`;
export const fmtDate = (value: string) => new Date(`${value.slice(0, 10)}T12:00:00`).toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' });
