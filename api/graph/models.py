"""
Neomodel node/relationship definitions for the geopolitical ontology graph.
"""
from neomodel import (
    StructuredNode,
    StructuredRel,
    StringProperty,
    FloatProperty,
    IntegerProperty,
    BooleanProperty,
    RelationshipTo,
)


# ─── Relationship Models ──────────────────────────────────────────────────────

class AlliedWithRel(StructuredRel):
    strength = FloatProperty(default=0.5)


class HostileToRel(StructuredRel):
    intensity = FloatProperty(default=0.5)


class HostsBaseRel(StructuredRel):
    pass


class CanStrikeRel(StructuredRel):
    difficulty = FloatProperty(default=0.5)
    weapon_uid = StringProperty()


class DependsOnRel(StructuredRel):
    pct_dependency = FloatProperty(default=0.5)
    daily_volume = FloatProperty(default=0.0)
    resource_type = StringProperty()


class ControlsRel(StructuredRel):
    pass


class ControlsChokepointRel(StructuredRel):
    pass


class FundsRel(StructuredRel):
    annual_usd = FloatProperty(default=0.0)


class ReligiouslyLoyalToRel(StructuredRel):
    pct_population = FloatProperty(default=0.0)


class InvestsInRel(StructuredRel):
    usd_value = FloatProperty(default=0.0)


# ─── Base Nodes ───────────────────────────────────────────────────────────────

class Actor(StructuredNode):
    __abstract_node__ = True

    uid = StringProperty(unique_index=True, required=True)
    name = StringProperty(required=True)
    stability_score = FloatProperty(default=1.0)
    confidence = FloatProperty(default=1.0)
    notes = StringProperty(default="")

    # Relationships (actor ↔ actor)
    allied_with = RelationshipTo("Actor", "ALLIED_WITH", model=AlliedWithRel)
    hostile_to = RelationshipTo("Actor", "HOSTILE_TO", model=HostileToRel)
    funds = RelationshipTo("Actor", "FUNDS", model=FundsRel)
    religiously_loyal_to = RelationshipTo("Actor", "RELIGIOUSLY_LOYAL_TO", model=ReligiouslyLoyalToRel)

    # Actor → Infrastructure
    can_strike = RelationshipTo("Infrastructure", "CAN_STRIKE", model=CanStrikeRel)
    controls = RelationshipTo("Infrastructure", "CONTROLS", model=ControlsRel)
    controls_chokepoint = RelationshipTo("Infrastructure", "CONTROLS_CHOKEPOINT", model=ControlsChokepointRel)
    invests_in = RelationshipTo("Infrastructure", "INVESTS_IN", model=InvestsInRel)

    # Actor → Resource
    depends_on_resource = RelationshipTo("Resource", "DEPENDS_ON", model=DependsOnRel)


class NationState(Actor):
    __label__ = "NationState"

    population = FloatProperty(default=0.0)
    pct_shia = FloatProperty(default=0.0)
    gdp_usd = FloatProperty(default=0.0)
    is_nuclear = BooleanProperty(default=False)
    regime_type = StringProperty(default="democracy")
    latitude = FloatProperty(default=0.0)
    longitude = FloatProperty(default=0.0)

    hosts_base = RelationshipTo("Infrastructure", "HOSTS_BASE", model=HostsBaseRel)
    depends_on_infra = RelationshipTo("Infrastructure", "DEPENDS_ON", model=DependsOnRel)


class MilitaryAlliance(Actor):
    __label__ = "MilitaryAlliance"

    member_count = IntegerProperty(default=0)


class NonStateActor(Actor):
    __label__ = "NonStateActor"

    ideology = StringProperty(default="")
    estimated_fighters = IntegerProperty(default=0)


# ─── Infrastructure ───────────────────────────────────────────────────────────

class Infrastructure(StructuredNode):
    __label__ = "Infrastructure"

    uid = StringProperty(unique_index=True, required=True)
    name = StringProperty(required=True)
    confidence = FloatProperty(default=1.0)
    type = StringProperty(default="")
    daily_capacity = FloatProperty(default=0.0)
    attack_difficulty = FloatProperty(default=0.5)
    collapse_impact = FloatProperty(default=0.5)
    operational = BooleanProperty(default=True)
    latitude = FloatProperty(default=0.0)
    longitude = FloatProperty(default=0.0)
    controlling_actor_uid = StringProperty(default="")
    stability_score = FloatProperty(default=1.0)
    notes = StringProperty(default="")

    # Infrastructure chains
    depends_on = RelationshipTo("Infrastructure", "DEPENDS_ON", model=DependsOnRel)


# ─── Resource ─────────────────────────────────────────────────────────────────

class Resource(StructuredNode):
    __label__ = "Resource"

    uid = StringProperty(unique_index=True, required=True)
    name = StringProperty(required=True)
    type = StringProperty(default="oil")
    unit = StringProperty(default="")


# ─── WeaponSystem ─────────────────────────────────────────────────────────────

class WeaponSystem(StructuredNode):
    __label__ = "WeaponSystem"

    uid = StringProperty(unique_index=True, required=True)
    name = StringProperty(required=True)
    unit_cost_usd = FloatProperty(default=0.0)
    daily_production_rate = IntegerProperty(default=0)
    current_stockpile = IntegerProperty(default=0)
    range_km = FloatProperty(default=0.0)
    effectiveness_vs_infrastructure = FloatProperty(default=0.5)
