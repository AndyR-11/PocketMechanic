<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { Wallet, Plus, Pencil, Trash2, X } from '@lucide/svelte';

  import {
    apiRequest,
    fmtDate,
    todayIso,
    type Vehicle,
    type Expense
  } from '../../lib/api';

  // An expense together with its vehicle information.
  type Entry = Expense & { vehicle: Vehicle };

  let entries = $state<Entry[]>([]);
  let vehicles = $state<Vehicle[]>([]);
  let loading = $state(true);
  let saving = $state(false);
  let error = $state('');
  let formError = $state('');

  let selectedVehicle = $state('all');
  let showForm = $state(false);
  let editingId = $state<number | null>(null);

  // Form fields
  let formVehicleId = $state('');
  let category = $state('');
  let amount = $state<number | undefined>(undefined);
  let expenseDate = $state(todayIso());
  let notes = $state('');

  // Show only expenses for the selected vehicle.
  let filtered = $derived(
    selectedVehicle === 'all'
      ? entries
      : entries.filter(
          entry => String(entry.vehicle_id) === selectedVehicle
        )
  );

  // Calculate the total amount of displayed expenses.
  let total = $derived(
    filtered.reduce(
      (sum, entry) => sum + Number(entry.amount),
      0
    )
  );

  function money(value: number): string {
    return value.toLocaleString('en-US', {
      style: 'currency',
      currency: 'USD'
    });
  }

  // READ: Load vehicles and expenses from FastAPI.
  async function load() {
    try {
      vehicles = await apiRequest<Vehicle[]>('/vehicles');

      const lists = await Promise.all(
        vehicles.map(async vehicle => {
          const records = await apiRequest<Expense[]>(
            `/vehicles/${vehicle.id}/expenses`
          );

          return records.map(record => ({
            ...record,
            vehicle
          }));
        })
      );

      entries = lists.flat().sort(
        (a, b) => b.date.localeCompare(a.date)
      );

      error = '';
    } catch (err) {
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
      loading = false;
    }
  }

  onMount(() => {
    void load();
  });

  // CREATE: Prepare an empty form.
  function openAdd() {
    editingId = null;

    formVehicleId = selectedVehicle !== 'all'
      ? selectedVehicle
      : String(vehicles[0]?.id ?? '');

    category = '';
    amount = undefined;
    expenseDate = todayIso();
    notes = '';
    formError = '';
    showForm = true;
  }

  // UPDATE: Load the selected expense into the form.
  function openEdit(entry: Entry) {
    editingId = entry.id;
    formVehicleId = String(entry.vehicle_id);
    category = entry.category;
    amount = Number(entry.amount);
    expenseDate = entry.date;
    notes = entry.notes ?? '';
    formError = '';
    showForm = true;
  }

  // Save a new or edited expense
  async function saveExpense(event: SubmitEvent) {
    event.preventDefault();

    if (
      !formVehicleId ||
      amount === undefined ||
      !Number.isFinite(amount)
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
      await load();
    } catch (err) {
      formError = err instanceof Error
        ? err.message
        : 'Could not save expense';
    } finally {
      saving = false;
    }
  }

  // DELETE: Remove an expense after user confirmation.
  async function deleteExpense(entry: Entry) {
    const confirmed = confirm(
      `Delete the ${entry.category} expense for ${entry.vehicle.make} ${entry.vehicle.model}?`
    );

    if (!confirmed) return;

    try {
      await apiRequest(`/expenses/${entry.id}`, {
        method: 'DELETE'
      });

      await load();
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

<!-- Page heading -->
<div class="heading">
  <div>
    <div class="eyebrow">VEHICLE COSTS</div>
    <h1>Expense Management</h1>
    <p>Track and manage expenses for all your vehicles.</p>
  </div>

  <button
    class="primary"
    onclick={openAdd}
    disabled={loading || vehicles.length === 0}
  >
    <Plus size={20} />
    Add Expense
  </button>
</div>

{#if error}
  <div class="alert" role="alert">{error}</div>
{/if}

<!-- Total expense summary -->
<section class="summary">
  <div class="summary-icon">
    <Wallet size={30} />
  </div>

  <div>
    <span>Total tracked expenses</span>
    <strong>{money(total)}</strong>
  </div>

  <small>
    {filtered.length}
    {filtered.length === 1 ? 'expense' : 'expenses'}
  </small>
</section>

<!-- Expense list and vehicle filter -->
<section class="panel">
  <div class="toolbar">
    <h2>Expense Records ({filtered.length})</h2>

    <label>
      Filter by vehicle

      <select bind:value={selectedVehicle}>
        <option value="all">All Vehicles</option>

        {#each vehicles as vehicle (vehicle.id)}
          <option value={String(vehicle.id)}>
            {vehicle.year} {vehicle.make} {vehicle.model}
          </option>
        {/each}
      </select>
    </label>
  </div>

  {#if loading}
    <p class="muted">Loading expenses...</p>

  {:else if vehicles.length === 0}
    <div class="empty">
      <Wallet size={48} color="#3478f6" />

      <h3>Add a vehicle first</h3>
      <p>You need a vehicle before tracking expenses.</p>

      <a class="primary" href="/vehicles">
        Add Vehicle
      </a>
    </div>

  {:else if filtered.length === 0}
    <div class="empty">
      <Wallet size={48} color="#3478f6" />

      <h3>No expenses found</h3>
      <p>Add your first expense to start tracking costs.</p>

      <button class="primary" onclick={openAdd}>
        <Plus size={20} />
        Add Expense
      </button>
    </div>

  {:else}
    <div class="records">
      {#each filtered as entry (entry.id)}
        <article class="record">
          <div class="record-icon">
            <Wallet size={24} />
          </div>

          <div class="record-body">
            <h3>{entry.category}</h3>

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
            <strong>{money(Number(entry.amount))}</strong>
            <span>{fmtDate(entry.date)}</span>
          </div>

          <div class="record-actions">
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
          </div>
        </article>
      {/each}
    </div>
  {/if}
</section>

<!-- Modal form for adding and editing expenses -->
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
        <h2>
          {editingId === null ? 'Add Expense' : 'Edit Expense'}
        </h2>

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
            {#each vehicles as vehicle (vehicle.id)}
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

          <button
            class="primary"
            type="submit"
            disabled={saving}
          >
            {saving ? 'Saving...' : 'Save Expense'}
          </button>
        </div>
      </form>
    </div>
  </div>
{/if}

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

  .heading p, .muted {
    color: #8794a8;
    font-size: 16px;
  }

  .primary, .secondary {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 9px;
    padding: 14px 20px;
    border: 0;
    border-radius: 11px;
    font-size: 16px;
    font-weight: 700;
    cursor: pointer;
    text-decoration: none;
  }

  .primary {
    background: #3478f6;
    color: white;
  }

  .primary:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .primary:hover:not(:disabled) {
    background: #2563dc;
  }

  .secondary {
    background: #edf1f8;
    color: #24324a;
  }

  .summary {
    display: flex;
    align-items: center;
    gap: 18px;
    background: white;
    border: 1px solid #e8edf5;
    border-radius: 17px;
    padding: 26px;
    margin-bottom: 24px;
  }

  .summary-icon {
    display: grid;
    place-items: center;
    background: #eaf1ff;
    color: #3478f6;
    width: 56px;
    height: 56px;
    border-radius: 14px;
    flex-shrink: 0;
  }

  .summary span {
    display: block;
    color: #8794a8;
    font-size: 15px;
  }

  .summary strong {
    display: block;
    font-size: 30px;
    margin-top: 4px;
  }

  .summary small {
    margin-left: auto;
    color: #8794a8;
  }

  .panel {
    background: white;
    border: 1px solid #e8edf5;
    border-radius: 17px;
    padding: 28px;
  }

  .toolbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 15px;
    margin-bottom: 20px;
  }

  .toolbar h2 {
    font-size: 23px;
    margin: 0;
  }

  .toolbar label {
    font-size: 15px;
    font-weight: 700;
    display: flex;
    align-items: center;
    gap: 10px;
  }

  select, input, textarea {
    border: 1px solid #dfe5ef;
    border-radius: 10px;
    padding: 12px;
    font: inherit;
    font-size: 16px;
    background: white;
    color: #17233b;
  }

  .record {
    display: flex;
    align-items: center;
    gap: 17px;
    padding: 22px 0;
    border-top: 1px solid #edf1f7;
  }

  .record-icon {
    width: 50px;
    height: 50px;
    border-radius: 13px;
    display: grid;
    place-items: center;
    background: #eaf1ff;
    color: #3478f6;
    flex-shrink: 0;
  }

  .record-body {
    flex: 1;
    min-width: 0;
  }

  .record-body h3 {
    font-size: 19px;
    margin-bottom: 7px;
  }

  .record-body p, .record-meta span {
    font-size: 15px;
    color: #8794a8;
    margin: 0;
  }

  .record-body .notes {
    margin-top: 9px;
    color: #475569;
    white-space: pre-wrap;
  }

  .record-meta {
    display: flex;
    flex-direction: column;
    gap: 7px;
    text-align: right;
    font-size: 15px;
  }

  .record-meta strong {
    font-size: 18px;
  }

  .record-actions {
    display: flex;
    gap: 6px;
  }

  .icon-button {
    border: 0;
    background: #f2f5fa;
    color: #59677d;
    border-radius: 9px;
    padding: 10px;
    display: grid;
    place-items: center;
    cursor: pointer;
  }

  .icon-button:hover {
    background: #e3eaf5;
  }

  .danger {
    color: #d83e49;
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
  }

  .overlay {
    position: fixed;
    inset: 0;
    background: #101a2c99;
    display: grid;
    place-items: center;
    padding: 20px;
    z-index: 30;
  }

  .dialog {
    width: min(100%, 650px);
    background: white;
    border-radius: 18px;
    padding: 32px;
    max-height: 90vh;
    overflow-y: auto;
  }

  .dialog-heading {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
  }

  .dialog-heading h2 {
    font-size: 25px;
    margin: 0;
  }

  .dialog form label {
    display: block;
    font-size: 15px;
    font-weight: 700;
    margin-bottom: 18px;
  }

  .dialog form input,
  .dialog form select,
  .dialog form textarea {
    display: block;
    width: 100%;
    margin-top: 9px;
    padding: 15px;
  }

  .two-col {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
  }

  .form-actions {
    display: flex;
    justify-content: flex-end;
    gap: 12px;
    margin-top: 12px;
  }

  @media (max-width: 650px) {
    .heading, .toolbar {
      align-items: flex-start;
      flex-direction: column;
    }

    .record {
      flex-wrap: wrap;
    }

    .record-meta {
      text-align: left;
    }

    .dialog {
      padding: 22px;
    }

    .two-col {
      grid-template-columns: 1fr;
    }
  }
</style>
