import * as React from 'react'
import { cn } from '@/lib/utils'

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: 'default' | 'green' | 'amber' | 'red' | 'blue' | 'purple'
}

export function Badge({ className, variant = 'default', ...props }: BadgeProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center rounded px-1.5 py-0.5 text-xs font-medium border',
        {
          default: 'bg-slate-800 text-slate-300 border-slate-700',
          green: 'bg-green-900/40 text-green-400 border-green-800',
          amber: 'bg-amber-900/40 text-amber-400 border-amber-800',
          red: 'bg-red-900/40 text-red-400 border-red-800',
          blue: 'bg-blue-900/40 text-blue-400 border-blue-800',
          purple: 'bg-purple-900/40 text-purple-400 border-purple-800',
        }[variant],
        className,
      )}
      {...props}
    />
  )
}
