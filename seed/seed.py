"""
Seed both Neo4j and PostgreSQL databases with geopolitical data.
Run with: docker-compose run --rm api python /seed/seed.py
"""
import sys
import os
import uuid
from datetime import datetime, timedelta

# Resolve paths robustly for Docker (WORKDIR=/app == api dir)
_script_dir = os.path.dirname(os.path.abspath(__file__))

# In Docker: /app is the api dir (mounted from ./api)
if os.path.exists("/app/main.py"):
    sys.path.insert(0, "/app")
else:
    # Local dev: seed/ is next to api/
    sys.path.insert(0, os.path.join(_script_dir, "..", "api"))

# Load .env from project root
_env_candidates = [
    os.path.join(_script_dir, "..", ".env"),
    "/.env",
    "/app/../.env",
]
from dotenv import load_dotenv
for _env in _env_candidates:
    if os.path.exists(_env):
        load_dotenv(_env)
        break

# ─── Neo4j / neomodel setup ───────────────────────────────────────────────────

from neomodel import config as neomodel_config, db as neo_db

neo4j_url = os.getenv("NEO4J_URL", "bolt://neo4j:7687")
neo4j_user = os.getenv("NEO4J_USER", "neo4j")
neo4j_password = os.getenv("NEO4J_PASSWORD", "password")
neomodel_config.DATABASE_URL = neo4j_url.replace("bolt://", f"bolt://{neo4j_user}:{neo4j_password}@")

from graph.models import (
    NationState, MilitaryAlliance, NonStateActor,
    Infrastructure, Resource, WeaponSystem,
)

# ─── PostgreSQL setup ─────────────────────────────────────────────────────────

from relational.database import engine, SessionLocal, Base
from relational.models import Event, EventType, Scenario, StabilitySnapshot

Base.metadata.create_all(bind=engine)
db = SessionLocal()

# ─── Helper ───────────────────────────────────────────────────────────────────

def clear_neo4j():
    print("Clearing Neo4j...")
    neo_db.cypher_query("MATCH (n) DETACH DELETE n")


def get_or_create_nation(uid, name, **kwargs) -> NationState:
    existing = NationState.nodes.get_or_none(uid=uid)
    if existing:
        return existing
    node = NationState(uid=uid, name=name, **kwargs)
    node.save()
    return node


def get_or_create_infra(uid, name, **kwargs) -> Infrastructure:
    existing = Infrastructure.nodes.get_or_none(uid=uid)
    if existing:
        return existing
    node = Infrastructure(uid=uid, name=name, **kwargs)
    node.save()
    return node


def get_or_create_nsa(uid, name, **kwargs) -> NonStateActor:
    existing = NonStateActor.nodes.get_or_none(uid=uid)
    if existing:
        return existing
    node = NonStateActor(uid=uid, name=name, **kwargs)
    node.save()
    return node


def get_or_create_resource(uid, name, **kwargs) -> Resource:
    existing = Resource.nodes.get_or_none(uid=uid)
    if existing:
        return existing
    node = Resource(uid=uid, name=name, **kwargs)
    node.save()
    return node


# ─────────────────────────────────────────────────────────────────────────────
#  NEO4J SEED
# ─────────────────────────────────────────────────────────────────────────────

print("Seeding Neo4j...")
clear_neo4j()

# ─── Nation States ────────────────────────────────────────────────────────────

iran = get_or_create_nation(
    "iran", "Iran",
    population=86e6,
    pct_shia=0.95,
    gdp_usd=363e9,
    is_nuclear=False,
    regime_type="theocracy",
    stability_score=0.65,
    confidence=0.9,
    latitude=32.4279,
    longitude=53.6880,
    notes="Supreme Leader: Khamenei. IRGC controls key assets.",
)

