<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { Wrench, Plus, Pencil, Trash2, X, ArrowRight } from '@lucide/svelte';
  import { apiRequest, todayIso, fmtDate, fmtMileage, type Vehicle, type Maintenance } from '../../lib/api';

  type Entry = Maintenance & { vehicle: Vehicle };
  let entries = $state<Entry[]>([]);
  let vehicles = $state<Vehicle[]>([]);
  let loading = $state(true);
  let saving = $state(false);
  let error = $state('');
  let selectedVehicle = $state('all');
  let showForm = $state(false);
  let editingId = $state<number | null>(null);
  let formVehicleId = $state('');
  let serviceType = $state('');
  let serviceDate = $state(todayIso());
  let mileage = $state(0);
  let cost = $state<number | undefined>(undefined);
  let notes = $state('');
  let filtered = $derived(selectedVehicle === 'all' ? entries : entries.filter(e => String(e.vehicle_id) === selectedVehicle));

  async function load() {
    try {
      vehicles = await apiRequest<Vehicle[]>('/vehicles');
      const lists = await Promise.all(vehicles.map(async vehicle => {
        const records = await apiRequest<Maintenance[]>(`/vehicles/${vehicle.id}/maintenance`);
        return records.map(record => ({ ...record, vehicle }));
      }));
      entries = lists.flat().sort((a,b) => b.service_date.localeCompare(a.service_date));
      error = '';
    } catch (err) {
      if (err instanceof Error && /401|not authenticated|unauthorized/i.test(err.message)) await goto('/login');
      else error = err instanceof Error ? err.message : 'Could not load maintenance';
    } finally { loading = false; }
  }
  onMount(() => { void load(); });
  function openAdd() {
    editingId = null;
    formVehicleId = selectedVehicle !== 'all' ? selectedVehicle : String(vehicles[0]?.id ?? '');
    serviceType = ''; serviceDate = todayIso();
    mileage = vehicles.find(v => String(v.id) === formVehicleId)?.mileage ?? 0;
    cost = undefined; notes = ''; error = ''; showForm = true;
  }
  function openEdit(entry: Entry) {
    editingId = entry.id; formVehicleId = String(entry.vehicle_id);
    serviceType = entry.service_type; serviceDate = entry.service_date;
    mileage = entry.mileage; cost = entry.cost == null ? undefined : Number(entry.cost);
    notes = entry.notes ?? ''; error = ''; showForm = true;
  }
  function changeVehicle(value: string) {
    formVehicleId = value;
    if (editingId === null) mileage = vehicles.find(v => String(v.id) === value)?.mileage ?? 0;
  }
  async function saveRecord(event: SubmitEvent) {
    event.preventDefault(); if (!formVehicleId) return;
    saving = true; error = '';
    try {
      const payload = {
        service_type: serviceType.trim(),
        service_date: serviceDate,
        mileage: Number(mileage),
        cost: cost == null || Number.isNaN(cost)
          ? null
          : Number(cost),
        notes: notes.trim() || null
      };
      await apiRequest(editingId === null ? `/vehicles/${formVehicleId}/maintenance` : `/maintenance/${editingId}`, {
        method: editingId === null ? 'POST' : 'PUT', body: JSON.stringify(payload)
      });
      showForm = false; await load();
    } catch (err) { error = err instanceof Error ? err.message : 'Could not save maintenance'; }
    finally { saving = false; }
  }
  async function deleteRecord(entry: Entry) {
    if (!confirm(`Delete the ${entry.service_type} record for ${entry.vehicle.make} ${entry.vehicle.model}?`)) return;
    try { await apiRequest(`/maintenance/${entry.id}`, { method: 'DELETE' }); await load(); }
    catch (err) { error = err instanceof Error ? err.message : 'Could not delete maintenance'; }
  }
