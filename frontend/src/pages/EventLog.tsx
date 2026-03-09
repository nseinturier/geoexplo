import { useState, useMemo } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  createColumnHelper, flexRender, getCoreRowModel, getFilteredRowModel,
  getSortedRowModel, useReactTable, type SortingState
} from '@tanstack/react-table'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  Legend, ResponsiveContainer
} from 'recharts'
import { fetchNodes, fetchEvents, createEvent, patchEvent, fetchSnapshots } from '@/api/client'
import type { GeoEvent, EventType } from '@/api/types'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Select } from '@/components/ui/select'
import { Dialog } from '@/components/ui/dialog'
import { StabilityBadge } from '@/components/StabilityBadge'
import { scoreColor } from '@/lib/utils'
import { useScenario } from '@/context/ScenarioContext'
import { Plus, CheckCircle, ArrowUpDown, BarChart2, ChevronUp, ChevronDown } from 'lucide-react'

const EVENT_TYPES: EventType[] = ['strike', 'political', 'economic', 'social', 'diplomatic']

const TYPE_VARIANT: Record<EventType, 'red' | 'blue' | 'amber' | 'purple' | 'green'> = {
  strike: 'red',
  political: 'blue',
  economic: 'amber',
  social: 'purple',
  diplomatic: 'green',
}

const col = createColumnHelper<GeoEvent>()

