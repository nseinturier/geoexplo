import { type ClassValue, clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function scoreColor(score: number | undefined | null): string {
  const s = score ?? 1
  if (s >= 0.7) return '#22c55e'
  if (s >= 0.4) return '#f59e0b'
  return '#ef4444'
}

export function scoreBg(score: number | undefined | null): string {
  const s = score ?? 1
  if (s >= 0.7) return 'bg-green-900/40 text-green-400 border-green-800'
  if (s >= 0.4) return 'bg-amber-900/40 text-amber-400 border-amber-800'
  return 'bg-red-900/40 text-red-400 border-red-800'
}

export function scoreLabel(score: number | undefined | null): string {
  const s = score ?? 1
  if (s >= 0.7) return 'Stable'
  if (s >= 0.4) return 'Stressed'
  return 'Critical'
}

export function formatScore(score: number | undefined | null): string {
  return ((score ?? 1) * 100).toFixed(0) + '%'
}
