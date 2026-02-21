// Prompt Library Store — state management for prompts, categories, favorites, history

import { create } from 'zustand'
import { useAuthStore } from './authStore'

const API_BASE = 'http://localhost:8000'

// ============================================================================
// Types
// ============================================================================

export interface PromptParameter {
    name: string
    type: string
    description: string
    required: boolean
    default?: any
    enum_values?: string[]
}

export interface PromptSummary {
    id: string
    category: string
    title: string
    description: string
    tags: string[]
    difficulty_level: string
    estimated_runtime: string
    usage_count: number
    is_favorited: boolean
}

export interface Prompt extends PromptSummary {
    prompt_template: string
    parameters: PromptParameter[]
    default_values: Record<string, any>
    expected_output: string | null
    requires_approval: boolean
    is_active: boolean
    average_runtime: number | null
    created_at: string
    updated_at: string
}

export interface PromptCategory {
    id: string
    name: string
    display_name: string
    description: string | null
    icon: string
    prompt_count: number
}

export interface PromptHistoryEntry {
    id: string
    prompt_id: string
    prompt_title: string
    parameters_used: Record<string, any>
    executed_at: string
    execution_time_ms: number
    status: string
    result_summary: string | null
}

// ============================================================================
// Store
// ============================================================================

interface PromptLibraryState {
    // Data
    prompts: PromptSummary[]
    categories: PromptCategory[]
    favorites: PromptSummary[]
    history: PromptHistoryEntry[]
    selectedPrompt: Prompt | null
    total: number

    // Filters
    activeCategory: string | null
    searchQuery: string
    activeDifficulty: string | null
    activeTag: string | null
    page: number
    perPage: number

    // UI
    isLoading: boolean
    isExecuting: boolean
    executionOutput: string
    executionChartData: any | null
    error: string | null
    view: 'grid' | 'list'

    // Actions
    fetchPrompts: () => Promise<void>
    fetchCategories: () => Promise<void>
    fetchFavorites: () => Promise<void>
    fetchHistory: () => Promise<void>
    selectPrompt: (id: string) => Promise<void>
    clearSelectedPrompt: () => void
    toggleFavorite: (promptId: string) => Promise<void>
    executePrompt: (promptId: string, parameters: Record<string, any>, sessionId?: string, customQuery?: string) => Promise<void>
    setCategory: (category: string | null) => void
    setSearch: (query: string) => void
    setDifficulty: (difficulty: string | null) => void
    setTag: (tag: string | null) => void
    setPage: (page: number) => void
    setView: (view: 'grid' | 'list') => void
    resetFilters: () => void
}

function getHeaders(): Record<string, string> {
    return useAuthStore.getState().getAuthHeaders()
}

