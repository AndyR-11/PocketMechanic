<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { CalendarClock, Plus, Pencil, Trash2, X, ArrowRight } from '@lucide/svelte';
  import { apiRequest, fmtMileage, type Vehicle, type ScheduleWithVehicle } from '../../lib/api';
  import { SERVICE_PRESETS, toInterval, describeInterval, describeDue, describeBaseline } from '../../lib/schedules';

  // Maintenance schedules for all of the user's vehicles (Contracts 19-23).
  let schedules = $state<ScheduleWithVehicle[]>([]);
  let vehicles = $state<Vehicle[]>([]);
  let loading = $state(true);
  let saving = $state(false);
  let error = $state('');
  let formError = $state('');
  let selectedVehicle = $state('all');
  let showForm = $state(false);
  let editingId = $state<number | null>(null);
  let formVehicleId = $state('');
  let serviceType = $state('');
  let intervalMiles = $state<number | null>(null);
  let intervalMonths = $state<number | null>(null);
  let filtered = $derived(selectedVehicle === 'all' ? schedules : schedules.filter(s => String(s.vehicle_id) === selectedVehicle));

  async function load() {
    try {
      [vehicles, schedules] = await Promise.all([
        apiRequest<Vehicle[]>('/vehicles'),
        apiRequest<ScheduleWithVehicle[]>('/schedules')
      ]);
      error = '';
    } catch (err) {
      if (err instanceof Error && /401|not authenticated|unauthorized/i.test(err.message)) await goto('/login');
      else error = err instanceof Error ? err.message : 'Could not load schedules';
    } finally { loading = false; }
  }
  onMount(() => { void load(); });

  function openAdd() {
    editingId = null;
    formVehicleId = selectedVehicle !== 'all' ? selectedVehicle : String(vehicles[0]?.id ?? '');
    serviceType = ''; intervalMiles = null; intervalMonths = null; formError = ''; showForm = true;
  }
  function openEdit(schedule: ScheduleWithVehicle) {
    editingId = schedule.id; formVehicleId = String(schedule.vehicle_id);
    serviceType = schedule.service_type; intervalMiles = schedule.interval_miles; intervalMonths = schedule.interval_months;
    formError = ''; showForm = true;
  }
  // Fill in suggested intervals when a common service is picked.
  function applyPreset() {
    const preset = SERVICE_PRESETS[serviceType.trim()];
    if (preset && editingId === null && intervalMiles == null && intervalMonths == null) {
      intervalMiles = preset.miles; intervalMonths = preset.months;
    }
  }
  async function saveSchedule(event: SubmitEvent) {
    event.preventDefault(); formError = '';
    const miles = toInterval(intervalMiles), months = toInterval(intervalMonths);
    if (!formVehicleId) return;
    if (miles === null && months === null) { formError = 'Enter a mileage interval, a time interval, or both.'; return; }
    saving = true;
    try {
      const intervals = { interval_miles: miles, interval_months: months };
      await apiRequest(editingId === null ? `/vehicles/${formVehicleId}/schedules` : `/schedules/${editingId}`, {
        method: editingId === null ? 'POST' : 'PUT',
        body: JSON.stringify(editingId === null ? { service_type: serviceType.trim(), ...intervals } : intervals)
      });
      showForm = false; await load();
    } catch (err) { formError = err instanceof Error ? err.message : 'Could not save schedule'; }
    finally { saving = false; }
  }
  async function deleteSchedule(schedule: ScheduleWithVehicle) {
    if (!confirm(`Delete the ${schedule.service_type} schedule for ${schedule.vehicle.make} ${schedule.vehicle.model}?`)) return;
    try { await apiRequest(`/schedules/${schedule.id}`, { method: 'DELETE' }); await load(); }
    catch (err) { error = err instanceof Error ? err.message : 'Could not delete schedule'; }
  }
  import ManualFinder from '../../lib/ManualFinder.svelte';
