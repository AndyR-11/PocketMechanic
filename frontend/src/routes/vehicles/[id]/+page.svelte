<script lang="ts">
  import { onMount } from 'svelte';
  import { page } from '$app/state';
  import { goto } from '$app/navigation';
  import { ArrowLeft, CarFront, Wrench, Plus, Pencil, Trash2, X, CalendarClock } from '@lucide/svelte';
  import { apiRequest, todayIso, fmtDate, fmtMileage, type Vehicle, type Maintenance, type Schedule } from '../../../lib/api';
  import { SERVICE_PRESETS, toInterval, describeInterval, describeDue, describeBaseline } from '../../../lib/schedules';

  let vehicle = $state<Vehicle | null>(null);
  let records = $state<Maintenance[]>([]);
  let loading = $state(true);
  let saving = $state(false);
  let error = $state('');
  let showForm = $state(false);
  let editingId = $state<number | null>(null);
  let serviceType = $state('');
  let serviceDate = $state(todayIso());
  let mileage = $state(0);
  let notes = $state('');
  let cost = $state('');
  const vehicleId = $derived(Number(page.params.id));

  // Maintenance schedules (Contracts 19-23)
  let schedules = $state<Schedule[]>([]);
  let showScheduleForm = $state(false);
  let editingScheduleId = $state<number | null>(null);
  let scheduleService = $state('');
  let intervalMiles = $state<number | null>(null);
  let intervalMonths = $state<number | null>(null);
  let scheduleError = $state('');

  async function load() {
    try {
      const [v, r, s] = await Promise.all([
        apiRequest<Vehicle>(`/vehicles/${vehicleId}`),
        apiRequest<Maintenance[]>(`/vehicles/${vehicleId}/maintenance`),
        apiRequest<Schedule[]>(`/vehicles/${vehicleId}/schedules`)
      ]);
      vehicle = v; records = r.sort((a,b) => b.service_date.localeCompare(a.service_date)); schedules = s; error = '';
    } catch (err) {
      if (err instanceof Error && /401|not authenticated|unauthorized/i.test(err.message)) await goto('/login');
      else error = err instanceof Error ? err.message : 'Could not load vehicle details';
    } finally { loading = false; }
  }
  onMount(() => { void load(); });

  function openAdd() {
    editingId = null; serviceType = ''; serviceDate = todayIso();
    mileage = vehicle?.mileage ?? 0; notes = ''; cost = ''; error = ''; showForm = true;
  }
  function openEdit(record: Maintenance) {
    editingId = record.id; serviceType = record.service_type; serviceDate = record.service_date;
    mileage = record.mileage; notes = record.notes ?? ''; cost = record.cost == null ? '' : String(record.cost); error = ''; showForm = true;
  }
  async function saveRecord(event: SubmitEvent) {
    event.preventDefault(); saving = true; error = '';
    try {
      const payload = { service_type: serviceType.trim(), service_date: serviceDate, mileage: Number(mileage), notes: notes.trim() || null, cost: String(cost ?? '').trim() || null };
      await apiRequest(editingId === null ? `/vehicles/${vehicleId}/maintenance` : `/maintenance/${editingId}`, {
        method: editingId === null ? 'POST' : 'PUT', body: JSON.stringify(payload)
      });
      showForm = false; await load();
    } catch (err) { error = err instanceof Error ? err.message : 'Could not save maintenance'; }
    finally { saving = false; }
  }
  function openAddSchedule() {
    editingScheduleId = null; scheduleService = ''; intervalMiles = null; intervalMonths = null;
    scheduleError = ''; showScheduleForm = true;
  }
  function openEditSchedule(schedule: Schedule) {
    editingScheduleId = schedule.id; scheduleService = schedule.service_type;
    intervalMiles = schedule.interval_miles; intervalMonths = schedule.interval_months;
    scheduleError = ''; showScheduleForm = true;
  }
  // Fill in suggested intervals when a common service is picked.
  function applyPreset() {
    const preset = SERVICE_PRESETS[scheduleService.trim()];
    if (preset && editingScheduleId === null && intervalMiles == null && intervalMonths == null) {
      intervalMiles = preset.miles; intervalMonths = preset.months;
    }
  }
  async function saveSchedule(event: SubmitEvent) {
    event.preventDefault(); scheduleError = '';
    const miles = toInterval(intervalMiles), months = toInterval(intervalMonths);
    if (miles === null && months === null) { scheduleError = 'Enter a mileage interval, a time interval, or both.'; return; }
    saving = true;
    try {
      const intervals = { interval_miles: miles, interval_months: months };
      await apiRequest(editingScheduleId === null ? `/vehicles/${vehicleId}/schedules` : `/schedules/${editingScheduleId}`, {
        method: editingScheduleId === null ? 'POST' : 'PUT',
        body: JSON.stringify(editingScheduleId === null ? { service_type: scheduleService.trim(), ...intervals } : intervals)
      });
      showScheduleForm = false; await load();
    } catch (err) { scheduleError = err instanceof Error ? err.message : 'Could not save schedule'; }
    finally { saving = false; }
  }
  async function deleteSchedule(schedule: Schedule) {
    if (!confirm(`Delete the ${schedule.service_type} schedule?`)) return;
    try { await apiRequest(`/schedules/${schedule.id}`, { method: 'DELETE' }); await load(); }
    catch (err) { error = err instanceof Error ? err.message : 'Could not delete schedule'; }
  }
  async function deleteRecord(record: Maintenance) {
    if (!confirm(`Delete the ${record.service_type} record from ${fmtDate(record.service_date)}?`)) return;
    try { await apiRequest(`/maintenance/${record.id}`, { method: 'DELETE' }); await load(); }
    catch (err) { error = err instanceof Error ? err.message : 'Could not delete maintenance'; }
  }
