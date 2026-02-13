import { create } from 'zustand'

interface ChartData {
    id: string
    chart_type: string
    title: string
    data: any[]
    layout?: any
    narrative?: {
        summary: string
        key_insights: string[]
        anomalies: any[]
        recommendations: string[]
    }
}

interface VizStore {
    charts: ChartData[]
    activeChartId: string | null
    crossFilterSource: string | null
    crossFilterValues: any[]

    addChart: (chart: ChartData) => void
    removeChart: (id: string) => void
    clearCharts: () => void
    setActiveChart: (id: string | null) => void
    setCrossFilter: (sourceId: string, values: any[]) => void
    clearCrossFilter: () => void
}

export const useVizStore = create<VizStore>((set) => ({
    charts: [],
    activeChartId: null,
    crossFilterSource: null,
    crossFilterValues: [],

    addChart: (chart) =>
        set((state) => ({
            charts: [...state.charts, { ...chart, id: chart.id || crypto.randomUUID() }],
        })),

    removeChart: (id) =>
        set((state) => ({
            charts: state.charts.filter((c) => c.id !== id),
        })),

    clearCharts: () => set({ charts: [], activeChartId: null }),

    setActiveChart: (id) => set({ activeChartId: id }),

    setCrossFilter: (sourceId, values) =>
        set({ crossFilterSource: sourceId, crossFilterValues: values }),

    clearCrossFilter: () =>
        set({ crossFilterSource: null, crossFilterValues: [] }),
}))
