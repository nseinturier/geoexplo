import axios from 'axios'
import { QueryClient } from '@tanstack/react-query'
import type {
  GraphNode, Edge, GeoEvent, Scenario, CascadeResult,
  StabilitySnapshot, ActorRisk
} from './types'

const BASE = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

export const api = axios.create({ baseURL: BASE })

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 10_000,
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
})

// ─── Nodes ────────────────────────────────────────────────────────────────────

export const fetchNodes = (type?: string) =>
  api.get<GraphNode[]>('/objects', { params: type ? { type } : {} }).then(r => r.data)

export const fetchNode = (uid: string) =>
  api.get<GraphNode>(`/objects/${uid}`).then(r => r.data)

export const fetchEdges = () =>
  api.get<Edge[]>('/objects/edges/all').then(r => r.data)

export const patchNode = (uid: string, props: Partial<GraphNode>) =>
  api.patch<GraphNode>(`/objects/${uid}`, props).then(r => r.data)

export const fetchNeighbors = (uid: string) =>
  api.get<GraphNode[]>(`/objects/${uid}/neighbors`).then(r => r.data)

// ─── Events ───────────────────────────────────────────────────────────────────

export const fetchEvents = (params?: Record<string, string>) =>
  api.get<GeoEvent[]>('/events', { params }).then(r => r.data)

export const createEvent = (body: Partial<GeoEvent>) =>
  api.post<GeoEvent>('/events', body).then(r => r.data)

export const patchEvent = (id: string, body: Partial<GeoEvent>) =>
  api.patch<GeoEvent>(`/events/${id}`, body).then(r => r.data)

// ─── Scenarios ────────────────────────────────────────────────────────────────

export const fetchScenarios = () =>
  api.get<Scenario[]>('/scenarios').then(r => r.data)

export const forkScenario = (name: string, description: string) =>
  api.post<Scenario>('/scenarios/fork', { name, description }).then(r => r.data)

export const compareScenario = (id: string) =>
  api.get(`/scenarios/${id}/compare`).then(r => r.data)

export const deleteScenario = (id: string) =>
  api.delete(`/scenarios/${id}`).then(r => r.data)

export const fetchSnapshots = (uid: string) =>
  api.get<StabilitySnapshot[]>(`/scenarios/snapshots/${uid}`).then(r => r.data)

// ─── Cascade ──────────────────────────────────────────────────────────────────

export const simulateCascade = (body: {
  source_uid: string
  impact: number
  max_depth: number
  persist: boolean
  scenario_id: string
}) => api.post<CascadeResult>('/cascade/simulate', body).then(r => r.data)

// ─── Analytics ────────────────────────────────────────────────────────────────

export const fetchMostVulnerable = () =>
  api.get('/analytics/most_vulnerable').then(r => r.data)

export const fetchChokepoints = () =>
  api.get('/analytics/chokepoints').then(r => r.data)

export const fetchActorRisk = (uid: string) =>
  api.get<ActorRisk>(`/analytics/actor_risk/${uid}`).then(r => r.data)
