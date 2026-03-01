import { describe, it, expect, vi, beforeEach } from 'vitest'

const waitFor = async (predicate: () => boolean, timeoutMs = 500) => {
  const start = Date.now()
  while (!predicate()) {
    if (Date.now() - start > timeoutMs) {
      throw new Error('Condition not met before timeout')
    }
    await new Promise((resolve) => setTimeout(resolve, 10))
  }
}

describe('authStore hydration', () => {
  beforeEach(() => {
    vi.resetModules()
    const backing = new Map<string, string>()
    const storage = {
      getItem: (key: string) => backing.get(key) ?? null,
      setItem: (key: string, value: string) => {
        backing.set(key, String(value))
      },
      removeItem: (key: string) => {
        backing.delete(key)
      },
      clear: () => {
        backing.clear()
      },
    }
    vi.stubGlobal('localStorage', storage)
  })

  it('restores token aliases after persisted-state rehydrate', async () => {
    localStorage.setItem(
      'dreamcatcher-auth',
      JSON.stringify({
        state: {
          user: null,
          token: 'persisted-access-token',
          refreshToken: 'persisted-refresh-token',
          isAuthenticated: true,
        },
        version: 0,
      })
    )

    vi.doMock('../utils/api', () => ({
      apiClient: {
        defaults: { baseURL: 'http://localhost:8000/api' },
        interceptors: {
          request: { use: vi.fn() },
          response: { use: vi.fn() },
        },
        post: vi.fn(),
        get: vi.fn(),
      },
    }))

    const { useAuthStore } = await import('./authStore')

    await waitFor(() => useAuthStore.getState().hasHydrated === true)

    expect(localStorage.getItem('auth_token')).toBe('persisted-access-token')
    expect(localStorage.getItem('refresh_token')).toBe('persisted-refresh-token')
    expect(useAuthStore.getState().isAuthenticated).toBe(true)
  })
})
