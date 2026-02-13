import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Lightbulb, AlertTriangle, TrendingUp, TrendingDown, X, ChevronRight, Sparkles } from 'lucide-react'

interface Insight {
    id: string
    title: string
    description: string
    severity: 'info' | 'warning' | 'critical'
    category: 'performance' | 'anomaly' | 'recommendation' | 'trend'
    action?: string
    relatedQuery?: string
    timestamp: Date
}

interface InsightsPanelProps {
    onInsightClick?: (insight: Insight) => void
    onDismiss?: (id: string) => void
}

export default function InsightsPanel({ onInsightClick, onDismiss }: InsightsPanelProps) {
    const [insights, setInsights] = useState<Insight[]>([])
    const [collapsed, setCollapsed] = useState(false)
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        // Simulate fetching insights from backend
        const fetchInsights = async () => {
            setLoading(true)
            // In production, this would be an API call
            await new Promise(resolve => setTimeout(resolve, 1000))
            setInsights(getSampleInsights())
            setLoading(false)
        }

        fetchInsights()

        // Refresh insights periodically
        const interval = setInterval(fetchInsights, 60000)
        return () => clearInterval(interval)
    }, [])

    const handleDismiss = (id: string) => {
        setInsights(insights.filter(i => i.id !== id))
        onDismiss?.(id)
    }

    const getSeverityIcon = (severity: string) => {
        switch (severity) {
            case 'critical':
                return <AlertTriangle size={16} className="text-[var(--accent-error)]" />
            case 'warning':
                return <AlertTriangle size={16} className="text-[var(--accent-warning)]" />
            default:
                return <Lightbulb size={16} className="text-[var(--accent-primary)]" />
        }
    }

    const getCategoryIcon = (category: string) => {
        switch (category) {
            case 'trend':
                return <TrendingUp size={14} />
            case 'anomaly':
                return <TrendingDown size={14} />
            default:
                return <Sparkles size={14} />
        }
    }

    if (loading) {
        return (
            <div className="glass-panel p-4">
                <div className="flex items-center gap-2 mb-4">
                    <div className="skeleton w-4 h-4 rounded" />
                    <div className="skeleton h-4 w-24" />
                </div>
                <div className="space-y-3">
                    {[1, 2, 3].map((i) => (
                        <div key={i} className="skeleton h-16 w-full rounded-lg" />
                    ))}
                </div>
            </div>
        )
    }

    if (insights.length === 0) {
        return (
            <div className="glass-panel p-4 text-center">
                <Sparkles size={24} className="mx-auto mb-2 text-[var(--text-muted)]" />
                <p className="text-sm text-[var(--text-muted)]">No insights at the moment</p>
            </div>
        )
    }

    return (
        <div className="glass-panel overflow-hidden">
            {/* Header */}
            <button
                onClick={() => setCollapsed(!collapsed)}
                className="w-full p-4 flex items-center justify-between hover:bg-[var(--bg-secondary)] transition-colors"
            >
                <div className="flex items-center gap-2">
                    <Sparkles size={18} className="text-[var(--accent-primary)]" />
                    <span className="font-medium">AI Insights</span>
                    <span className="px-2 py-0.5 text-xs rounded-full bg-[var(--accent-primary)]/10 text-[var(--accent-primary)]">
                        {insights.length}
                    </span>
                </div>
                <ChevronRight
                    size={18}
                    className={`text-[var(--text-muted)] transition-transform ${collapsed ? '' : 'rotate-90'}`}
                />
            </button>

            {/* Insights List */}
            <AnimatePresence>
                {!collapsed && (
                    <motion.div
                        initial={{ height: 0 }}
                        animate={{ height: 'auto' }}
                        exit={{ height: 0 }}
                        className="overflow-hidden"
                    >
                        <div className="px-4 pb-4 space-y-2">
                            {insights.map((insight, index) => (
                                <motion.div
                                    key={insight.id}
                                    initial={{ opacity: 0, x: -20 }}
                                    animate={{ opacity: 1, x: 0 }}
                                    exit={{ opacity: 0, x: 20 }}
                                    transition={{ delay: index * 0.05 }}
                                    className={`relative p-3 rounded-lg border transition-colors cursor-pointer group ${insight.severity === 'critical'
                                            ? 'border-[var(--accent-error)]/30 bg-[var(--accent-error)]/5 hover:bg-[var(--accent-error)]/10'
                                            : insight.severity === 'warning'
                                                ? 'border-[var(--accent-warning)]/30 bg-[var(--accent-warning)]/5 hover:bg-[var(--accent-warning)]/10'
                                                : 'border-[var(--glass-border)] hover:bg-[var(--bg-secondary)]'
                                        }`}
                                    onClick={() => onInsightClick?.(insight)}
                                >
                                    {/* Dismiss button */}
                                    <button
                                        onClick={(e) => {
                                            e.stopPropagation()
                                            handleDismiss(insight.id)
                                        }}
                                        className="absolute top-2 right-2 p-1 rounded opacity-0 group-hover:opacity-100 hover:bg-[var(--bg-secondary)] transition-all"
                                    >
                                        <X size={14} className="text-[var(--text-muted)]" />
                                    </button>

                                    <div className="flex items-start gap-2">
                                        <div className="mt-0.5">{getSeverityIcon(insight.severity)}</div>
                                        <div className="flex-1 min-w-0">
                                            <div className="flex items-center gap-2 mb-1">
                                                <span className="font-medium text-sm text-[var(--text-primary)]">
                                                    {insight.title}
                                                </span>
                                                <span className="flex items-center gap-1 px-1.5 py-0.5 text-xs rounded bg-[var(--bg-secondary)]">
                                                    {getCategoryIcon(insight.category)}
                                                    {insight.category}
                                                </span>
                                            </div>
                                            <p className="text-xs text-[var(--text-secondary)] line-clamp-2">
                                                {insight.description}
                                            </p>
                                            {insight.action && (
                                                <button className="mt-2 text-xs text-[var(--accent-primary)] hover:underline">
                                                    {insight.action} →
                                                </button>
                                            )}
                                        </div>
                                    </div>
                                </motion.div>
                            ))}
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    )
}

function getSampleInsights(): Insight[] {
    return [
        {
            id: '1',
            title: 'Revenue spike detected',
            description: 'Revenue increased 23% compared to last week. Consider investigating the cause for potential optimization opportunities.',
            severity: 'info',
            category: 'trend',
            action: 'View revenue details',
            relatedQuery: 'Show revenue trends for last 30 days',
            timestamp: new Date(),
        },
        {
            id: '2',
            title: 'High churn risk customers',
            description: '47 customers show high churn probability based on usage patterns and payment history.',
            severity: 'warning',
            category: 'anomaly',
            action: 'View at-risk customers',
            relatedQuery: 'Show high churn risk customers',
            timestamp: new Date(),
        },
        {
            id: '3',
            title: 'Tablespace approaching limit',
            description: 'USERS tablespace is at 85% capacity. Consider expanding or archiving old data.',
            severity: 'critical',
            category: 'performance',
            action: 'Check tablespace usage',
            relatedQuery: 'Show tablespace usage',
            timestamp: new Date(),
        },
        {
            id: '4',
            title: 'Product opportunity',
            description: 'Bundle A has 34% higher adoption in EMEA region. Consider marketing push in other regions.',
            severity: 'info',
            category: 'recommendation',
            action: 'View product analysis',
            relatedQuery: 'Compare product adoption by region',
            timestamp: new Date(),
        },
    ]
}
