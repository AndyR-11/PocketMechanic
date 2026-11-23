import { fmtDate, fmtMileage, type DashboardReminder } from './api';

export function describeReminderDue(reminder: DashboardReminder): string {
  const parts = [];
  if (reminder.due_mileage != null) parts.push(fmtMileage(reminder.due_mileage));
  if (reminder.due_date) parts.push(fmtDate(reminder.due_date));
  return parts.join(' or ');
}

export function reminderLabel(status: DashboardReminder['status']): string {
  return status === 'OVERDUE' ? 'Overdue' : 'Due soon';
}