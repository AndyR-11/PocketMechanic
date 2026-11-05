<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { CarFront, Plus, Pencil, Trash2, X, ArrowRight } from '@lucide/svelte';
  import { apiRequest, fmtMileage, type Vehicle } from '../../lib/api';

  let vehicles = $state<Vehicle[]>([]);
  let loading = $state(true);
  let saving = $state(false);
  let error = $state('');
  let showForm = $state(false);
  let editingId = $state<number | null>(null);
  let make = $state('');
  let model = $state('');
  let year = $state(new Date().getFullYear());
  let mileage = $state(0);
  let vin = $state('');
  let licensePlate = $state('');

  async function loadVehicles() {
    try {
      vehicles = await apiRequest<Vehicle[]>('/vehicles');
      error = '';
    } catch (err) {
      if (err instanceof Error && /401|not authenticated|unauthorized/i.test(err.message)) {
        await goto('/login');
      } else error = err instanceof Error ? err.message : 'Could not load vehicles';
    } finally { loading = false; }
  }
  onMount(() => { void loadVehicles(); });

  function openAdd() {
    editingId = null; make = ''; model = ''; year = new Date().getFullYear(); mileage = 0; vin = ''; licensePlate = '';
    error = ''; showForm = true;
  }
  function openEdit(vehicle: Vehicle) {
    editingId = vehicle.id; make = vehicle.make; model = vehicle.model;
    year = vehicle.year; mileage = vehicle.mileage; vin = vehicle.vin ?? ''; licensePlate = vehicle.license_plate ?? ''; error = ''; showForm = true;
  }
  async function saveVehicle(event: SubmitEvent) {
    event.preventDefault(); saving = true; error = '';
    try {
      const payload = { make: make.trim(), model: model.trim(), year: Number(year), mileage: Number(mileage), vin: vin.trim() || null, license_plate: licensePlate.trim() || null };
      await apiRequest(editingId === null ? '/vehicles' : `/vehicles/${editingId}`, {
        method: editingId === null ? 'POST' : 'PUT', body: JSON.stringify(payload)
      });
      showForm = false;
      await loadVehicles();
    } catch (err) { error = err instanceof Error ? err.message : 'Could not save vehicle'; }
    finally { saving = false; }
  }
  async function deleteVehicle(vehicle: Vehicle) {
    if (!confirm(`Delete ${vehicle.year} ${vehicle.make} ${vehicle.model}? Its maintenance records may also be deleted.`)) return;
    try { await apiRequest(`/vehicles/${vehicle.id}`, { method: 'DELETE' }); await loadVehicles(); }
    catch (err) { error = err instanceof Error ? err.message : 'Could not delete vehicle'; }
  }
</script>

<svelte:head><title>My Vehicles | PocketMechanic</title></svelte:head>
<div class="heading">
  <div><div class="eyebrow">YOUR GARAGE</div><h1>My Vehicles</h1><p>Manage your vehicles and keep track of their mileage.</p></div>
  <button class="primary" onclick={openAdd}><Plus size={20} /> Add Vehicle</button>
