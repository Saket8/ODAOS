import { useState, useEffect } from 'react'
import { LogIn, Eye, EyeOff, Loader2 } from 'lucide-react'
import { useAuthStore } from '../../stores/authStore'

export default function LoginGate({ children }: { children: React.ReactNode }) {
    const { isAuthenticated, isLoading, error, login, verifyToken } = useAuthStore()
    const [username, setUsername] = useState('')
    const [password, setPassword] = useState('')
    const [showPassword, setShowPassword] = useState(false)
    const [checking, setChecking] = useState(true)

    useEffect(() => {
        verifyToken().finally(() => setChecking(false))
    }, [])

    if (checking) {
        return (
            <div className="flex items-center justify-center h-full bg-[var(--bg-primary)]">
                <Loader2 className="w-5 h-5 animate-spin text-[var(--text-muted)]" />
            </div>
        )
    }

    if (isAuthenticated) return <>{children}</>

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        await login(username, password)
    }

    return (
        <div className="flex items-center justify-center h-full bg-[var(--bg-primary)]">
            <div className="w-full max-w-xs mx-4">
                <div className="text-center mb-6">
                    <h1 className="text-base font-semibold text-[var(--text-primary)]">Prompt Library</h1>
                    <p className="text-xs text-[var(--text-muted)] mt-1">Sign in to continue</p>
                </div>

                <form onSubmit={handleSubmit} className="space-y-3">
                    {error && (
                        <p className="text-xs text-rose-500 text-center">{error}</p>
                    )}

                    <div>
                        <label className="block text-[11px] font-medium text-[var(--text-muted)] mb-1">Username</label>
                        <input
                            type="text"
                            value={username}
                            onChange={(e) => setUsername(e.target.value)}
                            autoFocus
                            className="w-full px-3 py-2 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border-subtle)] text-[13px] text-[var(--text-primary)] focus:outline-none focus:border-[var(--text-muted)] transition-colors"
                        />
                    </div>

                    <div>
                        <label className="block text-[11px] font-medium text-[var(--text-muted)] mb-1">Password</label>
                        <div className="relative">
                            <input
                                type={showPassword ? 'text' : 'password'}
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                className="w-full px-3 py-2 pr-9 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border-subtle)] text-[13px] text-[var(--text-primary)] focus:outline-none focus:border-[var(--text-muted)] transition-colors"
                            />
                            <button
                                type="button"
                                onClick={() => setShowPassword(!showPassword)}
                                className="absolute right-2.5 top-1/2 -translate-y-1/2 text-[var(--text-muted)]"
                            >
                                {showPassword ? <EyeOff size={14} /> : <Eye size={14} />}
                            </button>
                        </div>
                    </div>

                    <button
                        type="submit"
                        disabled={isLoading || !username || !password}
                        className="w-full py-2 rounded-lg bg-[var(--text-primary)] text-[var(--bg-primary)] text-[13px] font-medium flex items-center justify-center gap-1.5 hover:opacity-90 disabled:opacity-40 transition-all"
                    >
                        {isLoading ? <Loader2 size={14} className="animate-spin" /> : <LogIn size={14} />}
                        {isLoading ? 'Signing in...' : 'Sign in'}
                    </button>
                </form>
            </div>
        </div>
    )
}
