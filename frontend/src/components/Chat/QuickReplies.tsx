interface QuickReply {
    text: string
    query: string
}

interface QuickRepliesProps {
    onSelect: (query: string) => void
    replies?: QuickReply[]
}

const defaultReplies: QuickReply[] = [
    { text: 'Drill down by region', query: 'Show breakdown by region' },
    { text: 'Compare trends', query: 'Compare to previous month' },
    { text: 'Show anomalies', query: 'Are there any anomalies?' },
]

export default function QuickReplies({ onSelect, replies = defaultReplies }: QuickRepliesProps) {
    return (
        <div className="flex flex-wrap gap-2 pb-2 max-w-3xl mx-auto px-4">
            {replies.map((reply) => (
                <button
                    key={reply.text}
                    onClick={() => onSelect(reply.query)}
                    className="px-3 py-1.5 text-[13px] rounded-full border border-[var(--border-primary)] hover:bg-[var(--bg-secondary)] transition-colors text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
                >
                    {reply.text}
                </button>
            ))}
        </div>
    )
}