us = get_or_create_nation(
    "us", "United States",
    population=335e6,
    pct_shia=0.01,
    gdp_usd=26e12,
    is_nuclear=True,
    regime_type="democracy",
    stability_score=0.85,
    confidence=0.95,
    latitude=37.0902,
    longitude=-95.7129,
    notes="NATO leader. Major military presence in Gulf.",
)

israel = get_or_create_nation(
    "israel", "Israel",
    population=9e6,
    pct_shia=0.02,
    gdp_usd=525e9,
    is_nuclear=True,
    regime_type="democracy",
    stability_score=0.75,
    confidence=0.9,
    latitude=31.0461,
    longitude=34.8516,
    notes="Advanced military. Samson Option.",
)

bahrain = get_or_create_nation(
    "bahrain", "Bahrain",
    population=1.7e6,
    pct_shia=0.55,
    gdp_usd=44e9,
    is_nuclear=False,
    regime_type="monarchy",
    stability_score=0.4,
    confidence=0.85,
    latitude=26.0667,
    longitude=50.5577,
    notes="Shia majority under Sunni Al Khalifa rule. High internal tension.",
)

uae = get_or_create_nation(
    "uae", "United Arab Emirates",
    population=9.9e6,
    pct_shia=0.15,
    gdp_usd=499e9,
    is_nuclear=False,
    regime_type="monarchy",
    stability_score=0.5,
    confidence=0.85,
    latitude=23.4241,
    longitude=53.8478,
    notes="Dubai airport attacked. Desalination highly vulnerable.",
)

saudi = get_or_create_nation(
    "saudi", "Saudi Arabia",
    population=35e6,
    pct_shia=0.15,
    gdp_usd=1.1e12,
    is_nuclear=False,
    regime_type="monarchy",
    stability_score=0.7,
    confidence=0.88,
    latitude=23.8859,
    longitude=45.0792,
    notes="ARAMCO backbone of global oil supply. Vision 2030.",
)

qatar = get_or_create_nation(
    "qatar", "Qatar",
    population=2.9e6,
    pct_shia=0.15,
    gdp_usd=235e9,
    is_nuclear=False,
    regime_type="monarchy",
    stability_score=0.75,
    confidence=0.88,
    latitude=25.3548,
    longitude=51.1839,
    notes="Hosts Al Udeid Air Base. LNG major exporter.",
)

kuwait = get_or_create_nation(
    "kuwait", "Kuwait",
    population=4.6e6,
    pct_shia=0.25,
    gdp_usd=164e9,
    is_nuclear=False,
    regime_type="monarchy",
    stability_score=0.72,
    confidence=0.87,
    latitude=29.3117,
    longitude=47.4818,
    notes="Oil-dependent. Shia minority politically active.",
)

oman = get_or_create_nation(
    "oman", "Oman",
    population=4.5e6,
    pct_shia=0.05,
    gdp_usd=114e9,
    is_nuclear=False,
    regime_type="monarchy",
    stability_score=0.78,
    confidence=0.87,
    latitude=21.5126,
    longitude=55.9233,
    notes="Borders Strait of Hormuz. Neutral mediator. Powers Gulf coast infra.",
)

russia = get_or_create_nation(
    "russia", "Russia",
    population=144e6,
    pct_shia=0.02,
    gdp_usd=1.8e12,
    is_nuclear=True,
    regime_type="authoritarian",
    stability_score=0.6,
    confidence=0.8,
    latitude=61.5240,
    longitude=105.3188,
    notes="Arms supplier to Iran. Veto power in UNSC.",
)

china = get_or_create_nation(
    "china", "China",
    population=1.4e9,
    pct_shia=0.01,
    gdp_usd=17.7e12,
    is_nuclear=True,
    regime_type="authoritarian",
    stability_score=0.78,
    confidence=0.85,
    latitude=35.8617,
    longitude=104.1954,
    notes="Largest importer of Iranian oil. BRI investor.",
)

