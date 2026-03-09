import * as React from 'react'
import { cn } from '@/lib/utils'

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'default' | 'ghost' | 'outline' | 'destructive' | 'secondary'
  size?: 'sm' | 'md' | 'lg' | 'icon'
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'default', size = 'md', ...props }, ref) => {
    return (
      <button
        ref={ref}
        className={cn(
          'inline-flex items-center justify-center gap-2 rounded font-medium transition-colors focus:outline-none focus:ring-1 focus:ring-blue-500 disabled:opacity-50 disabled:pointer-events-none',
          {
            default: 'bg-blue-600 hover:bg-blue-500 text-white',
            ghost: 'hover:bg-slate-800 text-slate-300 hover:text-white',
            outline: 'border border-slate-700 hover:bg-slate-800 text-slate-300',
            destructive: 'bg-red-700 hover:bg-red-600 text-white',
            secondary: 'bg-slate-800 hover:bg-slate-700 text-slate-200',
          }[variant],
          {
            sm: 'h-7 px-2 text-xs',
            md: 'h-8 px-3 text-sm',
            lg: 'h-10 px-4 text-sm',
            icon: 'h-8 w-8',
          }[size],
          className,
        )}
        {...props}
      />
    )
  },
)
Button.displayName = 'Button'
