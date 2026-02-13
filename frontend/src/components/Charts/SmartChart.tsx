import { useRef, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import Plot from 'react-plotly.js'
import { Download, Maximize2, Minimize2, ZoomIn, FileText } from 'lucide-react'

interface SmartNarrative {
    summary: string
    key_insights?: string[]
    insights?: string[]  // Alternative key name from API
    anomalies?: any[]
    recommendations?: string[]
}

interface DrillDownOption {
    label: string
    query: string
    dimension?: string
    value?: any
}

interface SmartChartProps {
    // Individual props (preferred when passing from MessageList)
    id?: string
    type?: 'bar' | 'line' | 'pie' | 'scatter' | 'heatmap' | 'area'
    title?: string
    data?: any[]
    layout?: any
    config?: any
    // Or legacy chartData object
    chartData?: {
        chart_type: string
        title: string
        data: any[]
        layout?: any
        config?: any
    }
    narrative?: SmartNarrative
    drillDownOptions?: DrillDownOption[]
    onDrillDown?: (option: DrillDownOption) => void
    onCrossFilter?: (selectedData: any) => void
    isLoading?: boolean
}

export default function SmartChart({
    id: _id,
    type,
    title,
    data,
    layout,
    chartData,
    narrative,
    drillDownOptions = [],
    onDrillDown,
    onCrossFilter,
    isLoading = false,
}: SmartChartProps) {
    const [isFullscreen, setIsFullscreen] = useState(false)
    const [showNarrative, setShowNarrative] = useState(false)
    const chartRef = useRef<HTMLDivElement>(null)

    // Support both individual props and chartData object
    const chartType = type || chartData?.chart_type || 'bar'
    const chartTitle = title || chartData?.title || 'Chart'
    const chartDataArr = data || chartData?.data || []
    const chartLayoutProp = layout || chartData?.layout || {}

    // Convert data to Plotly format based on chart type
    const getPlotlyData = () => {

        switch (chartType) {
            case 'pie':
                return [{
                    type: 'pie',
                    labels: chartDataArr.map((d: any) => d.label),
                    values: chartDataArr.map((d: any) => d.value),
                    hole: 0.4,
                    marker: {
                        colors: ['#60a5fa', '#a78bfa', '#34d399', '#fbbf24', '#f87171', '#38bdf8'],
                    },
                    textinfo: 'label+percent',
                    hoverinfo: 'label+value+percent',
                }]

            case 'bar':
                return [{
                    type: 'bar',
                    x: chartDataArr.map((d: any) => d.category || d.label),
                    y: chartDataArr.map((d: any) => d.value),
                    marker: {
                        color: '#60a5fa',
                        line: { color: '#3b82f6', width: 1 },
                    },
                    hovertemplate: '%{x}<br>%{y:,.0f}<extra></extra>',
                }]

            case 'line':
                return [{
                    type: 'scatter',
                    mode: 'lines+markers',
                    x: chartDataArr.map((d: any) => d.month || d.date || d.x),
                    y: chartDataArr.map((d: any) => d.value || d.y),
                    line: { color: '#60a5fa', width: 2, shape: 'spline' },
                    marker: { size: 8, color: '#60a5fa' },
                    fill: 'tozeroy',
                    fillcolor: 'rgba(96, 165, 250, 0.1)',
                }]

            case 'scatter':
                return [{
                    type: 'scatter',
                    mode: 'markers',
                    x: chartDataArr.map((d: any) => d.x),
                    y: chartDataArr.map((d: any) => d.y),
                    text: chartDataArr.map((d: any) => d.label || ''),
                    marker: {
                        size: 12,
                        color: chartDataArr.map((d: any) => d.y),
                        colorscale: 'Viridis',
                        showscale: true,
                    },
                    hovertemplate: '%{text}<br>X: %{x}<br>Y: %{y:.2f}<extra></extra>',
                }]

            case 'heatmap':
                return [{
                    type: 'heatmap',
                    z: chartDataArr.map((d: any) => d.values || d.z),
                    x: chartDataArr[0]?.x_labels || [],
                    y: chartDataArr.map((d: any) => d.y_label || d.label),
                    colorscale: 'Blues',
                    showscale: true,
                }]

            case 'area':
                return [{
                    type: 'scatter',
                    mode: 'lines',
                    fill: 'tozeroy',
                    x: chartDataArr.map((d: any) => d.x || d.date),
                    y: chartDataArr.map((d: any) => d.y || d.value),
                    line: { color: '#a78bfa', width: 2 },
                    fillcolor: 'rgba(167, 139, 250, 0.3)',
                }]

            default:
                return [{
                    type: 'bar',
                    x: chartDataArr.map((_: any, i: number) => `Item ${i + 1}`),
                    y: chartDataArr.map((d: any) => d.value || 0),
                }]
        }
    }

    const plotLayout = {
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        font: { family: 'Inter, sans-serif', color: '#cbd5e1', size: 12 },
        margin: { l: 50, r: 30, t: 40, b: 50 },
        title: {
            text: chartTitle,
            font: { size: 16, color: '#f8fafc' },
        },
        showlegend: chartType === 'pie',
        legend: { orientation: 'h', y: -0.1 },
        xaxis: {
            gridcolor: 'rgba(255,255,255,0.05)',
            zerolinecolor: 'rgba(255,255,255,0.1)',
        },
        yaxis: {
            gridcolor: 'rgba(255,255,255,0.05)',
            zerolinecolor: 'rgba(255,255,255,0.1)',
        },
        hoverlabel: {
            bgcolor: '#1e293b',
            font: { family: 'Inter, sans-serif', color: '#f8fafc' },
            bordercolor: '#475569',
        },
        ...chartLayoutProp,
    }


    const plotConfig = {
        responsive: true,
        displayModeBar: false,
    }

    const handleClick = (event: any) => {
        if (event.points && event.points.length > 0 && onCrossFilter) {
            onCrossFilter(event.points[0])
        }
    }

    const handleExport = async (format: 'png' | 'svg' | 'csv') => {
        const plotElement = chartRef.current?.querySelector('.js-plotly-plot') as any
        if (!plotElement) return

        if (format === 'csv') {
            // Export data as CSV
            const csvContent = chartDataArr.map((row: any) =>
                Object.values(row).join(',')
            ).join('\n')
            const blob = new Blob([csvContent], { type: 'text/csv' })
            const url = URL.createObjectURL(blob)
            const a = document.createElement('a')
            a.href = url
            a.download = `${chartTitle.replace(/\s+/g, '_')}.csv`
            a.click()
        } else {
            // Use Plotly's export functionality
            const Plotly = await import('plotly.js-dist-min')
            Plotly.downloadImage(plotElement, {
                format,
                filename: chartTitle.replace(/\s+/g, '_'),
                width: 1200,
                height: 800,
            })
        }
    }

    if (isLoading) {
        return (
            <div className="chart-container">
                <div className="skeleton h-64 w-full" />
                <div className="mt-4 space-y-2">
                    <div className="skeleton h-4 w-3/4" />
                    <div className="skeleton h-4 w-1/2" />
                </div>
            </div>
        )
    }

    return (
        <motion.div
            ref={chartRef}
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className={`chart-container ${isFullscreen ? 'fixed inset-4 z-50' : ''}`}
        >
            {/* Header */}
            <div className="flex items-center justify-between mb-2">
                <h3 className="font-medium text-[var(--text-primary)]">{chartTitle}</h3>
                <div className="flex items-center gap-1">
                    <button
                        onClick={() => setShowNarrative(!showNarrative)}
                        className="p-1.5 rounded hover:bg-[var(--bg-secondary)] transition-colors"
                        title="Show insights"
                    >
                        <FileText size={16} className="text-[var(--text-muted)]" />
                    </button>
                    <button
                        onClick={() => handleExport('png')}
                        className="p-1.5 rounded hover:bg-[var(--bg-secondary)] transition-colors"
                        title="Export as PNG"
                    >
                        <Download size={16} className="text-[var(--text-muted)]" />
                    </button>
                    <button
                        onClick={() => setIsFullscreen(!isFullscreen)}
                        className="p-1.5 rounded hover:bg-[var(--bg-secondary)] transition-colors"
                        title="Toggle fullscreen"
                    >
                        {isFullscreen ? (
                            <Minimize2 size={16} className="text-[var(--text-muted)]" />
                        ) : (
                            <Maximize2 size={16} className="text-[var(--text-muted)]" />
                        )}
                    </button>
                </div>
            </div>

            {/* Chart */}
            <Plot
                data={getPlotlyData() as any}
                layout={plotLayout as any}
                config={plotConfig as any}
                onClick={handleClick}
                style={{ width: '100%', height: isFullscreen ? 'calc(100% - 120px)' : '300px' }}
                useResizeHandler
            />

            {/* Drill-down options */}
            {drillDownOptions.length > 0 && (
                <div className="flex flex-wrap gap-2 mt-3 pt-3 border-t border-[var(--glass-border)]">
                    <span className="text-xs text-[var(--text-muted)]">Drill down:</span>
                    {drillDownOptions.map((option) => (
                        <button
                            key={option.label}
                            onClick={() => onDrillDown?.(option)}
                            className="flex items-center gap-1 px-2 py-1 text-xs rounded-full border border-[var(--glass-border)] hover:bg-[var(--bg-secondary)] hover:border-[var(--accent-primary)] transition-all"
                        >
                            <ZoomIn size={12} />
                            {option.label}
                        </button>
                    ))}
                </div>
            )}

            {/* Smart Narrative Panel */}
            <AnimatePresence>
                {showNarrative && narrative && (
                    <motion.div
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: 'auto' }}
                        exit={{ opacity: 0, height: 0 }}
                        className="mt-3 pt-3 border-t border-[var(--glass-border)]"
                    >
                        <h4 className="text-sm font-medium text-[var(--text-primary)] mb-2">AI Insights</h4>
                        <p className="text-sm text-[var(--text-secondary)] mb-2">{narrative.summary}</p>

                        {(narrative.key_insights || narrative.insights || []).length > 0 && (
                            <ul className="space-y-1 mb-2">
                                {(narrative.key_insights || narrative.insights || []).map((insight, i) => (
                                    <li key={i} className="flex items-start gap-2 text-xs text-[var(--text-muted)]">
                                        <span className="text-[var(--accent-success)]">•</span>
                                        {insight}
                                    </li>
                                ))}
                            </ul>
                        )}

                        {(narrative.recommendations || []).length > 0 && (
                            <div className="text-xs text-[var(--accent-primary)]">
                                💡 {(narrative.recommendations || [])[0]}
                            </div>
                        )}
                    </motion.div>
                )}
            </AnimatePresence>
        </motion.div>
    )
}
