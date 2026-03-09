import { scoreBg, formatScore, scoreLabel } from '@/lib/utils'

interface Props {
  score?: number | null
  showLabel?: boolean
}

export function StabilityBadge({ score, showLabel = true }: Props) {
  const s = score ?? 1
  return (
    <span className={`inline-flex items-center gap-1 rounded px-1.5 py-0.5 text-xs font-medium border ${scoreBg(s)}`}>
      <span className="font-mono">{formatScore(s)}</span>
      {showLabel && <span className="opacity-75">{scoreLabel(s)}</span>}
    </span>
  )
}
