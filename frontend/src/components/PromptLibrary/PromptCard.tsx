import { Star } from 'lucide-react'
import type { PromptSummary } from '../../stores/promptStore'
import { usePromptStore } from '../../stores/promptStore'

function capitalize(s: string): string {
    return s.charAt(0).toUpperCase() + s.slice(1)
}

export default function PromptCard({
    prompt,
    onSelect,
}: {
    prompt: PromptSummary
    onSelect: (id: string) => void
}) {
    const toggleFavorite = usePromptStore((s) => s.toggleFavorite)

    return (
        <div
            onClick={() => onSelect(prompt.id)}
            className="group relative p-4 rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-secondary)]/60 hover:bg-[var(--bg-secondary)] cursor-pointer transition-all duration-150 hover:border-[var(--border-primary)] flex flex-col"
        >
            {/* Favorite */}
            <button
                onClick={(e) => {
                    e.stopPropagation()
                    toggleFavorite(prompt.id)
                }}
                className="absolute top-3.5 right-3.5 p-1 rounded-md opacity-0 group-hover:opacity-100 hover:bg-[var(--bg-hover)] transition-all"
            >
                <Star
                    size={13}
                    className={
                        prompt.is_favorited
                            ? 'fill-amber-400 text-amber-400'
                            : 'text-[var(--text-muted)]'
                    }
                />
            </button>

            {/* Title */}
            <h3 className="text-[13px] font-medium text-[var(--text-primary)] leading-snug pr-6 mb-1.5">
                {prompt.title}
            </h3>

            {/* Description */}
            <p className="text-xs text-[var(--text-muted)] line-clamp-2 leading-relaxed mb-3 flex-1">
                {prompt.description}
            </p>

            {/* Footer — minimal */}
            <div className="flex items-center gap-2 text-[11px] text-[var(--text-muted)]">
                <span className={`
                    ${prompt.difficulty_level === 'beginner' ? 'text-emerald-500' :
                        prompt.difficulty_level === 'intermediate' ? 'text-amber-500' :
                            'text-rose-500'}
                `}>
                    {capitalize(prompt.difficulty_level)}
                </span>
                <span className="opacity-30">·</span>
                <span>{prompt.estimated_runtime}</span>
                {prompt.usage_count > 0 && (
                    <>
                        <span className="opacity-30">·</span>
                        <span>{prompt.usage_count} runs</span>
                    </>
                )}
            </div>
        </div>
    )
}
