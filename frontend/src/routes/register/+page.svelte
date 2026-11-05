<script lang="ts">
  import { goto } from '$app/navigation';
  import { UserRoundPlus, UserRound, Mail, LockKeyhole } from '@lucide/svelte';
  import { apiRequest } from '../../lib/api';

  let name = $state('');
  let email = $state('');
  let password = $state('');
  let confirmPassword = $state('');
  let error = $state('');
  let loading = $state(false);

  async function handleRegister(event: SubmitEvent) {
    event.preventDefault(); error = '';
    if (password !== confirmPassword) { error = 'Passwords do not match'; return; }
    loading = true;
    try {
      await apiRequest('/auth/register', {
        method: 'POST',
        body: JSON.stringify({ name: name.trim(), email, password })
      });
      await apiRequest('/auth/login', {
        method: 'POST',
        body: JSON.stringify({ email, password })
      });
      await goto('/', { replaceState: true });
    } catch (err) {
      error = err instanceof Error ? err.message : 'Registration failed';
    } finally { loading = false; }
  }
</script>
<div class="auth-container"><div class="auth-card">
  <div class="auth-icon"><UserRoundPlus size={31}/></div>
  <h1>Create your account</h1><p class="subtitle">Start tracking your vehicles with PocketMechanic</p>
  <form onsubmit={handleRegister}>
    <label for="name">Your name</label><div class="input-wrapper"><UserRound size={22}/><input id="name" bind:value={name} placeholder="Your full name" maxlength="100" required/></div>
    <label for="email">Email address</label><div class="input-wrapper"><Mail size={22}/><input id="email" type="email" bind:value={email} placeholder="you@example.com" required/></div>
    <label for="password">Password</label><div class="input-wrapper"><LockKeyhole size={22}/><input id="password" type="password" bind:value={password} minlength="8" placeholder="At least 8 characters" required/></div>
    <label for="confirm">Confirm password</label><div class="input-wrapper"><LockKeyhole size={22}/><input id="confirm" type="password" bind:value={confirmPassword} minlength="8" placeholder="Repeat your password" required/></div>
    {#if error}<p class="error" role="alert">{error}</p>{/if}
    <button type="submit" disabled={loading}>{loading ? 'Creating account...' : 'Create Account'}</button>
  </form>
  <p class="footer">Already have an account? <a href="/login">Sign in</a></p>
</div></div>
<style>
.auth-container{min-height:calc(100vh - 192px);display:grid;place-items:center}.auth-card{width:100%;max-width:528px;background:white;border:1px solid #e8edf5;border-radius:21.5px;padding:48px;box-shadow:0 14.5px 48px rgba(20,40,80,.06)}.auth-icon{width:62.5px;height:62.5px;background:#eaf1ff;color:#3478f6;border-radius:17px;display:grid;place-items:center;margin-bottom:29px}h1{font-size:32.5px;margin-bottom:9.5px}.subtitle{color:#8b97aa;font-size:17px;margin-bottom:30px}label{display:block;font-size:15.5px;font-weight:700;margin:19px 0 10px}.input-wrapper{display:flex;align-items:center;gap:14.5px;border:1px solid #dfe5ef;border-radius:12px;padding:0 17px;color:#9ba7b9}.input-wrapper:focus-within{border-color:#3478f6}input{width:100%;padding:17px 0;border:0;outline:0;background:transparent;color:#17233b;font-size:17px}button{width:100%;margin-top:31px;padding:17px;border:0;border-radius:12px;background:#3478f6;color:white;font-size:17px;font-weight:700;cursor:pointer}button:disabled{opacity:.6}.error{color:#dc2626;font-size:15.5px;margin-top:19px}.footer{text-align:center;margin:31px 0 0;font-size:15.5px;color:#8b97aa}.footer a{color:#3478f6;font-weight:700}@media(max-width:600px){.auth-card{padding:25px}}
</style>
