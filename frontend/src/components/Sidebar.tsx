import { NavLink } from 'react-router-dom'
import { Map, Network, Users, ScrollText, Globe2 } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useQuery } from '@tanstack/react-query'
import { fetchScenarios } from '@/api/client'
import { Select } from '@/components/ui/select'
import { useScenario } from '@/context/ScenarioContext'

const NAV = [
  { to: '/map', icon: Map, label: 'War Map' },
  { to: '/graph', icon: Network, label: 'Graph Explorer' },
  { to: '/actors', icon: Users, label: 'Actor Dashboard' },
  { to: '/events', icon: ScrollText, label: 'Event Log' },
]

export function Sidebar() {
  const { scenarioId, setScenarioId } = useScenario()
  const { data: scenarios = [] } = useQuery({ queryKey: ['scenarios'], queryFn: fetchScenarios })

  return (
    <aside className="flex flex-col w-56 min-h-0 border-r border-slate-800 bg-[#080c18]">
      {/* Logo */}
      <div className="flex items-center gap-2 px-4 h-12 border-b border-slate-800 shrink-0">
        <Globe2 size={18} className="text-blue-400" />
        <span className="text-sm font-semibold tracking-wide text-slate-100">GeoIntel</span>
      </div>

      {/* Nav */}
      <nav className="flex-1 py-3 space-y-0.5 px-2">
        {NAV.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              cn(
                'flex items-center gap-2.5 px-3 py-2 rounded text-sm transition-colors',
                isActive
                  ? 'bg-blue-900/40 text-blue-300'
                  : 'text-slate-400 hover:text-slate-100 hover:bg-slate-800/50',
              )
            }
          >
            <Icon size={15} />
            {label}
          </NavLink>
        ))}
      </nav>

      {/* Scenario selector */}
      <div className="px-3 pb-4 shrink-0 space-y-1 border-t border-slate-800 pt-3">
        <p className="text-[10px] font-medium uppercase tracking-wider text-slate-500 px-1">Scenario</p>
        <Select
          value={scenarioId}
          onChange={e => setScenarioId(e.target.value)}
          className="text-xs"
        >
          <option value="production">Production</option>
          {scenarios
            .filter(s => !s.is_production)
            .map(s => (
              <option key={s.id} value={s.id}>{s.name}</option>
            ))}
        </Select>
      </div>
    </aside>
  )
}
