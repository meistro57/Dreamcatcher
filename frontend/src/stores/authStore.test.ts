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

  it('persists tokens after successful login', async () => {
    const postMock = vi.fn().mockResolvedValue({
      data: {
        access_token: 'access-123',
        refresh_token: 'refresh-123',
        token_type: 'bearer',
        expires_in: 1800,
        user: {
          id: 'u1',
          email: 'user@example.com',
          username: 'user',
          full_name: 'User One',
          is_active: true,
          is_verified: true,
          created_at: new Date().toISOString(),
          roles: ['user'],
        },
      },
    })

    vi.doMock('axios', () => ({
      default: { post: vi.fn() },
    }))

    vi.doMock('../utils/api', () => ({
      apiClient: {
        defaults: { baseURL: 'http://localhost:8000/api' },
        interceptors: {
          request: { use: vi.fn() },
          response: { use: vi.fn() },
        },
        post: postMock,
        get: vi.fn(),
      },
    }))

    const { useAuthStore } = await import('./authStore')
    const success = await useAuthStore.getState().login('user', 'TempPass123!')

    expect(success).toBe(true)
    expect(localStorage.getItem('auth_token')).toBe('access-123')
    expect(localStorage.getItem('refresh_token')).toBe('refresh-123')
    expect(useAuthStore.getState().isAuthenticated).toBe(true)
  })

  it('refreshes access token and keeps session authenticated', async () => {
    const axiosPostMock = vi.fn().mockResolvedValue({
      data: {
        access_token: 'access-refreshed',
        refresh_token: 'refresh-refreshed',
        token_type: 'bearer',
        expires_in: 1800,
        user: {
          id: 'u1',
          email: 'user@example.com',
          username: 'user',
          full_name: 'User One',
          is_active: true,
          is_verified: true,
          created_at: new Date().toISOString(),
          roles: ['user'],
        },
      },
    })

    vi.doMock('axios', () => ({
      default: { post: axiosPostMock },
    }))

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
    useAuthStore.setState({
      refreshToken: 'refresh-existing',
      token: 'access-existing',
      user: {
        id: 'u1',
        email: 'user@example.com',
        username: 'user',
        full_name: 'User One',
        is_active: true,
        is_verified: true,
        created_at: new Date().toISOString(),
        roles: ['user'],
      },
      isAuthenticated: true,
    })

    const refreshed = await useAuthStore.getState().refreshAccessToken()

    expect(refreshed).toBe(true)
    expect(localStorage.getItem('auth_token')).toBe('access-refreshed')
    expect(localStorage.getItem('refresh_token')).toBe('refresh-refreshed')
    expect(useAuthStore.getState().isAuthenticated).toBe(true)
  })

  it('clears persisted auth state on logout', async () => {
    const postMock = vi.fn().mockResolvedValue({ data: { message: 'ok' } })

    vi.doMock('axios', () => ({
      default: { post: vi.fn() },
    }))

    vi.doMock('../utils/api', () => ({
      apiClient: {
        defaults: { baseURL: 'http://localhost:8000/api' },
        interceptors: {
          request: { use: vi.fn() },
          response: { use: vi.fn() },
        },
        post: postMock,
        get: vi.fn(),
      },
    }))

    const { useAuthStore } = await import('./authStore')
    useAuthStore.setState({
      token: 'access-existing',
      refreshToken: 'refresh-existing',
      user: {
        id: 'u1',
        email: 'user@example.com',
        username: 'user',
        full_name: 'User One',
        is_active: true,
        is_verified: true,
        created_at: new Date().toISOString(),
        roles: ['user'],
      },
      isAuthenticated: true,
    })
    localStorage.setItem('auth_token', 'access-existing')
    localStorage.setItem('refresh_token', 'refresh-existing')

    useAuthStore.getState().logout()

    expect(localStorage.getItem('auth_token')).toBe(null)
    expect(localStorage.getItem('refresh_token')).toBe(null)
    expect(useAuthStore.getState().isAuthenticated).toBe(false)
  })
})
