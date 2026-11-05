<script lang="ts">
  import { goto } from '$app/navigation';
  import { LogIn, Mail, LockKeyhole } from '@lucide/svelte';
  import { apiRequest } from '../../lib/api';

  let email = $state('');
  let password = $state('');
  let error = $state('');
  let loading = $state(false);

  async function handleLogin(event: SubmitEvent) {
    event.preventDefault();
    error = '';
    loading = true;

    try {
      await apiRequest('/auth/login', {
        method: 'POST',
        body: JSON.stringify({ email, password })
      });

      await goto('/');
    } catch (err) {
      error = err instanceof Error ? err.message : 'Login failed';
    } finally {
      loading = false;
    }
  }
</script>

<div class="auth-container">
  <div class="auth-card">
    <div class="auth-icon"><LogIn size={31} /></div>
    <h1>Welcome back</h1>
    <p class="subtitle">Sign in to your PocketMechanic account</p>

    <form onsubmit={handleLogin}>
      <label for="email">Email address</label>
      <div class="input-wrapper">
        <Mail size={22} />
        <input
          id="email"
          type="email"
          placeholder="you@example.com"
          bind:value={email}
          required
        />
      </div>

      <label for="password">Password</label>
      <div class="input-wrapper">
        <LockKeyhole size={22} />
        <input
          id="password"
          type="password"
          placeholder="Enter your password"
          bind:value={password}
          required
        />
      </div>

      {#if error}
        <p class="error">{error}</p>
      {/if}

      <button type="submit" disabled={loading}>
        {loading ? 'Signing in...' : 'Sign In'}
      </button>
    </form>

    <p class="footer">
      Don't have an account? <a href="/register">Create one</a>
    </p>
  </div>
</div>

<style>
  .auth-container {
    min-height: calc(100vh - 192px);
    display: grid;
    place-items: center;
  }

  .auth-card {
    width: 100%;
    max-width: 528px;
    background: white;
    border: 1px solid #e8edf5;
    border-radius: 21.5px;
    padding: 48px;
    box-shadow: 0 14.5px 48px rgba(20, 40, 80, 0.06);
  }

  .auth-icon {
    width: 62.5px;
    height: 62.5px;
    background: #eaf1ff;
    color: #3478f6;
    border-radius: 17px;
    display: grid;
    place-items: center;
    margin-bottom: 29px;
  }

  h1 {
    font-size: 32.5px;
    margin-bottom: 9.5px;
  }

  .subtitle {
    color: #8b97aa;
    font-size: 17px;
    margin-bottom: 36px;
  }

  label {
    display: block;
    font-size: 15.5px;
    font-weight: 700;
    margin: 21.5px 0 11px;
  }

  .input-wrapper {
    display: flex;
    align-items: center;
    gap: 14.5px;
    border: 1px solid #dfe5ef;
    border-radius: 12px;
    padding: 0 17px;
    color: #9ba7b9;
  }

  .input-wrapper:focus-within {
    border-color: #3478f6;
  }

  input {
    width: 100%;
    padding: 17px 0;
    border: none;
    outline: none;
    background: transparent;
    color: #17233b;
    font-size: 17px;
  }

  button {
    width: 100%;
    margin-top: 31px;
    padding: 17px;
    border: none;
    border-radius: 12px;
    background: #3478f6;
    color: white;
    font-size: 17px;
    font-weight: 700;
  }

  button:disabled {
    opacity: 0.6;
  }

  .error {
    color: #dc2626;
    font-size: 15.5px;
    margin-top: 19px;
  }

  .footer {
    text-align: center;
    margin: 31px 0 0;
    font-size: 15.5px;
    color: #8b97aa;
  }

  .footer a {
    color: #3478f6;
    font-weight: 700;
  }
</style>