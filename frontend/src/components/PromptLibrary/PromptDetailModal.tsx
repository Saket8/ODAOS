import { useState, useEffect } from 'react'
import { X, Play, Star, Copy, Check, Loader2 } from 'lucide-react'
import { usePromptStore } from '../../stores/promptStore'
import type { Prompt, PromptParameter } from '../../stores/promptStore'

function capitalize(s: string): string {
    return s.charAt(0).toUpperCase() + s.slice(1)
}

export default function PromptDetailModal({
    prompt,
    onClose,
}: {
    prompt: Prompt
    onClose: () => void
}) {
    const { isExecuting, executionOutput, error, executePrompt, toggleFavorite } =
        usePromptStore()
    const [params, setParams] = useState<Record<string, any>>({})
    const [copied, setCopied] = useState(false)

    useEffect(() => {
        const defaults: Record<string, any> = { ...prompt.default_values }
        prompt.parameters.forEach((p) => {
            if (p.default !== undefined && !(p.name in defaults)) {
                defaults[p.name] = p.default
            }
        })
        setParams(defaults)
    }, [prompt])

    const handleExecute = () => {
        executePrompt(prompt.id, params)
    }

    const handleCopy = () => {
        let text = prompt.prompt_template
        for (const [key, value] of Object.entries(params)) {
            text = text.replace(`{${key}}`, String(value))
        }
        navigator.clipboard.writeText(text)
        setCopied(true)
        setTimeout(() => setCopied(false), 2000)
    }

    const renderInput = (param: PromptParameter) => {
        const value = params[param.name] ?? param.default ?? ''
        const baseClass = "w-full px-3 py-1.5 rounded-lg bg-[var(--bg-primary)] border border-[var(--border-subtle)] text-[13px] text-[var(--text-primary)] focus:outline-none focus:border-[var(--text-muted)] transition-colors"

        if (param.type === 'enum' && param.enum_values) {
            return (
                <select
                    value={value}
                    onChange={(e) => setParams({ ...params, [param.name]: e.target.value })}
                    className={baseClass}
                >
                    {param.enum_values.map((v) => (
                        <option key={v} value={v}>{v}</option>
                    ))}
                </select>
            )
        }

        if (param.type === 'integer' || param.type === 'number') {
            return (
                <input
                    type="number"
                    value={value}
                    onChange={(e) => setParams({ ...params, [param.name]: Number(e.target.value) })}
                    className={baseClass}
                />
            )
        }

        return (
            <input
                type="text"
                value={value}
                onChange={(e) => setParams({ ...params, [param.name]: e.target.value })}
                placeholder={param.description}
                className={`${baseClass} placeholder:text-[var(--text-muted)]`}
            />
        )
    }

    let preview = prompt.prompt_template
    for (const [key, value] of Object.entries(params)) {
        preview = preview.replace(`{${key}}`, String(value))
    }

    return (
        <div
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/40"
            onClick={onClose}
        >
            <div
                onClick={(e) => e.stopPropagation()}
                className="relative w-full max-w-lg max-h-[80vh] mx-4 bg-[var(--bg-primary)] border border-[var(--border-primary)] rounded-xl shadow-xl flex flex-col overflow-hidden"
            >
                {/* Header */}
                <div className="flex items-start justify-between px-5 pt-5 pb-3">
                    <div className="flex-1 min-w-0 pr-3">
                        <div className="flex items-center gap-2 mb-1 text-[11px] text-[var(--text-muted)]">
                            <span className={
                                prompt.difficulty_level === 'beginner' ? 'text-emerald-500' :
                                    prompt.difficulty_level === 'intermediate' ? 'text-amber-500' :
                                        'text-rose-500'
                            }>
                                {capitalize(prompt.difficulty_level)}
                            </span>
                            <span className="opacity-40">·</span>
                            <span>{prompt.estimated_runtime}</span>
                            {prompt.requires_approval && (
                                <>
                                    <span className="opacity-40">·</span>
                                    <span className="text-amber-500">Needs Approval</span>
                                </>
                            )}
                        </div>
                        <h2 className="text-base font-semibold text-[var(--text-primary)] leading-snug">{prompt.title}</h2>
                        <p className="text-xs text-[var(--text-muted)] mt-1 leading-relaxed">{prompt.description}</p>
                    </div>
                    <div className="flex items-center gap-0.5 flex-shrink-0">
                        <button
                            onClick={() => toggleFavorite(prompt.id)}
                            className="p-1.5 rounded-md hover:bg-[var(--bg-hover)] transition-colors"
                        >
                            <Star
                                size={15}
                                className={prompt.is_favorited ? 'fill-amber-400 text-amber-400' : 'text-[var(--text-muted)]'}
                            />
                        </button>
                        <button onClick={onClose} className="p-1.5 rounded-md hover:bg-[var(--bg-hover)] transition-colors">
                            <X size={15} className="text-[var(--text-muted)]" />
                        </button>
                    </div>
                </div>

                {/* Body */}
                <div className="flex-1 overflow-y-auto px-5 pb-4 space-y-4">
                    {/* Parameters */}
                    {prompt.parameters.length > 0 && (
                        <div className="space-y-2.5">
                            <h3 className="text-xs font-medium text-[var(--text-secondary)]">Parameters</h3>
                            {prompt.parameters.map((param) => (
                                <div key={param.name}>
                                    <label className="flex items-baseline gap-1.5 text-[12px] text-[var(--text-muted)] mb-1">
                                        <span className="text-[var(--text-secondary)] font-medium">{param.name}</span>
                                        {param.required && <span className="text-rose-500 text-[10px]">required</span>}
                                    </label>
                                    {renderInput(param)}
                                </div>
                            ))}
                        </div>
                    )}

                    {/* Preview */}
                    <div>
                        <div className="flex items-center justify-between mb-1.5">
                            <h3 className="text-xs font-medium text-[var(--text-secondary)]">Query preview</h3>
                            <button
                                onClick={handleCopy}
                                className="flex items-center gap-1 text-[11px] text-[var(--text-muted)] hover:text-[var(--text-secondary)]"
                            >
                                {copied ? <Check size={11} className="text-emerald-500" /> : <Copy size={11} />}
                                {copied ? 'Copied' : 'Copy'}
                            </button>
                        </div>
                        <div className="p-3 rounded-lg bg-[var(--bg-secondary)] text-xs text-[var(--text-secondary)] font-mono whitespace-pre-wrap leading-relaxed border border-[var(--border-subtle)]">
                            {preview}
                        </div>
                    </div>

                    {/* Expected output hint */}
                    {prompt.expected_output && (
                        <p className="text-[11px] text-[var(--text-muted)] leading-relaxed">
                            <span className="font-medium text-[var(--text-secondary)]">Expected: </span>
                            {prompt.expected_output}
                        </p>
                    )}

                    {/* Execution output */}
                    {(executionOutput || isExecuting) && (
                        <div>
                            <h3 className="text-xs font-medium text-[var(--text-secondary)] mb-1.5 flex items-center gap-1.5">
                                Output
                                {isExecuting && <Loader2 size={11} className="animate-spin" />}
                            </h3>
                            <div className="p-3 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border-subtle)] max-h-52 overflow-y-auto">
                                <pre className="text-xs text-[var(--text-primary)] whitespace-pre-wrap font-mono leading-relaxed">
                                    {executionOutput || 'Running...'}
                                </pre>
                            </div>
                        </div>
                    )}

                    {error && (
                        <p className="text-xs text-rose-500 px-3 py-2 rounded-lg bg-rose-500/5 border border-rose-500/10">
                            {error}
                        </p>
                    )}
                </div>

                {/* Footer */}
                <div className="px-5 py-3 border-t border-[var(--border-subtle)] flex items-center justify-end gap-2">
                    <button
                        onClick={onClose}
                        className="px-3 py-1.5 rounded-lg text-[13px] text-[var(--text-secondary)] hover:bg-[var(--bg-hover)] transition-colors"
                    >
                        Close
                    </button>
                    <button
                        onClick={handleExecute}
                        disabled={isExecuting}
                        className="px-4 py-1.5 rounded-lg bg-[var(--text-primary)] text-[var(--bg-primary)] text-[13px] font-medium flex items-center gap-1.5 hover:opacity-90 disabled:opacity-40 transition-all"
                    >
                        {isExecuting ? (
                            <Loader2 size={13} className="animate-spin" />
                        ) : (
                            <Play size={13} />
                        )}
                        {isExecuting ? 'Running...' : 'Execute'}
                    </button>
                </div>
            </div>
        </div>
    )
}
