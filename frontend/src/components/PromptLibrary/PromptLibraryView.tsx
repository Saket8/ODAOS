import { useEffect, useState, useCallback } from 'react'
import {
    Search,
    Star,
    History,
    RefreshCw,
    X,
    ChevronLeft,
    LogOut,
    Loader2,
    Sun,
    Moon,
} from 'lucide-react'
import { usePromptStore } from '../../stores/promptStore'
import { useAuthStore } from '../../stores/authStore'
import { useTheme } from '../../hooks/useTheme'
import PromptCard from './PromptCard'
import PromptDetailModal from './PromptDetailModal'
import { useNavigate } from 'react-router-dom'

function capitalize(s: string): string {
    return s.charAt(0).toUpperCase() + s.slice(1)
}

export default function PromptLibraryView() {
    const navigate = useNavigate()
    const { darkMode, toggleTheme } = useTheme()
    const { username, logout } = useAuthStore()
    const {
        prompts,
        categories,
        favorites,
        history,
        selectedPrompt,
        total,
        activeCategory,
        searchQuery,
        activeDifficulty,
        page,
        perPage,
        isLoading,
        fetchPrompts,
        fetchCategories,
        fetchFavorites,
        fetchHistory,
        selectPrompt,
        clearSelectedPrompt,
        setCategory,
        setSearch,
        setDifficulty,
        setPage,
        resetFilters,
    } = usePromptStore()

    const [searchInput, setSearchInput] = useState(searchQuery)
    const [activeTab, setActiveTab] = useState<'all' | 'favorites' | 'history'>('all')

    useEffect(() => {
        fetchPrompts()
        fetchCategories()
        fetchFavorites()
        fetchHistory()
    }, [])

    const debouncedSearch = useCallback(
        debounce((query: string) => {
            setSearch(query)
            fetchPrompts()
        }, 300),
        []
    )

    const handleSearchChange = (value: string) => {
        setSearchInput(value)
        debouncedSearch(value)
    }

    const handleLogout = () => {
        logout()
        navigate('/')
    }

    const totalPages = Math.ceil(total / perPage)

    // Split categories into BRM and DBA groups
    const brmCategories = categories.filter((c) => c.name.startsWith('BRM_'))
    const dbaCategories = categories.filter((c) => c.name.startsWith('DBA_'))

    return (
        <div className="flex h-full bg-[var(--bg-primary)]">
            {/* Left nav */}
            <div className="w-48 flex-shrink-0 border-r border-[var(--border-subtle)] bg-[var(--bg-sidebar)] flex flex-col">
                {/* Back */}
                <div className="p-3">
                    <button
                        onClick={() => navigate('/')}
                        className="flex items-center gap-1.5 text-xs text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-colors"
                    >
                        <ChevronLeft size={14} />
                        Back to chat
                    </button>
                </div>

                {/* Nav tabs */}
                <div className="px-2 space-y-px">
                    <button
                        onClick={() => { setActiveTab('all'); setCategory(null); }}
                        className={`w-full flex items-center justify-between px-3 py-2 rounded-lg text-[13px] transition-colors ${activeTab === 'all' && !activeCategory
                            ? 'bg-[var(--bg-hover)] text-[var(--text-primary)] font-medium'
                            : 'text-[var(--text-secondary)] hover:bg-[var(--bg-hover)]'
                            }`}
                    >
                        All Prompts
                        <span className="text-[11px] text-[var(--text-muted)] tabular-nums">{total}</span>
                    </button>
                    <button
                        onClick={() => setActiveTab('favorites')}
                        className={`w-full flex items-center justify-between px-3 py-2 rounded-lg text-[13px] transition-colors ${activeTab === 'favorites'
                            ? 'bg-[var(--bg-hover)] text-[var(--text-primary)] font-medium'
                            : 'text-[var(--text-secondary)] hover:bg-[var(--bg-hover)]'
                            }`}
                    >
                        <span className="flex items-center gap-2"><Star size={13} /> Favorites</span>
                        <span className="text-[11px] text-[var(--text-muted)] tabular-nums">{favorites.length}</span>
                    </button>
                    <button
                        onClick={() => setActiveTab('history')}
                        className={`w-full flex items-center justify-between px-3 py-2 rounded-lg text-[13px] transition-colors ${activeTab === 'history'
                            ? 'bg-[var(--bg-hover)] text-[var(--text-primary)] font-medium'
                            : 'text-[var(--text-secondary)] hover:bg-[var(--bg-hover)]'
                            }`}
                    >
                        <span className="flex items-center gap-2"><History size={13} /> History</span>
                        <span className="text-[11px] text-[var(--text-muted)] tabular-nums">{history.length}</span>
                    </button>
                </div>

                {/* Categories — grouped by BRM / DBA */}
                {activeTab === 'all' && categories.length > 0 && (
                    <div className="flex-1 overflow-y-auto mt-3 px-2 border-t border-[var(--border-subtle)] pt-3">
                        {/* BRM Analytics */}
                        {brmCategories.length > 0 && (
                            <>
                                <div className="px-3 pb-1.5 text-[10px] font-medium uppercase tracking-wider text-[var(--text-muted)]">
                                    BRM Analytics
                                </div>
                                {brmCategories.map((cat) => (
                                    <button
                                        key={cat.id}
                                        onClick={() => { setActiveTab('all'); setCategory(cat.name); }}
                                        className={`w-full flex items-center justify-between px-3 py-1.5 rounded-lg text-[13px] transition-colors ${activeCategory === cat.name
                                            ? 'bg-[var(--bg-hover)] text-[var(--text-primary)] font-medium'
                                            : 'text-[var(--text-secondary)] hover:bg-[var(--bg-hover)]'
                                            }`}
                                    >
                                        <span className="truncate">{cat.display_name}</span>
                                        <span className="text-[11px] text-[var(--text-muted)] tabular-nums">{cat.prompt_count}</span>
                                    </button>
                                ))}
                            </>
                        )}

                        {/* DBA */}
                        {dbaCategories.length > 0 && (
                            <>
                                <div className="px-3 pt-3 pb-1.5 text-[10px] font-medium uppercase tracking-wider text-[var(--text-muted)]">
                                    DBA
                                </div>
                                {dbaCategories.map((cat) => (
                                    <button
                                        key={cat.id}
                                        onClick={() => { setActiveTab('all'); setCategory(cat.name); }}
                                        className={`w-full flex items-center justify-between px-3 py-1.5 rounded-lg text-[13px] transition-colors ${activeCategory === cat.name
                                            ? 'bg-[var(--bg-hover)] text-[var(--text-primary)] font-medium'
                                            : 'text-[var(--text-secondary)] hover:bg-[var(--bg-hover)]'
                                            }`}
                                    >
                                        <span className="truncate">{cat.display_name}</span>
                                        <span className="text-[11px] text-[var(--text-muted)] tabular-nums">{cat.prompt_count}</span>
                                    </button>
                                ))}
                            </>
                        )}
                    </div>
                )}

                {/* User + theme */}
                <div className="p-3 mt-auto border-t border-[var(--border-subtle)] space-y-2">
                    <div className="flex items-center justify-between">
                        <button
                            onClick={toggleTheme}
                            className="flex items-center gap-1.5 px-2 py-1 rounded-md text-[11px] text-[var(--text-muted)] hover:bg-[var(--bg-hover)] hover:text-[var(--text-primary)] transition-colors"
                            title={darkMode ? 'Switch to light mode' : 'Switch to dark mode'}
                        >
                            {darkMode ? <Sun size={12} /> : <Moon size={12} />}
                            {darkMode ? 'Light' : 'Dark'}
                        </button>
                        <button
                            onClick={handleLogout}
                            className="p-1 rounded hover:bg-[var(--bg-hover)] hover:text-red-400 transition-colors"
                            title="Sign out"
                        >
                            <LogOut size={12} />
                        </button>
                    </div>
                    <div className="text-[11px] text-[var(--text-muted)] truncate">
                        {username}
                    </div>
                </div>
            </div>

            {/* Main */}
            <div className="flex-1 flex flex-col min-w-0">
                {/* Toolbar */}
                <div className="px-5 py-2.5 border-b border-[var(--border-subtle)] flex items-center gap-3">
                    {/* Search */}
                    <div className="relative flex-1 max-w-sm">
                        <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-muted)]" />
                        <input
                            type="text"
                            value={searchInput}
                            onChange={(e) => handleSearchChange(e.target.value)}
                            placeholder="Search prompts..."
                            className="w-full pl-9 pr-8 py-1.5 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border-subtle)] text-[13px] text-[var(--text-primary)] placeholder:text-[var(--text-muted)] focus:outline-none focus:border-[var(--text-muted)] transition-colors"
                        />
                        {searchInput && (
                            <button
                                onClick={() => handleSearchChange('')}
                                className="absolute right-2.5 top-1/2 -translate-y-1/2 text-[var(--text-muted)]"
                            >
                                <X size={12} />
                            </button>
                        )}
                    </div>

                    {/* Difficulty pills */}
                    <div className="flex items-center gap-px bg-[var(--bg-secondary)] rounded-lg p-0.5">
                        {(['beginner', 'intermediate', 'advanced'] as const).map((d) => (
                            <button
                                key={d}
                                onClick={() => setDifficulty(activeDifficulty === d ? null : d)}
                                className={`px-2.5 py-1 rounded-md text-[11px] font-medium transition-colors ${activeDifficulty === d
                                    ? 'bg-[var(--bg-primary)] text-[var(--text-primary)] shadow-sm'
                                    : 'text-[var(--text-muted)] hover:text-[var(--text-secondary)]'
                                    }`}
                            >
                                {capitalize(d)}
                            </button>
                        ))}
                    </div>

                    <div className="flex items-center gap-1 ml-auto">
                        {(activeCategory || searchQuery || activeDifficulty) && (
                            <button
                                onClick={resetFilters}
                                className="px-2 py-1 rounded-md text-[11px] text-[var(--text-muted)] hover:text-[var(--text-secondary)] transition-colors"
                            >
                                Clear filters
                            </button>
                        )}
                        <button
                            onClick={() => fetchPrompts()}
                            className="p-1.5 rounded-md hover:bg-[var(--bg-hover)] text-[var(--text-muted)] transition-colors"
                            title="Refresh"
                        >
                            <RefreshCw size={14} />
                        </button>
                    </div>
                </div>

                {/* Content */}
                <div className="flex-1 overflow-y-auto p-5">
                    {activeTab === 'all' && (
                        <>
                            {isLoading ? (
                                <div className="flex items-center justify-center h-48">
                                    <Loader2 className="w-5 h-5 animate-spin text-[var(--text-muted)]" />
                                </div>
                            ) : prompts.length === 0 ? (
                                <div className="flex flex-col items-center justify-center h-48 text-[var(--text-muted)]">
                                    <p className="text-sm">No prompts match your filters</p>
                                    <button
                                        onClick={resetFilters}
                                        className="mt-2 text-xs hover:underline"
                                    >
                                        Clear filters
                                    </button>
                                </div>
                            ) : (
                                <>
                                    <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3">
                                        {prompts.map((prompt) => (
                                            <PromptCard
                                                key={prompt.id}
                                                prompt={prompt}
                                                onSelect={(id) => selectPrompt(id)}
                                            />
                                        ))}
                                    </div>

                                    {totalPages > 1 && (
                                        <div className="flex items-center justify-center gap-3 mt-6 text-[12px] text-[var(--text-muted)]">
                                            <button
                                                onClick={() => setPage(page - 1)}
                                                disabled={page <= 1}
                                                className="hover:text-[var(--text-secondary)] disabled:opacity-30"
                                            >
                                                Previous
                                            </button>
                                            <span className="tabular-nums">{page} / {totalPages}</span>
                                            <button
                                                onClick={() => setPage(page + 1)}
                                                disabled={page >= totalPages}
                                                className="hover:text-[var(--text-secondary)] disabled:opacity-30"
                                            >
                                                Next
                                            </button>
                                        </div>
                                    )}
                                </>
                            )}
                        </>
                    )}

                    {activeTab === 'favorites' && (
                        <div>
                            <h2 className="text-sm font-medium text-[var(--text-primary)] mb-4">Favorites</h2>
                            {favorites.length === 0 ? (
                                <p className="text-sm text-[var(--text-muted)] py-12 text-center">
                                    Star prompts to save them here
                                </p>
                            ) : (
                                <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3">
                                    {favorites.map((prompt) => (
                                        <PromptCard
                                            key={prompt.id}
                                            prompt={prompt}
                                            onSelect={(id) => selectPrompt(id)}
                                        />
                                    ))}
                                </div>
                            )}
                        </div>
                    )}

                    {activeTab === 'history' && (
                        <div>
                            <h2 className="text-sm font-medium text-[var(--text-primary)] mb-4">Run History</h2>
                            {history.length === 0 ? (
                                <p className="text-sm text-[var(--text-muted)] py-12 text-center">
                                    Execute a prompt to see it here
                                </p>
                            ) : (
                                <div className="space-y-1">
                                    {history.map((entry) => (
                                        <div
                                            key={entry.id}
                                            onClick={() => selectPrompt(entry.prompt_id)}
                                            className="flex items-center gap-3 px-3 py-2.5 rounded-lg hover:bg-[var(--bg-secondary)] cursor-pointer transition-colors"
                                        >
                                            <div className="flex-1 min-w-0">
                                                <p className="text-[13px] text-[var(--text-primary)] truncate">
                                                    {entry.prompt_title}
                                                </p>
                                            </div>
                                            <span className={`text-[11px] ${entry.status === 'success' ? 'text-emerald-500' : 'text-rose-500'}`}>
                                                {capitalize(entry.status)}
                                            </span>
                                            <span className="text-[11px] text-[var(--text-muted)] tabular-nums">
                                                {entry.execution_time_ms}ms
                                            </span>
                                            <span className="text-[11px] text-[var(--text-muted)]">
                                                {new Date(entry.executed_at).toLocaleDateString()}
                                            </span>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    )}
                </div>
            </div>

            {selectedPrompt && (
                <PromptDetailModal prompt={selectedPrompt} onClose={clearSelectedPrompt} />
            )}
        </div>
    )
}

function debounce<T extends (...args: any[]) => any>(fn: T, ms: number) {
    let timer: ReturnType<typeof setTimeout>
    return (...args: Parameters<T>) => {
        clearTimeout(timer)
        timer = setTimeout(() => fn(...args), ms)
    }
}
