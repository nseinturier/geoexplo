import { useState, useRef, useCallback, useMemo } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import ForceGraph2D, { type ForceGraphMethods } from 'react-force-graph-2d'
import { fetchNodes, fetchEdges, simulateCascade } from '@/api/client'
import type { CascadeAffected } from '@/api/types'
import { scoreColor } from '@/lib/utils'
import { StabilityBadge } from '@/components/StabilityBadge'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Slider } from '@/components/ui/slider'
import { Zap, X, RotateCcw, GitBranch } from 'lucide-react'
import { useScenario } from '@/context/ScenarioContext'

const REL_COLORS: Record<string, string> = {
  ALLIED_WITH: '#22c55e',
  HOSTILE_TO: '#ef4444',
  DEPENDS_ON: '#3b82f6',
  CAN_STRIKE: '#f97316',
  CONTROLS: '#8b5cf6',
  CONTROLS_CHOKEPOINT: '#a855f7',
  HOSTS_BASE: '#06b6d4',
  FUNDS: '#f59e0b',
  INVESTS_IN: '#10b981',
  RELIGIOUSLY_LOYAL_TO: '#ec4899',
}

const ALL_REL_TYPES = Object.keys(REL_COLORS)

const EVENT_TYPE_COLORS: Record<string, 'green' | 'amber' | 'red' | 'blue' | 'purple'> = {
  strike: 'red',
  political: 'blue',
  economic: 'amber',
  social: 'purple',
  diplomatic: 'green',
}

interface FGNode {
  id: string
  name: string
  labels: string[]
  stability_score: number
  color: string
  size: number
  cascadeAffected?: boolean
}

interface FGLink {
  source: string
  target: string
  rel_type: string
  color: string
}