</script>
<svelte:head><title>Maintenance | PocketMechanic</title></svelte:head>
<div class="heading"><div><div class="eyebrow">SERVICE HISTORY</div><h1>Maintenance</h1><p>Track services and expenses across your vehicles.</p></div><button class="primary" onclick={openAdd} disabled={vehicles.length === 0}><Plus size={20}/> Log Maintenance</button></div>
{#if error && !showForm}<div class="alert" role="alert">{error}</div>{/if}
<div class="panel"><div class="toolbar"><h2>Service Records <span>({filtered.length})</span></h2><label>Filter by vehicle <select bind:value={selectedVehicle}><option value="all">All Vehicles</option>{#each vehicles as vehicle}<option value={String(vehicle.id)}>{vehicle.year} {vehicle.make} {vehicle.model}</option>{/each}</select></label></div>
{#if loading}<p class="muted">Loading maintenance...</p>
{:else if vehicles.length === 0}<div class="empty"><Wrench size={48} color="#3478f6"/><h3>Add a vehicle first</h3><p>You'll be able to log maintenance after adding a vehicle.</p><a class="primary" href="/vehicles">Add Vehicle</a></div>
{:else if filtered.length === 0}<div class="empty"><Wrench size={48} color="#3478f6"/><h3>No maintenance records found</h3><p>Log your first service right here.</p><button class="primary" onclick={openAdd}>Log Maintenance</button></div>
{:else}<div class="records">{#each filtered as entry (entry.id)}<article class="record"><div class="record-icon"><Wrench size={24}/></div><div class="record-body"><h3>{entry.service_type}</h3><p>{entry.vehicle.year} {entry.vehicle.make} {entry.vehicle.model}</p>{#if entry.notes}<p class="notes">{entry.notes}</p>{/if}</div><div class="record-meta"><strong>{fmtDate(entry.service_date)}</strong><span>{fmtMileage(entry.mileage)}</span>{#if entry.cost != null}<strong class="cost">${Number(entry.cost).toFixed(2)}</strong>{/if}</div><div class="record-actions"><button class="icon-button" title="Edit" aria-label="Edit maintenance" onclick={() => openEdit(entry)}><Pencil size={19}/></button><button class="icon-button danger" title="Delete" aria-label="Delete maintenance" onclick={() => deleteRecord(entry)}><Trash2 size={19}/></button><a class="details" href={`/vehicles/${entry.vehicle_id}`} aria-label="View vehicle details"><ArrowRight size={21}/></a></div></article>{/each}</div>{/if}
</div>
{#if showForm}
  <div class="overlay" role="presentation" onclick={(e) => { if (e.target === e.currentTarget) showForm = false; }}>
    <div class="dialog" role="dialog" aria-modal="true" aria-label="Maintenance form" tabindex="-1">
      <div class="dialog-heading"><h2>{editingId === null ? 'Log Maintenance' : 'Edit Maintenance'}</h2><button class="icon-button" aria-label="Close" onclick={() => showForm = false}><X size={22}/></button></div>
      <form onsubmit={saveRecord}>
        <label>Vehicle<select value={formVehicleId} onchange={(e) => changeVehicle(e.currentTarget.value)} disabled={editingId !== null} required>{#each vehicles as vehicle}<option value={String(vehicle.id)}>{vehicle.year} {vehicle.make} {vehicle.model}</option>{/each}</select></label>
        <label>Service Type<input bind:value={serviceType} maxlength="100" placeholder="Oil Change" required/></label>
        <div class="two-col"><label>Service Date<input type="date" bind:value={serviceDate} max={todayIso()} required/></label><label>Mileage<input type="number" min="0" bind:value={mileage} required/></label></div>
        <label>Cost in USD (optional)<input type="number" min="0" step="0.01" bind:value={cost} placeholder="79.99" /></label>
        <label>Notes (optional)<textarea bind:value={notes} rows="3" placeholder="Additional details..."></textarea></label>
        {#if error}<p class="alert" role="alert">{error}</p>{/if}
        <div class="form-actions"><button type="button" class="secondary" onclick={() => showForm = false}>Cancel</button><button class="primary" type="submit" disabled={saving}>{saving ? 'Saving...' : 'Save Maintenance'}</button></div>
      </form>
    </div>
  </div>
{/if}
<style>
.heading{display:flex;justify-content:space-between;align-items:center;gap:20px;margin-bottom:30px}.eyebrow{font-size:13px;letter-spacing:1.5px;color:#3478f6;font-weight:800;margin-bottom:10px}h1{font-size:33px;margin-bottom:9px}.heading p,.muted{color:#8794a8;font-size:16px}.primary,.secondary{display:inline-flex;align-items:center;justify-content:center;gap:9px;padding:14px 20px;border:0;border-radius:11px;font-size:16px;font-weight:700;cursor:pointer}.primary{background:#3478f6;color:white}.primary:disabled{opacity:.5;cursor:not-allowed}.secondary{background:#edf1f8;color:#24324a}.panel{background:white;border:1px solid #e8edf5;border-radius:17px;padding:28px}.toolbar{display:flex;justify-content:space-between;align-items:center;gap:15px;margin-bottom:20px}.toolbar h2{font-size:23px;margin:0}.toolbar h2 span{color:#8794a8;font-size:17px}.toolbar label{font-size:15px;font-weight:700;display:flex;align-items:center;gap:10px}select,input,textarea{border:1px solid #dfe5ef;border-radius:10px;padding:12px;font:inherit;font-size:16px;background:white;color:#17233b}.record{display:flex;align-items:center;gap:17px;padding:22px 0;border-top:1px solid #edf1f7}.record-icon{width:50px;height:50px;border-radius:13px;display:grid;place-items:center;background:#eaf1ff;color:#3478f6;flex-shrink:0}.record-body{flex:1;min-width:0}.record-body h3{font-size:19px;margin-bottom:7px}.record-body p,.record-meta span{font-size:15px;color:#8794a8;margin:0}.record-body .notes{margin-top:9px;color:#475569;white-space:pre-wrap}.record-meta{display:flex;flex-direction:column;gap:7px;text-align:right;font-size:15px}.record-meta .cost{color:#17233b}.record-actions{display:flex;align-items:center;gap:6px}.icon-button{border:0;background:#f2f5fa;color:#59677d;border-radius:9px;padding:10px;display:grid;place-items:center;cursor:pointer}.danger{color:#d83e49}.details{color:#3478f6;padding:8px}.empty{text-align:center;padding:75px 12px}.empty h3{font-size:22px;margin:17px 0 8px}.empty p{color:#8794a8;font-size:16px;margin-bottom:24px}.alert{color:#b91c1c;background:#fff1f2;border-radius:10px;padding:13px;margin-bottom:18px;font-size:15px}.overlay{position:fixed;inset:0;background:#101a2c99;display:grid;place-items:center;padding:20px;z-index:30}.dialog{width:min(100%,650px);background:white;border-radius:18px;padding:32px;max-height:90vh;overflow-y:auto}.dialog-heading{display:flex;justify-content:space-between;align-items:center;margin-bottom:20px}.dialog-heading h2{font-size:25px;margin:0}.dialog form label{display:block;font-size:15px;font-weight:700;margin-bottom:18px}.dialog form input,.dialog form select,.dialog form textarea{display:block;width:100%;margin-top:9px;padding:15px}.two-col{display:grid;grid-template-columns:1fr 1fr;gap:16px}.form-actions{display:flex;justify-content:flex-end;gap:12px;margin-top:12px}@media(max-width:650px){.heading,.toolbar{align-items:flex-start;flex-direction:column}.record{flex-wrap:wrap}.record-meta{text-align:left}.dialog{padding:22px}.two-col{grid-template-columns:1fr}}
</style>