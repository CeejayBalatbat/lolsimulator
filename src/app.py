import streamlit as st
import pandas as pd
from copy import deepcopy

# Import your Engine components
from scraper import DataDragon
from loader import ItemLoader
from engine import Stats, StatType, DamageType, ProcType
from ability import Ability, AbilityConfig, AbilityLevelData, ScalingRatio
from simulation import TimeEngine
from pipeline import EventManager, CombatSystem, DamageEngine
from stat_pipeline import StatPipeline

# ------------------------------------------------------------------
# 1. SETUP & CACHING
# ------------------------------------------------------------------
@st.cache_resource
def load_library():
    dd = DataDragon()
    # Fetch live data from Riot/DataDragon
    raw = dd.fetch_items()
    return ItemLoader.load_all(raw)

st.set_page_config(page_title="LoL Sim 2026", layout="wide")
st.title("⚔️ League of Legends Combat Simulator")
st.caption("Phase 11: Granular Damage Tracking & Event Reset")

# Load Data
with st.spinner("Downloading Riot Data..."):
    library = load_library()

# ------------------------------------------------------------------
# 2. SIDEBAR: CHAMPION & SHOP
# ------------------------------------------------------------------
st.sidebar.header("1. Champion (Ezreal)")

# A. Level & Base Stats
level = st.sidebar.slider("Level", 1, 18, 9)
base_ad = 62.0 + (3.0 * level)
base_as = 0.625
bonus_as_growth = 0.025 * level

base_mana = st.sidebar.number_input("Base Mana", 0, 2000, 375 + (50 * level)) # Approx Ezreal growth
base_mana_regen = st.sidebar.number_input("Base Mana Regen", 0.0, 20.0, 2.0) # Per Second

st.sidebar.markdown(f"**Base AD:** `{base_ad:.0f}`")
st.sidebar.markdown(f"**Base AS:** `{base_as:.3f} (+{bonus_as_growth:.1%})`")
st.sidebar.divider()

# B. Inventory
st.sidebar.header("2. Build")
all_items = sorted(list(library.keys()))
selected_items = st.sidebar.multiselect(
    "Inventory (Max 6)", 
    options=all_items,
    default=["Trinity Force"],
    max_selections=6
)

# Cost Calc
current_cost = sum(library[name].cost for name in selected_items)
st.sidebar.info(f"💰 Total Gold: {current_cost}g")


st.sidebar.divider()

# ==========================================
# 🛠️ DEV TOOLS
# ==========================================
st.sidebar.header("🛠️ Dev Tools")
if st.sidebar.button("🗑️ Nuke Cache & Reload", type="secondary", use_container_width=True):
    # This wipes Streamlit's memory clean
    st.cache_resource.clear()
    
    # This instantly refreshes the page with the new code
    st.rerun() 
# ==========================================
   


# ------------------------------------------------------------------
# 3. COMBAT SCENARIO & TARGET ANALYSIS (Live Updates)
# ------------------------------------------------------------------
st.header("3. Combat Scenario")

c1, c2, c3 = st.columns(3)
with c1:
    target_hp = st.number_input("Enemy HP", 500, 10000, 2000, step=100)
with c2:
    target_armor = st.number_input("Enemy Armor", 0, 500, 50, step=10)
with c3:
    sim_duration = st.slider("Fight Duration", 1, 30, 10)

st.divider()

# --- LIVE PREVIEW SECTION ---
# This runs on every slider change, so metrics update instantly.

# A. Create Preview Objects
preview_items = [library[name] for name in selected_items]
preview_attacker = Stats(
    base_ad=base_ad, 
    base_attack_speed=base_as,
    bonus_attack_speed=bonus_as_growth
)

# B. Resolve Stats (Get final Pen/Lethality)
final_attacker_stats = StatPipeline.resolve(preview_attacker, preview_items, [])

# --- TARGET ANALYSIS DISPLAY ---
st.subheader("🧐 Target Analysis")

# 1. Get Penetration Stats
current_lethality = final_attacker_stats.lethality
current_percent_pen = final_attacker_stats.armor_pen_percent

# 2. Calculate "Post-Penetration" Armor
eff_armor = target_armor * (1.0 - current_percent_pen)
eff_armor = max(0, eff_armor - current_lethality)

# 3. Calculate Mitigation & Effective HP
mitigation = 100.0 / (100.0 + eff_armor)
reduction_percent = (1.0 - mitigation) * 100.0
ehp_physical = target_hp * (1.0 + (eff_armor / 100.0))

