import { useState, useRef, useEffect } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { ArrowUp, Loader2 } from 'lucide-react'
import MessageList from './MessageList'
import { useChatStore } from '../../stores/chatStore'

const API_BASE_URL = 'http://localhost:8000'

interface ChatContainerProps {
    sessionId: string | null
    onSessionCreated: (id: string) => void
}

export default function ChatContainer({ sessionId, onSessionCreated }: ChatContainerProps) {
    const [input, setInput] = useState('')
    const [isStreaming, setIsStreaming] = useState(false)
    const inputRef = useRef<HTMLTextAreaElement>(null)
    const messagesEndRef = useRef<HTMLDivElement>(null)

    const { messages, addMessage, updateLastMessage, setLastMessageChart, clearMessages } = useChatStore()

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }, [messages])

    useEffect(() => {
        if (!sessionId) {
            clearMessages()
        }
    }, [sessionId, clearMessages])

    // Auto-resize textarea
    useEffect(() => {
        if (inputRef.current) {
            inputRef.current.style.height = 'auto'
            inputRef.current.style.height = Math.min(inputRef.current.scrollHeight, 160) + 'px'
        }
    }, [input])

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        if (!input.trim() || isStreaming) return

        const userMessage = input.trim()
        setInput('')

        addMessage({ role: 'user', content: userMessage })
        addMessage({ role: 'assistant', content: '', isStreaming: true })
        setIsStreaming(true)

        try {
            const eventSource = new EventSource(
                `${API_BASE_URL}/api/chat/stream?message=${encodeURIComponent(userMessage)}&session_id=${sessionId || ''}`
            )

            let fullContent = ''

            eventSource.addEventListener('token', (event) => {
                const data = JSON.parse(event.data)
                fullContent += data.content
                updateLastMessage(fullContent, true)
            })

            eventSource.addEventListener('done', (event) => {
                const data = JSON.parse(event.data)
                updateLastMessage(fullContent, false)
                if (data.session_id && !sessionId) {
                    onSessionCreated(data.session_id)
                }
                eventSource.close()
                setIsStreaming(false)
            })

            eventSource.addEventListener('error', (event) => {
                try {
                    const data = JSON.parse((event as MessageEvent).data)
                    updateLastMessage(`Error: ${data.message}`, false)
                } catch {
                    updateLastMessage(fullContent || 'Connection error', false)
                }
                eventSource.close()
                setIsStreaming(false)
            })

            eventSource.addEventListener('chart', (event) => {
                const data = JSON.parse(event.data)
                if (data.data) {
                    setLastMessageChart(data.data)
                }
            })

            eventSource.addEventListener('suggestions', () => { })

            eventSource.onerror = () => {
                updateLastMessage(fullContent || 'Connection error', false)
                eventSource.close()
                setIsStreaming(false)
            }
        } catch {
            updateLastMessage('Failed to send message', false)
            setIsStreaming(false)
        }
    }

    const handleQuickReply = (query: string) => {
        setInput(query)
        inputRef.current?.focus()
    }

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault()
            handleSubmit(e)
        }
    }

    return (
        <div className="flex flex-col h-full">
            {/* Messages Area */}
            <div className="flex-1 overflow-y-auto">
                {messages.length === 0 ? (
                    <WelcomeScreen onQuickReply={handleQuickReply} />
                ) : (
                    <div className="pb-4">
                        <MessageList messages={messages} />
                        <div ref={messagesEndRef} />
                    </div>
                )}
            </div>

            {/* Input Area */}
            <div className="px-4 pb-4 pt-2">
                <form onSubmit={handleSubmit} className="max-w-3xl mx-auto">
                    <div className="relative bg-[var(--bg-input)] border border-[var(--border-primary)] rounded-2xl shadow-[var(--shadow-sm)] focus-within:border-[var(--text-muted)] transition-colors">
                        <textarea
                            ref={inputRef}
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyDown={handleKeyDown}
                            placeholder="Ask about your billing data..."
                            rows={1}
                            className="w-full bg-transparent outline-none resize-none px-4 pt-3 pb-10 text-[15px] text-[var(--text-primary)] placeholder:text-[var(--text-muted)]"
                            style={{ minHeight: '52px', maxHeight: '160px' }}
                        />
                        <div className="absolute bottom-2 right-2">
                            <button
                                type="submit"
                                disabled={!input.trim() || isStreaming}
                                className={`w-8 h-8 rounded-full flex items-center justify-center transition-all ${input.trim() && !isStreaming
                                        ? 'bg-[var(--text-primary)] text-[var(--bg-primary)] hover:opacity-80'
                                        : 'bg-[var(--bg-tertiary)] text-[var(--text-muted)] cursor-not-allowed'
                                    }`}
                            >
                                {isStreaming ? (
                                    <Loader2 size={16} className="animate-spin" />
                                ) : (
                                    <ArrowUp size={16} />
                                )}
                            </button>
                        </div>
                    </div>
                    <p className="text-center text-[11px] text-[var(--text-muted)] mt-2">
                        ODAOS can make mistakes. Verify important information.
                    </p>
                </form>
            </div>
        </div>
    )
}

function WelcomeScreen({ onQuickReply }: { onQuickReply: (q: string) => void }) {
    const suggestions = [
        { label: 'Show me revenue trends', desc: 'Monthly revenue over time' },
        { label: 'Customer distribution by region', desc: 'Geographic breakdown' },
        { label: 'ARPU vs Churn probability', desc: 'Correlation analysis' },
        { label: 'Product market share', desc: 'Subscription mix' },
    ]

    return (
        <div className="flex flex-col items-center justify-center h-full px-4">
            <div className="max-w-2xl w-full text-center mb-10">
                <h1 className="text-3xl font-semibold mb-3 text-[var(--text-primary)]">
                    What can I help with?
                </h1>
                <p className="text-[var(--text-muted)] text-sm">
                    Ask questions about your Oracle BRM data in natural language
                </p>
            </div>

            <div className="grid grid-cols-2 gap-2.5 max-w-2xl w-full">
                {suggestions.map((item, index) => (
                    <motion.button
                        key={item.label}
                        initial={{ opacity: 0, y: 12 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.05 * index, duration: 0.2 }}
                        onClick={() => onQuickReply(item.label)}
                        className="text-left p-4 rounded-xl border border-[var(--border-subtle)] hover:bg-[var(--bg-secondary)] transition-colors group"
                    >
                        <p className="text-sm font-medium text-[var(--text-primary)] group-hover:text-[var(--accent-success)] transition-colors">
                            {item.label}
                        </p>
                        <p className="text-xs text-[var(--text-muted)] mt-1">
                            {item.desc}
                        </p>
                    </motion.button>
                ))}
            </div>
        </div>
    )
}
