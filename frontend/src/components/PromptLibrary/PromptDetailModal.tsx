import { useState, useEffect, lazy, Suspense } from 'react'
import { X, Play, Star, Copy, Check, Loader2 } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { usePromptStore } from '../../stores/promptStore'
import type { Prompt, PromptParameter } from '../../stores/promptStore'

const SmartChart = lazy(() => import('../Charts/SmartChart'))

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
    const { isExecuting, executionOutput, executionChartData, error, executePrompt, toggleFavorite } =
        usePromptStore()
    const [params, setParams] = useState<Record<string, any>>({})
    const [copied, setCopied] = useState(false)
    const [editedQuery, setEditedQuery] = useState('')

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
        // Compute the default preview to compare
        let defaultPreview = prompt.prompt_template
        for (const [key, value] of Object.entries(params)) {
            defaultPreview = defaultPreview.replace(`{${key}}`, String(value))
        }
        // If user edited the query, send as customQuery
        const customQuery = editedQuery !== defaultPreview ? editedQuery : undefined
        executePrompt(prompt.id, params, undefined, customQuery)
    }

    const handleCopy = () => {
        navigator.clipboard.writeText(editedQuery)
        setCopied(true)
        setTimeout(() => setCopied(false), 2000)
    }

    const renderInput = (param: PromptParameter) => {
        const value = params[param.name] ?? param.default ?? ''
        const baseClass = "w-full px-4 py-2.5 rounded-lg bg-[var(--bg-primary)] border border-[var(--border-subtle)] text-sm text-[var(--text-primary)] focus:outline-none focus:border-[var(--text-muted)] transition-colors"

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

    // Compute template preview and sync editedQuery when params change
    let preview = prompt.prompt_template
    for (const [key, value] of Object.entries(params)) {
        preview = preview.replace(`{${key}}`, String(value))
    }

    useEffect(() => {
        setEditedQuery(preview)
    }, [preview])

    const isQueryEdited = editedQuery !== preview

    return (
        <div
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/40"
            onClick={onClose}
        >
            <div
                onClick={(e) => e.stopPropagation()}
                className="relative w-full max-w-4xl max-h-[90vh] mx-4 bg-[var(--bg-primary)] border border-[var(--border-primary)] rounded-xl shadow-xl flex flex-col overflow-hidden"
            >
                {/* Header */}
                <div className="flex items-start justify-between px-8 pt-6 pb-4">
                    <div className="flex-1 min-w-0 pr-4">
                        <div className="flex items-center gap-2 mb-1.5 text-xs text-[var(--text-muted)]">
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
                        <h2 className="text-xl font-semibold text-[var(--text-primary)] leading-snug">{prompt.title}</h2>
                        <p className="text-sm text-[var(--text-muted)] mt-1.5 leading-relaxed">{prompt.description}</p>
                    </div>
                    <div className="flex items-center gap-0.5 flex-shrink-0">
                        <button
                            onClick={() => toggleFavorite(prompt.id)}
                            className="p-1.5 rounded-md hover:bg-[var(--bg-hover)] transition-colors"
                        >
                            <Star
                                size={18}
                                className={prompt.is_favorited ? 'fill-amber-400 text-amber-400' : 'text-[var(--text-muted)]'}
                            />
                        </button>
                        <button onClick={onClose} className="p-1.5 rounded-md hover:bg-[var(--bg-hover)] transition-colors">
                            <X size={18} className="text-[var(--text-muted)]" />
                        </button>
                    </div>
                </div>

                {/* Body */}
                <div className="flex-1 overflow-y-auto px-8 pb-6 space-y-5">
                    {/* Parameters */}
                    {prompt.parameters.length > 0 && (
                        <div className="space-y-3">
                            <h3 className="text-sm font-medium text-[var(--text-secondary)]">Parameters</h3>
                            {prompt.parameters.map((param) => (
                                <div key={param.name}>
                                    <label className="flex items-baseline gap-1.5 text-[13px] text-[var(--text-muted)] mb-1.5">
                                        <span className="text-[var(--text-secondary)] font-medium">{param.name}</span>
                                        {param.required && <span className="text-rose-500 text-[11px]">required</span>}
                                    </label>
                                    {renderInput(param)}
                                </div>
                            ))}
                        </div>
                    )}

                    {/* Preview */}
                    <div>
                        <div className="flex items-center justify-between mb-1.5">
                            <div className="flex items-center gap-2">
                                <h3 className="text-sm font-medium text-[var(--text-secondary)]">Query preview</h3>
                                {isQueryEdited && (
                                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-amber-500/10 text-amber-500 font-medium">edited</span>
                                )}
                            </div>
                            <div className="flex items-center gap-2">
                                {isQueryEdited && (
                                    <button
                                        onClick={() => setEditedQuery(preview)}
                                        className="flex items-center gap-1 text-[11px] text-amber-500 hover:text-amber-400"
                                    >
                                        Reset
                                    </button>
                                )}
                                <button
                                    onClick={handleCopy}
                                    className="flex items-center gap-1 text-[11px] text-[var(--text-muted)] hover:text-[var(--text-secondary)]"
                                >
                                    {copied ? <Check size={11} className="text-emerald-500" /> : <Copy size={11} />}
                                    {copied ? 'Copied' : 'Copy'}
                                </button>
                            </div>
                        </div>
                        <textarea
                            value={editedQuery}
                            onChange={(e) => setEditedQuery(e.target.value)}
                            rows={6}
                            className="w-full p-4 rounded-lg bg-[var(--bg-secondary)] text-sm text-[var(--text-secondary)] font-mono leading-relaxed border border-[var(--border-subtle)] focus:outline-none focus:border-[var(--text-muted)] transition-colors resize-y"
                        />
                    </div>

                    {/* Expected output hint */}
                    {prompt.expected_output && (
                        <p className="text-xs text-[var(--text-muted)] leading-relaxed">
                            <span className="font-medium text-[var(--text-secondary)]">Expected: </span>
                            {prompt.expected_output}
                        </p>
                    )}

                    {/* Chart visualization */}
                    {executionChartData && (
                        <Suspense fallback={
                            <div className="h-48 flex items-center justify-center text-sm text-[var(--text-muted)]">
                                Loading visualization...
                            </div>
                        }>
                            <div className="border border-[var(--border-subtle)] rounded-lg overflow-hidden">
                                <SmartChart
                                    id={executionChartData.id || 'prompt-chart'}
                                    type={executionChartData.chart?.chart_type || executionChartData.type || executionChartData.chart_type || 'bar'}
                                    title={executionChartData.chart?.title || executionChartData.title || prompt.title}
                                    data={executionChartData.chart?.data || executionChartData.data || []}
                                    layout={executionChartData.chart?.layout || executionChartData.layout}
                                    narrative={executionChartData.narrative}
                                    drillDownOptions={executionChartData.drill_down_options || executionChartData.drillDownOptions}
                                />
                            </div>
                        </Suspense>
                    )}

                    {/* Execution output — rendered with Markdown */}
                    {(executionOutput || isExecuting) && (
                        <div>
                            <h3 className="text-sm font-medium text-[var(--text-secondary)] mb-2 flex items-center gap-2">
                                Output
                                {isExecuting && <Loader2 size={14} className="animate-spin" />}
                            </h3>
                            <div className="p-5 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border-subtle)] max-h-[400px] overflow-y-auto">
                                <div className="prose prose-base dark:prose-invert max-w-none text-[var(--text-primary)]">
                                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                                        {executionOutput || 'Running...'}
                                    </ReactMarkdown>
                                </div>
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
                <div className="px-8 py-4 border-t border-[var(--border-subtle)] flex items-center justify-end gap-3">
                    <button
                        onClick={onClose}
                        className="px-4 py-2 rounded-lg text-sm text-[var(--text-secondary)] hover:bg-[var(--bg-hover)] transition-colors"
                    >
                        Close
                    </button>
                    <button
                        onClick={handleExecute}
                        disabled={isExecuting}
                        className="px-5 py-2 rounded-lg bg-[var(--text-primary)] text-[var(--bg-primary)] text-sm font-medium flex items-center gap-2 hover:opacity-90 disabled:opacity-40 transition-all"
                    >
                        {isExecuting ? (
                            <Loader2 size={15} className="animate-spin" />
                        ) : (
                            <Play size={15} />
                        )}
                        {isExecuting ? 'Running...' : 'Execute'}
                    </button>
                </div>
            </div>
        </div>
    )
}