export function EventLog() {
  const { scenarioId } = useScenario()
  const qc = useQueryClient()

  // Filters
  const [typeFilter, setTypeFilter] = useState('')
  const [confirmedFilter, setConfirmedFilter] = useState('')
  const [actorFilter, setActorFilter] = useState('')
  const [globalFilter, setGlobalFilter] = useState('')
  const [sorting, setSorting] = useState<SortingState>([{ id: 'timestamp', desc: true }])

  // Add event dialog
  const [showAdd, setShowAdd] = useState(false)
  const [form, setForm] = useState<Partial<GeoEvent>>({
    event_type: 'strike',
    confidence: 0.8,
    confirmed: false,
    scenario_id: scenarioId,
    properties: {},
  })

  // Stability chart
  const [chartUid, setChartUid] = useState('')

  const { data: nodes = [] } = useQuery({ queryKey: ['nodes'], queryFn: () => import('@/api/client').then(m => m.fetchNodes()) })
  const nodeMap = useMemo(() => Object.fromEntries(nodes.map(n => [n.uid, n.name])), [nodes])

  const evParams = useMemo(() => {
    const p: Record<string, string> = { scenario_id: scenarioId }
    if (typeFilter) p.event_type = typeFilter
    if (confirmedFilter) p.confirmed = confirmedFilter
    if (actorFilter) p.actor_uid = actorFilter
    return p
  }, [scenarioId, typeFilter, confirmedFilter, actorFilter])

  const { data: events = [], isLoading } = useQuery({
    queryKey: ['events', evParams],
    queryFn: () => fetchEvents(evParams),
  })

  const { data: snapshots = [] } = useQuery({
    queryKey: ['snapshots', chartUid],
    queryFn: () => fetchSnapshots(chartUid),
    enabled: !!chartUid,
  })

  const { mutate: confirmEvent, isPending: confirming } = useMutation({
    mutationFn: (id: string) => patchEvent(id, { confirmed: true } as any),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['events'] }),
  })

  const { mutate: addEvent, isPending: adding } = useMutation({
    mutationFn: () => createEvent({ ...form, scenario_id: scenarioId }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['events'] })
      setShowAdd(false)
      setForm({ event_type: 'strike', confidence: 0.8, confirmed: false, scenario_id: scenarioId, properties: {} })
    },
  })

  const columns = useMemo(() => [
    col.accessor('timestamp', {
      header: ({ column }) => (
        <button
          className="flex items-center gap-1 text-slate-400 hover:text-slate-200"
          onClick={() => column.toggleSorting()}
        >
          Time
          {column.getIsSorted() === 'asc' ? <ChevronUp size={11} /> : column.getIsSorted() === 'desc' ? <ChevronDown size={11} /> : <ArrowUpDown size={11} />}
        </button>
      ),
      cell: info => {
        const d = new Date(info.getValue())
        return (
          <span className="text-xs font-mono text-slate-400">
            {d.toLocaleDateString()} {d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </span>
        )
      },
    }),
    col.accessor('event_type', {
      header: 'Type',
      cell: info => (
        <Badge variant={TYPE_VARIANT[info.getValue()]}>{info.getValue()}</Badge>
      ),
    }),
    col.accessor('actor_uid', {
      header: 'Actor → Target',
      cell: info => {
        const row = info.row.original
        return (
          <span className="text-xs text-slate-300">
            <span className="text-blue-400">{nodeMap[row.actor_uid] ?? row.actor_uid}</span>
            <span className="text-slate-600 mx-1">→</span>
            <span className="text-amber-400">{nodeMap[row.target_uid] ?? row.target_uid}</span>
          </span>
        )
      },
    }),
    col.accessor('description', {
      header: 'Description',
      cell: info => (
        <span className="text-xs text-slate-400 line-clamp-2 max-w-xs">{info.getValue()}</span>
      ),
    }),
    col.accessor('confidence', {
      header: 'Conf.',
      cell: info => (
        <span className="text-xs font-mono text-slate-400">{(info.getValue() * 100).toFixed(0)}%</span>
      ),
    }),
    col.accessor('casualties', {
      header: 'KIA',
      cell: info => (
        <span className="text-xs font-mono text-slate-500">
          {info.getValue() != null ? info.getValue() : '—'}
        </span>
      ),
    }),
    col.accessor('confirmed', {
      header: 'Status',
      cell: info => info.getValue()
        ? <Badge variant="green" className="gap-1"><CheckCircle size={9} />Confirmed</Badge>
        : <Badge variant="amber">Unconfirmed</Badge>,
    }),
    col.display({
      id: 'actions',
      header: '',
      cell: ({ row }) => !row.original.confirmed ? (
        <Button
          size="sm"
          variant="outline"
          className="text-[11px] h-6 px-2 gap-1 text-green-400 border-green-900 hover:bg-green-900/20"
          onClick={() => confirmEvent(row.original.id)}
          disabled={confirming}
        >
          <CheckCircle size={10} /> Confirm
        </Button>
      ) : null,
    }),
  ], [nodeMap, confirmEvent, confirming])

  const table = useReactTable({
    data: events,
    columns,
    state: { sorting, globalFilter },
    onSortingChange: setSorting,
    onGlobalFilterChange: setGlobalFilter,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
  })

  // Stability chart data
  const chartData = useMemo(() => {
    const byScenario: Record<string, { time: string; [key: string]: string | number }[]> = {}
    snapshots.forEach(s => {
      if (!byScenario[s.scenario_id]) byScenario[s.scenario_id] = []
      byScenario[s.scenario_id].push({ time: s.timestamp.slice(0, 16), score: s.stability_score })
    })
    // Merge into single array
    const times = [...new Set(snapshots.map(s => s.timestamp.slice(0, 16)))].sort()
    return times.map(t => {
      const row: Record<string, string | number> = { time: t }
      Object.keys(byScenario).forEach(sid => {
        const match = byScenario[sid].find(x => x.time === t)
        if (match) row[sid] = match.score as number
      })
      return row
    })
  }, [snapshots])

  const scenarioIds = [...new Set(snapshots.map(s => s.scenario_id))]

  return (
    <div className="flex flex-col h-full">
      {/* Toolbar */}
      <div className="flex items-center gap-2 px-5 py-3 border-b border-slate-800 bg-[#080c18] shrink-0 flex-wrap">
        <h1 className="text-sm font-semibold text-slate-100 mr-2">Event Log</h1>

        <Input
          placeholder="Search…"
          value={globalFilter}
          onChange={e => setGlobalFilter(e.target.value)}
          className="w-36 h-7 text-xs"
        />

        <Select value={typeFilter} onChange={e => setTypeFilter(e.target.value)} className="w-32 h-7 text-xs">
          <option value="">All types</option>
          {EVENT_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
        </Select>

        <Select value={confirmedFilter} onChange={e => setConfirmedFilter(e.target.value)} className="w-32 h-7 text-xs">
          <option value="">All status</option>
          <option value="true">Confirmed</option>
          <option value="false">Unconfirmed</option>
        </Select>

        <Select value={actorFilter} onChange={e => setActorFilter(e.target.value)} className="w-40 h-7 text-xs">
          <option value="">All actors</option>
          {nodes.map(n => <option key={n.uid} value={n.uid}>{n.name}</option>)}
        </Select>

        <div className="flex-1" />
        <span className="text-xs text-slate-600">{table.getFilteredRowModel().rows.length} events</span>
        <Button size="sm" onClick={() => setShowAdd(true)} className="gap-1.5">
          <Plus size={12} /> Add Event
        </Button>
      </div>

      {/* Table */}
      <div className="flex-1 overflow-auto px-5 py-3">
        {isLoading ? (
          <div className="text-slate-500 text-sm py-8 text-center">Loading events…</div>
        ) : (
          <table className="w-full text-left border-collapse">
            <thead className="sticky top-0 bg-[#080c18] z-10">
              {table.getHeaderGroups().map(hg => (
                <tr key={hg.id}>
                  {hg.headers.map(h => (
                    <th key={h.id} className="px-3 py-2 text-[11px] font-medium uppercase tracking-wider text-slate-500 border-b border-slate-800 whitespace-nowrap">
                      {flexRender(h.column.columnDef.header, h.getContext())}
                    </th>
                  ))}
                </tr>
              ))}
            </thead>
            <tbody>
              {table.getRowModel().rows.map(row => (
                <tr key={row.id} className="border-b border-slate-800/50 hover:bg-slate-800/20 transition-colors">
                  {row.getVisibleCells().map(cell => (
                    <td key={cell.id} className="px-3 py-2.5">
                      {flexRender(cell.column.columnDef.cell, cell.getContext())}
                    </td>
                  ))}
                </tr>
              ))}
              {table.getRowModel().rows.length === 0 && (
                <tr>
                  <td colSpan={columns.length} className="px-3 py-8 text-center text-slate-600 text-sm">
                    No events found
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        )}
      </div>

      {/* Stability chart */}
      <div className="border-t border-slate-800 px-5 py-4 bg-[#080c18] shrink-0">
        <div className="flex items-center gap-3 mb-3">
          <h2 className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
            <BarChart2 size={13} className="text-blue-400" /> Stability Timeline
          </h2>
          <Select
            value={chartUid}
            onChange={e => setChartUid(e.target.value)}
            className="w-52 h-7 text-xs"
          >
            <option value="">Select object…</option>
            {nodes.map(n => <option key={n.uid} value={n.uid}>{n.name}</option>)}
          </Select>
        </div>

        {chartUid && chartData.length > 0 ? (
          <ResponsiveContainer width="100%" height={180}>
            <LineChart data={chartData} margin={{ top: 4, right: 16, left: 0, bottom: 4 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis
                dataKey="time"
                tick={{ fill: '#475569', fontSize: 10 }}
                tickLine={false}
                axisLine={false}
                tickFormatter={v => v.slice(5)}
              />
              <YAxis
                domain={[0, 1]}
                tick={{ fill: '#475569', fontSize: 10 }}
                tickLine={false}
                axisLine={false}
                tickFormatter={v => `${(v * 100).toFixed(0)}%`}
                width={38}
              />
              <Tooltip
                contentStyle={{ background: '#0d1525', border: '1px solid #1e293b', borderRadius: 6, fontSize: 11 }}
                labelStyle={{ color: '#94a3b8' }}
                formatter={(v: number) => [`${(v * 100).toFixed(1)}%`]}
              />
              <Legend wrapperStyle={{ fontSize: 11 }} />
              {scenarioIds.map((sid, i) => (
                <Line
                  key={sid}
                  type="monotone"
                  dataKey={sid}
                  stroke={['#3b82f6', '#22c55e', '#f59e0b', '#ef4444'][i % 4]}
                  dot={false}
                  strokeWidth={2}
                />
              ))}
            </LineChart>
          </ResponsiveContainer>
        ) : chartUid ? (
          <div className="text-center text-slate-600 text-xs py-6">No snapshots yet — confirm events to generate data</div>
        ) : null}
      </div>

      {/* Add Event dialog */}
      <Dialog open={showAdd} onClose={() => setShowAdd(false)} title="Add Event">
        <div className="space-y-3">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs text-slate-400 block mb-1">Event Type</label>
              <Select
                value={form.event_type}
                onChange={e => setForm(f => ({ ...f, event_type: e.target.value as EventType }))}
              >
                {EVENT_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
              </Select>
            </div>
            <div>
              <label className="text-xs text-slate-400 block mb-1">Confidence</label>
              <input
                type="range" min={0} max={1} step={0.05}
                value={form.confidence ?? 0.8}
                onChange={e => setForm(f => ({ ...f, confidence: Number(e.target.value) }))}
                className="w-full accent-blue-500"
              />
              <div className="text-right text-[10px] text-slate-500 font-mono">
                {((form.confidence ?? 0.8) * 100).toFixed(0)}%
              </div>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs text-slate-400 block mb-1">Actor</label>
              <Select
                value={form.actor_uid ?? ''}
                onChange={e => setForm(f => ({ ...f, actor_uid: e.target.value }))}
              >
                <option value="">Select…</option>
                {nodes.map(n => <option key={n.uid} value={n.uid}>{n.name}</option>)}
              </Select>
            </div>
            <div>
              <label className="text-xs text-slate-400 block mb-1">Target</label>
              <Select
                value={form.target_uid ?? ''}
                onChange={e => setForm(f => ({ ...f, target_uid: e.target.value }))}
              >
                <option value="">Select…</option>
                {nodes.map(n => <option key={n.uid} value={n.uid}>{n.name}</option>)}
              </Select>
            </div>
          </div>

          <div>
            <label className="text-xs text-slate-400 block mb-1">Description</label>
            <textarea
              rows={3}
              value={form.description ?? ''}
              onChange={e => setForm(f => ({ ...f, description: e.target.value }))}
              className="w-full rounded border border-slate-700 bg-slate-900 px-2 py-1.5 text-xs text-slate-100 resize-none focus:outline-none focus:ring-1 focus:ring-blue-500"
              placeholder="Describe the event…"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs text-slate-400 block mb-1">Casualties</label>
              <Input
                type="number" min={0}
                value={form.casualties ?? ''}
                onChange={e => setForm(f => ({ ...f, casualties: e.target.value ? Number(e.target.value) : undefined }))}
                placeholder="0"
                className="text-xs"
              />
            </div>
            <div className="flex items-end pb-1">
              <label className="flex items-center gap-2 text-xs text-slate-400">
                <input
                  type="checkbox"
                  checked={form.confirmed ?? false}
                  onChange={e => setForm(f => ({ ...f, confirmed: e.target.checked }))}
                  className="accent-blue-500"
                />
                Confirmed (triggers cascade)
              </label>
            </div>
          </div>

          <div className="flex gap-2 justify-end pt-2 border-t border-slate-800">
            <Button variant="ghost" size="sm" onClick={() => setShowAdd(false)}>Cancel</Button>
            <Button
              size="sm"
              onClick={() => addEvent()}
              disabled={adding || !form.actor_uid || !form.target_uid}
            >
              {adding ? 'Submitting…' : 'Submit Event'}
            </Button>
          </div>
        </div>
      </Dialog>
    </div>
  )
}
