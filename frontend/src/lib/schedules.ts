import { fmtDate, fmtMileage, type Schedule } from './api';

// Shared by the Schedules page and the vehicle details page.

// General guidelines only. Users should check their owner's manual.
export const SERVICE_PRESETS: Record<string, { miles: number | null; months: number | null }> = {
  'Oil Change': { miles: 5000, months: 6 },
  'Tire Rotation': { miles: 6000, months: 6 },
  'Engine Air Filter': { miles: 15000, months: 12 },
  'Cabin Air Filter': { miles: 15000, months: 12 },
  'Brake Inspection': { miles: 12000, months: 12 },
  'Coolant Flush': { miles: 30000, months: 24 },
  'Transmission Fluid': { miles: 30000, months: 24 }
};

export function toInterval(value: number | string | null | undefined): number | null {
  return value === null || value === undefined || String(value) === '' ? null : Number(value);
}

export function describeInterval(schedule: Schedule): string {
  const parts = [];
  if (schedule.interval_miles) parts.push(fmtMileage(schedule.interval_miles));
  if (schedule.interval_months) {
    parts.push(`${schedule.interval_months} ${schedule.interval_months === 1 ? 'month' : 'months'}`);
  }
  return `Every ${parts.join(' or ')}`;
}

export function describeDue(schedule: Schedule): string {
  const parts = [];
  if (schedule.next_due_mileage != null) parts.push(fmtMileage(schedule.next_due_mileage));
  if (schedule.next_due_date) parts.push(fmtDate(schedule.next_due_date));
  return parts.join(' or ');
}

export function describeBaseline(schedule: Schedule): string {
  const when = `${fmtDate(schedule.last_service_date)} at ${fmtMileage(schedule.last_service_mileage)}`;
  return schedule.last_service_from_record
    ? `Last done ${when}`
    : `Counting from ${when} (no matching service logged yet)`;
}
