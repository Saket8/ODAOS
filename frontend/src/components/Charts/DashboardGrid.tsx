import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import SmartChart from './SmartChart'
import { RefreshCw, Grid, List } from 'lucide-react'

interface ChartData {
    id: string
    chart_type: string
    title: string
    data: any[]
    layout?: any
}

interface DashboardGridProps {
    charts: ChartData[]
    onChartClick?: (chartId: string) => void
    onCrossFilter?: (sourceId: string, selectedData: any) => void
    isLoading?: boolean
}

export default function DashboardGrid({
    charts,
    onChartClick: _onChartClick,
    onCrossFilter,
    isLoading = false,
}: DashboardGridProps) {
    const [layout, setLayout] = useState<'grid' | 'list'>('grid')
    const [crossFilterActive, setCrossFilterActive] = useState<string | null>(null)

    const handleCrossFilter = (chartId: string, data: any) => {
        setCrossFilterActive(chartId)
        onCrossFilter?.(chartId, data)
    }

    const clearCrossFilter = () => {
        setCrossFilterActive(null)
    }

    if (isLoading) {
        return (
            <div className={`grid ${layout === 'grid' ? 'grid-cols-1 md:grid-cols-2' : 'grid-cols-1'} gap-4`}>
                {[1, 2, 3, 4].map((i) => (
                    <div key={i} className="skeleton h-80 w-full rounded-xl" />
                ))}
            </div>
        )
    }

    if (charts.length === 0) {
        return (
            <div className="text-center py-12 text-[var(--text-muted)]">
                <p>No charts to display. Ask a question to generate visualizations.</p>
            </div>
        )
    }

    return (
        <div>
            {/* Controls */}
            <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                    <span className="text-sm text-[var(--text-muted)]">{charts.length} chart(s)</span>
                    {crossFilterActive && (
                        <button
                            onClick={clearCrossFilter}
                            className="flex items-center gap-1 px-2 py-1 text-xs rounded-full bg-[var(--accent-primary)]/10 text-[var(--accent-primary)] hover:bg-[var(--accent-primary)]/20 transition-colors"
                        >
                            <RefreshCw size={12} />
                            Clear filter
                        </button>
                    )}
                </div>
                <div className="flex items-center gap-1 bg-[var(--bg-secondary)] rounded-lg p-1">
                    <button
                        onClick={() => setLayout('grid')}
                        className={`p-1.5 rounded ${layout === 'grid' ? 'bg-[var(--bg-glass)]' : ''} transition-colors`}
                    >
                        <Grid size={16} />
                    </button>
                    <button
                        onClick={() => setLayout('list')}
                        className={`p-1.5 rounded ${layout === 'list' ? 'bg-[var(--bg-glass)]' : ''} transition-colors`}
                    >
                        <List size={16} />
                    </button>
                </div>
            </div>

            {/* Charts Grid */}
            <div className={`grid ${layout === 'grid' ? 'grid-cols-1 md:grid-cols-2' : 'grid-cols-1'} gap-4`}>
                <AnimatePresence>
                    {charts.map((chart, index) => (
                        <motion.div
                            key={chart.id}
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: -20 }}
                            transition={{ delay: index * 0.1 }}
                            className={`${crossFilterActive && crossFilterActive !== chart.id ? 'opacity-50' : ''} transition-opacity`}
                        >
                            <SmartChart
                                chartData={chart}
                                onCrossFilter={(data) => handleCrossFilter(chart.id, data)}
                                drillDownOptions={[
                                    { label: 'By Region', query: `${chart.title} by region`, dimension: 'region', value: '*' },
                                    { label: 'By Time', query: `${chart.title} over time`, dimension: 'time', value: '*' },
                                ]}
                            />
                        </motion.div>
                    ))}
                </AnimatePresence>
            </div>
        </div>
    )
}
