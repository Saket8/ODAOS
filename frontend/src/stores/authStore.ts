// Auth store — manages Basic Auth token for prompt library access

import { create } from 'zustand'

const API_BASE = 'http://localhost:8000'

interface AuthState {
    isAuthenticated: boolean
    username: string | null
    token: string | null
    isLoading: boolean
    error: string | null
    login: (username: string, password: string) => Promise<boolean>
    logout: () => void
    verifyToken: () => Promise<boolean>
    getAuthHeaders: () => Record<string, string>
}

export const useAuthStore = create<AuthState>((set, get) => ({
    isAuthenticated: false,
    username: null,
    token: localStorage.getItem('odaos_token'),
    isLoading: false,
    error: null,

    login: async (username: string, password: string) => {
        set({ isLoading: true, error: null })
        try {
            const token = btoa(`${username}:${password}`)
            const response = await fetch(`${API_BASE}/api/auth/login`, {
                method: 'POST',
                headers: { Authorization: `Basic ${token}` },
            })

            if (!response.ok) {
                const data = await response.json().catch(() => ({ detail: 'Login failed' }))
                set({ isLoading: false, error: data.detail || 'Invalid credentials' })
                return false
            }

            const data = await response.json()
            localStorage.setItem('odaos_token', data.token)
            set({
                isAuthenticated: true,
                username: data.username,
                token: data.token,
                isLoading: false,
                error: null,
            })
            return true
        } catch (err) {
            set({ isLoading: false, error: 'Connection failed' })
            return false
        }
    },

    logout: () => {
        localStorage.removeItem('odaos_token')
        set({ isAuthenticated: false, username: null, token: null, error: null })
    },

    verifyToken: async () => {
        const { token } = get()
        if (!token) return false

        try {
            const response = await fetch(`${API_BASE}/api/auth/verify`, {
                headers: { Authorization: `Basic ${token}` },
            })
            if (response.ok) {
                const data = await response.json()
                set({ isAuthenticated: true, username: data.username })
                return true
            } else {
                localStorage.removeItem('odaos_token')
                set({ isAuthenticated: false, username: null, token: null })
                return false
            }
        } catch {
            return false
        }
    },

    getAuthHeaders: () => {
        const { token } = get()
        return token ? { Authorization: `Basic ${token}` } : {}
    },
}))