japan = get_or_create_nation(
    "japan", "Japan",
    population=125e6,
    pct_shia=0.001,
    gdp_usd=4.2e12,
    is_nuclear=False,
    regime_type="democracy",
    stability_score=0.8,
    confidence=0.92,
    latitude=36.2048,
    longitude=138.2529,
    notes="75% oil from Gulf. Hormuz closure = economic crisis.",
)

india = get_or_create_nation(
    "india", "India",
    population=1.4e9,
    pct_shia=0.1,
    gdp_usd=3.5e12,
    is_nuclear=True,
    regime_type="democracy",
    stability_score=0.74,
    confidence=0.87,
    latitude=20.5937,
    longitude=78.9629,
    notes="60% oil via Hormuz. Large Shia diaspora.",
)

pakistan = get_or_create_nation(
    "pakistan", "Pakistan",
    population=230e6,
    pct_shia=0.20,
    gdp_usd=376e9,
    is_nuclear=True,
    regime_type="democracy",
    stability_score=0.45,
    confidence=0.75,
    latitude=30.3753,
    longitude=69.3451,
    notes="20% Shia. Haqqani network. Nuclear arsenal.",
)

germany = get_or_create_nation(
    "germany", "Germany",
    population=84e6,
    pct_shia=0.02,
    gdp_usd=4.1e12,
    is_nuclear=False,
    regime_type="democracy",
    stability_score=0.88,
    confidence=0.93,
    latitude=51.1657,
    longitude=10.4515,
    notes="Major EU economy. Dependent on energy imports.",
)

france = get_or_create_nation(
    "france", "France",
    population=68e6,
    pct_shia=0.04,
    gdp_usd=2.9e12,
    is_nuclear=True,
    regime_type="democracy",
    stability_score=0.84,
    confidence=0.92,
    latitude=46.2276,
    longitude=2.2137,
    notes="P5 member. Major arms exporter.",
)

uk = get_or_create_nation(
    "uk", "United Kingdom",
    population=67e6,
    pct_shia=0.03,
    gdp_usd=3.1e12,
    is_nuclear=True,
    regime_type="democracy",
    stability_score=0.82,
    confidence=0.92,
    latitude=55.3781,
    longitude=-3.4360,
    notes="P5 member. Five Eyes. Naval presence in Gulf.",
)

print(f"  Created {len([iran,us,israel,bahrain,uae,saudi,qatar,kuwait,russia,china,japan,india,pakistan,germany,france,uk])} NationStates")

# ─── Non-State Actors ─────────────────────────────────────────────────────────

hezbollah = get_or_create_nsa(
    "hezbollah", "Hezbollah",
    ideology="Shia Islamist",
    estimated_fighters=100000,
    stability_score=0.7,
    confidence=0.85,
    notes="Iranian proxy. 150k+ rockets targeting Israel.",
)

hamas = get_or_create_nsa(
    "hamas", "Hamas",
    ideology="Sunni Islamist",
    estimated_fighters=30000,
    stability_score=0.5,
    confidence=0.8,
    notes="Gaza-based. Receives Iranian funding.",
)

houthis = get_or_create_nsa(
    "houthis", "Houthi Movement",
    ideology="Zaydi Shia",
    estimated_fighters=200000,
    stability_score=0.65,
    confidence=0.78,
    notes="Controls Yemen. Red Sea attacks. Iranian-backed.",
)

irgc = get_or_create_nsa(
    "irgc", "IRGC",
    ideology="Iranian Revolutionary",
    estimated_fighters=125000,
    stability_score=0.75,
    confidence=0.88,
    notes="Runs Quds Force. Controls Iran's missile program.",
)

print("  Created Non-State Actors")

# ─── Infrastructure ───────────────────────────────────────────────────────────

hormuz = get_or_create_infra(
    "strait_of_hormuz", "Strait of Hormuz",
    type="chokepoint",
    collapse_impact=0.95,
    attack_difficulty=0.2,
    daily_capacity=21e6,  # barrels/day
    operational=True,
    latitude=26.5667,
    longitude=56.2500,
    controlling_actor_uid="iran",
    notes="20% of global oil transit. Iran can mine/block.",
)

