import type { User } from './api';

export const account = $state<{ user: User | null }>({ user: null });
