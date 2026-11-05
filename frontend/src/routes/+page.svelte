<script lang="ts">
  import { onMount } from 'svelte';

  let backendStatus = $state('Checking...');

  onMount(async () => {
    try {
      const response = await fetch('http://localhost:8000/health');

      if (!response.ok) {
        throw new Error('Backend request failed');
      }

      const data = await response.json();
      backendStatus = data.status;
    } catch {
      backendStatus = 'Backend unavailable';
    }
  });
</script>

<main>
  <h1>Welcome to PocketMechanic!</h1>
  <p>Track your vehicles, maintenance, and expenses.</p>

  <h2>Backend Connection</h2>
  <p>Status: {backendStatus}</p>
</main>