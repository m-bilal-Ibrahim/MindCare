// ============================================================
// MindCare — API Service Layer
// All HTTP calls live here. Swap dummy data for real endpoints.
// ============================================================

import { API_BASE_URL } from '../constants';
import type { SignInPayload, SignUpPayload, ApiResponse } from '../types';

// ——— Generic fetch wrapper (CSRF + auth headers ready) ———
async function apiFetch<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<ApiResponse<T>> {
  const token =
    typeof window !== 'undefined' ? localStorage.getItem('mc_access_token') : null;

  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...options.headers,
  };

  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...options,
      headers,
      credentials: 'include', // send cookies for CSRF protection
    });

    if (!response.ok) {
      const err = await response.json().catch(() => ({ message: 'Unknown error' }));
      return { data: null, error: err.message ?? 'Request failed', loading: false };
    }

    const data: T = await response.json();
    return { data, error: null, loading: false };
  } catch (err) {
    const message = err instanceof Error ? err.message : 'Network error';
    return { data: null, error: message, loading: false };
  }
}

// ——— Auth endpoints (placeholder — wire up when backend ready) ———

export async function signIn(
  payload: SignInPayload
): Promise<ApiResponse<{ token: string; user: { id: string; name: string; role: string } }>> {
  // TODO: replace with real call → return apiFetch('/auth/sign-in', { method: 'POST', body: JSON.stringify(payload) });
  console.info('[MindCare] signIn called with', payload);

  // Dummy response for UI testing
  return new Promise((resolve) =>
    setTimeout(() => {
      resolve({
        data: { token: 'dummy-jwt-token', user: { id: '1', name: 'Layla Ahmed', role: 'client' } },
        error: null,
        loading: false,
      });
    }, 800)
  );
}

export async function signUp(
  payload: SignUpPayload
): Promise<ApiResponse<{ token: string; userId: string }>> {
  // TODO: return apiFetch('/auth/sign-up', { method: 'POST', body: JSON.stringify(payload) });
  console.info('[MindCare] signUp called with', payload);

  return new Promise((resolve) =>
    setTimeout(() => {
      resolve({ data: { token: 'dummy-jwt-token', userId: 'new-user-123' }, error: null, loading: false });
    }, 800)
  );
}

export async function getTherapists(): Promise<ApiResponse<{ id: string; name: string; specialty: string }[]>> {
  // TODO: return apiFetch('/therapists');
  return new Promise((resolve) =>
    setTimeout(() => {
      resolve({
        data: [
          { id: 't1', name: 'Dr. Tariq', specialty: 'Anxiety' },
          { id: 't2', name: 'Dr. Aisha', specialty: 'Depression' },
          { id: 't3', name: 'Dr. Sana', specialty: 'Trauma' },
        ],
        error: null,
        loading: false,
      });
    }, 600)
  );
}

export { apiFetch };