</script>

<svelte:head><title>Vehicle Details | PocketMechanic</title></svelte:head>
<a class="back" href="/vehicles"><ArrowLeft size={19}/> Back to My Vehicles</a>
{#if error}<div class="alert" role="alert">{error}</div>{/if}
{#if loading}<div class="panel">Loading vehicle...</div>
{:else if vehicle}
  <div class="heading"><div><div class="eyebrow">VEHICLE DETAILS</div><h1>{vehicle.year} {vehicle.make} {vehicle.model}</h1><p>View vehicle information and maintenance history.</p></div><button class="primary" onclick={openAdd}><Plus size={20}/> Add Maintenance</button></div>
  <div class="overview panel"><div class="big-icon"><CarFront size={34}/></div><div><span>MAKE</span><strong>{vehicle.make}</strong></div><div><span>MODEL</span><strong>{vehicle.model}</strong></div><div><span>YEAR</span><strong>{vehicle.year}</strong></div><div><span>MILEAGE</span><strong>{fmtMileage(vehicle.mileage)}</strong></div>{#if vehicle.vin}<div><span>VIN</span><strong>{vehicle.vin}</strong></div>{/if}{#if vehicle.license_plate}<div><span>PLATE</span><strong>{vehicle.license_plate}</strong></div>{/if}</div>
  <section class="panel"><div class="section-head"><div><h2>Maintenance History</h2><p>{records.length} service {records.length === 1 ? 'record' : 'records'}</p></div></div>
    {#if records.length === 0}<div class="empty"><Wrench size={44} color="#3478f6"/><h3>No maintenance records yet</h3><p>Add a service to begin tracking this vehicle's history.</p><button class="primary" onclick={openAdd}>Add Maintenance</button></div>
    {:else}<div class="records">{#each records as record (record.id)}<div class="record"><div class="record-icon"><Wrench size={23}/></div><div class="record-body"><h3>{record.service_type}</h3><p>{fmtDate(record.service_date)} · {fmtMileage(record.mileage)}{#if record.cost != null} · ${Number(record.cost).toFixed(2)}{/if}</p>{#if record.notes}<p class="notes">{record.notes}</p>{/if}</div><div class="record-actions"><button class="icon-button" aria-label="Edit maintenance" onclick={() => openEdit(record)}><Pencil size={19}/></button><button class="icon-button danger" aria-label="Delete maintenance" onclick={() => deleteRecord(record)}><Trash2 size={19}/></button></div></div>{/each}</div>{/if}
  </section>
  <section class="panel"><div class="section-head schedule-head"><div><h2>Maintenance Schedule</h2><p>Set how often each service is due. Logging a matching service restarts its schedule.</p></div><button class="secondary" onclick={openAddSchedule}><Plus size={18}/> Add Schedule</button></div>
    {#if schedules.length === 0}<div class="empty"><CalendarClock size={44} color="#3478f6"/><h3>No schedules yet</h3><p>Add a schedule to see when each service is due next.</p><button class="primary" onclick={openAddSchedule}>Add Schedule</button></div>
    {:else}<div class="records">{#each schedules as schedule (schedule.id)}<div class="record"><div class="record-icon"><CalendarClock size={23}/></div><div class="record-body"><h3>{schedule.service_type}</h3><p>{describeInterval(schedule)}</p><p class="due">Next due: <strong>{describeDue(schedule)}</strong></p><p class="baseline">{describeBaseline(schedule)}</p></div><div class="record-actions"><button class="icon-button" aria-label="Edit schedule" onclick={() => openEditSchedule(schedule)}><Pencil size={19}/></button><button class="icon-button danger" aria-label="Delete schedule" onclick={() => deleteSchedule(schedule)}><Trash2 size={19}/></button></div></div>{/each}</div>{/if}
  </section>
{/if}
{#if showScheduleForm}
  <div class="overlay" role="presentation" onclick={(e) => { if (e.target === e.currentTarget) showScheduleForm = false; }}><div class="dialog" role="dialog" aria-modal="true" aria-label="Schedule form" tabindex="-1"><div class="dialog-heading"><h2>{editingScheduleId === null ? 'Add Schedule' : 'Edit Schedule'}</h2><button class="icon-button" aria-label="Close" onclick={() => showScheduleForm = false}><X size={22}/></button></div><form onsubmit={saveSchedule}>
    <label>Service Type<input bind:value={scheduleService} onchange={applyPreset} list="service-presets" maxlength="100" placeholder="Oil Change" required disabled={editingScheduleId !== null}/></label>
    <datalist id="service-presets">{#each Object.keys(SERVICE_PRESETS) as name (name)}<option value={name}></option>{/each}</datalist>
    <div class="two-col"><label>Every (miles)<input type="number" min="1" max="100000" bind:value={intervalMiles} placeholder="5000"/></label><label>Every (months)<input type="number" min="1" max="120" bind:value={intervalMonths} placeholder="6"/></label></div>
    <p class="hint">Fill in one or both. Suggested intervals are general guidelines, so check your owner's manual.</p>
    {#if scheduleError}<p class="alert">{scheduleError}</p>{/if}
    <div class="form-actions"><button type="button" class="secondary" onclick={() => showScheduleForm = false}>Cancel</button><button type="submit" class="primary" disabled={saving}>{saving ? 'Saving...' : 'Save Schedule'}</button></div>
  </form></div></div>
{/if}
{#if showForm}
  <div class="overlay" role="presentation" onclick={(e) => { if (e.target === e.currentTarget) showForm = false; }}><section class="dialog" role="dialog" aria-modal="true" aria-label="Maintenance form"><div class="dialog-heading"><h2>{editingId === null ? 'Add Maintenance' : 'Edit Maintenance'}</h2><button class="icon-button" aria-label="Close" onclick={() => showForm = false}><X size={22}/></button></div><form onsubmit={saveRecord}>
    <label>Service Type<input bind:value={serviceType} maxlength="100" placeholder="Oil Change" required/></label>
    <div class="two-col"><label>Service Date<input type="date" bind:value={serviceDate} max={todayIso()} required/></label><label>Mileage<input type="number" min="0" bind:value={mileage} required/></label></div>
    <label>Cost in USD (optional)<input type="number" min="0" step="0.01" bind:value={cost} placeholder="79.99" /></label>
    <label>Notes (optional)<textarea bind:value={notes} rows="4" placeholder="Additional details about the service..."></textarea></label>
    {#if error}<p class="alert">{error}</p>{/if}
    <div class="form-actions"><button type="button" class="secondary" onclick={() => showForm = false}>Cancel</button><button type="submit" class="primary" disabled={saving}>{saving ? 'Saving...' : 'Save Maintenance'}</button></div>
  </form></section></div>
{/if}
<style>
  .back{display:inline-flex;align-items:center;gap:8px;color:#3478f6;font-weight:700;font-size:15px;margin-bottom:28px}.heading{display:flex;justify-content:space-between;align-items:center;gap:20px;margin-bottom:28px}.eyebrow{font-size:13px;letter-spacing:1.5px;color:#3478f6;font-weight:800;margin-bottom:10px}h1{font-size:32px;margin-bottom:9px}.heading p,.section-head p{color:#8794a8;font-size:16px}.primary,.secondary{display:inline-flex;align-items:center;justify-content:center;gap:9px;padding:14px 20px;border:0;border-radius:11px;font-size:16px;font-weight:700;cursor:pointer}.primary{background:#3478f6;color:#fff}.primary:disabled{opacity:.6}.secondary{background:#edf1f8;color:#24324a}.panel{background:white;border:1px solid #e8edf5;border-radius:17px;padding:28px;margin-bottom:25px}.overview{display:flex;align-items:center;gap:35px;flex-wrap:wrap}.overview>div:not(.big-icon){display:flex;flex-direction:column;gap:8px}.overview span{font-size:12px;color:#8794a8;font-weight:800;letter-spacing:1px}.overview strong{font-size:20px}.big-icon,.record-icon{display:grid;place-items:center;background:#eaf1ff;color:#3478f6;border-radius:14px}.big-icon{width:75px;height:75px}.section-head h2{font-size:23px;margin-bottom:8px}.empty{text-align:center;padding:65px 10px}.empty h3{font-size:21px;margin:18px 0 8px}.empty p{color:#8794a8;font-size:15px;margin-bottom:22px}.record{display:flex;align-items:flex-start;gap:17px;padding:21px 0;border-top:1px solid #edf1f7}.record-icon{width:49px;height:49px;flex-shrink:0}.record-body{flex:1;min-width:0}.record-body h3{font-size:19px;margin-bottom:7px}.record-body p{font-size:15px;color:#8794a8;margin-bottom:0}.record-body .notes{color:#475569;margin-top:10px;white-space:pre-wrap}.record-actions{display:flex;gap:7px}.icon-button{border:0;background:#f2f5fa;color:#59677d;border-radius:9px;padding:10px;display:grid;place-items:center;cursor:pointer}.danger{color:#d83e49}.alert{color:#b91c1c;background:#fff1f2;border-radius:10px;padding:13px;margin-bottom:18px;font-size:15px}.overlay{position:fixed;inset:0;background:#101a2c99;display:grid;place-items:center;padding:20px;z-index:30}.dialog{width:min(100%,650px);background:#fff;border-radius:18px;padding:32px;max-height:90vh;overflow-y:auto}.dialog-heading{display:flex;align-items:center;justify-content:space-between;margin-bottom:18px}.dialog-heading h2{font-size:25px;margin:0}label{display:block;font-weight:700;font-size:15px;margin-bottom:18px}input,textarea{display:block;width:100%;margin-top:9px;padding:15px;border:1px solid #dfe5ef;border-radius:10px;font-size:17px;color:#17233b;font-family:inherit}.two-col{display:grid;grid-template-columns:1fr 1fr;gap:16px}.form-actions{display:flex;justify-content:flex-end;gap:12px;margin-top:12px}.schedule-head{display:flex;justify-content:space-between;align-items:flex-start;gap:16px;margin-bottom:6px}.record-body .due{color:#24324a;margin-top:6px}.record-body .baseline{font-size:14px;margin-top:4px}.hint{color:#8794a8;font-size:14px;margin:-6px 0 16px}input:disabled{background:#f2f5fa;color:#59677d}@media(max-width:650px){.schedule-head{flex-direction:column}.heading{align-items:flex-start;flex-direction:column}.two-col{grid-template-columns:1fr}.dialog{padding:22px}}
</style>