# 4. Display Metrics
t1, t2, t3, t4 = st.columns(4)
t1.metric("Enemy Armor", f"{target_armor:.0f} → {eff_armor:.0f}", help="Base → After Pen")
t2.metric("Dmg Reduction", f"{reduction_percent:.1f}%")
t3.metric("Effective HP", f"{ehp_physical:.0f}", delta=f"+{ehp_physical - target_hp:.0f} Armor Value")
t4.metric("Penetration", f"{current_percent_pen*100:.0f}% + {current_lethality:.0f} Flat")

st.divider()

# ------------------------------------------------------------------
# 4. EXECUTION ENGINE
# ------------------------------------------------------------------
if st.button("🔥 RUN SIMULATION", type="primary", use_container_width=True):

    # A. Setup Objects (CRITICAL: Deepcopy only ONCE to reset passive states)
    items = deepcopy([library[name] for name in selected_items])
    

    with st.expander("🔍 Engine Diagnostic: What Passives do I actually have?"):
        for item in items:
            st.write(f"**{item.name} Passives:**")
            if not item.passives:
                st.write("- None")
            for p in item.passives:
                st.write(f"- {p.__class__.__name__}")
    
    # B. Define Stats
    attacker = Stats(
        base_ad=base_ad, 
        base_attack_speed=base_as,
        bonus_attack_speed=bonus_as_growth,
        # NEW MANA STATS
        base_mana=base_mana,
        current_mana=base_mana, 
        base_mana_regen=base_mana_regen
    )
    
    target = Stats(
        base_hp=target_hp, 
        current_health=target_hp, 
        base_armor=target_armor,
        base_mr=target_armor
    )

    # C. Define Ezreal Q (Mystic Shot)
    q_config = AbilityConfig(
        name="Mystic Shot",
        damage_type=DamageType.PHYSICAL,
        ratios=[ScalingRatio(StatType.AD, 1.30)], 
        level_data=[AbilityLevelData(base_damage=120, 
                                     mana_cost=30, 
                                     cooldown=4.5)], 
        proc_type=ProcType.SPELL | ProcType.ON_HIT
    )
    abilities = [Ability(q_config, rank=1)]
    
    # D. Initialize Pipeline
    bus = EventManager()
    dmg_engine = DamageEngine()
    system = CombatSystem(bus, dmg_engine)
    
    # E. Setup Simulation
    sim = TimeEngine(bus, attacker, target, items)
    sim.max_duration = float(sim_duration)
    
    # F. Register Passives to the Event Bus
    for item in items:
        for p in item.passives:
            if hasattr(p, 'register'): 
                p.register(bus)

    # G. Run
    sim.run(abilities)
    
    # ------------------------------------------------------------------
    # 5. GRANULAR VISUALIZATION
    # ------------------------------------------------------------------
    if hasattr(sim, 'damage_history') and sim.damage_history:
        df = pd.DataFrame(sim.damage_history)
        
        # Row 1: High Level Metrics
        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Total Damage", f"{sim.total_damage_done:.1f}")
        m2.metric("Avg. Hit", f"{df['Damage'].mean():.1f}") # Make sure key matches sim.py ('Damage')
        m3.metric("Highest Crit/Hit", f"{df['Damage'].max():.1f}")
        m4.metric("Gold Efficiency", f"{(sim.total_damage_done/max(1, current_cost)):.2f}")
        m5.metric("Mana Remaining", f"{sim.attacker.current_mana:.0f} / {sim.attacker.total_mana:.0f}")

        # Row 2: Charts
        col_chart1, col_chart2 = st.columns(2)
        
        with col_chart1:
            st.subheader("📈 Damage per Hit")
            st.scatter_chart(df, x="Time", y="Damage", color="Source")

        with col_chart2:
            st.subheader("⏱️ Cumulative Damage")
            df["Total"] = df["Damage"].cumsum()
            st.line_chart(df, x="Time", y="Total")

        # Row 3: Breakdown & Log
        st.subheader("📊 Source Breakdown")
        breakdown = df.groupby("Source")["Damage"].sum().reset_index()
        st.bar_chart(breakdown.set_index("Source"))

        with st.expander("📂 View Raw Combat Log"):
            st.dataframe(df, use_container_width=True)
            
    else:
        st.error("Simulation ran but no damage was recorded. Check Ability/Attack logic.")

    st.success(f"Simulation complete for {', '.join(selected_items)}!")