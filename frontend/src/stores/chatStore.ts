import { create } from 'zustand'

interface Message {
    role: 'user' | 'assistant'
    content: string
    isStreaming?: boolean
    chartData?: any
    timestamp?: Date
}

interface ChatStore {
    messages: Message[]
    currentSessionId: string | null
    addMessage: (message: Message) => void
    updateLastMessage: (content: string, isStreaming: boolean) => void
    setLastMessageChart: (chartData: any) => void
    clearMessages: () => void
    setSessionId: (id: string | null) => void
}

export const useChatStore = create<ChatStore>((set) => ({
    messages: [],
    currentSessionId: null,

    addMessage: (message) =>
        set((state) => ({
            messages: [...state.messages, { ...message, timestamp: new Date() }],
        })),

    updateLastMessage: (content, isStreaming) =>
        set((state) => {
            const messages = [...state.messages]
            if (messages.length > 0) {
                messages[messages.length - 1] = {
                    ...messages[messages.length - 1],
                    content,
                    isStreaming,
                }
            }
            return { messages }
        }),

    setLastMessageChart: (chartData) =>
        set((state) => {
            const messages = [...state.messages]
            if (messages.length > 0) {
                messages[messages.length - 1] = {
                    ...messages[messages.length - 1],
                    chartData,
                }
            }
            return { messages }
        }),

    clearMessages: () => set({ messages: [] }),

    setSessionId: (id) => set({ currentSessionId: id }),
}))

