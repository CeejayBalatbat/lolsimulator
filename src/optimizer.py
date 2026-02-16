from typing import List, Tuple
from engine import Stats, DamageResult
from item import ItemConfig
from scenario import Scenario
from simulation import TimeEngine
from pipeline import EventManager, CombatSystem, DamageEngine
from ability import Ability
from stat_pipeline import StatPipeline

class SimulationResult:
    def __init__(self, build_name: str, total_damage: float, dps: float, cost: int):
        self.build_name = build_name
        self.total_damage = total_damage
        self.dps = dps
        self.cost = cost

class Optimizer:
    def __init__(self, scenario: Scenario, base_champ: Stats, abilities: List[Ability]):
        self.scenario = scenario
        self.base_champ = base_champ
        self.abilities = abilities

    def evaluate_build(self, build_name: str, items: List[ItemConfig]) -> SimulationResult:
        # 1. Setup Infrastructure
        bus = EventManager()
        damage_engine = DamageEngine()
        combat_system = CombatSystem(bus, damage_engine)

        # 2. Setup Entities
        # We clone the target so one simulation doesn't hurt the next one
        target_copy = self.scenario.target_stats.snapshot()
        
        # 3. Initialize Engine (THE FIX IS HERE)
        # Old: sim = TimeEngine(bus, final_stats, target_copy)
        # New: We pass base_champ + items. The Engine calculates the stats itself.
        sim = TimeEngine(bus, self.base_champ, target_copy, items)

        # 4. Register Passives
        # We must manually register item passives to the bus
        for item in items:
            for passive in item.passives:
                if hasattr(passive, 'register'):
                    passive.register(bus)

        # 5. Run Simulation
        sim.run(self.abilities)

        # 6. Collect Results
        cost = sum(i.cost for i in items)
        
        return SimulationResult(
            build_name, 
            sim.total_damage_done, 
            sim.total_damage_done / self.scenario.duration, 
            cost
        )

    def compare_builds(self, builds: List[Tuple[str, List[ItemConfig]]]):
        results = []
        
        print(f"\n--- OPTIMIZER RESULTS ---")
        print(f"Scenario: {self.scenario.name} ({self.scenario.duration}s)")
        
        for name, items in builds:
            res = self.evaluate_build(name, items)
            results.append(res)

        # Sort by DPS (Highest First)
        results.sort(key=lambda x: x.dps, reverse=True)

        # Print Table
        print(f"{'RANK':<6} {'BUILD':<25} {'DPS':<10} {'TOTAL':<10} {'COST':<8}")
        print("-" * 65)
        
        for i, res in enumerate(results):
            print(f"{i+1:<6} {res.build_name:<25} {res.dps:<10.1f} {res.total_damage:<10.0f} {res.cost:<8}")