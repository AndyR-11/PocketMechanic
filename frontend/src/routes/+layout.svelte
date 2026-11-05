<script lang="ts">
  import '../app.css';
  import { page } from '$app/state';
  import { goto } from '$app/navigation';
  import { apiRequest, type User } from '../lib/api';
  import { account } from '../lib/account.svelte';

  import {
    LayoutDashboard,
    CarFront,
    Wrench,
    Wallet,
    Bell,
    LogOut
  } from '@lucide/svelte';

  let { children } = $props();

  const navigation = [
    { label: 'Dashboard', href: '/', icon: LayoutDashboard },
    { label: 'My Vehicles', href: '/vehicles', icon: CarFront },
    { label: 'Maintenance', href: '/maintenance', icon: Wrench },
    { label: 'Expenses', href: '/expenses', icon: Wallet },
    { label: 'Reminders', href: '/reminders', icon: Bell }
  ];

  let isAuthPage = $derived(
    page.url.pathname === '/login' ||
    page.url.pathname === '/register'
  );

  let initials = $derived(
    (account.user?.name ?? 'My Account')
      .split(/\s+/)
      .filter(Boolean)
      .slice(0, 2)
      .map((word) => word[0].toUpperCase())
      .join('')
  );

  $effect(() => {
    if (isAuthPage) {
      account.user = null;
      return;
    }

    apiRequest<User>('/auth/me')
      .then((user) => {
        account.user = user;
      })
      .catch(() => {
        account.user = null;
      });
  });

  let loggingOut = $state(false);
  let logoutError = $state('');

  async function handleLogout() {
    if (loggingOut) return;

    loggingOut = true;
    logoutError = '';

    try {
      await apiRequest('/auth/logout', {
        method: 'POST'
      });

      await goto('/login', { replaceState: true });
    } catch (err) {
      logoutError = err instanceof Error
        ? err.message
        : 'Logout failed';
    } finally {
      loggingOut = false;
    }
  }
</script>

<svelte:head>
  <title>PocketMechanic</title>
  <meta
    name="description"
    content="Manage your vehicles and maintenance with PocketMechanic."
  />
</svelte:head>

