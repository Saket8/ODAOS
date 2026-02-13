import { motion } from 'framer-motion'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Copy, Check, ThumbsUp, ThumbsDown } from 'lucide-react'
import { useState, lazy, Suspense } from 'react'

const SmartChart = lazy(() => import('../Charts/SmartChart'))

interface ChartData {
    id: string
    type: string
    title: string
    data: any[]
    layout?: any
    config?: any
    narrative?: {
        summary: string
        insights: string[]
        recommendations: string[]
    }
    drillDownOptions?: { label: string; query: string }[]
}

interface Message {
    role: 'user' | 'assistant'
    content: string
    isStreaming?: boolean
    chartData?: ChartData
}

interface MessageListProps {
    messages: Message[]
}

export default function MessageList({ messages }: MessageListProps) {
    return (
        <div className="max-w-3xl mx-auto px-4">
            {messages.map((message, index) => (
                <MessageRow key={index} message={message} />
            ))}
        </div>
    )
}

function MessageRow({ message }: { message: Message }) {
    const [copied, setCopied] = useState(false)
    const [hovering, setHovering] = useState(false)
    const isUser = message.role === 'user'

    const handleCopy = async () => {
        await navigator.clipboard.writeText(message.content)
        setCopied(true)
        setTimeout(() => setCopied(false), 2000)
    }

    return (
        <div
            className={`py-5 ${isUser ? '' : ''}`}
            onMouseEnter={() => setHovering(true)}
            onMouseLeave={() => setHovering(false)}
        >
            <div className="flex gap-4">
                {/* Avatar */}
                <div className="flex-shrink-0 mt-0.5">
                    {isUser ? (
                        <div className="w-7 h-7 rounded-full bg-gradient-to-br from-emerald-400 to-teal-500 flex items-center justify-center">
                            <span className="text-white text-xs font-bold">U</span>
                        </div>
                    ) : (
                        <div className="w-7 h-7 rounded-full bg-[var(--bg-tertiary)] border border-[var(--border-subtle)] flex items-center justify-center">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" className="text-[var(--text-secondary)]">
                                <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                            </svg>
                        </div>
                    )}
                </div>

                {/* Content */}
                <div className="flex-1 min-w-0">
                    <div className="text-xs font-semibold text-[var(--text-secondary)] mb-1.5">
                        {isUser ? 'You' : 'ODAOS'}
                    </div>

                    {isUser ? (
                        <p className="text-[15px] leading-relaxed text-[var(--text-primary)]">
                            {message.content}
                        </p>
                    ) : (
                        <>
                            {/* Chart */}
                            {message.chartData && (
                                <Suspense fallback={
                                    <div className="h-48 flex items-center justify-center text-sm text-[var(--text-muted)]">
                                        Loading visualization...
                                    </div>
                                }>
                                    <div className="mb-4">
                                        <SmartChart
                                            id={message.chartData.id}
                                            type={message.chartData.type as any}
                                            title={message.chartData.title}
                                            data={message.chartData.data}
                                            layout={message.chartData.layout}
                                            narrative={message.chartData.narrative}
                                            drillDownOptions={message.chartData.drillDownOptions}
                                        />
                                    </div>
                                </Suspense>
                            )}

                            {/* Text */}
                            <div className="prose prose-sm dark:prose-invert max-w-none">
                                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                                    {message.content || (message.isStreaming ? '' : 'Thinking...')}
                                </ReactMarkdown>
                                {message.isStreaming && (
                                    <span className="inline-block w-0.5 h-4 bg-[var(--text-secondary)] animate-pulse ml-0.5 align-middle" />
                                )}
                            </div>

                            {/* Actions — hover reveal */}
                            {message.content && !message.isStreaming && (
                                <motion.div
                                    initial={{ opacity: 0 }}
                                    animate={{ opacity: hovering ? 1 : 0 }}
                                    className="flex items-center gap-1 mt-2"
                                >
                                    <button
                                        onClick={handleCopy}
                                        className="p-1.5 rounded-md hover:bg-[var(--bg-hover)] transition-colors"
                                        title="Copy"
                                    >
                                        {copied ? (
                                            <Check size={14} className="text-[var(--accent-success)]" />
                                        ) : (
                                            <Copy size={14} className="text-[var(--text-muted)]" />
                                        )}
                                    </button>
                                    <button className="p-1.5 rounded-md hover:bg-[var(--bg-hover)] transition-colors" title="Good response">
                                        <ThumbsUp size={14} className="text-[var(--text-muted)]" />
                                    </button>
                                    <button className="p-1.5 rounded-md hover:bg-[var(--bg-hover)] transition-colors" title="Bad response">
                                        <ThumbsDown size={14} className="text-[var(--text-muted)]" />
                                    </button>
                                </motion.div>
                            )}
                        </>
                    )}
                </div>
            </div>
        </div>
    )
}
