<script lang="ts">
  import { onMount } from 'svelte';
  import { BookOpen, Search, ExternalLink, Info } from '@lucide/svelte';
  import { apiRequest, type Vehicle } from './api';

  type ManualLink = {
    title: string;
    url: string;
    source_type: 'likely_official' | 'manufacturer_portal' | 'third_party_copy';
    source_label: string;
    description: string;
  };

  type ManualResponse = {
    vehicle_name: string;
    manuals: ManualLink[];
    automatic_results_found: boolean;
    aaa_fallback: {
      title: string;
      url: string;
      note: string;
    };
  };

  let vehicles = $state<Vehicle[]>([]);
  let selectedVehicle = $state('');
  let loadingVehicles = $state(true);
  let finding = $state(false);
  let result = $state<ManualResponse | null>(null);
  let error = $state('');

  onMount(() => { void loadVehicles(); });

  async function loadVehicles() {
    loadingVehicles = true;
    try {
      vehicles = await apiRequest<Vehicle[]>('/vehicles');
      selectedVehicle = String(vehicles[0]?.id ?? '');
    } catch (e) {
      error = e instanceof Error ? e.message : 'Could not load your vehicles.';
    } finally {
      loadingVehicles = false;
    }
  }

  function vehicleChanged(event: Event) {
    selectedVehicle = (event.currentTarget as HTMLSelectElement).value;
    result = null;
    error = '';
  }

  async function findManual(event: SubmitEvent) {
    event.preventDefault();
    if (!selectedVehicle || finding) return;
    finding = true;
    error = '';
    result = null;
    try {
      result = await apiRequest<ManualResponse>(
        `/ai/manuals?vehicle_id=${encodeURIComponent(selectedVehicle)}`
      );
    } catch (e) {
      error = e instanceof Error ? e.message : 'The search could not be completed.';
    } finally {
      finding = false;
    }
  }
</script>

<section class="finder" aria-label="Find maintenance guide">
  <header class="heading-row">
    <span class="book-icon"><BookOpen size={27} /></span>
    <div>
      <div class="eyebrow">MAINTENANCE MANUAL FINDER</div>
      <h2>Find your vehicle's maintenance guide</h2>
    </div>
  </header>

  <form onsubmit={findManual}>
    <label for="manual-vehicle">Your vehicle</label>
    <div class="search-row">
      <select
        id="manual-vehicle"
        value={selectedVehicle}
        onchange={vehicleChanged}
        disabled={loadingVehicles || finding}
      >
        {#if loadingVehicles}
          <option value="">Loading vehicles...</option>
        {:else if vehicles.length === 0}
          <option value="">No vehicles found</option>
        {:else}
          {#each vehicles as v (v.id)}
            <option value={String(v.id)}>
              {v.year} {v.make} {v.model} — {v.mileage.toLocaleString()} mi
            </option>
          {/each}
        {/if}
      </select>
      <button type="submit" disabled={finding || !selectedVehicle}>
        <Search size={19} />
        {finding ? 'Searching...' : 'Find maintenance guide'}
      </button>
    </div>
  </form>

  {#if error}
    <p class="error" role="alert">{error}</p>
  {/if}

  {#if result}
    <div class="results" aria-live="polite">
      <div class="eyebrow">MAINTENANCE GUIDES</div>
      <h3>{result.vehicle_name}</h3>
      {#if result.manuals.length > 0}
        <div class="links">
          {#each result.manuals as manual (manual.url)}
            <article class="link-card">
              <div class="source-kind">{manual.source_label}</div>
              <a href={manual.url} target="_blank" rel="noopener noreferrer">
                {manual.title}
                <ExternalLink size={16} />
              </a>
              {#if manual.description}
                <p>{manual.description}</p>
              {/if}
            </article>
          {/each}
        </div>
      {:else}
        <div class="notice">
          <Info size={20} />
          <span>A vehicle-specific maintenance guide could not be found automatically.</span>
        </div>
      {/if}
      {#if !result.automatic_results_found}
        <div class="aaa">
          <strong>General maintenance guide</strong>
          <a href={result.aaa_fallback.url} target="_blank" rel="noopener noreferrer">
            AAA's maintenance checklist
            <ExternalLink size={15} />
          </a>
          <small>General maintenance guidance, not a vehicle-specific manufacturer schedule.</small>
        </div>
      {/if}
    </div>
  {/if}

  {#if !loadingVehicles && vehicles.length === 0}
    <p class="no-vehicles">
      First <a href="/vehicles">add a vehicle</a> to your account.
    </p>
  {/if}
</section>

<style>
  .finder { margin-top: 28px; background: white; border: 1px solid #e8edf5; border-radius: 17px; padding: 28px; }
  .heading-row { display: flex; gap: 17px; align-items: center; margin-bottom: 24px; }
  .book-icon { width: 54px; height: 54px; display: grid; place-items: center; flex: none; background: #eaf1ff; border-radius: 13px; color: #3478f6; }
  .eyebrow { color: #3478f6; font-weight: 800; font-size: 12px; letter-spacing: 1.3px; margin-bottom: 7px; }
  h2 { margin: 0; color: #17233b; font-size: 24px; }
  h3 { font-size: 22px; color: #17233b; margin: 0 0 18px; }
  p { margin: 0; color: #8794a8; font-size: 14px; line-height: 1.6; }
  label { display: block; margin-bottom: 9px; font-weight: 700; color: #17233b; font-size: 15px; }
  .search-row { display: flex; gap: 12px; }
  select { flex: 1; min-width: 0; border: 1px solid #dfe5ef; border-radius: 10px; background: #fff; padding: 13px; font-size: 15px; color: #17233b; }
  button { display: inline-flex; align-items: center; justify-content: center; gap: 8px; border: 0; border-radius: 10px; color: white; background: #3478f6; font-size: 15px; font-weight: 700; padding: 13px 20px; cursor: pointer; }
  button:hover:not(:disabled) { background: #2563dc; }
  button:disabled { opacity: .55; cursor: not-allowed; }
  .results { margin-top: 24px; padding-top: 20px; border-top: 1px solid #e8edf5; }
  .links { display: grid; gap: 11px; }
  .link-card { padding: 16px; border: 1px solid #e0e8f6; background: #f9fbff; border-radius: 11px; }
  .source-kind { font-weight: 800; color: #506b90; font-size: 12px; margin-bottom: 8px; }
  .link-card a, .aaa a { display: inline-flex; align-items: center; gap: 7px; font-weight: 700; color: #3478f6; text-decoration: none; overflow-wrap: anywhere; }
  .link-card a:hover, .aaa a:hover { text-decoration: underline; }
  .link-card p { margin-top: 8px; }
  .notice { background: #f4f7fb; border-radius: 10px; padding: 15px; display: flex; align-items: center; gap: 10px; color: #59677d; font-size: 14px; }
  .aaa { margin-top: 15px; padding: 18px; display: grid; gap: 8px; font-size: 14px; background: #f9fbff; border: 1px solid #e0e8f6; border-radius: 11px; }
  .aaa strong { color: #17233b; font-size: 16px; }
  .aaa small { color: #8794a8; }
  .no-vehicles { margin-top: 16px; }
  .no-vehicles a { color: #3478f6; font-weight: 700; }
  .error { margin-top: 15px; padding: 13px; color: #b91c1c; background: #fff1f2; border-radius: 10px; }
  @media (max-width: 700px) {
    .finder { padding: 18px; }
    .search-row { flex-direction: column; }
    button { width: 100%; }
  }
</style>