uae_desal_1 = get_or_create_infra(
    "uae_desal_1", "UAE Desalination Plant – Jebel Ali",
    type="desalination",
    collapse_impact=0.9,
    attack_difficulty=0.1,
    daily_capacity=300e6,  # m3/day
    operational=True,
    latitude=24.9836,
    longitude=55.0,
    controlling_actor_uid="uae",
    notes="Largest in UAE. Powers Dubai/Abu Dhabi water supply.",
)

uae_desal_2 = get_or_create_infra(
    "uae_desal_2", "UAE Desalination Plant – Taweelah",
    type="desalination",
    collapse_impact=0.85,
    attack_difficulty=0.12,
    daily_capacity=250e6,
    operational=True,
    latitude=24.5,
    longitude=54.6,
    controlling_actor_uid="uae",
    notes="Northern Abu Dhabi water supply.",
)

uae_desal_3 = get_or_create_infra(
    "uae_desal_3", "UAE Desalination Plant – Mirfa",
    type="desalination",
    collapse_impact=0.75,
    attack_difficulty=0.15,
    daily_capacity=120e6,
    operational=True,
    latitude=23.9,
    longitude=52.9,
    controlling_actor_uid="uae",
    notes="Western Abu Dhabi supply. Gas-powered.",
)

bahrain_desal = get_or_create_infra(
    "bahrain_desal", "Bahrain Al Dur Desalination Plant",
    type="desalination",
    collapse_impact=0.9,
    attack_difficulty=0.1,
    daily_capacity=100e6,
    operational=True,
    latitude=26.2,
    longitude=50.65,
    controlling_actor_uid="bahrain",
    notes="Only large desal plant. 100% water dependency.",
)

fifth_fleet = get_or_create_infra(
    "us_fifth_fleet_bahrain", "US Fifth Fleet Base – Bahrain",
    type="military_base",
    collapse_impact=0.7,
    attack_difficulty=0.45,
    daily_capacity=0,
    operational=True,
    latitude=26.2,
    longitude=50.6,
    controlling_actor_uid="us",
    notes="NAVCENT HQ. ~7,000 personnel. Targeted by Iran proxies.",
)

saudi_aramco = get_or_create_infra(
    "saudi_aramco", "Saudi Aramco – Abqaiq Processing",
    type="oil_field",
    collapse_impact=0.85,
    attack_difficulty=0.25,
    daily_capacity=7e6,
    operational=True,
    latitude=25.9333,
    longitude=49.6833,
    controlling_actor_uid="saudi",
    notes="World's largest oil processing facility. 6-7m bbl/day.",
)

dubai_airport = get_or_create_infra(
    "dubai_airport", "Dubai International Airport",
    type="port",
    collapse_impact=0.6,
    attack_difficulty=0.3,
    daily_capacity=0,
    operational=False,  # Already attacked
    latitude=25.2532,
    longitude=55.3657,
    controlling_actor_uid="uae",
    notes="Attacked by Iranian drones. Currently non-operational.",
)

us_stock_market = get_or_create_infra(
    "us_stock_market", "US Stock Market (NYSE/NASDAQ)",
    type="financial_market",
    collapse_impact=0.7,
    attack_difficulty=0.6,
    daily_capacity=50e9,  # USD/day
    operational=True,
    latitude=40.7069,
    longitude=-74.0089,
    controlling_actor_uid="us",
    notes="Exposed to Gulf oil shock. GCC sovereign wealth invested.",
)

iran_uranium = get_or_create_infra(
    "iran_natanz", "Iran Natanz Nuclear Facility",
    type="power_plant",
    collapse_impact=0.7,
    attack_difficulty=0.5,
    daily_capacity=0,
    operational=True,
    latitude=33.7225,
    longitude=51.7272,
    controlling_actor_uid="iran",
    notes="Primary uranium enrichment site. Hardened. Struck 2021.",
)

