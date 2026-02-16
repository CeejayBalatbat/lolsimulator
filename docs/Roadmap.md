# Project Roadmap

This roadmap defines the order in which systems are built
Steps must be done sequentially

## Phase 0: Foundations

### Goal
Create a minimal, bare-bone, correct damage engine independent of league content

"Given raw damage numbers and target defensed, can i compute the final damage correctly and consistenly?"

### Tasks
- Implement DamageType enum (physical, magic, true)
- Implement Stats container
    - Recalculation Pipeline
        - Calculate base stats
        - Flat item Stats
        - Percentage Multipliers ie deathcap
        - Conversion Passives
- Implement resistance formulas (armor / MR)
- Implement DamageInstance
- Implement DamageEngine that:
  - accepts damage instances
  - applies mitigation
  - returns total + breakdown

### Exit Criteria
- Given known inputs, damage math matches League formulas
- Engine is the only place where mitigation is applied


---

## Phase 2: Abilities as Data (No Items Yet)

### Goal
Introduce abilities without special cases.

### Tasks
- Define Ability data structure:
  - base damage
  - ratios
  - damage type
  - flags (applies_on_hit, can_crit)
- Implement ability cast returning DamageInstances
- Add one simple ability (e.g. flat magic damage Q)

### Exit Criteria
- Abilities do not apply damage directly
- Damage flows through DamageEngine only
- Ability logic is reusable and data-driven

---

## Phase 3: Event System

### Goal
Unify autos, abilities, and future effects under events.

### Tasks
- Define Event types:
  - AutoAttackEvent
  - AbilityCastEvent
- Engine processes events → damage instances
- Log events for debugging

### Exit Criteria
- All combat actions are events
- Events produce damage instances
- Engine resolves damage centrally

---

## Phase 4: Items as Modifiers (Stat-Only)

### Goal
Introduce items without passives.

### Tasks
- Implement Item class:
  - stat modifiers only
- Items modify Champion stats on equip
- No damage logic in items yet

### Exit Criteria
- Item stats correctly affect damage output
- No item creates damage instances

---

## Phase 5: Item Passives (Pattern-Based)

### Goal
Add passives without hardcoding item-by-item logic.

### Tasks
- Define Passive base class
- Implement common passive patterns:
  - flat on-hit damage
  - damage amp
- Items reference passive types via config
- Passives register hooks to events

### Exit Criteria
- Passives respond to events
- Passives do not apply mitigation
- Same passive logic reused by multiple items

---

## Phase 6: On-Hit and Trigger Logic

### Goal
Correctly model conditional effects.

### Tasks
- Define trigger points:
  - on_hit
  - on_damage
  - on_cast
- Ensure correct ordering:
  - base damage
  - on-hit
  - amps
- Validate stacking behavior

### Exit Criteria
- On-hit effects trigger only when allowed
- Trigger ordering is explicit and testable

---

## Phase 7: Time and Cooldowns

### Goal
Move from single actions to rotations.

### Tasks
- Introduce time simulation
- Implement cooldown tracking
- Simulate rotations over time windows

### Exit Criteria
- DPS over time is measurable
- Cooldowns gate abilities correctly

---

## Phase 8: Build Evaluation

### Goal
Compare builds under controlled assumptions.

### Tasks
- Define simulation context:
  - level
  - target stats
  - time window
  - rotation
- Simulate multiple builds
- Rank results by objective function

### Exit Criteria
- Build comparison is deterministic
- Results are reproducible

---

## Phase 9: Champion Scaling and Expansion

### Goal
Generalize beyond one champion.

### Tasks
- Add stat growth per level
- Add multiple champions
- Validate shared logic holds

### Exit Criteria
- No champion-specific hacks in engine
- Champion differences live in data

---

## Phase 10: Data Ingestion (Optional)

### Goal
Reduce manual data entry.

### Tasks
- Parse Riot data files
- Normalize into internal schemas
- Validate against manual champions

### Exit Criteria
- Parsed data produces same results as manual data

## Phase 11: The Cockpit (UI & Visualization)
### Goal

Stop editing Python files to change Armor values. Create a GUI for rapid testing.
### Tasks

    Streamlit Integration:

        Sidebar for Champion/Item selection.

        Sliders for Enemy Stats (HP, Armor, MR).

    Real-Time Graphs:

        Plot "Damage vs Time" (cumulative).

        Plot "DPS vs Time" (instantaneous).

    Interactive Shop:

        Searchable dropdown using the Phase 10 library.

        Drag-and-drop inventory management.

Exit Criteria

    You can compare "Lethality vs Crit" in <10 seconds without touching code.

    Non-programmers (friends/Discord) could theoretically use it.

Phase 12: Target State & Debuffs (The "Vayne" Phase)
Goal

Support mechanics that care about the Target's status (Stacks, Marks, Poisons).
Tasks

    Debuff System:

        Apply stacks to the Target (not just self-buffs).

        Example: Black Cleaver (Shred Armor per stack).

        Example: Vayne Silver Bolts (3 stacks = True Dmg).

    Conditional Damage Modifiers:

        "Deals 20% more damage if target is below 50% HP" (Coup de Grace).

        "Deals more damage if target is CC'd" (Horizon Focus).

    Execution Logic:

        Collector (Kill if below 5%).

Exit Criteria

    Vayne/Kai'sa passives work automatically.

    Armor Shred (Black Cleaver) correctly increases subsequent physical damage.

Phase 13: Resources & Constraints (The "Mana" Phase)
Goal

Stop infinite spell spam. Realism requires resource management.
Tasks

    Resource Tracks:

        Mana, Energy, Rage, Fury.

    Gating Logic:

        cast() fails if current_mana < cost.

    Regeneration:

        Mana regen per second (Base + Items like Tear).

    Refund Mechanics:

        "Restores mana on hit" (Essence Reaver / Presence of Mind).

Exit Criteria

    Ezreal stops casting Q when he runs OOM.

    "Blue Buff" or "Tear" actually increases DPS by allowing more casts.

Phase 14: The Genetic Optimizer (Automated Theorycrafting)
Goal

Stop manually defining "Build A vs Build B". Let the AI find the mathematical best build from the entire shop.
Tasks

    Combinatorial Generator:

        Generate valid 6-item permutations (billions of combinations).

    Genetic Algorithm / Heuristic Search:

        "Evolve" builds over generations to find local maxima.

        Constraint: "Must cost < 15,000g" or "Must include Boots".

    Pareto Frontiers:

        Plot "Best DPS for X Gold" (Efficiency Curve).

Exit Criteria

    You press one button: "Find Best Ezreal Build".

    The engine outputs the optimal 6 items without you telling it what to try.

Phase 15: The Duel (Defensive Simulation)
Goal

Valuing Defensive Stats (Armor/HP) by simulating incoming damage.
Tasks

    Enemy Actor:

        The "Target" attacks back (simple auto-attacks or scripted rotation).

    Time-to-Death (TTD) Metric:

        Instead of just Max DPS, calculate "Who dies first?"

    Defensive Item Value:

        Calculate "Effective HP" vs specific damage types.

        Verify if Guardian Angel or Zhonyas actually wins the fight by stalling.

Exit Criteria

    Simulator can determine if "Glass Cannon" Ezreal dies before killing a "Tank" Darius.

    Defensive stats (Armor/MR) have value in the simulation ranking.