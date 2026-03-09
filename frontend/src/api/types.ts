export interface RelationshipData {
  type: string
  props: Record<string, unknown>
  target_uid?: string
  target_name?: string
  target_labels?: string[]
  source_uid?: string
  source_name?: string
  source_labels?: string[]
}

export interface GraphNode {
  uid: string
  name: string
  _labels: string[]
  stability_score?: number
  confidence?: number
  notes?: string
  // NationState
  latitude?: number
  longitude?: number
  is_nuclear?: boolean
  regime_type?: string
  gdp_usd?: number
  pct_shia?: number
  population?: number
  // Infrastructure
  type?: string
  operational?: boolean
  collapse_impact?: number
  attack_difficulty?: number
  daily_capacity?: number
  controlling_actor_uid?: string
  // NonStateActor
  ideology?: string
  estimated_fighters?: number
  // Relationships (only in detail response)
  outgoing_relationships?: RelationshipData[]
  incoming_relationships?: RelationshipData[]
}

export interface Edge {
  source_uid: string
  target_uid: string
  rel_type: string
  rel_props: Record<string, unknown>
}

export type EventType = 'strike' | 'political' | 'economic' | 'social' | 'diplomatic'

export interface GeoEvent {
  id: string
  timestamp: string
  scenario_id: string
  event_type: EventType
  actor_uid: string
  target_uid: string
  description: string
  confirmed: boolean
  confidence: number
  casualties?: number
  properties: Record<string, unknown>
  created_at: string
}

export interface Scenario {
  id: string
  name: string
  description: string
  forked_from?: string
  is_production: boolean
  created_at: string
}

export interface CascadeAffected {
  uid: string
  name: string
  old_score: number
  new_score: number
  depth: number
  operational: boolean
}

export interface CascadeResult {
  source_uid: string
  impact: number
  affected: CascadeAffected[]
}

export interface StabilitySnapshot {
  id: string
  timestamp: string
  scenario_id: string
  object_uid: string
  stability_score: number
  water_stress?: number
  notes?: string
}

export interface PathItem {
  type: 'node' | 'relationship'
  uid?: string
  name?: string
  labels?: string[]
  rel_type?: string
}

export interface ActorRisk {
  uid: string
  name: string
  stability_score: number
  enemy_count: number
  attacker_count: number
  exposed_infrastructure: number
  dependency_count: number
  composite_risk: number
}