export function GraphExplorer() {
  const { scenarioId } = useScenario()
  const graphRef = useRef<ForceGraphMethods<FGNode, FGLink> | undefined>(undefined)

  const { data: nodes = [] } = useQuery({ queryKey: ['nodes'], queryFn: () => import('@/api/client').then(m => m.fetchNodes()) })
  const { data: edges = [] } = useQuery({ queryKey: ['edges'], queryFn: fetchEdges })

  const [selectedNode, setSelectedNode] = useState<FGNode | null>(null)
  const [cascadeResults, setCascadeResults] = useState<CascadeAffected[]>([])
  const [impact, setImpact] = useState(0.7)
  const [maxDepth, setMaxDepth] = useState(6)
  const [persist, setPersist] = useState(false)
  const [visibleRels, setVisibleRels] = useState<Set<string>>(new Set(ALL_REL_TYPES))

  const affectedUids = useMemo(() => new Set(cascadeResults.map(r => r.uid)), [cascadeResults])

  const fgNodes: FGNode[] = useMemo(() => nodes.map(n => ({
    id: n.uid,
    name: n.name,
    labels: n._labels ?? [],
    stability_score: n.stability_score ?? 1,
    color: affectedUids.has(n.uid) ? '#f97316' : scoreColor(n.stability_score),
    size: (n._labels ?? []).includes('NationState') ? 6 : 4,
    cascadeAffected: affectedUids.has(n.uid),
  })), [nodes, affectedUids])

  const fgLinks: FGLink[] = useMemo(() => edges
    .filter(e => visibleRels.has(e.rel_type))
    .map(e => ({
      source: e.source_uid,
      target: e.target_uid,
      rel_type: e.rel_type,
      color: REL_COLORS[e.rel_type] ?? '#475569',
    })), [edges, visibleRels])

  const { mutate: runCascade, isPending: simulating } = useMutation({
    mutationFn: () => simulateCascade({
      source_uid: selectedNode!.id,
      impact,
      max_depth: maxDepth,
      persist,
      scenario_id: scenarioId,
    }),
    onSuccess: data => setCascadeResults(data.affected),
  })

  const handleNodeClick = useCallback((node: FGNode) => {
    setSelectedNode(node)
    setCascadeResults([])
    graphRef.current?.centerAt((node as any).x, (node as any).y, 600)
    graphRef.current?.zoom(4, 600)
  }, [])

  const toggleRel = (rel: string) =>
    setVisibleRels(prev => {
      const next = new Set(prev)
      next.has(rel) ? next.delete(rel) : next.add(rel)
      return next
    })

  return (
    <div className="flex h-full">
      {/* Left controls panel */}
      <div className="w-56 border-r border-slate-800 bg-[#080c18] flex flex-col overflow-y-auto shrink-0">
        <div className="p-3 border-b border-slate-800">
          <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-500 mb-2">Relationship Types</p>
          <div className="space-y-1">
            {ALL_REL_TYPES.map(rel => (
              <label key={rel} className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={visibleRels.has(rel)}
                  onChange={() => toggleRel(rel)}
                  className="accent-blue-500 w-3 h-3"
                />
                <span className="w-2 h-2 rounded-full shrink-0" style={{ background: REL_COLORS[rel] }} />
                <span className="text-[11px] text-slate-400 truncate">{rel.replace(/_/g, ' ')}</span>
              </label>
            ))}
          </div>
        </div>

        {/* Legend */}
        <div className="p-3 border-b border-slate-800 space-y-1.5">
          <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-500 mb-2">Nodes</p>
          <div className="flex items-center gap-2 text-xs text-slate-400">
            <span className="w-3 h-3 rounded-full bg-green-500 shrink-0" /> Stable
          </div>
          <div className="flex items-center gap-2 text-xs text-slate-400">
            <span className="w-3 h-3 rounded-full bg-amber-500 shrink-0" /> Stressed
          </div>
          <div className="flex items-center gap-2 text-xs text-slate-400">
            <span className="w-3 h-3 rounded-full bg-red-500 shrink-0" /> Critical
          </div>
          <div className="flex items-center gap-2 text-xs text-slate-400">
            <span className="w-3 h-3 rounded-full bg-orange-400 shrink-0" /> Cascade Hit
          </div>
        </div>

        {/* Stats */}
        <div className="p-3 text-xs text-slate-500 space-y-1">
          <div>{fgNodes.length} nodes · {fgLinks.length} links</div>
          {cascadeResults.length > 0 && (
            <div className="text-orange-400">{cascadeResults.length} nodes affected</div>
          )}
        </div>
      </div>

      {/* Graph */}
      <div className="flex-1 relative bg-[#060a14]">
        <ForceGraph2D
          ref={graphRef}
          graphData={{ nodes: fgNodes, links: fgLinks }}
          nodeId="id"
          nodeLabel="name"
          nodeColor="color"
          nodeVal="size"
          linkColor="color"
          linkDirectionalArrowLength={4}
          linkDirectionalArrowRelPos={1}
          linkWidth={1}
          backgroundColor="#060a14"
          onNodeClick={handleNodeClick}
          nodeCanvasObject={(node, ctx, globalScale) => {
            const n = node as FGNode & { x: number; y: number }
            const r = n.size ?? 4
            ctx.beginPath()
            ctx.arc(n.x, n.y, r, 0, 2 * Math.PI)
            ctx.fillStyle = n.color
            ctx.fill()
            if (n.cascadeAffected) {
              ctx.strokeStyle = '#fb923c'
              ctx.lineWidth = 1.5
              ctx.stroke()
            }
            if (selectedNode?.id === n.id) {
              ctx.strokeStyle = '#fff'
              ctx.lineWidth = 1.5
              ctx.stroke()
            }
            if (globalScale > 2.5) {
              const label = n.name
              ctx.font = `${10 / globalScale}px Inter`
              ctx.fillStyle = '#e2e8f0'
              ctx.textAlign = 'center'
              ctx.fillText(label, n.x, n.y + r + 8 / globalScale)
            }
          }}
          cooldownTicks={100}
        />

        {/* No selection hint */}
        {!selectedNode && (
          <div className="absolute top-4 left-1/2 -translate-x-1/2 text-xs text-slate-600 bg-[#0d1525]/80 px-3 py-1.5 rounded-full border border-slate-800">
            Click a node to inspect or simulate
          </div>
        )}
      </div>

      {/* Right panel — node detail + cascade controls */}
      {selectedNode && (
        <aside className="w-72 border-l border-slate-800 bg-[#0d1525] flex flex-col overflow-y-auto shrink-0">
          <div className="flex items-center justify-between px-4 py-3 border-b border-slate-800 shrink-0">
            <div>
              <p className="text-sm font-semibold text-slate-100">{selectedNode.name}</p>
              <div className="flex gap-1 mt-1">
                {selectedNode.labels.map(l => (
                  <span key={l} className="text-[10px] px-1 py-0.5 rounded bg-slate-800 text-slate-500">{l}</span>
                ))}
              </div>
            </div>
            <button onClick={() => { setSelectedNode(null); setCascadeResults([]) }} className="text-slate-500 hover:text-slate-200">
              <X size={15} />
            </button>
          </div>

          <div className="flex-1 px-4 py-3 space-y-5">
            {/* Stability */}
            <div className="flex items-center justify-between">
              <span className="text-xs text-slate-400">Stability</span>
              <StabilityBadge score={selectedNode.stability_score} />
            </div>

            {/* Cascade simulator */}
            <div className="space-y-3 border-t border-slate-800 pt-4">
              <p className="text-xs font-semibold text-slate-300 flex items-center gap-2">
                <Zap size={13} className="text-amber-400" /> Strike Simulation
              </p>
              <Slider label="Impact" value={impact} onChange={setImpact} min={0} max={1} step={0.05} />
              <Slider label="Max Depth" value={maxDepth} onChange={setMaxDepth} min={1} max={10} step={1} />
              <label className="flex items-center gap-2 text-xs text-slate-400">
                <input
                  type="checkbox"
                  checked={persist}
                  onChange={e => setPersist(e.target.checked)}
                  className="accent-blue-500"
                />
                Persist to database
              </label>
              <Button
                onClick={() => runCascade()}
                disabled={simulating}
                className="w-full gap-2"
                size="sm"
              >
                <Zap size={12} />
                {simulating ? 'Simulating…' : 'Simulate Strike'}
              </Button>
            </div>

            {/* Cascade results */}
            {cascadeResults.length > 0 && (
              <div className="space-y-2 border-t border-slate-800 pt-4">
                <div className="flex items-center justify-between">
                  <p className="text-xs font-semibold text-orange-400">
                    {cascadeResults.length} nodes affected
                  </p>
                  <button
                    onClick={() => setCascadeResults([])}
                    className="text-slate-600 hover:text-slate-400"
                  >
                    <RotateCcw size={12} />
                  </button>
                </div>
                <div className="space-y-1 max-h-64 overflow-y-auto">
                  {cascadeResults.slice(0, 20).map(r => (
                    <div key={r.uid} className="flex items-center justify-between text-xs py-1 border-b border-slate-800/50">
                      <div>
                        <span className="text-slate-200">{r.name}</span>
                        <span className="text-slate-600 ml-1">d:{r.depth}</span>
                      </div>
                      <div className="flex items-center gap-1 font-mono text-[10px]">
                        <span className="text-slate-500">{(r.old_score * 100).toFixed(0)}%</span>
                        <span className="text-slate-700">→</span>
                        <span className="text-red-400">{(r.new_score * 100).toFixed(0)}%</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </aside>
      )}
    </div>
  )
}