oman_strait_power = get_or_create_infra(
    "oman_power_grid", "Oman Coastal Power Grid",
    type="power_plant",
    collapse_impact=0.6,
    attack_difficulty=0.3,
    daily_capacity=5000,
    operational=True,
    latitude=23.6,
    longitude=58.5,
    controlling_actor_uid="oman",
    notes="Powers Gulf Coast desalination chain.",
)

print("  Created Infrastructure nodes")

# ─── Resources ────────────────────────────────────────────────────────────────

oil_res = get_or_create_resource("oil_gulf", "Gulf Oil", type="oil", unit="barrels/day")
water_res = get_or_create_resource("water_gulf", "Gulf Water", type="water", unit="m3/day")
usd_res = get_or_create_resource("usd_global", "USD Financial", type="usd", unit="USD/day")
food_res = get_or_create_resource("food_global", "Global Food Supply", type="food", unit="tonnes/day")

print("  Created Resources")

# ─── Weapon Systems ───────────────────────────────────────────────────────────

shahed_drone = WeaponSystem(
    uid="shahed_136",
    name="Shahed-136 Drone",
    unit_cost_usd=20000,
    daily_production_rate=30,
    current_stockpile=1000,
    range_km=2500,
    effectiveness_vs_infrastructure=0.7,
).save()

ballistic_missile = WeaponSystem(
    uid="shahab_3",
    name="Shahab-3 Ballistic Missile",
    unit_cost_usd=500000,
    daily_production_rate=2,
    current_stockpile=300,
    range_km=1300,
    effectiveness_vs_infrastructure=0.85,
).save()

print("  Created Weapon Systems")

# ─────────────────────────────────────────────────────────────────────────────
#  RELATIONSHIPS
# ─────────────────────────────────────────────────────────────────────────────

print("Creating relationships...")

# Actor ↔ Actor
iran.hostile_to.connect(us, {"intensity": 0.95})
iran.hostile_to.connect(israel, {"intensity": 0.98})
us.hostile_to.connect(iran, {"intensity": 0.75})
israel.hostile_to.connect(iran, {"intensity": 0.9})

us.allied_with.connect(israel, {"strength": 0.95})
us.allied_with.connect(bahrain, {"strength": 0.8})
us.allied_with.connect(saudi, {"strength": 0.75})
us.allied_with.connect(uae, {"strength": 0.7})
us.allied_with.connect(qatar, {"strength": 0.8})
us.allied_with.connect(kuwait, {"strength": 0.75})
us.allied_with.connect(uk, {"strength": 0.95})
us.allied_with.connect(germany, {"strength": 0.85})
us.allied_with.connect(france, {"strength": 0.85})
us.allied_with.connect(japan, {"strength": 0.9})

russia.allied_with.connect(iran, {"strength": 0.6})
china.allied_with.connect(iran, {"strength": 0.5})

russia.funds.connect(iran, {"annual_usd": 5e9})
china.funds.connect(iran, {"annual_usd": 20e9})
iran.funds.connect(hezbollah, {"annual_usd": 1e9})
iran.funds.connect(hamas, {"annual_usd": 3e8})
iran.funds.connect(houthis, {"annual_usd": 5e8})
iran.funds.connect(irgc, {"annual_usd": 8e9})

iran.religiously_loyal_to.connect(hezbollah, {"pct_population": 0.8})
iran.religiously_loyal_to.connect(houthis, {"pct_population": 0.6})

bahrain.religiously_loyal_to.connect(iran, {"pct_population": 0.3})
pakistan.religiously_loyal_to.connect(iran, {"pct_population": 0.12})
iraq_proxy = get_or_create_nation(
    "iraq", "Iraq",
    population=41e6,
    pct_shia=0.6,
    gdp_usd=264e9,
    is_nuclear=False,
    regime_type="democracy",
    stability_score=0.4,
    latitude=33.2232,
    longitude=43.6793,
)
iraq_proxy.religiously_loyal_to.connect(iran, {"pct_population": 0.45})

