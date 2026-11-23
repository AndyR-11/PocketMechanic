<script lang="ts">
  import { page } from '$app/state';
  import { Bell, X } from '@lucide/svelte';
  import { apiRequest, type DashboardReminder } from './api';
  import { describeReminderDue, reminderLabel } from './reminders';

  const DISMISS_KEY = 'pm-reminders-popup-dismissed';

  let reminders = $state<DashboardReminder[]>([]);
  let open = $state(false);
  let loaded = $state(false);
  let request = 0;
  let autoShown = false;
  let seenPath = '';
  let dialog = $state<HTMLDivElement | null>(null);

  let path = $derived(page.url.pathname);
  let overdue = $derived(reminders.filter((item) => item.status === 'OVERDUE').length);
  let upcoming = $derived(reminders.length - overdue);
  let preview = $derived(reminders.slice(0, 6));

  function dismissed() {
    try {
      return sessionStorage.getItem(DISMISS_KEY) === '1';
    } catch {
      return false;
    }
  }

  function dismiss() {
    try {
      sessionStorage.setItem(DISMISS_KEY, '1');
    } catch {
      // Private browsing can block sessionStorage. Closing still works.
    }
    open = false;
  }

  async function refresh() {
    const id = ++request;
    let next: DashboardReminder[] = [];
    try {
      next = await apiRequest<DashboardReminder[]>('/reminders');
    } catch {
      next = [];
    }
    if (id !== request) return;
    reminders = next;
    loaded = true;
    // The dashboard is the only page that opens this on its own.
    // Opening it over Schedules would cover that form.
    if (!autoShown && !dismissed() && path === '/' && next.length > 0) {
      autoShown = true;
      open = true;
    }
  }

  $effect(() => {
    const current = path;
    if (current === '/login' || current === '/register') {
      reminders = [];
      loaded = false;
      open = false;
      seenPath = current;
      return;
    }
    if (seenPath && seenPath !== current) open = false;
    seenPath = current;
    void refresh();
  });

  $effect(() => {
    if (open) dialog?.focus();
  });
</script>

<svelte:window onkeydown={(event) => { if (open && event.key === 'Escape') dismiss(); }} />

<button
  class="bell"
  type="button"
  aria-haspopup="dialog"
  aria-expanded={open}
  aria-label={loaded && reminders.length > 0
    ? `Service reminders, ${reminders.length} need attention`
    : 'Service reminders'}
  onclick={() => open = true}
>
  <Bell size={20} />
  {#if loaded && reminders.length > 0}
    <span class="count" class:upcoming={overdue === 0}>{reminders.length}</span>
  {/if}
</button>

{#if open}
  <div
    class="overlay"
    role="presentation"
    onclick={(event) => { if (event.target === event.currentTarget) dismiss(); }}
  >
    <div
      class="dialog"
      role="dialog"
      aria-modal="true"
      aria-labelledby="reminder-popup-title"
      tabindex="-1"
      bind:this={dialog}
    >
      <div class="dialog-heading">
        <div>
          <h2 id="reminder-popup-title">Service reminders</h2>
          <p>
            {#if reminders.length === 0}
              Nothing is due soon.
            {:else}
              {overdue} overdue · {upcoming} due soon
            {/if}
          </p>
        </div>
        <button class="icon-button" type="button" aria-label="Close reminders" onclick={dismiss}>
          <X size={22} />
        </button>
      </div>

      {#if reminders.length === 0}
        <p class="empty">Schedules that are overdue, or due within 500 miles or 30 days, show up here.</p>
      {:else}
        <ul>
          {#each preview as reminder (reminder.schedule_id)}
            <li>
              <strong>{reminder.service_type}</strong>
              <span class="badge" class:overdue={reminder.status === 'OVERDUE'}>{reminderLabel(reminder.status)}</span>
              <span>{reminder.vehicle_name}</span>
              <span>Due {describeReminderDue(reminder)}</span>
            </li>
          {/each}
        </ul>
        {#if reminders.length > preview.length}
          <p class="more">Showing {preview.length} of {reminders.length}.</p>
        {/if}
      {/if}

      <div class="actions">
        <button class="secondary" type="button" onclick={dismiss}>Dismiss</button>
        <a class="primary" href="/reminders" onclick={dismiss}>View reminders</a>
      </div>
    </div>
  </div>
{/if}

<style>
  .bell {
    position: relative;
    width: 42px;
    height: 42px;
    border: 0;
    border-radius: 50%;
    background: #eaf1ff;
    color: #3478f6;
    display: grid;
    place-items: center;
  }

  .count {
    position: absolute;
    top: -4px;
    right: -4px;
    min-width: 18px;
    height: 18px;
    padding: 0 4px;
    border-radius: 999px;
    background: #d83e49;
    color: white;
    font-size: 11px;
    font-weight: 800;
    display: grid;
    place-items: center;
  }

  .count.upcoming {
    background: #d97706;
  }

  .overlay {
    position: fixed;
    inset: 0;
    background: #101a2c99;
    display: grid;
    place-items: center;
    padding: 20px;
    z-index: 40;
  }

  .dialog {
    width: min(100%, 520px);
    max-height: min(90vh, 640px);
    overflow: auto;
    background: white;
    border-radius: 18px;
    padding: 28px;
  }

  .dialog-heading {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 12px;
    margin-bottom: 8px;
  }

  h2 {
    font-size: 24px;
    margin-bottom: 6px;
  }

  .dialog-heading p,
  .empty,
  .more,
  li span {
    color: #8794a8;
    font-size: 15px;
  }

  .icon-button {
    border: 0;
    background: #f2f5fa;
    color: #59677d;
    border-radius: 9px;
    padding: 8px;
    display: grid;
    place-items: center;
  }

  ul {
    list-style: none;
    margin: 12px 0 0;
    padding: 0;
  }

  li {
    padding: 14px 0;
    border-top: 1px solid #edf1f7;
  }

  li strong {
    font-size: 16px;
  }

  li span {
    display: block;
    margin-top: 4px;
  }

  .badge {
    display: inline-block;
    width: auto;
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

  .actions {
    display: flex;
    justify-content: flex-end;
    gap: 12px;
    margin-top: 18px;
  }

  .primary,
  .secondary {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    padding: 12px 16px;
    border: 0;
    border-radius: 11px;
    font-size: 15px;
    font-weight: 700;
  }

  .primary {
    background: #3478f6;
    color: white;
  }

  .secondary {
    background: #edf1f8;
    color: #24324a;
  }
</style>