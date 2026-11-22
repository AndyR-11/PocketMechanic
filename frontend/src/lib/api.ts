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

export type Expense = {
  id: number;
  vehicle_id: number;
  amount: string | number;
  category: string;
  date: string;
  notes: string | null;
  created_at: string;
  source_maintenance_id: number | null;
};

export type Schedule = {
  id: number;
  vehicle_id: number;
  service_type: string;
  interval_miles: number | null;
  interval_months: number | null;
  start_date: string;
  start_mileage: number;
  created_at: string;
  last_service_date: string;
  last_service_mileage: number;
  last_service_from_record: boolean;
  next_due_mileage: number | null;
  next_due_date: string | null;
};

export type ScheduleWithVehicle = Schedule & {
  vehicle: { id: number; year: number; make: string; model: string; mileage: number };
};

export type CostSummary = {
  total: string | number;
  count: number;
  by_category: { category: string; total: string | number; count: number }[];
  by_month: { month: string; total: string | number }[];
};

export type DashboardReminder = {
  schedule_id: number;
  vehicle_id: number;
  vehicle_name: string;
  service_type: string;
  status: 'OVERDUE' | 'UPCOMING';
  due_mileage: number | null;
  due_date: string | null;
};

export type DashboardSummary = {
  vehicles: { id: number; year: number; make: string; model: string; mileage: number }[];
  vehicle_count: number;
  maintenance_count: number;
  recent_maintenance: {
    id: number;
    vehicle_id: number;
    vehicle_make: string;
    vehicle_model: string;
    service_type: string;
    service_date: string;
  }[];
  total_expenses: string | number;
  schedule_count: number;
  reminders_available: boolean;
  reminders: DashboardReminder[];
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