# Infrastructure: actor → infra
bahrain.hosts_base.connect(fifth_fleet)
qatar.hosts_base.connect(get_or_create_infra("al_udeid", "Al Udeid Air Base – Qatar",
    type="military_base", collapse_impact=0.65, attack_difficulty=0.5,
    latitude=25.1174, longitude=51.3149, controlling_actor_uid="us"))
saudi.hosts_base.connect(saudi_aramco)
iran.controls_chokepoint.connect(hormuz)
iran.controls.connect(iran_uranium)
uae.controls.connect(uae_desal_1)
uae.controls.connect(uae_desal_2)
uae.controls.connect(uae_desal_3)
bahrain.controls.connect(bahrain_desal)
us.controls.connect(fifth_fleet)
us.controls.connect(us_stock_market)

# CAN_STRIKE
iran.can_strike.connect(hormuz, {"difficulty": 0.1, "weapon_uid": "shahed_136"})
iran.can_strike.connect(uae_desal_1, {"difficulty": 0.15, "weapon_uid": "shahed_136"})
iran.can_strike.connect(uae_desal_2, {"difficulty": 0.15, "weapon_uid": "shahed_136"})
iran.can_strike.connect(uae_desal_3, {"difficulty": 0.18, "weapon_uid": "shahed_136"})
iran.can_strike.connect(bahrain_desal, {"difficulty": 0.12, "weapon_uid": "shahed_136"})
iran.can_strike.connect(fifth_fleet, {"difficulty": 0.35, "weapon_uid": "shahab_3"})
iran.can_strike.connect(saudi_aramco, {"difficulty": 0.25, "weapon_uid": "shahed_136"})
houthis.can_strike.connect(hormuz, {"difficulty": 0.2, "weapon_uid": "shahed_136"})
houthis.can_strike.connect(saudi_aramco, {"difficulty": 0.3, "weapon_uid": "shahed_136"})
israel.can_strike.connect(iran_uranium, {"difficulty": 0.4, "weapon_uid": "shahab_3"})
us.can_strike.connect(iran_uranium, {"difficulty": 0.2, "weapon_uid": "shahab_3"})

# DEPENDS_ON: nations on infrastructure
japan.depends_on_infra.connect(hormuz, {"pct_dependency": 0.75, "daily_volume": 3.5e6, "resource_type": "oil"})
china.depends_on_infra.connect(hormuz, {"pct_dependency": 0.40, "daily_volume": 4.0e6, "resource_type": "oil"})
india.depends_on_infra.connect(hormuz, {"pct_dependency": 0.60, "daily_volume": 2.5e6, "resource_type": "oil"})
south_korea = get_or_create_nation(
    "south_korea", "South Korea",
    population=51e6,
    pct_shia=0.0,
    gdp_usd=1.7e12,
    is_nuclear=False,
    regime_type="democracy",
    stability_score=0.82,
    latitude=35.9078,
    longitude=127.7669,
)
south_korea.depends_on_infra.connect(hormuz, {"pct_dependency": 0.70, "daily_volume": 1.5e6, "resource_type": "oil"})
germany.depends_on_infra.connect(hormuz, {"pct_dependency": 0.10, "daily_volume": 0.3e6, "resource_type": "oil"})
france.depends_on_infra.connect(hormuz, {"pct_dependency": 0.08, "daily_volume": 0.2e6, "resource_type": "oil"})

uae.depends_on_infra.connect(uae_desal_1, {"pct_dependency": 0.60, "daily_volume": 300e6, "resource_type": "water"})
uae.depends_on_infra.connect(uae_desal_2, {"pct_dependency": 0.25, "daily_volume": 125e6, "resource_type": "water"})
uae.depends_on_infra.connect(uae_desal_3, {"pct_dependency": 0.15, "daily_volume": 75e6, "resource_type": "water"})
bahrain.depends_on_infra.connect(bahrain_desal, {"pct_dependency": 0.95, "daily_volume": 100e6, "resource_type": "water"})

