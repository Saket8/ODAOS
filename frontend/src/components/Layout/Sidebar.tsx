import { useState, useEffect } from 'react'
import { Plus, Search, MessageSquare, Trash2, PanelLeftClose } from 'lucide-react'

const API_BASE = 'http://localhost:8000'

interface Session {
    id: string
    title: string
    preview?: string
    updatedAt: string
    bookmarked: boolean
}

interface SidebarProps {
    currentSessionId: string | null
    onSessionSelect: (id: string) => void
    onNewSession: () => void
    onClose?: () => void
}

export default function Sidebar({ currentSessionId, onSessionSelect, onNewSession, onClose }: SidebarProps) {
    const [sessions, setSessions] = useState<Session[]>([])
    const [search, setSearch] = useState('')
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        fetchSessions()
    }, [])

    const fetchSessions = async () => {
        try {
            const response = await fetch(`${API_BASE}/api/sessions/`)
            if (response.ok) {
                const data = await response.json()
                setSessions(data.sessions || [])
            }
        } catch (error) {
            console.error('Failed to fetch sessions:', error)
        } finally {
            setLoading(false)
        }
    }

    const filteredSessions = sessions.filter(s =>
        s.title.toLowerCase().includes(search.toLowerCase())
    )

    const handleDelete = async (e: React.MouseEvent, sessionId: string) => {
        e.stopPropagation()
        try {
            await fetch(`${API_BASE}/api/sessions/${sessionId}`, { method: 'DELETE' })
            setSessions(sessions.filter(s => s.id !== sessionId))
            if (currentSessionId === sessionId) {
                onNewSession()
            }
        } catch (error) {
            console.error('Failed to delete session:', error)
        }
    }

    return (
        <div className="h-full flex flex-col bg-[var(--bg-sidebar)]">
            {/* Top actions */}
            <div className="p-2 flex items-center gap-1">
                {onClose && (
                    <button
                        onClick={onClose}
                        className="p-2 rounded-lg hover:bg-[var(--bg-hover)] transition-colors"
                        title="Close sidebar"
                    >
                        <PanelLeftClose size={18} className="text-[var(--text-secondary)]" />
                    </button>
                )}
                <div className="flex-1" />
                <button
                    onClick={onNewSession}
                    className="p-2 rounded-lg hover:bg-[var(--bg-hover)] transition-colors"
                    title="New chat"
                >
                    <Plus size={18} className="text-[var(--text-secondary)]" />
                </button>
            </div>

            {/* Search */}
            <div className="px-3 pb-2">
                <div className="relative">
                    <Search size={14} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-[var(--text-muted)]" />
                    <input
                        type="text"
                        value={search}
                        onChange={(e) => setSearch(e.target.value)}
                        placeholder="Search..."
                        className="w-full pl-8 pr-3 py-1.5 bg-[var(--bg-secondary)] border-none rounded-lg text-xs text-[var(--text-primary)] placeholder:text-[var(--text-muted)] focus:outline-none focus:ring-1 focus:ring-[var(--border-primary)]"
                    />
                </div>
            </div>

            {/* Session List */}
            <div className="flex-1 overflow-y-auto px-2">
                {loading ? (
                    <div className="space-y-1 p-1">
                        {[1, 2, 3].map((i) => (
                            <div key={i} className="skeleton h-10 w-full" />
                        ))}
                    </div>
                ) : filteredSessions.length === 0 ? (
                    <div className="text-center py-8 text-[var(--text-muted)] text-xs">
                        {sessions.length === 0 ? 'No conversations yet' : 'No results'}
                    </div>
                ) : (
                    <div className="space-y-0.5 py-1">
                        {filteredSessions.map((session) => (
                            <div
                                key={session.id}
                                onClick={() => onSessionSelect(session.id)}
                                className={`group relative flex items-center gap-2 px-3 py-2.5 rounded-lg cursor-pointer transition-colors text-sm ${session.id === currentSessionId
                                        ? 'bg-[var(--bg-hover)] text-[var(--text-primary)]'
                                        : 'text-[var(--text-secondary)] hover:bg-[var(--bg-hover)]'
                                    }`}
                            >
                                <MessageSquare size={14} className="flex-shrink-0 opacity-50" />
                                <span className="truncate flex-1 text-[13px]">{session.title}</span>
                                <button
                                    onClick={(e) => handleDelete(e, session.id)}
                                    className="opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-[var(--bg-tertiary)] transition-all"
                                >
                                    <Trash2 size={13} className="text-[var(--text-muted)]" />
                                </button>
                            </div>
                        ))}
                    </div>
                )}
            </div>

            {/* Footer */}
            <div className="p-3 border-t border-[var(--border-subtle)]">
                <div className="text-[11px] text-[var(--text-muted)] text-center">
                    {sessions.length} conversation{sessions.length !== 1 ? 's' : ''}
                </div>
            </div>
        </div>
    )
}
