<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { CarFront, Wrench, CalendarDays, Plus, ArrowRight } from '@lucide/svelte';
  import { apiRequest, fmtDate, fmtMileage, type Vehicle, type Maintenance } from '../lib/api';
  type Entry = Maintenance & { vehicle: Vehicle };
  let vehicles = $state<Vehicle[]>([]);
  let records = $state<Entry[]>([]);
  let loading = $state(true);
  let error = $state('');

  onMount(async () => {
    try {
      await apiRequest('/auth/me');
      vehicles = await apiRequest<Vehicle[]>('/vehicles');
      const lists = await Promise.all(vehicles.map(async (vehicle) => {
        const maintenance = await apiRequest<Maintenance[]>(`/vehicles/${vehicle.id}/maintenance`);
        return maintenance.map((record) => ({ ...record, vehicle }));
      }));
      records = lists.flat().sort((a,b) => b.service_date.localeCompare(a.service_date));
    } catch (err) {
      if (err instanceof Error && /401|not authenticated|unauthorized/i.test(err.message)) await goto('/login', { replaceState: true });
      else error = err instanceof Error ? err.message : 'Could not load dashboard';
    } finally { loading = false; }
  });
</script>
<svelte:head><title>Dashboard | PocketMechanic</title></svelte:head>
{#if loading}<div class="loading">Loading dashboard...</div>
{:else}
  <div class="heading"><div><div class="eyebrow">YOUR WORKSPACE</div><h1>Dashboard Overview</h1><p>Welcome to PocketMechanic. Keep your vehicles in top shape.</p></div><a href="/vehicles" class="primary"><Plus size={20}/> Add Vehicle</a></div>
  {#if error}<div class="alert" role="alert">{error}</div>{/if}
  <div class="stats">
    <div class="stat"><div class="stat-icon blue"><CarFront size={27}/></div><p>Total Vehicles</p><strong>{vehicles.length}</strong></div>
    <div class="stat"><div class="stat-icon green"><Wrench size={27}/></div><p>Maintenance Records</p><strong>{records.length}</strong></div>
    <div class="stat"><div class="stat-icon orange"><CalendarDays size={27}/></div><p>Upcoming Services</p><strong>—</strong><small>Scheduling not yet implemented</small></div>
  </div>
  <div class="sections">
    <section class="panel"><div class="panel-head"><div><h2>My Garage</h2><p>Your registered vehicles</p></div><a href="/vehicles">View All <ArrowRight size={17}/></a></div>
      {#if vehicles.length === 0}<div class="empty"><CarFront size={46} color="#3478f6"/><h3>No vehicles added yet</h3><p>Add your first vehicle to start tracking maintenance.</p><a href="/vehicles" class="primary">Add Your First Vehicle</a></div>
      {:else}<div class="items">{#each vehicles.slice(0, 4) as vehicle (vehicle.id)}<a class="item" href={`/vehicles/${vehicle.id}`}><div class="item-icon"><CarFront size={23}/></div><div><strong>{vehicle.year} {vehicle.make} {vehicle.model}</strong><span>{fmtMileage(vehicle.mileage)}</span></div><ArrowRight size={18} color="#3478f6"/></a>{/each}</div>{/if}
    </section>
    <section class="panel"><div class="panel-head"><div><h2>Recent Maintenance</h2><p>Your latest service activity</p></div><a href="/maintenance">View All <ArrowRight size={17}/></a></div>
      {#if records.length === 0}<div class="empty"><Wrench size={46} color="#3478f6"/><h3>No maintenance records</h3><p>Your maintenance history will appear here.</p></div>
      {:else}<div class="items">{#each records.slice(0, 5) as record (record.id)}<a class="item" href={`/vehicles/${record.vehicle_id}`}><div class="item-icon"><Wrench size={23}/></div><div><strong>{record.service_type}</strong><span>{record.vehicle.make} {record.vehicle.model} · {fmtDate(record.service_date)}</span></div><ArrowRight size={18} color="#3478f6"/></a>{/each}</div>{/if}
    </section>
  </div>
{/if}
<style>
  .loading{text-align:center;padding:80px;color:#8794a8;font-size:17px}.heading{display:flex;justify-content:space-between;align-items:center;gap:20px;margin-bottom:30px}.eyebrow{font-size:13px;letter-spacing:1.5px;color:#3478f6;font-weight:800;margin-bottom:10px}h1{font-size:33px;margin-bottom:9px}.heading p,.panel-head p{color:#8794a8;font-size:16px}.primary{display:inline-flex;align-items:center;justify-content:center;gap:9px;background:#3478f6;color:white;padding:14px 20px;border-radius:11px;font-size:16px;font-weight:700}.primary:hover{background:#2563dc}.stats{display:grid;grid-template-columns:repeat(3,1fr);gap:22px;margin-bottom:28px}.stat,.panel{background:white;border:1px solid #e8edf5;border-radius:17px;padding:27px}.stat-icon{width:57px;height:57px;border-radius:14px;display:grid;place-items:center;color:#3478f6;margin-bottom:22px}.blue{background:#eaf1ff}.green{background:#e8f8ef;color:#16a34a}.orange{background:#fff4e5;color:#d97706}.stat p{font-size:16px;color:#8794a8;margin-bottom:8px}.stat strong{font-size:34px}.stat small{display:block;color:#8794a8;font-size:12px;margin-top:7px}.sections{display:grid;grid-template-columns:1fr 1fr;gap:24px}.panel{min-height:360px}.panel-head{display:flex;align-items:flex-start;justify-content:space-between;gap:12px;margin-bottom:22px}.panel-head h2{font-size:22px;margin-bottom:7px}.panel-head a{display:inline-flex;align-items:center;gap:5px;color:#3478f6;font-weight:700;font-size:14px;white-space:nowrap}.empty{text-align:center;padding:46px 10px 20px}.empty h3{font-size:20px;margin:17px 0 8px}.empty p{color:#8794a8;font-size:15px;line-height:1.6;margin-bottom:23px}.item{display:flex;align-items:center;gap:13px;padding:16px 0;border-top:1px solid #edf1f7}.item-icon{width:46px;height:46px;border-radius:12px;display:grid;place-items:center;background:#eaf1ff;color:#3478f6;flex-shrink:0}.item>div:nth-child(2){flex:1;min-width:0}.item strong{display:block;font-size:16px;margin-bottom:5px}.item span{display:block;font-size:14px;color:#8794a8}.alert{color:#b91c1c;background:#fff1f2;border-radius:10px;padding:13px;margin-bottom:18px;font-size:15px}@media(max-width:1100px){.stats,.sections{grid-template-columns:1fr}}@media(max-width:650px){.heading{align-items:flex-start;flex-direction:column}}
</style>
