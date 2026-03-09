import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { fetchNodes, fetchNode, patchNode, fetchActorRisk } from '@/api/client'
import type { GraphNode } from '@/api/types'
import { scoreColor, scoreBg, formatScore } from '@/lib/utils'
import { StabilityBadge } from '@/components/StabilityBadge'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import {
  ChevronDown, ChevronRight, Atom, Shield, TrendingUp,
  Users, AlertTriangle, Search, BarChart2, Edit2, Save, X
} from 'lucide-react'

const ACTOR_LABELS = ['NationState', 'MilitaryAlliance', 'NonStateActor']

function regimeBadge(regime?: string): 'blue' | 'amber' | 'red' | 'purple' | 'green' | 'default' {
  const map: Record<string, 'blue' | 'amber' | 'red' | 'purple' | 'green'> = {
    democracy: 'blue',
    monarchy: 'amber',
    theocracy: 'red',
    authoritarian: 'purple',
  }
  return map[regime ?? ''] ?? 'default'
}

function ActorCard({ node }: { node: GraphNode }) {
  const qc = useQueryClient()
  const [showRels, setShowRels] = useState(false)
  const [editNotes, setEditNotes] = useState(false)
  const [notes, setNotes] = useState(node.notes ?? '')
  const [showRisk, setShowRisk] = useState(false)

  const { data: detail } = useQuery({
    queryKey: ['node', node.uid],
    queryFn: () => fetchNode(node.uid),
    enabled: showRels,
  })

  const { data: risk } = useQuery({
    queryKey: ['risk', node.uid],
    queryFn: () => fetchActorRisk(node.uid),
    enabled: showRisk,
  })

  const { mutate: save, isPending: saving } = useMutation({
    mutationFn: () => patchNode(node.uid, { notes }),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['nodes'] }); setEditNotes(false) },
  })

  const isNation = (node._labels ?? []).includes('NationState')

  return (
    <Card className="flex flex-col">
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0">
            <CardTitle className="text-slate-100 text-sm leading-tight truncate">{node.name}</CardTitle>
            <div className="flex items-center gap-1.5 mt-1.5 flex-wrap">
              <StabilityBadge score={node.stability_score} />
              {node.is_nuclear && (
                <Badge variant="red" className="gap-1"><Atom size={9} />Nuclear</Badge>
              )}
              {node.regime_type && (
                <Badge variant={regimeBadge(node.regime_type)}>{node.regime_type}</Badge>
              )}
            </div>
          </div>
          {/* Stability ring */}
          <div className="shrink-0 relative w-10 h-10">
            <svg viewBox="0 0 36 36" className="w-10 h-10 -rotate-90">
              <circle cx="18" cy="18" r="15" fill="none" stroke="#1e293b" strokeWidth="3" />
              <circle
                cx="18" cy="18" r="15" fill="none"
                stroke={scoreColor(node.stability_score)}
                strokeWidth="3"
                strokeDasharray={`${(node.stability_score ?? 1) * 94.2} 94.2`}
                strokeLinecap="round"
              />
            </svg>
            <span className="absolute inset-0 flex items-center justify-center text-[9px] font-mono text-slate-300">
              {Math.round((node.stability_score ?? 1) * 100)}
            </span>
          </div>
        </div>
      </CardHeader>

      <CardContent className="flex-1 space-y-3">
        {/* Key metrics */}
        {isNation && (
          <div className="grid grid-cols-2 gap-2">
            {node.gdp_usd && (
              <div className="bg-slate-900/60 rounded px-2 py-1.5">
                <div className="flex items-center gap-1 text-[10px] text-slate-500 mb-0.5">
                  <TrendingUp size={9} /> GDP
                </div>
                <div className="text-xs text-slate-200 font-mono">
                  ${node.gdp_usd >= 1e12 ? (node.gdp_usd / 1e12).toFixed(1) + 'T' : (node.gdp_usd / 1e9).toFixed(0) + 'B'}
                </div>
              </div>
            )}
            {node.population && (
              <div className="bg-slate-900/60 rounded px-2 py-1.5">
                <div className="flex items-center gap-1 text-[10px] text-slate-500 mb-0.5">
                  <Users size={9} /> Pop
                </div>
                <div className="text-xs text-slate-200 font-mono">
                  {node.population >= 1e9 ? (node.population / 1e9).toFixed(1) + 'B' : (node.population / 1e6).toFixed(0) + 'M'}
                </div>
              </div>
            )}
            {node.pct_shia != null && node.pct_shia > 0 && (
              <div className="bg-slate-900/60 rounded px-2 py-1.5">
                <div className="text-[10px] text-slate-500 mb-0.5">Shia %</div>
                <div className="text-xs text-slate-200 font-mono">{(node.pct_shia * 100).toFixed(0)}%</div>
              </div>
            )}
            {node.confidence != null && (
              <div className="bg-slate-900/60 rounded px-2 py-1.5">
                <div className="flex items-center gap-1 text-[10px] text-slate-500 mb-0.5">
                  <Shield size={9} /> Conf.
                </div>
                <div className="text-xs text-slate-200 font-mono">{(node.confidence * 100).toFixed(0)}%</div>
              </div>
            )}
          </div>
        )}

        {/* Notes */}
        <div>
          {!editNotes ? (
            <div
              className="text-xs text-slate-500 leading-relaxed cursor-pointer hover:text-slate-400 min-h-[2rem]"
              onClick={() => setEditNotes(true)}
            >
              {node.notes || <span className="text-slate-700 italic">Click to add notes…</span>}
            </div>
          ) : (
            <div className="space-y-1.5">
              <textarea
                rows={2}
                value={notes}
                onChange={e => setNotes(e.target.value)}
                className="w-full rounded border border-slate-700 bg-slate-900 px-2 py-1 text-xs text-slate-100 resize-none focus:outline-none focus:ring-1 focus:ring-blue-500"
                autoFocus
              />
              <div className="flex gap-1">
                <Button size="sm" onClick={() => save()} disabled={saving}>
                  <Save size={10} /> {saving ? '…' : 'Save'}
                </Button>
                <Button size="sm" variant="ghost" onClick={() => setEditNotes(false)}>
                  <X size={10} />
                </Button>
              </div>
            </div>
          )}
        </div>

        {/* Relationships toggle */}
        <button
          onClick={() => setShowRels(r => !r)}
          className="flex items-center gap-1 text-[11px] text-slate-500 hover:text-slate-300 transition-colors"
        >
          {showRels ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
          Relationships
        </button>

        {showRels && detail && (
          <div className="space-y-1 text-xs border-t border-slate-800 pt-2">
            {detail.outgoing_relationships?.slice(0, 6).map((r, i) => (
              <div key={i} className="flex items-center gap-1.5 text-slate-400">
                <span className="text-[10px] px-1 py-0.5 rounded bg-slate-800 text-slate-500 shrink-0">
                  {r.type.replace(/_/g, ' ')}
                </span>
                <span className="truncate text-slate-300">{r.target_name}</span>
              </div>
            ))}
          </div>
        )}

        {/* Risk toggle */}
        <button
          onClick={() => setShowRisk(r => !r)}
          className="flex items-center gap-1 text-[11px] text-slate-500 hover:text-slate-300 transition-colors"
        >
          {showRisk ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
          Risk Analysis
        </button>

        {showRisk && risk && (
          <div className="grid grid-cols-2 gap-1.5 text-xs border-t border-slate-800 pt-2">
            <div className="flex flex-col">
              <span className="text-[10px] text-slate-500">Composite Risk</span>
              <span
                className="font-mono text-sm font-semibold"
                style={{ color: scoreColor(1 - risk.composite_risk) }}
              >
                {(risk.composite_risk * 100).toFixed(0)}%
              </span>
            </div>
            <div className="flex flex-col">
              <span className="text-[10px] text-slate-500">Enemies</span>
              <span className="font-mono text-sm text-slate-200">{risk.enemy_count}</span>
            </div>
            <div className="flex flex-col">
              <span className="text-[10px] text-slate-500">Exposed Infra</span>
              <span className="font-mono text-sm text-slate-200">{risk.exposed_infrastructure}</span>
            </div>
            <div className="flex flex-col">
              <span className="text-[10px] text-slate-500">Dependencies</span>
              <span className="font-mono text-sm text-slate-200">{risk.dependency_count}</span>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

export function ActorDashboard() {
  const [search, setSearch] = useState('')

  const { data: allNodes = [], isLoading } = useQuery({
    queryKey: ['nodes'],
    queryFn: () => import('@/api/client').then(m => m.fetchNodes()),
  })

  const actors = allNodes.filter(n =>
    (n._labels ?? []).some(l => ACTOR_LABELS.includes(l)) &&
    (search === '' || n.name.toLowerCase().includes(search.toLowerCase())),
  )

  return (
    <div className="flex flex-col h-full">
      {/* Toolbar */}
      <div className="flex items-center gap-3 px-5 py-3 border-b border-slate-800 bg-[#080c18] shrink-0">
        <h1 className="text-sm font-semibold text-slate-100">Actor Dashboard</h1>
        <div className="flex-1" />
        <div className="relative w-52">
          <Search size={13} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-500" />
          <Input
            placeholder="Search actors…"
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="pl-7 text-xs h-7"
          />
        </div>
        <span className="text-xs text-slate-600">{actors.length} actors</span>
      </div>

      {/* Grid */}
      <div className="flex-1 overflow-y-auto px-5 py-4">
        {isLoading ? (
          <div className="text-slate-500 text-sm">Loading…</div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3">
            {actors.map(n => <ActorCard key={n.uid} node={n} />)}
          </div>
        )}
      </div>
    </div>
  )
}