</div>
{#if error}<div class="alert" role="alert">{error}</div>{/if}
{#if loading}
  <div class="panel muted">Loading vehicles...</div>
{:else if vehicles.length === 0}
  <div class="panel empty"><CarFront size={48} color="#3478f6" /><h2>Your garage is empty</h2><p>Add your first vehicle to get started.</p><button class="primary" onclick={openAdd}><Plus size={20} /> Add Your First Vehicle</button></div>
{:else}
  <div class="vehicle-grid">
    {#each vehicles as vehicle (vehicle.id)}
      <article class="panel vehicle-card">
        <div class="vehicle-icon"><CarFront size={30} /></div>
        <div class="vehicle-year">{vehicle.year}</div>
        <h2>{vehicle.make} {vehicle.model}</h2>
        {#if vehicle.license_plate}<p class="muted">Plate: {vehicle.license_plate}</p>{/if}<p class="muted">Current mileage</p><div class="mileage">{fmtMileage(vehicle.mileage)}</div>
        <div class="actions">
          <a class="details" href={`/vehicles/${vehicle.id}`}>View Details <ArrowRight size={17} /></a>
          <button class="icon-button" aria-label={`Edit ${vehicle.make} ${vehicle.model}`} title="Edit" onclick={() => openEdit(vehicle)}><Pencil size={19} /></button>
          <button class="icon-button danger" aria-label={`Delete ${vehicle.make} ${vehicle.model}`} title="Delete" onclick={() => deleteVehicle(vehicle)}><Trash2 size={19} /></button>
        </div>
      </article>
    {/each}
  </div>
{/if}

{#if showForm}
  <div class="overlay" role="presentation" onclick={(e) => { if (e.target === e.currentTarget) showForm = false; }}>
    <section class="dialog" role="dialog" aria-modal="true" aria-label={editingId === null ? 'Add vehicle' : 'Edit vehicle'}>
      <div class="dialog-heading"><h2>{editingId === null ? 'Add Vehicle' : 'Edit Vehicle'}</h2><button class="icon-button" aria-label="Close" onclick={() => showForm = false}><X size={22}/></button></div>
      <form onsubmit={saveVehicle}>
        <div class="two-col"><label>Make<input bind:value={make} maxlength="100" placeholder="Toyota" required /></label><label>Model<input bind:value={model} maxlength="100" placeholder="Camry" required /></label></div>
        <div class="two-col"><label>Year<input type="number" min="1886" max="2100" bind:value={year} required /></label><label>Mileage<input type="number" min="0" bind:value={mileage} required /></label></div>
        <div class="two-col"><label>VIN (optional)<input bind:value={vin} maxlength="17" minlength="17" placeholder="17-character VIN" /></label><label>License Plate (optional)<input bind:value={licensePlate} maxlength="20" placeholder="ABC1234" /></label></div>
        {#if error}<p class="form-error">{error}</p>{/if}
        <div class="form-actions"><button type="button" class="secondary" onclick={() => showForm = false}>Cancel</button><button class="primary" type="submit" disabled={saving}>{saving ? 'Saving...' : 'Save Vehicle'}</button></div>
      </form>
    </section>
  </div>
{/if}

<style>
  .heading{display:flex;justify-content:space-between;align-items:center;gap:20px;margin-bottom:30px}.eyebrow{font-size:13px;letter-spacing:1.5px;color:#3478f6;font-weight:800;margin-bottom:10px}h1{font-size:33px;margin-bottom:9px}.heading p,.muted{color:#8794a8;font-size:16px}.primary,.secondary{display:inline-flex;align-items:center;justify-content:center;gap:9px;padding:14px 20px;border:0;border-radius:11px;font-size:16px;font-weight:700;cursor:pointer}.primary{background:#3478f6;color:#fff}.primary:hover{background:#2563dc}.primary:disabled{opacity:.6}.secondary{background:#edf1f8;color:#24324a}.panel{background:white;border:1px solid #e8edf5;border-radius:17px;padding:28px}.empty{text-align:center;padding:85px 20px}.empty h2{font-size:23px;margin:20px 0 9px}.empty p{margin-bottom:26px}.vehicle-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(285px,1fr));gap:22px}.vehicle-icon{background:#eaf1ff;color:#3478f6;width:62px;height:62px;display:grid;place-items:center;border-radius:16px;margin-bottom:22px}.vehicle-year{color:#3478f6;font-weight:800;font-size:15px}.vehicle-card h2{font-size:24px;margin:7px 0 24px}.mileage{font-size:24px;font-weight:800;margin:5px 0 24px}.actions{display:flex;align-items:center;gap:8px;border-top:1px solid #edf1f7;padding-top:18px}.details{display:inline-flex;align-items:center;gap:8px;color:#3478f6;font-weight:700;font-size:15px;margin-right:auto}.icon-button{border:0;background:#f2f5fa;color:#59677d;border-radius:9px;padding:10px;display:grid;place-items:center;cursor:pointer}.danger{color:#d83e49}.alert,.form-error{color:#b91c1c;background:#fff1f2;border-radius:10px;padding:13px;margin-bottom:18px;font-size:15px}.overlay{position:fixed;inset:0;background:#101a2c99;display:grid;place-items:center;padding:20px;z-index:30}.dialog{width:min(100%,620px);background:#fff;border-radius:18px;padding:32px;box-shadow:0 20px 70px #0002}.dialog-heading{display:flex;align-items:center;justify-content:space-between;margin-bottom:18px}.dialog-heading h2{font-size:25px;margin:0}label{display:block;font-weight:700;font-size:15px;margin-bottom:18px}input{display:block;width:100%;margin-top:9px;padding:15px;border:1px solid #dfe5ef;border-radius:10px;font-size:17px;color:#17233b}.two-col{display:grid;grid-template-columns:1fr 1fr;gap:16px}.form-actions{display:flex;justify-content:flex-end;gap:12px;margin-top:12px}@media(max-width:650px){.heading{align-items:flex-start;flex-direction:column}.two-col{grid-template-columns:1fr}.dialog{padding:22px}}
</style>
