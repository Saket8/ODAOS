import { motion } from 'framer-motion'
import { Sparkles, X, ChevronRight } from 'lucide-react'
import { useState } from 'react'

interface Recommendation {
    id: string
    text: string
    query: string
    confidence: number
}

interface ContextRecommendationsProps {
    context?: string
    onRecommendationClick?: (query: string) => void
}

export default function ContextRecommendations({
    context,
    onRecommendationClick,
}: ContextRecommendationsProps) {
    const [visible, setVisible] = useState(true)
    const recommendations = getRecommendations(context)

    if (!visible || recommendations.length === 0) return null

    return (
        <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="glass-card p-3"
        >
            <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-1.5 text-xs text-[var(--text-muted)]">
                    <Sparkles size={12} className="text-[var(--accent-primary)]" />
                    Recommended queries
                </div>
                <button
                    onClick={() => setVisible(false)}
                    className="p-1 rounded hover:bg-[var(--bg-secondary)] transition-colors"
                >
                    <X size={12} className="text-[var(--text-muted)]" />
                </button>
            </div>

            <div className="space-y-1">
                {recommendations.map((rec) => (
                    <button
                        key={rec.id}
                        onClick={() => onRecommendationClick?.(rec.query)}
                        className="w-full flex items-center justify-between p-2 rounded-lg text-left text-sm hover:bg-[var(--bg-secondary)] transition-colors group"
                    >
                        <span className="text-[var(--text-secondary)] group-hover:text-[var(--text-primary)]">
                            {rec.text}
                        </span>
                        <div className="flex items-center gap-2">
                            <span className="text-xs text-[var(--text-muted)] opacity-0 group-hover:opacity-100 transition-opacity">
                                {Math.round(rec.confidence * 100)}% match
                            </span>
                            <ChevronRight size={14} className="text-[var(--text-muted)] group-hover:translate-x-1 transition-transform" />
                        </div>
                    </button>
                ))}
            </div>
        </motion.div>
    )
}

function getRecommendations(context?: string): Recommendation[] {
    // In production, this would be powered by AI/ML based on context
    if (!context) {
        return [
            { id: '1', text: 'Show today\'s key metrics', query: 'What are the key metrics for today?', confidence: 0.95 },
            { id: '2', text: 'Revenue breakdown by region', query: 'Show revenue by region', confidence: 0.88 },
            { id: '3', text: 'Database health check', query: 'How is the database performing?', confidence: 0.82 },
        ]
    }

    const contextLower = context.toLowerCase()

    if (contextLower.includes('revenue')) {
        return [
            { id: '1', text: 'Compare to last month', query: 'Compare revenue to last month', confidence: 0.92 },
            { id: '2', text: 'Revenue by product', query: 'Show revenue breakdown by product', confidence: 0.87 },
            { id: '3', text: 'Top revenue customers', query: 'Who are the top revenue generating customers?', confidence: 0.81 },
        ]
    }

    if (contextLower.includes('customer')) {
        return [
            { id: '1', text: 'Customer acquisition trend', query: 'Show customer acquisition over time', confidence: 0.90 },
            { id: '2', text: 'Churn analysis', query: 'What is the customer churn rate?', confidence: 0.85 },
            { id: '3', text: 'Customer by segment', query: 'Show customer distribution by segment', confidence: 0.79 },
        ]
    }

    if (contextLower.includes('database') || contextLower.includes('performance')) {
        return [
            { id: '1', text: 'Slow queries', query: 'Show the slowest running queries', confidence: 0.93 },
            { id: '2', text: 'Tablespace usage', query: 'Show tablespace usage', confidence: 0.88 },
            { id: '3', text: 'Active sessions', query: 'How many active sessions are there?', confidence: 0.84 },
        ]
    }

    return [
        { id: '1', text: 'Show summary dashboard', query: 'Give me an overview of the system', confidence: 0.75 },
        { id: '2', text: 'Recent activity', query: 'What happened in the last 24 hours?', confidence: 0.70 },
    ]
}
