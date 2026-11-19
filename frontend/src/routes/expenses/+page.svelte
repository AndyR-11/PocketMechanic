
<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { Wallet, Plus, Pencil, Trash2, X, Wrench } from '@lucide/svelte';
  import { apiRequest, fmtDate, todayIso, type CostSummary } from '../../lib/api';
  import './expenses.css';

  type ExpenseVehicle = {
    id: number;
    year: number;
    make: string;
    model: string;
  };

  type ExpenseEntry = {
    id: number;
    vehicle_id: number;
    amount: string | number;
    category: string;
    date: string;
    notes: string | null;
    source: 'manual' | 'maintenance';
    maintenance_id: number | null;
    vehicle: ExpenseVehicle;
  };

  type ExpenseOverview = {
    vehicles: ExpenseVehicle[];
    items: ExpenseEntry[];
    total: string | number;
    count: number;
  };

  let overview = $state<ExpenseOverview>({
    vehicles: [],
    items: [],
    total: '0.00',
    count: 0
  });

  let loading = $state(true);
  let saving = $state(false);
  let error = $state('');
  let formError = $state('');

  let selectedVehicle = $state('all');
  let showForm = $state(false);
  let editingId = $state<number | null>(null);

  let formVehicleId = $state('');
  let category = $state('');
  let amount = $state<number | undefined>(undefined);
  let expenseDate = $state(todayIso());
  let notes = $state('');

  let requestNumber = 0;

  // Cost analysis (Contract 25)
  let summary = $state<CostSummary | null>(null);
  let summaryError = $state('');

  let largestCategory = $derived(
    Math.max(1, ...(summary?.by_category ?? []).map(g => Number(g.total)))
  );
  let largestMonth = $derived(
    Math.max(1, ...(summary?.by_month ?? []).map(g => Number(g.total)))
  );

  function monthLabel(month: string): string {
    const [year, number] = month.split('-').map(Number);
    return new Date(year, number - 1, 1).toLocaleDateString('en-US', {
      month: 'short',
      year: 'numeric'
    });
  }

  async function loadSummary(currentRequest: number) {
    try {
      const query = selectedVehicle === 'all'
        ? ''
        : `?vehicle_id=${selectedVehicle}`;

      const result = await apiRequest<CostSummary>(
        `/expenses/summary${query}`
      );

      if (currentRequest !== requestNumber) return;

      summary = result;
      summaryError = '';
    } catch (err) {
      if (currentRequest !== requestNumber) return;

      summaryError = err instanceof Error
        ? err.message
        : 'Could not load cost analysis';
    }
  }

  function money(value: string | number): string {
    return Number(value).toLocaleString('en-US', {
      style: 'currency',
      currency: 'USD'
    });
  }

  async function loadExpenses() {
    const currentRequest = ++requestNumber;
    loading = true;

    try {
      const query = selectedVehicle === 'all'
        ? ''
        : `?vehicle_id=${selectedVehicle}`;

      const [result] = await Promise.all([
        apiRequest<ExpenseOverview>(`/expenses${query}`),
        loadSummary(currentRequest)
      ]);

      if (currentRequest !== requestNumber) return;

      overview = result;
      error = '';
    } catch (err) {
      if (currentRequest !== requestNumber) return;

      if (
        err instanceof Error &&
        /401|not authenticated|unauthorized/i.test(err.message)
      ) {
        await goto('/login');
      } else {
        error = err instanceof Error
          ? err.message
          : 'Could not load expenses';
      }
    } finally {
      if (currentRequest === requestNumber) {
        loading = false;
      }
    }
  }

  onMount(() => {
    void loadExpenses();
  });

  function changeVehicle(event: Event) {
    selectedVehicle = (event.currentTarget as HTMLSelectElement).value;
    void loadExpenses();
  }

  function openAdd() {
    editingId = null;
    formVehicleId = selectedVehicle !== 'all'
      ? selectedVehicle
      : String(overview.vehicles[0]?.id ?? '');

    category = '';
    amount = undefined;
    expenseDate = todayIso();
    notes = '';
    formError = '';
    showForm = true;
  }

  function openEdit(entry: ExpenseEntry) {
    if (entry.source !== 'manual') return;

    editingId = entry.id;
    formVehicleId = String(entry.vehicle_id);
    category = entry.category;
    amount = Number(entry.amount);
    expenseDate = entry.date;
    notes = entry.notes ?? '';
    formError = '';
    showForm = true;
  }

  async function saveExpense(event: SubmitEvent) {
    event.preventDefault();

    if (
      !formVehicleId ||
      amount === undefined ||
      !Number.isFinite(amount) ||
      amount < 0
    ) {
      formError = 'Enter a valid amount and select a vehicle.';
      return;
    }

    saving = true;
    formError = '';

    try {
      const payload = {
        category: category.trim(),
        amount: amount.toFixed(2),
        date: expenseDate,
        notes: notes.trim() || null
      };

      const endpoint = editingId === null
        ? `/vehicles/${formVehicleId}/expenses`
        : `/expenses/${editingId}`;

      await apiRequest(endpoint, {
        method: editingId === null ? 'POST' : 'PUT',
        body: JSON.stringify(payload)
      });

      showForm = false;
      await loadExpenses();
    } catch (err) {
      formError = err instanceof Error
        ? err.message
        : 'Could not save expense';
    } finally {
      saving = false;
    }
  }

  async function deleteExpense(entry: ExpenseEntry) {
    if (entry.source !== 'manual') return;

    if (!confirm(`Delete the ${entry.category} expense?`)) {
      return;
    }

    try {
      await apiRequest(`/expenses/${entry.id}`, {
        method: 'DELETE'
      });

      await loadExpenses();
    } catch (err) {
      error = err instanceof Error
        ? err.message
        : 'Could not delete expense';
    }
  }