{#if isAuthPage}
  <main class="auth-layout">
    {@render children()}
  </main>
{:else}
  <div class="app-shell">
    <aside class="sidebar">
      <div class="brand">
        <div class="brand-icon">P</div>
        <div>
          <strong>PocketMechanic</strong>
          <small>VEHICLE MANAGEMENT</small>
        </div>
      </div>

      <div class="nav-label">WORKSPACE</div>

      <nav>
        {#each navigation as item}
          <a
            href={item.href}
            class:active={page.url.pathname === item.href}
          >
            <span class="nav-icon">
              <item.icon size={23} strokeWidth={1.8} />
            </span>
            {item.label}
          </a>
        {/each}
      </nav>

      <div class="sidebar-footer">
        <a
          class="sidebar-bottom"
          class:active={page.url.pathname === '/account'}
          href="/account"
        >
          <div class="avatar">{initials}</div>
          <div class="account-text">
            <strong>{account.user?.name ?? 'My Account'}</strong>
            <small>My Account</small>
          </div>
        </a>

        {#if logoutError}
          <p class="logout-error" role="alert">
            {logoutError}
          </p>
        {/if}

        <button
          class="logout-button"
          onclick={handleLogout}
          disabled={loggingOut}
        >
          <LogOut size={22} strokeWidth={1.8} />
          {loggingOut ? 'Logging out...' : 'Log Out'}
        </button>
      </div>
    </aside>

    <div class="main-area">
      <header class="topbar">
        <div class="breadcrumb">
          Workspace / {page.url.pathname === '/account'
            ? 'My Account'
            : navigation.find((item) =>
                item.href === page.url.pathname
              )?.label ?? 'Overview'}
        </div>

        <div class="topbar-right">
          <span class="status-dot"></span>
          <span>System Online</span>
          <a class="top-avatar" href="/account" aria-label="My Account">{initials}</a>
        </div>
      </header>

      <main class="content">
        {@render children()}
      </main>
    </div>
  </div>
{/if}

<style>
  .auth-layout {
    min-height: 100vh;
    display: grid;
    place-items: center;
    padding: 29px;
    background: #f5f7fb;
  }

  .app-shell {
    display: flex;
    min-height: 100vh;
  }

  .sidebar {
    width: 306px;
    background: #111d35;
    color: #fff;
    padding: 33.5px 21.5px;
    display: flex;
    flex-direction: column;
    flex-shrink: 0;
  }

  .brand {
    display: flex;
    align-items: center;
    gap: 14.5px;
    padding: 0 9.5px;
    margin-bottom: 66px;
  }

  .brand-icon {
    width: 50.5px;
    height: 50.5px;
    background: #3478f6;
    border-radius: 14.5px;
    display: grid;
    place-items: center;
    font-size: 29px;
    font-weight: 800;
  }

  .brand strong {
    font-size: 18px;
    display: block;
  }

  .brand small {
    display: block;
    color: #8e9bb5;
    font-size: 11px;
    letter-spacing: 1px;
    margin-top: 5px;
  }

  .nav-label {
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 2px;
    color: #697b9d;
    padding-left: 19px;
    margin-bottom: 18px;
  }

  nav {
    display: flex;
    flex-direction: column;
    gap: 7px;
  }

  nav a {
    padding: 17px 19px;
    border-radius: 12px;
    color: #a5b3cd;
    font-size: 17px;
    font-weight: 600;
    display: flex;
    align-items: center;
    gap: 17px;
    transition: background 0.2s, color 0.2s;
  }

  nav a:hover {
    background: #1c2c4b;
    color: white;
  }

  nav a.active {
    background: #2868df;
    color: white;
  }

  .nav-icon {
    width: 24px;
    text-align: center;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .sidebar-footer {
    margin-top: auto;
    border-top: 1px solid #2a3953;
    padding-top: 21.5px;
  }

  .sidebar-bottom {
    padding: 11px 9.5px;
    margin-bottom: 10px;
    display: flex;
    align-items: center;
    gap: 14.5px;
    border-radius: 12px;
    color: white;
    transition: background 0.2s;
  }

  .sidebar-bottom:hover,
  .sidebar-bottom.active {
    background: #1c2c4b;
  }

  .account-text {
    min-width: 0;
  }

  .account-text strong {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .avatar,
  .top-avatar {
    width: 45.5px;
    height: 45.5px;
    background: #2b4676;
    border-radius: 50%;
    display: grid;
    place-items: center;
    font-size: 14.5px;
    font-weight: 700;
    flex-shrink: 0;
  }

  .sidebar-bottom strong {
    display: block;
    font-size: 15.5px;
  }

  .sidebar-bottom small {
    display: block;
    color: #8e9bb5;
    font-size: 13px;
    margin-top: 5px;
  }

  .logout-button {
    display: flex;
    align-items: center;
    gap: 17px;
    width: 100%;
    padding: 15.5px 19px;
    background: transparent;
    border: none;
    border-radius: 12px;
    color: #a5b3cd;
    font-size: 17px;
    font-weight: 600;
    text-align: left;
    cursor: pointer;
  }

  .logout-button:hover {
    background: #1c2c4b;
    color: white;
  }

  .logout-button:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  .logout-error {
    padding: 0 14.5px;
    color: #fca5a5;
    font-size: 14.5px;
    line-height: 1.5;
  }

  .main-area {
    flex: 1;
    min-width: 0;
  }

  .topbar {
    height: 93.5px;
    background: white;
    border-bottom: 1px solid #e8edf5;
    padding: 0 48px;
    display: flex;
    align-items: center;
    justify-content: space-between;
  }

  .breadcrumb {
    color: #8a97ab;
    font-size: 15.5px;
  }

  .topbar-right {
    display: flex;
    align-items: center;
    gap: 12px;
    color: #6d7a90;
    font-size: 14.5px;
  }

  .status-dot {
    width: 9.5px;
    height: 9.5px;
    background: #22c55e;
    border-radius: 50%;
  }

  .top-avatar {
    background: #e7efff;
    color: #3478f6;
    margin-left: 19px;
  }

  .content {
    padding: 45.5px 48px;
    max-width: 1800px;
    margin: auto;
  }

  @media (max-width: 800px) {
    .app-shell {
      flex-direction: column;
    }

    .sidebar {
      width: 100%;
      padding: 19px;
    }

    .brand {
      margin-bottom: 21.5px;
    }

    nav {
      flex-direction: row;
      overflow-x: auto;
    }

    nav a {
      white-space: nowrap;
    }

    .nav-label,
    .sidebar-bottom {
      display: none;
    }

    .sidebar-footer {
      margin-top: 14.5px;
      border-top: none;
      padding-top: 0;
    }

    .logout-button {
      width: auto;
    }

    .topbar {
      padding: 0 24px;
    }

    .content {
      padding: 29px 24px;
    }
  }
</style>