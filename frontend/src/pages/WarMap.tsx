import { useState, useCallback } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { MapContainer, TileLayer, CircleMarker, Tooltip, useMap } from 'react-leaflet'
import { fetchNodes, patchNode } from '@/api/client'
import type { GraphNode } from '@/api/types'
import { scoreColor } from '@/lib/utils'
import { StabilityBadge } from '@/components/StabilityBadge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { X, Edit2, Save, AlertTriangle, Zap } from 'lucide-react'

const LAYER_TYPES: Record<string, string[]> = {
  'Nation States': ['NationState'],
  'Military Bases': ['military_base'],
  'Oil Fields': ['oil_field'],
  'Chokepoints': ['chokepoint'],
  'Desalination': ['desalination'],
  'Financial': ['financial_market'],
  'Ports': ['port'],
}

function FitBounds({ nodes }: { nodes: GraphNode[] }) {
  useMap() // just to satisfy hook rules; bounds set on load
  return null
}

export function WarMap() {
  const qc = useQueryClient()
  const { data: allNodes = [], isLoading } = useQuery({
    queryKey: ['nodes'],
    queryFn: () => fetchNodes(),
  })

  const [selected, setSelected] = useState<GraphNode | null>(null)
  const [editing, setEditing] = useState(false)
  const [editVals, setEditVals] = useState<Partial<GraphNode>>({})
  const [layers, setLayers] = useState<Record<string, boolean>>({
    'Nation States': true,
    'Military Bases': true,
    'Oil Fields': true,
    'Chokepoints': true,
    'Desalination': true,
    'Financial': true,
    'Ports': true,
  })

  const { mutate: saveNode, isPending: saving } = useMutation({
    mutationFn: () => patchNode(selected!.uid, editVals),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['nodes'] })
      setEditing(false)
      setEditVals({})
    },
  })

  const shouldShow = useCallback(
    (n: GraphNode) => {
      const labels = n._labels ?? []
      if (labels.includes('NationState') && layers['Nation States']) return true
      const type = n.type ?? ''
      if (type === 'military_base' && layers['Military Bases']) return true
      if (type === 'oil_field' && layers['Oil Fields']) return true
      if (type === 'chokepoint' && layers['Chokepoints']) return true
      if (type === 'desalination' && layers['Desalination']) return true
      if (type === 'financial_market' && layers['Financial']) return true
      if (type === 'port' && layers['Ports']) return true
      return false
    },
    [layers],
  )

  const markers = allNodes.filter(
    n => n.latitude !== undefined && n.longitude !== undefined && shouldShow(n),
  )

  const isNation = (n: GraphNode) => (n._labels ?? []).includes('NationState')

  return (
    <div className="flex h-full">
      {/* Map */}
      <div className="flex-1 relative">
        {isLoading && (
          <div className="absolute inset-0 z-10 flex items-center justify-center bg-[#080c18]/80">
            <span className="text-slate-400 text-sm">Loading nodes…</span>
          </div>
        )}
        <MapContainer
          center={[25.5, 52]}
          zoom={5}
          style={{ height: '100%', width: '100%', background: '#080c18' }}
          zoomControl={true}
        >
          <TileLayer
            attribution='&copy; <a href="https://carto.com">CartoDB</a>'
            url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
            subdomains="abcd"
            maxZoom={19}
          />
          {markers.map(n => (
            <CircleMarker
              key={n.uid}
              center={[n.latitude!, n.longitude!]}
              radius={isNation(n) ? 10 : 7}
              pathOptions={{
                fillColor: scoreColor(n.stability_score),
                color: n.operational === false ? '#ef4444' : scoreColor(n.stability_score),
                weight: n.operational === false ? 2 : 1,
                fillOpacity: 0.85,
                opacity: 1,
                dashArray: n.operational === false ? '4' : undefined,
              }}
              eventHandlers={{
                click: () => {
                  setSelected(n)
                  setEditing(false)
                  setEditVals({})
                },
              }}
            >
              <Tooltip direction="top" offset={[0, -8]} opacity={0.95}>
                <div className="text-xs">
                  <div className="font-semibold">{n.name}</div>
                  <div>Score: {((n.stability_score ?? 1) * 100).toFixed(0)}%</div>
                  {n.type && <div>Type: {n.type}</div>}
                  {n.operational === false && <div className="text-red-400">⚠ Non-operational</div>}
                </div>
              </Tooltip>
            </CircleMarker>
          ))}
        </MapContainer>

        {/* Layer toggles */}
        <div className="absolute bottom-6 left-4 z-[1000] bg-[#0d1525]/90 border border-slate-800 rounded-lg p-3 space-y-1.5 backdrop-blur">
          <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-500 mb-2">Layers</p>
          {Object.keys(LAYER_TYPES).map(name => (
            <label key={name} className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={layers[name]}
                onChange={e => setLayers(l => ({ ...l, [name]: e.target.checked }))}
                className="accent-blue-500 w-3.5 h-3.5"
              />
              <span className="text-xs text-slate-300">{name}</span>
            </label>
          ))}
        </div>

        {/* Legend */}
        <div className="absolute bottom-6 right-4 z-[1000] bg-[#0d1525]/90 border border-slate-800 rounded-lg px-3 py-2 flex gap-4 text-xs backdrop-blur">
          <span className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-green-500 inline-block" />
            Stable ≥70%
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-amber-500 inline-block" />
            Stressed 40–70%
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-red-500 inline-block" />
            Critical &lt;40%
          </span>
        </div>
      </div>

      {/* Selected node panel */}
      {selected && (
        <aside className="w-80 border-l border-slate-800 bg-[#0d1525] overflow-y-auto flex flex-col">
          {/* Header */}
          <div className="flex items-center justify-between px-4 py-3 border-b border-slate-800 shrink-0">
            <div>
              <h2 className="text-sm font-semibold text-slate-100">{selected.name}</h2>
              <div className="flex gap-1 mt-1 flex-wrap">
                {selected._labels?.map(l => (
                  <span key={l} className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-400">{l}</span>
                ))}
              </div>
            </div>
            <button onClick={() => setSelected(null)} className="text-slate-500 hover:text-slate-200 shrink-0">
              <X size={16} />
            </button>
          </div>

          <div className="flex-1 px-4 py-3 space-y-4">
            {/* Stability */}
            <div className="flex items-center justify-between">
              <span className="text-xs text-slate-400">Stability</span>
              <StabilityBadge score={selected.stability_score} />
            </div>

            {selected.operational === false && (
              <div className="flex items-center gap-2 text-xs text-red-400 bg-red-900/20 border border-red-900/40 rounded px-3 py-2">
                <AlertTriangle size={13} />
                Non-operational
              </div>
            )}

            {/* Properties table */}
            {!editing && (
              <div className="space-y-1.5">
                {[
                  ['Type', selected.type],
                  ['Regime', selected.regime_type],
                  ['Nuclear', selected.is_nuclear ? '☢ Yes' : selected.is_nuclear === false ? 'No' : undefined],
                  ['GDP', selected.gdp_usd ? `$${(selected.gdp_usd / 1e12).toFixed(1)}T` : undefined],
                  ['Population', selected.population ? `${(selected.population / 1e6).toFixed(0)}M` : undefined],
                  ['Shia %', selected.pct_shia != null ? `${(selected.pct_shia * 100).toFixed(0)}%` : undefined],
                  ['Collapse Impact', selected.collapse_impact?.toFixed(2)],
                  ['Attack Difficulty', selected.attack_difficulty?.toFixed(2)],
                  ['Confidence', selected.confidence?.toFixed(2)],
                  ['Controlling Actor', selected.controlling_actor_uid],
                ].filter(([, v]) => v !== undefined).map(([k, v]) => (
                  <div key={String(k)} className="flex items-center justify-between text-xs">
                    <span className="text-slate-500">{k}</span>
                    <span className="text-slate-200 font-mono">{String(v)}</span>
                  </div>
                ))}
              </div>
            )}

            {/* Notes */}
            {!editing && selected.notes && (
              <div>
                <p className="text-[10px] uppercase tracking-wider text-slate-500 mb-1">Notes</p>
                <p className="text-xs text-slate-300 leading-relaxed">{selected.notes}</p>
              </div>
            )}

            {/* Edit form */}
            {editing && (
              <div className="space-y-3">
                <div>
                  <label className="text-xs text-slate-400 block mb-1">Stability Score</label>
                  <input
                    type="range" min={0} max={1} step={0.01}
                    value={editVals.stability_score ?? selected.stability_score ?? 1}
                    onChange={e => setEditVals(v => ({ ...v, stability_score: Number(e.target.value) }))}
                    className="w-full accent-blue-500"
                  />
                  <div className="text-right text-xs text-slate-400 font-mono">
                    {((editVals.stability_score ?? selected.stability_score ?? 1) * 100).toFixed(0)}%
                  </div>
                </div>

                <div>
                  <label className="text-xs text-slate-400 block mb-1">Confidence</label>
                  <input
                    type="range" min={0} max={1} step={0.01}
                    value={editVals.confidence ?? selected.confidence ?? 1}
                    onChange={e => setEditVals(v => ({ ...v, confidence: Number(e.target.value) }))}
                    className="w-full accent-blue-500"
                  />
                  <div className="text-right text-xs text-slate-400 font-mono">
                    {((editVals.confidence ?? selected.confidence ?? 1) * 100).toFixed(0)}%
                  </div>
                </div>

                {'operational' in selected && (
                  <label className="flex items-center gap-2 text-xs text-slate-300">
                    <input
                      type="checkbox"
                      checked={editVals.operational ?? selected.operational ?? true}
                      onChange={e => setEditVals(v => ({ ...v, operational: e.target.checked }))}
                      className="accent-blue-500"
                    />
                    Operational
                  </label>
                )}

                <div>
                  <label className="text-xs text-slate-400 block mb-1">Notes</label>
                  <textarea
                    rows={3}
                    value={editVals.notes ?? selected.notes ?? ''}
                    onChange={e => setEditVals(v => ({ ...v, notes: e.target.value }))}
                    className="w-full rounded border border-slate-700 bg-slate-900 px-2 py-1.5 text-xs text-slate-100 resize-none focus:outline-none focus:ring-1 focus:ring-blue-500"
                  />
                </div>
              </div>
            )}
          </div>

          {/* Actions */}
          <div className="px-4 py-3 border-t border-slate-800 flex gap-2 shrink-0">
            {!editing ? (
              <Button size="sm" variant="secondary" onClick={() => setEditing(true)} className="gap-1.5">
                <Edit2 size={12} /> Edit
              </Button>
            ) : (
              <>
                <Button size="sm" onClick={() => saveNode()} disabled={saving} className="gap-1.5">
                  <Save size={12} /> {saving ? 'Saving…' : 'Save'}
                </Button>
                <Button size="sm" variant="ghost" onClick={() => { setEditing(false); setEditVals({}) }}>
                  Cancel
                </Button>
              </>
            )}
          </div>
        </aside>
      )}
    </div>
  )
}