export const usePromptStore = create<PromptLibraryState>((set, get) => ({
    // Data defaults
    prompts: [],
    categories: [],
    favorites: [],
    history: [],
    selectedPrompt: null,
    total: 0,

    // Filter defaults
    activeCategory: null,
    searchQuery: '',
    activeDifficulty: null,
    activeTag: null,
    page: 1,
    perPage: 20,

    // UI defaults
    isLoading: false,
    isExecuting: false,
    executionOutput: '',
    executionChartData: null,
    error: null,
    view: 'grid',

    // ========================================================================
    // Data Fetching
    // ========================================================================

    fetchPrompts: async () => {
        const { activeCategory, searchQuery, activeDifficulty, activeTag, page, perPage } = get()
        set({ isLoading: true, error: null })

        try {
            const params = new URLSearchParams()
            if (activeCategory) params.set('category', activeCategory)
            if (searchQuery) params.set('search', searchQuery)
            if (activeDifficulty) params.set('difficulty', activeDifficulty)
            if (activeTag) params.set('tag', activeTag)
            params.set('page', String(page))
            params.set('per_page', String(perPage))

            const response = await fetch(`${API_BASE}/api/prompts?${params}`, {
                headers: getHeaders(),
            })

            if (!response.ok) throw new Error('Failed to fetch prompts')

            const data = await response.json()
            set({
                prompts: data.prompts,
                total: data.total,
                isLoading: false,
            })
        } catch (err) {
            set({ isLoading: false, error: (err as Error).message })
        }
    },

    fetchCategories: async () => {
        try {
            const response = await fetch(`${API_BASE}/api/prompts/categories`, {
                headers: getHeaders(),
            })
            if (!response.ok) throw new Error('Failed to fetch categories')
            const data = await response.json()
            set({ categories: data })
        } catch (err) {
            console.error('Failed to fetch categories:', err)
        }
    },

    fetchFavorites: async () => {
        try {
            const response = await fetch(`${API_BASE}/api/prompts/favorites`, {
                headers: getHeaders(),
            })
            if (!response.ok) throw new Error('Failed to fetch favorites')
            const data = await response.json()
            set({ favorites: data })
        } catch (err) {
            console.error('Failed to fetch favorites:', err)
        }
    },

    fetchHistory: async () => {
        try {
            const response = await fetch(`${API_BASE}/api/prompts/history`, {
                headers: getHeaders(),
            })
            if (!response.ok) throw new Error('Failed to fetch history')
            const data = await response.json()
            set({ history: data.entries || [] })
        } catch (err) {
            console.error('Failed to fetch history:', err)
        }
    },

    // ========================================================================
    // Single prompt
    // ========================================================================

    selectPrompt: async (id: string) => {
        set({ isLoading: true, error: null, executionOutput: '' })
        try {
            const response = await fetch(`${API_BASE}/api/prompts/${id}`, {
                headers: getHeaders(),
            })
            if (!response.ok) throw new Error('Prompt not found')
            const data = await response.json()
            set({ selectedPrompt: data, isLoading: false })
        } catch (err) {
            set({ isLoading: false, error: (err as Error).message })
        }
    },

    clearSelectedPrompt: () => set({ selectedPrompt: null, executionOutput: '', executionChartData: null }),

    // ========================================================================
    // Favorites
    // ========================================================================

    toggleFavorite: async (promptId: string) => {
        try {
            const response = await fetch(`${API_BASE}/api/prompts/${promptId}/favorite`, {
                method: 'POST',
                headers: getHeaders(),
            })
            if (!response.ok) throw new Error('Failed to toggle favorite')
            const data = await response.json()

            // Update prompts list
            set((state) => ({
                prompts: state.prompts.map((p) =>
                    p.id === promptId ? { ...p, is_favorited: data.favorited } : p
                ),
                selectedPrompt:
                    state.selectedPrompt?.id === promptId
                        ? { ...state.selectedPrompt, is_favorited: data.favorited }
                        : state.selectedPrompt,
            }))

            // Refresh favorites
            get().fetchFavorites()
        } catch (err) {
            console.error('Failed to toggle favorite:', err)
        }
    },

    // ========================================================================
    // Execution
    // ========================================================================

    executePrompt: async (promptId: string, parameters: Record<string, any>, sessionId?: string, customQuery?: string) => {
        set({ isExecuting: true, executionOutput: '', executionChartData: null, error: null })

        try {
            const response = await fetch(`${API_BASE}/api/prompts/${promptId}/execute`, {
                method: 'POST',
                headers: {
                    ...getHeaders(),
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    parameters,
                    session_id: sessionId,
                    ...(customQuery ? { custom_query: customQuery } : {}),
                }),
            })

            if (!response.ok) {
                const err = await response.json().catch(() => ({ detail: 'Execution failed' }))
                throw new Error(err.detail || 'Execution failed')
            }

            // Parse SSE stream
            const reader = response.body!.getReader()
            const decoder = new TextDecoder()
            let buffer = ''

            while (true) {
                const { done, value } = await reader.read()
                if (done) break

                buffer += decoder.decode(value, { stream: true })
                const lines = buffer.split('\n')
                buffer = lines.pop() || ''

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        try {
                            const event = JSON.parse(line.slice(6))
                            if (event.content) {
                                set((state) => ({
                                    executionOutput: state.executionOutput + event.content,
                                }))
                            }
                            if (event.type === 'done') {
                                set({ isExecuting: false })
                                // Refresh history
                                get().fetchHistory()
                                return
                            }
                            if (event.type === 'error') {
                                set({ isExecuting: false, error: event.message })
                                return
                            }
                            if (event.type === 'chart' && event.data) {
                                set({ executionChartData: event.data })
                            }
                        } catch {
                            // Skip malformed events
                        }
                    }
                }
            }

            set({ isExecuting: false })
        } catch (err) {
            set({ isExecuting: false, error: (err as Error).message })
        }
    },

    // ========================================================================
    // Filters
    // ========================================================================

    setCategory: (category) => {
        set({ activeCategory: category, page: 1 })
        get().fetchPrompts()
    },

    setSearch: (query) => {
        set({ searchQuery: query, page: 1 })
        // Debounce is handled in the component
    },

    setDifficulty: (difficulty) => {
        set({ activeDifficulty: difficulty, page: 1 })
        get().fetchPrompts()
    },

    setTag: (tag) => {
        set({ activeTag: tag, page: 1 })
        get().fetchPrompts()
    },

    setPage: (page) => {
        set({ page })
        get().fetchPrompts()
    },

    setView: (view) => set({ view }),

    resetFilters: () => {
        set({
            activeCategory: null,
            searchQuery: '',
            activeDifficulty: null,
            activeTag: null,
            page: 1,
        })
        get().fetchPrompts()
    },
}))
