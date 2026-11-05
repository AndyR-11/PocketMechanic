<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { apiRequest, type User } from '../../lib/api';
  import { account } from '../../lib/account.svelte';

  let name = $state('');
  let email = $state('');
  let loading = $state(true);
  let saving = $state(false);
  let error = $state('');
  let saved = $state(false);

  onMount(async () => {
    try {
      const user = await apiRequest<User>('/auth/me');
      name = user.name;
      email = user.email;
    } catch (err) {
      if (err instanceof Error && /401|not authenticated|unauthorized|expired/i.test(err.message)) {
        await goto('/login', { replaceState: true });
      } else error = err instanceof Error ? err.message : 'Could not load your account';
    } finally {
      loading = false;
    }
  });

  async function saveAccount(event: SubmitEvent) {
    event.preventDefault();
    saving = true;
    saved = false;
    error = '';

    try {
      const user = await apiRequest<User>('/auth/me', {
        method: 'PUT',
        body: JSON.stringify({ name: name.trim(), email: email.trim() })
      });
      account.user = user;
      name = user.name;
      email = user.email;
      saved = true;
    } catch (err) {
      error = err instanceof Error ? err.message : 'Could not save your account';
    } finally {
      saving = false;
    }
  }
</script>

<div class="heading">
  <div class="eyebrow">YOUR PROFILE</div>
  <h1>My Account</h1>
  <p>Update the name and email address on your account.</p>
</div>

{#if loading}
  <div class="panel muted">Loading account...</div>
{:else}
  <form class="panel" onsubmit={saveAccount}>
    <label>
      Name
      <input bind:value={name} maxlength="100" required oninput={() => (saved = false)} />
    </label>
    <label>
      Email address
      <input type="email" bind:value={email} required oninput={() => (saved = false)} />
    </label>

    {#if error}<p class="form-error" role="alert">{error}</p>{/if}
    {#if saved}<p class="form-success" role="status">Your account was updated.</p>{/if}

    <div class="form-actions">
      <button class="primary" type="submit" disabled={saving}>
        {saving ? 'Saving...' : 'Save Changes'}
      </button>
    </div>
  </form>
{/if}

<style>
  .heading { margin-bottom: 30px; }
  .eyebrow { font-size: 13px; letter-spacing: 1.5px; color: #3478f6; font-weight: 800; margin-bottom: 10px; }
  h1 { font-size: 33px; margin: 0 0 9px; }
  .heading p, .muted { color: #8794a8; font-size: 16px; margin: 0; }
  .panel { background: white; border: 1px solid #e8edf5; border-radius: 17px; padding: 28px; max-width: 560px; }
  form { display: flex; flex-direction: column; gap: 18px; }
  label { display: flex; flex-direction: column; gap: 8px; font-size: 15px; font-weight: 700; color: #24324a; }
  input { padding: 14px 16px; border: 1px solid #dfe5ef; border-radius: 11px; font-size: 16px; font-weight: 500; color: #17233b; }
  input:focus { outline: 2px solid #3478f6; outline-offset: 0; border-color: transparent; }
  .form-error, .form-success { margin: 0; padding: 12px 14px; border-radius: 10px; font-size: 15px; }
  .form-error { background: #fdf0f0; color: #b42318; }
  .form-success { background: #ecfdf3; color: #067647; }
  .form-actions { display: flex; justify-content: flex-end; }
  .primary { padding: 14px 20px; border: 0; border-radius: 11px; background: #3478f6; color: white; font-size: 16px; font-weight: 700; cursor: pointer; }
  .primary:hover { background: #2563dc; }
  .primary:disabled { opacity: 0.6; }
</style>