# Infrastructure chains: desal depends on power
uae_desal_1.depends_on.connect(saudi_aramco, {"pct_dependency": 0.3, "resource_type": "power"})
uae_desal_2.depends_on.connect(oman_strait_power, {"pct_dependency": 0.5, "resource_type": "power"})
uae_desal_3.depends_on.connect(saudi_aramco, {"pct_dependency": 0.4, "resource_type": "power"})
bahrain_desal.depends_on.connect(saudi_aramco, {"pct_dependency": 0.2, "resource_type": "power"})

# Hormuz → everything downstream
us_stock_market.depends_on.connect(hormuz, {"pct_dependency": 0.15, "resource_type": "oil_price"})

# Financial: Gulf → US market
saudi.invests_in.connect(us_stock_market, {"usd_value": 800e9})
uae.invests_in.connect(us_stock_market, {"usd_value": 350e9})
kuwait.invests_in.connect(us_stock_market, {"usd_value": 200e9})
us_stock_market.depends_on.connect(saudi_aramco, {"pct_dependency": 0.25, "resource_type": "oil"})

print("  Relationships created")

# ─────────────────────────────────────────────────────────────────────────────
#  POSTGRESQL SEED
# ─────────────────────────────────────────────────────────────────────────────

print("Seeding PostgreSQL...")

# Clear existing
db.query(Event).delete()
db.query(StabilitySnapshot).delete()
db.query(Scenario).delete()
db.commit()

# Production scenario
prod_scenario = Scenario(
    id="production",
    name="Production",
    description="Live geopolitical tracking",
    forked_from=None,
    created_at=datetime.utcnow(),
    is_production=True,
)
db.add(prod_scenario)

# Events
base_dt = datetime(2025, 10, 1)

