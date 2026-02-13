// Type declarations for react-plotly.js
declare module 'react-plotly.js' {
    import { Component } from 'react'
    import Plotly from 'plotly.js-dist-min'

    interface PlotParams {
        data: Plotly.Data[]
        layout?: Partial<Plotly.Layout>
        config?: Partial<Plotly.Config>
        frames?: Plotly.Frame[]
        style?: React.CSSProperties
        className?: string
        useResizeHandler?: boolean
        debug?: boolean
        onInitialized?: (figure: Readonly<{ data: Plotly.Data[]; layout: Partial<Plotly.Layout>; frames?: Plotly.Frame[] }>, graphDiv: HTMLElement) => void
        onUpdate?: (figure: Readonly<{ data: Plotly.Data[]; layout: Partial<Plotly.Layout>; frames?: Plotly.Frame[] }>, graphDiv: HTMLElement) => void
        onPurge?: (figure: Readonly<{ data: Plotly.Data[]; layout: Partial<Plotly.Layout>; frames?: Plotly.Frame[] }>, graphDiv: HTMLElement) => void
        onError?: (err: Error) => void
        onClick?: (event: Plotly.PlotMouseEvent) => void
        onHover?: (event: Plotly.PlotHoverEvent) => void
        onUnhover?: (event: Plotly.PlotMouseEvent) => void
        onSelected?: (event: Plotly.PlotSelectionEvent) => void
        onRelayout?: (event: Plotly.PlotRelayoutEvent) => void
        onRestyle?: (event: Plotly.PlotRestyleEvent) => void
        onRedraw?: () => void
        onAnimated?: () => void
        onAnimatingFrame?: (event: { name: string; frame: Plotly.Frame; animation: { frame?: { redraw?: boolean } } }) => void
        onAfterExport?: () => void
        onAfterPlot?: () => void
        onAutoSize?: () => void
        onBeforeExport?: () => void
        onButtonClicked?: (event: Plotly.ButtonClickEvent) => void
        onClickAnnotation?: (event: Plotly.ClickAnnotationEvent) => void
        onDeselect?: () => void
        onDoubleClick?: () => void
        onFramework?: () => void
        onLegendClick?: (event: Plotly.LegendClickEvent) => boolean
        onLegendDoubleClick?: (event: Plotly.LegendClickEvent) => boolean
        onSliderChange?: (event: Plotly.SliderChangeEvent) => void
        onSliderEnd?: (event: Plotly.SliderEndEvent) => void
        onSliderStart?: (event: Plotly.SliderStartEvent) => void
        onTransitioning?: () => void
        onTransitionInterrupted?: () => void
        divId?: string
    }

    class Plot extends Component<PlotParams> { }
    export default Plot
}

// Type declarations for plotly.js-dist-min
declare module 'plotly.js-dist-min' {
    export * from 'plotly.js'
    export { default } from 'plotly.js'
}
