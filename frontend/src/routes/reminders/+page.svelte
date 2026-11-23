<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { Bell, CalendarClock } from '@lucide/svelte';
  import { apiRequest, type DashboardReminder, type Vehicle } from '../../lib/api';
  import { describeReminderDue, reminderLabel } from '../../lib/reminders';

  let reminders = $state<DashboardReminder[]>([]);
  let vehicles = $state<Vehicle[]>([]);
  let loading = $state(true);
  let error = $state('');
  let filter = $state<'ALL' | 'OVERDUE' | 'UPCOMING'>('ALL');

  let overdue = $derived(reminders.filter((item) => item.status === 'OVERDUE').length);
  let upcoming = $derived(reminders.length - overdue);
  let visible = $derived(
    filter === 'ALL' ? reminders : reminders.filter((item) => item.status === filter)
  );

  function milesLeft(reminder: DashboardReminder) {
    const vehicle = vehicles.find((item) => item.id === reminder.vehicle_id);
    if (!vehicle || reminder.due_mileage == null) return null;
    return reminder.due_mileage - vehicle.mileage;
  }

  function daysLeft(reminder: DashboardReminder) {
    if (!reminder.due_date) return null;
    const due = new Date(`${reminder.due_date.slice(0, 10)}T12:00:00`);
    const today = new Date();
    today.setHours(12, 0, 0, 0);
    return Math.round((due.getTime() - today.getTime()) / 86400000);
  }

  function remaining(reminder: DashboardReminder) {
    const parts = [];
    const miles = milesLeft(reminder);
    const days = daysLeft(reminder);
    if (miles != null) {
      parts.push(miles < 0 ? `${Math.abs(miles).toLocaleString()} mi past due` : miles === 0 ? 'Due now by mileage' : `${miles.toLocaleString()} mi left`);
    }
    if (days != null) {
      parts.push(days < 0 ? `${Math.abs(days)} ${Math.abs(days) === 1 ? 'day' : 'days'} past due` : days === 0 ? 'Due today' : `${days} ${days === 1 ? 'day' : 'days'} left`);
    }
    return parts.join(' · ');
  }

  onMount(async () => {
    try {
      [vehicles, reminders] = await Promise.all([
        apiRequest<Vehicle[]>('/vehicles'),
        apiRequest<DashboardReminder[]>('/reminders')
      ]);
    } catch (err) {
      if (err instanceof Error && /401|not authenticated|unauthorized/i.test(err.message)) {
        await goto('/login', { replaceState: true });
      } else {
        error = err instanceof Error ? err.message : 'Could not load reminders';
      }
    } finally {
      loading = false;
    }
  });
</script>

<svelte:head><title>Reminders | PocketMechanic</title></svelte:head>

<div class="heading">
  <div>
    <div class="eyebrow">SERVICE REMINDERS</div>
    <h1>Reminders</h1>
    <p>Services that are overdue, or due within 500 miles or 30 days. Schedules are managed separately.</p>
  </div>
  <a class="primary" href="/schedules"><CalendarClock size={20} /> Manage schedules</a>
</div>