events_data = [
    {
        "id": uuid.uuid4(),
        "timestamp": base_dt,
        "scenario_id": "production",
        "event_type": EventType.strike,
        "actor_uid": "israel",
        "target_uid": "iran",
        "description": "Joint US-Israeli strike kills Supreme Leader Khamenei and IRGC commanders in Tehran.",
        "confirmed": True,
        "confidence": 0.95,
        "casualties": 12,
        "properties": {"location": "Tehran", "weapon": "precision_strike"},
    },
    {
        "id": uuid.uuid4(),
        "timestamp": base_dt + timedelta(hours=6),
        "scenario_id": "production",
        "event_type": EventType.strike,
        "actor_uid": "iran",
        "target_uid": "iran",
        "description": "Unconfirmed: Iranian strike on school in southern Iran attributed to internal collapse.",
        "confirmed": False,
        "confidence": 0.6,
        "casualties": None,
        "properties": {"location": "Ahvaz", "source": "social_media"},
    },
    {
        "id": uuid.uuid4(),
        "timestamp": base_dt + timedelta(hours=12),
        "scenario_id": "production",
        "event_type": EventType.strike,
        "actor_uid": "iran",
        "target_uid": "dubai_airport",
        "description": "Iranian Shahed-136 drone strike disables Dubai International Airport runways.",
        "confirmed": True,
        "confidence": 0.92,
        "casualties": 0,
        "properties": {"weapon": "shahed_136", "location": "Dubai"},
    },
    {
        "id": uuid.uuid4(),
        "timestamp": base_dt + timedelta(hours=18),
        "scenario_id": "production",
        "event_type": EventType.strike,
        "actor_uid": "iran",
        "target_uid": "us_fifth_fleet_bahrain",
        "description": "Ballistic missile barrage targets US Fifth Fleet HQ in Bahrain. Partial damage.",
        "confirmed": True,
        "confidence": 0.9,
        "casualties": 45,
        "properties": {"weapon": "shahab_3", "damaged": True},
    },
    {
        "id": uuid.uuid4(),
        "timestamp": base_dt + timedelta(days=1),
        "scenario_id": "production",
        "event_type": EventType.social,
        "actor_uid": "hezbollah",
        "target_uid": "pakistan",
        "description": "Shia uprising surrounds US Embassy in Islamabad. Embassy staff evacuated.",
        "confirmed": True,
        "confidence": 0.85,
        "casualties": 8,
        "properties": {"triggered_by": "khamenei_strike", "crowd_size": 50000},
    },
    {
        "id": uuid.uuid4(),
        "timestamp": base_dt + timedelta(days=1, hours=6),
        "scenario_id": "production",
        "event_type": EventType.economic,
        "actor_uid": "iran",
        "target_uid": "strait_of_hormuz",
        "description": "Iran announces closure of Strait of Hormuz. Naval mines detected. Oil spikes to $180/bbl.",
        "confirmed": True,
        "confidence": 0.97,
        "casualties": 0,
        "properties": {"oil_price_impact": 180, "daily_oil_blocked_mbd": 21},
    },
    {
        "id": uuid.uuid4(),
        "timestamp": base_dt + timedelta(days=2),
        "scenario_id": "production",
        "event_type": EventType.diplomatic,
        "actor_uid": "china",
        "target_uid": "us",
        "description": "China warns US of consequences if conflict expands. Calls for UNSC emergency session.",
        "confirmed": False,
        "confidence": 0.7,
        "casualties": None,
        "properties": {"channel": "state_media"},
    },
    {
        "id": uuid.uuid4(),
        "timestamp": base_dt + timedelta(days=2, hours=12),
        "scenario_id": "production",
        "event_type": EventType.strike,
        "actor_uid": "houthis",
        "target_uid": "saudi_aramco",
        "description": "Houthi drone swarm targets Abqaiq facility. Partial disruption to processing.",
        "confirmed": False,
        "confidence": 0.65,
        "casualties": 3,
        "properties": {"weapon": "drone_swarm", "production_impact_pct": 20},
    },
]

for ev_data in events_data:
    event = Event(**ev_data, created_at=datetime.utcnow())
    db.add(event)

# Initial stability snapshots (reflect starting state)
snapshot_uids = [
    ("iran", 0.65),
    ("us", 0.85),
    ("israel", 0.75),
    ("bahrain", 0.4),
    ("uae", 0.5),
    ("saudi", 0.7),
    ("qatar", 0.75),
    ("kuwait", 0.72),
    ("russia", 0.6),
    ("china", 0.78),
    ("japan", 0.8),
    ("india", 0.74),
    ("pakistan", 0.45),
    ("germany", 0.88),
    ("france", 0.84),
    ("uk", 0.82),
    ("iraq", 0.4),
    ("south_korea", 0.82),
    ("hezbollah", 0.7),
    ("hamas", 0.5),
    ("houthis", 0.65),
    ("irgc", 0.75),
    ("strait_of_hormuz", 1.0),
    ("uae_desal_1", 1.0),
    ("uae_desal_2", 1.0),
    ("uae_desal_3", 1.0),
    ("bahrain_desal", 1.0),
    ("us_fifth_fleet_bahrain", 0.7),
    ("saudi_aramco", 1.0),
    ("dubai_airport", 0.0),
    ("us_stock_market", 0.8),
    ("iran_natanz", 1.0),
]

for obj_uid, score in snapshot_uids:
    snap = StabilitySnapshot(
        id=uuid.uuid4(),
        timestamp=base_dt - timedelta(hours=1),
        scenario_id="production",
        object_uid=obj_uid,
        stability_score=score,
        notes="Initial seeded value",
    )
    db.add(snap)

db.commit()
print(f"  Created {len(events_data)} events, {len(snapshot_uids)} stability snapshots, 1 scenario")
print("\n✅ Seed complete!")
db.close()