</script>
<svelte:head><title>Schedules | PocketMechanic</title></svelte:head>
<div class="heading"><div><div class="eyebrow">MAINTENANCE PLANNING</div><h1>Schedules</h1><p>Set how often each service is due. Logging a matching service restarts its schedule.</p></div><button class="primary" onclick={openAdd} disabled={vehicles.length === 0}><Plus size={20}/> Add Schedule</button></div>
{#if error}<div class="alert" role="alert">{error}</div>{/if}
<div class="panel"><div class="toolbar"><h2>Maintenance Schedules <span>({filtered.length})</span></h2><label>Filter by vehicle <select bind:value={selectedVehicle}><option value="all">All Vehicles</option>{#each vehicles as vehicle (vehicle.id)}<option value={String(vehicle.id)}>{vehicle.year} {vehicle.make} {vehicle.model}</option>{/each}</select></label></div>
{#if loading}<p class="muted">Loading schedules...</p>
{:else if vehicles.length === 0}<div class="empty"><CalendarClock size={48} color="#3478f6"/><h3>Add a vehicle first</h3><p>You'll be able to schedule maintenance after adding a vehicle.</p><a class="primary" href="/vehicles">Add Vehicle</a></div>
{:else if filtered.length === 0}<div class="empty"><CalendarClock size={48} color="#3478f6"/><h3>No schedules yet</h3><p>Add a schedule to see when each service is due next.</p><button class="primary" onclick={openAdd}>Add Schedule</button></div>
{:else}<div class="records">{#each filtered as schedule (schedule.id)}<article class="record"><div class="record-icon"><CalendarClock size={24}/></div><div class="record-body"><h3>{schedule.service_type}</h3><p>{schedule.vehicle.year} {schedule.vehicle.make} {schedule.vehicle.model} · {describeInterval(schedule)}</p><p class="baseline">{describeBaseline(schedule)}</p></div><div class="record-meta"><span>Next due</span><strong>{describeDue(schedule)}</strong><span>Now at {fmtMileage(schedule.vehicle.mileage)}</span></div><div class="record-actions"><button class="icon-button" title="Edit" aria-label="Edit schedule" onclick={() => openEdit(schedule)}><Pencil size={19}/></button><button class="icon-button danger" title="Delete" aria-label="Delete schedule" onclick={() => deleteSchedule(schedule)}><Trash2 size={19}/></button><a class="details" href={`/vehicles/${schedule.vehicle_id}`} aria-label="View vehicle details"><ArrowRight size={21}/></a></div></article>{/each}</div>{/if}
</div>
<ManualFinder />
{#if showForm}
  <div class="overlay" role="presentation" onclick={(e) => { if (e.target === e.currentTarget) showForm = false; }}>
    <div class="dialog" role="dialog" aria-modal="true" aria-label="Schedule form" tabindex="-1">
      <div class="dialog-heading"><h2>{editingId === null ? 'Add Schedule' : 'Edit Schedule'}</h2><button class="icon-button" aria-label="Close" onclick={() => showForm = false}><X size={22}/></button></div>
      <form onsubmit={saveSchedule}>
        <label>Vehicle<select bind:value={formVehicleId} disabled={editingId !== null} required>{#each vehicles as vehicle (vehicle.id)}<option value={String(vehicle.id)}>{vehicle.year} {vehicle.make} {vehicle.model}</option>{/each}</select></label>
        <label>Service Type<input bind:value={serviceType} onchange={applyPreset} list="schedule-presets" maxlength="100" placeholder="Oil Change" required disabled={editingId !== null}/></label>
        <datalist id="schedule-presets">{#each Object.keys(SERVICE_PRESETS) as name (name)}<option value={name}></option>{/each}</datalist>
        <div class="two-col"><label>Every (miles)<input type="number" min="1" max="100000" bind:value={intervalMiles} placeholder="5000"/></label><label>Every (months)<input type="number" min="1" max="120" bind:value={intervalMonths} placeholder="6"/></label></div>
        <p class="hint">Fill in one or both. Suggested intervals are general guidelines, so check your owner's manual.</p>
        {#if formError}<p class="alert" role="alert">{formError}</p>{/if}
        <div class="form-actions"><button type="button" class="secondary" onclick={() => showForm = false}>Cancel</button><button class="primary" type="submit" disabled={saving}>{saving ? 'Saving...' : 'Save Schedule'}</button></div>
      </form>
    </div>
  </div>
{/if}
<style>
.heading{display:flex;justify-content:space-between;align-items:center;gap:20px;margin-bottom:30px}.eyebrow{font-size:13px;letter-spacing:1.5px;color:#3478f6;font-weight:800;margin-bottom:10px}h1{font-size:33px;margin-bottom:9px}.heading p,.muted{color:#8794a8;font-size:16px}.primary,.secondary{display:inline-flex;align-items:center;justify-content:center;gap:9px;padding:14px 20px;border:0;border-radius:11px;font-size:16px;font-weight:700;cursor:pointer}.primary{background:#3478f6;color:white}.primary:disabled{opacity:.5;cursor:not-allowed}.secondary{background:#edf1f8;color:#24324a}.panel{background:white;border:1px solid #e8edf5;border-radius:17px;padding:28px}.toolbar{display:flex;justify-content:space-between;align-items:center;gap:15px;margin-bottom:20px}.toolbar h2{font-size:23px;margin:0}.toolbar h2 span{color:#8794a8;font-size:17px}.toolbar label{font-size:15px;font-weight:700;display:flex;align-items:center;gap:10px}select,input{border:1px solid #dfe5ef;border-radius:10px;padding:12px;font:inherit;font-size:16px;background:white;color:#17233b}input:disabled,select:disabled{background:#f2f5fa;color:#59677d}.record{display:flex;align-items:center;gap:17px;padding:22px 0;border-top:1px solid #edf1f7}.record-icon{width:50px;height:50px;border-radius:13px;display:grid;place-items:center;background:#eaf1ff;color:#3478f6;flex-shrink:0}.record-body{flex:1;min-width:0}.record-body h3{font-size:19px;margin-bottom:7px}.record-body p,.record-meta span{font-size:15px;color:#8794a8;margin:0}.record-body .baseline{font-size:14px;margin-top:5px}.record-meta{display:flex;flex-direction:column;gap:5px;text-align:right;font-size:15px}.record-actions{display:flex;align-items:center;gap:6px}.icon-button{border:0;background:#f2f5fa;color:#59677d;border-radius:9px;padding:10px;display:grid;place-items:center;cursor:pointer}.danger{color:#d83e49}.details{color:#3478f6;padding:8px}.empty{text-align:center;padding:75px 12px}.empty h3{font-size:22px;margin:17px 0 8px}.empty p{color:#8794a8;font-size:16px;margin-bottom:24px}.alert{color:#b91c1c;background:#fff1f2;border-radius:10px;padding:13px;margin-bottom:18px;font-size:15px}.overlay{position:fixed;inset:0;background:#101a2c99;display:grid;place-items:center;padding:20px;z-index:30}.dialog{width:min(100%,650px);background:white;border-radius:18px;padding:32px;max-height:90vh;overflow-y:auto}.dialog-heading{display:flex;justify-content:space-between;align-items:center;margin-bottom:20px}.dialog-heading h2{font-size:25px;margin:0}.dialog form label{display:block;font-size:15px;font-weight:700;margin-bottom:18px}.dialog form input,.dialog form select{display:block;width:100%;margin-top:9px;padding:15px}.two-col{display:grid;grid-template-columns:1fr 1fr;gap:16px}.hint{color:#8794a8;font-size:14px;margin:-6px 0 16px}.form-actions{display:flex;justify-content:flex-end;gap:12px;margin-top:12px}@media(max-width:650px){.heading,.toolbar{align-items:flex-start;flex-direction:column}.record{flex-wrap:wrap}.record-meta{text-align:left}.dialog{padding:22px}.two-col{grid-template-columns:1fr}}
</style>
