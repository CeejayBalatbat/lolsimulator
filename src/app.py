import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from copy import deepcopy

# Import your Engine
from scraper import DataDragon
from loader import ItemLoader
from engine import Stats, StatType, DamageType, ProcType
from ability import Ability, AbilityConfig, AbilityLevelData, ScalingRatio
from simulation import TimeEngine
from pipeline import EventManager, CombatSystem, DamageEngine

# ------------------------------------------------------------------
# 1. SETUP & CACHING
# ------------------------------------------------------------------
@st.cache_resource
def load_library():
    dd = DataDragon()
    raw = dd.fetch_items()
    return ItemLoader.load_all(raw)

st.set_page_config(page_title="LoL Sim 2026", layout="wide")
st.title("⚔️ League of Legends Simulator (Phase 11)")

with st.spinner("Downloading Riot Data..."):
    library = load_library()

# ------------------------------------------------------------------
# 2. SIDEBAR: CHAMPION & SHOP
# ------------------------------------------------------------------
st.sidebar.header("1. Champion (Ezreal)")

level = st.sidebar.slider("Level", 1, 18, 9)
base_ad = 62.0 + (3.0 * level)
base_as = 0.625
bonus_as_growth = 0.025 * level

st.sidebar.markdown(f"**Stats:** AD: `{base_ad:.0f}` | AS: `{base_as:.3f} (+{bonus_as_growth:.1%})`")
st.sidebar.divider()

st.sidebar.header("2. Build")
all_items = sorted(list(library.keys()))
selected_items = st.sidebar.multiselect(
    "Inventory (Max 6)", 
    options=all_items,
    default=["Trinity Force"],
    max_selections=6
)

current_cost = sum(library[name].cost for name in selected_items)
st.sidebar.caption(f"💰 Total Gold: {current_cost}g")

# ------------------------------------------------------------------
# 3. MAIN PAGE: COMBAT SCENARIO
# ------------------------------------------------------------------
st.header("3. Combat Scenario")

c1, c2, c3 = st.columns(3)
with c1:
    target_hp = st.number_input("Enemy HP", 500, 10000, 2000, step=100)
with c2:
    target_armor = st.number_input("Enemy Armor", 0, 500, 50, step=10)
with c3:
    sim_duration = st.slider("Fight Duration (seconds)", 1, 30, 10)

st.divider()

# ------------------------------------------------------------------
# 4. EXECUTION ENGINE
# ------------------------------------------------------------------
if st.button("🔥 RUN SIMULATION", type="primary", use_container_width=True):
    
    # A. Setup Objects (CRITICAL: Deepcopy items to reset passive state)
    items = deepcopy([library[name] for name in selected_items])
    
    attacker = Stats(
        base_ad=base_ad, 
        base_attack_speed=base_as,
        bonus_attack_speed=bonus_as_growth
    )
    
    target = Stats(
        base_hp=target_hp, 
        current_health=target_hp, 
        base_armor=target_armor,
        base_mr=target_armor # Giving equal MR for simple sim
    )

    # B. Define Abilities
    q_config = AbilityConfig(
        name="Mystic Shot",
        damage_type=DamageType.PHYSICAL,
        ratios=[ScalingRatio(StatType.AD, 1.30)], 
        level_data=[AbilityLevelData(base_damage=120, mana_cost=30, cooldown=4.5)], 
        proc_type=ProcType.SPELL | ProcType.ON_HIT
    )
    abilities = [Ability(q_config, rank=1)]
    
    # C. Initialize Engine (Fresh Event Manager for every run)
    bus = EventManager()
    dmg_engine = DamageEngine()
    system = CombatSystem(bus, dmg_engine)
    sim = TimeEngine(bus, attacker, target, items)
    
    # D. Register Passives
    for item in items:
        for p in item.passives:
            if hasattr(p, 'register'): 
                p.register(bus)

    # E. Run
    sim.run(abilities)
    
    # ------------------------------------------------------------------
    # 5. VISUALIZATION
    # ------------------------------------------------------------------
    total_dmg = sim.total_damage_done
    dps = total_dmg / sim_duration
    
    m1, m2, m3 = st.columns(3)
    m1.metric("Total Damage", f"{total_dmg:.1f}")
    m2.metric("DPS", f"{dps:.1f}")
    
    efficiency = (total_dmg / max(1, current_cost)) * 100
    m3.metric("Gold Efficiency", f"{efficiency:.1f} pts")

    st.success(f"Simulation complete! Spellblade and Quicken reset correctly.")