{#if error}
  <div class="alert" role="alert">{error}</div>
{/if}

<div class="stats">
  <div class="stat">
    <p>Overdue</p>
    <strong>{loading ? '—' : overdue}</strong>
  </div>
  <div class="stat">
    <p>Due soon</p>
    <strong>{loading ? '—' : upcoming}</strong>
  </div>
  <div class="stat">
    <p>Needs attention</p>
    <strong>{loading ? '—' : reminders.length}</strong>
  </div>
</div>

<div class="panel">
  <div class="toolbar">
    <h2>Needs attention <span>({loading ? '…' : visible.length})</span></h2>
    <div class="filters" role="group" aria-label="Filter reminders">
      <button type="button" class:active={filter === 'ALL'} aria-pressed={filter === 'ALL'} onclick={() => filter = 'ALL'}>All</button>
      <button type="button" class:active={filter === 'OVERDUE'} aria-pressed={filter === 'OVERDUE'} onclick={() => filter = 'OVERDUE'}>Overdue</button>
      <button type="button" class:active={filter === 'UPCOMING'} aria-pressed={filter === 'UPCOMING'} onclick={() => filter = 'UPCOMING'}>Due soon</button>
    </div>
  </div>

  {#if loading}
    <p class="muted">Loading reminders...</p>
  {:else if vehicles.length === 0}
    <div class="empty">
      <Bell size={48} color="#3478f6" />
      <h3>Add a vehicle first</h3>
      <p>You'll be able to see service reminders after adding a vehicle and a schedule.</p>
      <a class="primary" href="/vehicles">Add Vehicle</a>
    </div>
  {:else if reminders.length === 0}
    <div class="empty">
      <Bell size={48} color="#3478f6" />
      <h3>Nothing is due soon</h3>
      <p>When a schedule is overdue, or within 500 miles or 30 days, it shows up here.</p>
      <a class="primary" href="/schedules">Review schedules</a>
    </div>
  {:else if visible.length === 0}
    <p class="muted">No reminders in this view.</p>
  {:else}
    <div class="records">
      {#each visible as reminder (reminder.schedule_id)}
        <a class="record" href={`/vehicles/${reminder.vehicle_id}`}>
          <div class="record-icon" class:overdue={reminder.status === 'OVERDUE'}>
            <Bell size={24} />
          </div>
          <div class="record-body">
            <h3>
              {reminder.service_type}
              <span class="badge" class:overdue={reminder.status === 'OVERDUE'}>{reminderLabel(reminder.status)}</span>
            </h3>
            <p>{reminder.vehicle_name}</p>
            <p class="remaining">{remaining(reminder)}</p>
          </div>
          <div class="record-meta">
            <span>Due</span>
            <strong>{describeReminderDue(reminder)}</strong>
          </div>
        </a>
      {/each}
    </div>
  {/if}
</div>

<style>
  .heading {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 20px;
    margin-bottom: 30px;
  }

  .eyebrow {
    font-size: 13px;
    letter-spacing: 1.5px;
    color: #3478f6;
    font-weight: 800;
    margin-bottom: 10px;
  }

  h1 {
    font-size: 33px;
    margin-bottom: 9px;
  }

  .heading p,
  .muted {
    color: #8794a8;
    font-size: 16px;
  }

  .primary {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 9px;
    background: #3478f6;
    color: white;
    padding: 14px 20px;
    border-radius: 11px;
    font-size: 16px;
    font-weight: 700;
  }

  .stats {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 22px;
    margin-bottom: 28px;
  }

  .stat,
  .panel {
    background: white;
    border: 1px solid #e8edf5;
    border-radius: 17px;
    padding: 27px;
  }

  .stat p {
    font-size: 16px;
    color: #8794a8;
    margin-bottom: 8px;
  }

  .stat strong {
    font-size: 34px;
  }

  .toolbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 15px;
    margin-bottom: 8px;
  }

  .toolbar h2 {
    font-size: 23px;
    margin: 0;
  }

  .toolbar h2 span {
    color: #8794a8;
    font-size: 17px;
  }

  .filters {
    display: flex;
    gap: 8px;
  }

  .filters button {
    border: 0;
    background: #f2f5fa;
    color: #59677d;
    border-radius: 999px;
    padding: 8px 14px;
    font-weight: 700;
    font-size: 14px;
  }

  .filters button.active {
    background: #3478f6;
    color: white;
  }

  .record {
    display: flex;
    align-items: center;
    gap: 17px;
    padding: 22px 0;
    border-top: 1px solid #edf1f7;
    color: inherit;
  }

  .record-icon {
    width: 50px;
    height: 50px;
    border-radius: 13px;
    display: grid;
    place-items: center;
    background: #fff4e5;
    color: #d97706;
    flex-shrink: 0;
  }

  .record-icon.overdue {
    background: #fdecec;
    color: #d83e49;
  }

  .record-body {
    flex: 1;
    min-width: 0;
  }

  .record-body h3 {
    font-size: 19px;
    margin-bottom: 7px;
  }

  .record-body p,
  .record-meta span {
    font-size: 15px;
    color: #8794a8;
    margin: 0;
  }

  .remaining {
    margin-top: 5px;
  }

  .record-meta {
    display: flex;
    flex-direction: column;
    gap: 5px;
    text-align: right;
  }

  .record-meta strong {
    font-size: 16px;
  }

  .badge {
    display: inline-block;
    margin-left: 8px;
    padding: 2px 8px;
    border-radius: 999px;
    font-size: 11px;
    font-weight: 800;
    letter-spacing: 0.4px;
    background: #fff4e5;
    color: #b45309;
    vertical-align: middle;
  }

  .badge.overdue {
    background: #fdecec;
    color: #b91c1c;
  }

  .empty {
    text-align: center;
    padding: 75px 12px;
  }

  .empty h3 {
    font-size: 22px;
    margin: 17px 0 8px;
  }

  .empty p {
    color: #8794a8;
    font-size: 16px;
    margin-bottom: 24px;
  }

  .alert {
    color: #b91c1c;
    background: #fff1f2;
    border-radius: 10px;
    padding: 13px;
    margin-bottom: 18px;
    font-size: 15px;
  }

  @media (max-width: 800px) {
    .stats {
      grid-template-columns: 1fr;
    }

    .heading,
    .toolbar,
    .record {
      align-items: flex-start;
      flex-direction: column;
    }

    .record-meta {
      text-align: left;
    }
  }
</style>