</script>

<svelte:head>
  <title>Expenses | PocketMechanic</title>
</svelte:head>

<div class="expenses-page">
  <div class="heading">
    <div>
      <div class="eyebrow">VEHICLE COSTS</div>
      <h1>Expense Management</h1>
      <p>Track expenses and maintenance costs for your vehicles.</p>
    </div>

    <button
      class="primary"
      onclick={openAdd}
      disabled={loading || overview.vehicles.length === 0}
    >
      <Plus size={20} />
      Add Expense
    </button>
  </div>

  {#if error}
    <div class="alert" role="alert">{error}</div>
  {/if}

  <section class="summary">
    <div class="summary-icon">
      <Wallet size={30} />
    </div>
    <div>
      <span>Total tracked expenses</span>
      <strong>{money(overview.total)}</strong>
    </div>
    <small>
      {overview.count}
      {overview.count === 1 ? 'record' : 'records'}
    </small>
  </section>

  {#if summary && summary.count > 0}
    <section class="panel analysis">
      <div class="toolbar">
        <h2>Cost Analysis</h2>
        <span class="muted">
          {selectedVehicle === 'all' ? 'All vehicles' : 'Selected vehicle'}
        </span>
      </div>
      {#if summaryError}
        <p class="alert" role="alert">{summaryError}</p>
      {/if}
      <div class="analysis-grid">
        <div>
          <h3>By Category</h3>
          {#each summary.by_category as group (group.category)}
            <div class="bar-row">
              <div class="bar-label">
                <span>{group.category}</span>
                <strong>{money(group.total)}</strong>
              </div>
              <div class="bar-track">
                <div
                  class="bar-fill"
                  style:width={`${(Number(group.total) / largestCategory) * 100}%`}
                ></div>
              </div>
              <small>
                {group.count} {group.count === 1 ? 'expense' : 'expenses'}
                · {Math.round((Number(group.total) / Number(summary.total)) * 100)}% of total
              </small>
            </div>
          {/each}
        </div>
        <div>
          <h3>By Month</h3>
          {#each summary.by_month as group (group.month)}
            <div class="bar-row">
              <div class="bar-label">
                <span>{monthLabel(group.month)}</span>
                <strong>{money(group.total)}</strong>
              </div>
              <div class="bar-track">
                <div
                  class="bar-fill month"
                  style:width={`${(Number(group.total) / largestMonth) * 100}%`}
                ></div>
              </div>
            </div>
          {/each}
        </div>
      </div>
    </section>
  {/if}

  <section class="panel">
    <div class="toolbar">
      <h2>Expense Records ({overview.count})</h2>

      <label>
        Filter by vehicle
        <select
          value={selectedVehicle}
          onchange={changeVehicle}
          disabled={loading}
        >
          <option value="all">All Vehicles</option>

          {#each overview.vehicles as vehicle (vehicle.id)}
            <option value={String(vehicle.id)}>
              {vehicle.year} {vehicle.make} {vehicle.model}
            </option>
          {/each}
        </select>
      </label>
    </div>

    {#if loading}
      <p class="muted">Loading expenses...</p>

    {:else if overview.vehicles.length === 0}
      <div class="empty">
        <Wallet size={48} color="#3478f6" />
        <h3>Add a vehicle first</h3>
        <p>You need a vehicle before tracking expenses.</p>
        <a class="primary" href="/vehicles">Add Vehicle</a>
      </div>

    {:else if overview.items.length === 0}
      <div class="empty">
        <Wallet size={48} color="#3478f6" />
        <h3>No expenses found</h3>
        <p>Add an expense or log maintenance with a cost.</p>
        <button class="primary" onclick={openAdd}>
          <Plus size={20} />
          Add Expense
        </button>
      </div>

    {:else}
      <div class="records">
        {#each overview.items as entry (`${entry.source}-${entry.id}`)}
          <article class="record">
            <div class="record-icon">
              {#if entry.source === 'maintenance'}
                <Wrench size={23} />
              {:else}
                <Wallet size={23} />
              {/if}
            </div>

            <div class="record-body">
              <div class="record-title">
                <h3>{entry.category}</h3>
              </div>

              <p>
                {entry.vehicle.year}
                {entry.vehicle.make}
                {entry.vehicle.model}
              </p>

              {#if entry.notes}
                <p class="notes">{entry.notes}</p>
              {/if}
            </div>

            <div class="record-meta">
              <strong>{money(entry.amount)}</strong>
              <span>{fmtDate(entry.date)}</span>
            </div>

            <div class="record-actions">
              {#if entry.source === 'manual'}
                <button
                  class="icon-button"
                  title="Edit expense"
                  aria-label="Edit expense"
                  onclick={() => openEdit(entry)}
                >
                  <Pencil size={19} />
                </button>

                <button
                  class="icon-button danger"
                  title="Delete expense"
                  aria-label="Delete expense"
                  onclick={() => deleteExpense(entry)}
                >
                  <Trash2 size={19} />
                </button>
              {:else}
                <a
                  class="maintenance-link"
                  href="/maintenance"
                  title="Manage maintenance record"
                >
                  View Maintenance
                </a>
              {/if}
            </div>
          </article>
        {/each}
      </div>
    {/if}
  </section>

  {#if showForm}
    <div
      class="overlay"
      role="presentation"
      onclick={(event) => {
        if (event.target === event.currentTarget) {
          showForm = false;
        }
      }}
    >
      <div
        class="dialog"
        role="dialog"
        aria-modal="true"
        aria-label="Expense form"
        tabindex="-1"
      >
        <div class="dialog-heading">
          <h2>{editingId === null ? 'Add Expense' : 'Edit Expense'}</h2>
          <button
            class="icon-button"
            aria-label="Close"
            onclick={() => showForm = false}
          >
            <X size={22} />
          </button>
        </div>

        <form onsubmit={saveExpense}>
          <label>
            Vehicle
            <select
              bind:value={formVehicleId}
              disabled={editingId !== null}
              required
            >
              {#each overview.vehicles as vehicle (vehicle.id)}
                <option value={String(vehicle.id)}>
                  {vehicle.year}
                  {vehicle.make}
                  {vehicle.model}
                </option>
              {/each}
            </select>
          </label>

          <label>
            Category
            <input
              bind:value={category}
              placeholder="Fuel, Tires, Insurance..."
              maxlength="100"
              required
            />
          </label>

          <div class="two-col">
            <label>
              Amount (USD)
              <input
                type="number"
                min="0"
                max="99999999.99"
                step="0.01"
                bind:value={amount}
                required
              />
            </label>

            <label>
              Expense Date
              <input
                type="date"
                bind:value={expenseDate}
                max={todayIso()}
                required
              />
            </label>
          </div>

          <label>
            Notes (optional)
            <textarea
              bind:value={notes}
              maxlength="2000"
              rows="3"
              placeholder="Additional details..."
            ></textarea>
          </label>

          {#if formError}
            <p class="alert" role="alert">{formError}</p>
          {/if}

          <div class="form-actions">
            <button
              type="button"
              class="secondary"
              onclick={() => showForm = false}
            >
              Cancel
            </button>

            <button class="primary" type="submit" disabled={saving}>
              {saving ? 'Saving...' : 'Save Expense'}
            </button>
          </div>
        </form>
      </div>
    </div>
  {/if}
</div>
