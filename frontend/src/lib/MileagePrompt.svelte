<script lang="ts">
  import { untrack } from 'svelte';
  import { Gauge, X } from '@lucide/svelte';
  import { apiRequest, fmtMileage, type Vehicle } from './api';

  // Shown after login so users can keep each vehicle's mileage current.
  // Uses the existing vehicle update (Contract 7), which rejects lower mileage.
  let { vehicles, ondone }: { vehicles: Vehicle[]; ondone: () => void } = $props();

  type Mode = 'driven' | 'total';
  type Entry = { mode: Mode; value: number | null; error: string };

  // The vehicle list is fixed while the popup is open.
  let entries = $state<Record<number, Entry>>(
    untrack(() => Object.fromEntries(
      vehicles.map((v) => [v.id, { mode: 'driven' as Mode, value: null, error: '' }])
    ))
  );
  let saving = $state(false);

  function newMileage(vehicle: Vehicle): number | null {
    const entry = entries[vehicle.id];
    if (entry.value === null || entry.value === undefined || String(entry.value) === '') return null;
    const value = Number(entry.value);
    return entry.mode === 'driven' ? vehicle.mileage + value : value;
  }

  function check(vehicle: Vehicle): boolean {
    const entry = entries[vehicle.id];
    entry.error = '';
    const value = Number(entry.value);
    if (entry.value === null || String(entry.value) === '') return true;
    if (!Number.isInteger(value) || value < 0) {
      entry.error = 'Enter a whole number of miles.';
    } else if (entry.mode === 'total' && value < vehicle.mileage) {
      entry.error = `Total miles cannot be lower than ${fmtMileage(vehicle.mileage)}.`;
    }
    return entry.error === '';
  }

  async function save(event: SubmitEvent) {
    event.preventDefault();
    if (!vehicles.map(check).every(Boolean)) return;

    saving = true;
    let failed = false;
    for (const vehicle of vehicles) {
      const mileage = newMileage(vehicle);
      if (mileage === null || mileage === vehicle.mileage) continue;
      try {
        await apiRequest(`/vehicles/${vehicle.id}`, {
          method: 'PUT',
          body: JSON.stringify({ mileage })
        });
      } catch (err) {
        entries[vehicle.id].error = err instanceof Error ? err.message : 'Could not update mileage';
        failed = true;
      }
    }
    saving = false;
    if (!failed) ondone();
  }
</script>

<div class="overlay" role="presentation">
  <div class="dialog" role="dialog" aria-modal="true" aria-label="Update mileage" tabindex="-1">
    <div class="dialog-heading">
      <div class="title">
        <div class="icon"><Gauge size={24} /></div>
        <div>
          <h2>Update your mileage</h2>
          <p>Keeping mileage current helps your schedules show when service is due.</p>
        </div>
      </div>
      <button class="icon-button" type="button" aria-label="Skip" onclick={ondone}><X size={22} /></button>
    </div>

    <form onsubmit={save}>
      {#each vehicles as vehicle (vehicle.id)}
        {@const entry = entries[vehicle.id]}
        {@const preview = newMileage(vehicle)}
        <fieldset>
          <legend>{vehicle.year} {vehicle.make} {vehicle.model}</legend>
          <p class="current">Current: {fmtMileage(vehicle.mileage)}</p>
          <div class="modes">
            <button type="button" class:active={entry.mode === 'driven'}
              onclick={() => { entry.mode = 'driven'; entry.error = ''; }}>Miles driven since last time</button>
            <button type="button" class:active={entry.mode === 'total'}
              onclick={() => { entry.mode = 'total'; entry.error = ''; }}>New total (odometer)</button>
          </div>
          <input
            type="number"
            min={entry.mode === 'total' ? vehicle.mileage : 0}
            step="1"
            bind:value={entry.value}
            placeholder={entry.mode === 'driven' ? 'e.g. 350' : String(vehicle.mileage)}
            aria-label={`${entry.mode === 'driven' ? 'Miles driven' : 'Total miles'} for ${vehicle.make} ${vehicle.model}`}
          />
          {#if entry.error}
            <p class="error" role="alert">{entry.error}</p>
          {:else if preview !== null && preview !== vehicle.mileage}
            <p class="preview">New mileage: {fmtMileage(preview)}</p>
          {/if}
        </fieldset>
      {/each}

      <p class="hint">Leave a vehicle blank to keep its current mileage.</p>
      <div class="form-actions">
        <button type="button" class="secondary" onclick={ondone}>Skip for now</button>
        <button type="submit" class="primary" disabled={saving}>{saving ? 'Saving...' : 'Save Mileage'}</button>
      </div>
    </form>
  </div>
</div>

<style>
  .overlay { position: fixed; inset: 0; background: #101a2c99; display: grid; place-items: center; padding: 20px; z-index: 50; }
  .dialog { width: min(100%, 620px); background: #fff; border-radius: 18px; padding: 30px; max-height: 90vh; overflow-y: auto; text-align: left; }
  .dialog-heading { display: flex; justify-content: space-between; align-items: flex-start; gap: 16px; margin-bottom: 18px; }
  .title { display: flex; gap: 14px; align-items: flex-start; }
  .icon { width: 46px; height: 46px; flex-shrink: 0; display: grid; place-items: center; background: #eaf1ff; color: #3478f6; border-radius: 12px; }
  h2 { font-size: 23px; margin: 0 0 6px; }
  .title p, .current, .hint { color: #8794a8; font-size: 15px; margin: 0; }
  fieldset { border: 1px solid #e8edf5; border-radius: 14px; padding: 16px 18px; margin: 0 0 14px; }
  legend { font-weight: 700; font-size: 16px; padding: 0 6px; }
  .current { margin-bottom: 12px; }
  .modes { display: flex; gap: 8px; margin-bottom: 10px; flex-wrap: wrap; }
  .modes button { border: 1px solid #dfe5ef; background: #fff; color: #475569; border-radius: 9px; padding: 8px 12px; font-size: 14px; font-weight: 600; cursor: pointer; }
  .modes button.active { background: #eaf1ff; border-color: #3478f6; color: #1d4ed8; }
  input { display: block; width: 100%; padding: 13px 14px; border: 1px solid #dfe5ef; border-radius: 10px; font-size: 16px; color: #17233b; font-family: inherit; box-sizing: border-box; }
  input:focus { outline: 2px solid #3478f6; border-color: transparent; }
  .preview { color: #067647; font-size: 14px; margin: 8px 0 0; }
  .error { color: #b91c1c; font-size: 14px; margin: 8px 0 0; }
  .hint { margin: 4px 0 18px; }
  .form-actions { display: flex; justify-content: flex-end; gap: 12px; }
  .primary, .secondary { padding: 13px 20px; border: 0; border-radius: 11px; font-size: 16px; font-weight: 700; cursor: pointer; width: auto; margin: 0; }
  .primary { background: #3478f6; color: #fff; }
  .primary:disabled { opacity: 0.6; }
  .secondary { background: #edf1f8; color: #24324a; }
  .icon-button { border: 0; background: #f2f5fa; color: #59677d; border-radius: 9px; padding: 9px; display: grid; place-items: center; cursor: pointer; width: auto; margin: 0; }
  @media (max-width: 560px) { .dialog { padding: 22px; } .form-actions { flex-direction: column-reverse; } }
</style>
