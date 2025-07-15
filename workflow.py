import os
from compiler_frontend import CompilerFrontend
from cpu_synthesis import CPUSynthesis
from compiler_backend import ParamCompilerBackend
from simulator import Simulator
from peak_power_estimator import PeakPowerEstimator
from itertools import chain, combinations
import json
import shutil
import hashlib
from pathlib import Path
from energy_calculator import EnergyCalculator


class Workflow:
    def __init__(self, param_file='params.txt'):
        self.compiler_frontend = CompilerFrontend()
        self.cpu_synthesis = CPUSynthesis()
        self.compiler_backend = ParamCompilerBackend()
        self.simulator = Simulator()
        self.peak_power_estimator = PeakPowerEstimator()

        self.config_path = "config.json"

        # Load config file
        with open("config.json") as f:
            config = json.load(f)
        self.constraints = config.get("constraints", {})

        # Load parameters from file
        try:
            with open(param_file, 'r') as f:
                self.possible_parameters = [line.strip() for line in f if line.strip()]
        except FileNotFoundError:
            print(f"[ERROR] Parameter file '{param_file}' not found.")
            self.possible_parameters = []

    def _violates_constraint(self, metric, value):
        if value is None:
            return True
        key = f"max_{metric.replace(' ', '_')}"
        limit = self.constraints.get(key)
        return limit is not None and value > limit

    def evaluate(self, bc_path, parameters, target_metric):
        # Step 1: Compile
        elf_path, asm_file = self.compiler_backend.compile(bc_path, parameters)
        if not elf_path:
            return None

        # Step 2: Simulate
        sim_metrics = self.simulator.simulate(elf_path)

        # Step 3: Synthesize CPU (if needed)
        cpu_area = self.cpu_synthesis.synthesize(parameters)

        # Step 4: Estimate Peak Power (if needed)
        power_metrics = self.peak_power_estimator.estimate_peak_power(parameters=parameters)
        peak_power = power_metrics.get("peak power") if power_metrics else None

        # Estimate Energy (using EnergyCalculator with runtime)
        exec_time = sim_metrics.get("exec time")
        energy = None

        mcpat_out_path = "mcpat-out.txt"
        if exec_time is not None and os.path.exists(mcpat_out_path):
            try:
                calc = EnergyCalculator(mcpat_out_path)
                energy = calc.getEnergy(float(exec_time))
            except Exception as e:
                print(f"[EnergyCalc] ⚠️ Failed to estimate energy: {e}")

        # Step 5: Collect metrics
        metrics = {
            "exec time": sim_metrics.get("exec time"),
            "energy": energy,
            "code size": asm_file.get("code size"),
            "CPU area": cpu_area,
            "peak power": peak_power
        }

        # Step 6: Check constraint
        for metric, value in metrics.items():
            if self._violates_constraint(metric, value):
                key = f"max_{metric.replace(' ', '_')}"
                limit = self.constraints.get(key)
                print(f"❌ Violates constraint: {metric} = {value:.10f} > max {limit:.10f}")
                return None

        return metrics.get(target_metric)

    def save_result_outputs(self, parameters, base_result_dir="results"):
        # Generate a unique result folder name based on parameters
        if not parameters:
            name = "default"
        else:
            hash_suffix = hashlib.md5(" ".join(sorted(parameters)).encode()).hexdigest()[:6]
            name = "_".join(p.strip("-") for p in parameters) + f"_{hash_suffix}"

        result_path = Path(base_result_dir) / name
        result_path.mkdir(parents=True, exist_ok=True)

        print(f"[ResultSaver] Saving results to: {result_path}")

        # ✅ Copy only mcpat-in.xml and mcpat-out.txt if they exist
        for file in ["mcpat-in.xml", "mcpat-out.txt"]:
            src_file = Path(file)
            if src_file.exists():
                shutil.copy(src_file, result_path / src_file.name)

        # ✅ Copy entire directories if they exist
        dirs_to_copy = {
            "output": result_path / "output",
            "m5out": result_path / "m5out",
            "yosys_out": result_path / "yosys_out"
        }

        for src_name, dest_path in dirs_to_copy.items():
            src_path = Path(src_name)
            if src_path.exists() and src_path.is_dir():
                shutil.copytree(src_path, dest_path, dirs_exist_ok=True)

        return result_path

    def greedy_parameter_search(self, bc_path, target_metric):
        best_parameters = []
        best_score = self.evaluate(bc_path, best_parameters, target_metric)

        if best_score is None:
            print(f"[ERROR] Could not compute initial '{target_metric}'. Aborting.")
            return [], None

        print(f"Initial {target_metric}: {best_score}")

        for param in self.possible_parameters:
            trial_params = best_parameters + [param]
            trial_score = self.evaluate(bc_path, trial_params, target_metric)

            if trial_score is None:
                print(f"[WARNING] Skipping {trial_params} due to backend failure.")
                continue

            self.save_result_outputs(trial_params)

            print(f"Trying {trial_params} => {target_metric}: {trial_score:.10f}")
            if trial_score < best_score:
                print(f"✅ Keeping {param}")
                best_parameters.append(param)
                best_score = trial_score
            else:
                print(f"❌ Discarding {param}")

        if best_score is not None:
            print(f"\n[BruteForce] ✅ Best combination: {best_parameters}")
            print(f"[BruteForce] ✅ Best {target_metric}: {best_score:.8f}")
        else:
            print("\n[BruteForce] ❌ No valid combination found that satisfies constraints.")
        return best_parameters, best_score

    def generate_valid_param_combinations(self, params, conflicts):
        def is_valid(combo):
            for conflict in conflicts:
                if all(p in combo for p in conflict):
                    return False
            return True

        all_combos = list(chain.from_iterable(combinations(params, r) for r in range(len(params) + 1)))
        valid_combos = [list(c) for c in all_combos if is_valid(c)]
        return valid_combos

    def brute_force_search(self, bc_path, target_metric):
        print("[BruteForce] Starting brute-force parameter search...")
        params = self.possible_parameters

        best_score = None
        best_params = []

        all_combos = self.generate_valid_param_combinations(params, [])
        print(f"[BruteForce] Trying {len(all_combos)} combinations...")

        for combo in all_combos:
            trial_score = self.evaluate(bc_path, combo, target_metric)
            print(f"Trying {combo} => {target_metric}: {trial_score}")

            if trial_score is not None:
                self.save_result_outputs(combo)

                if best_score is None or trial_score < best_score:
                    best_score = trial_score
                    best_params = combo
                    print(f"✅ New best: {trial_score} with {combo}")

        if best_score is not None:
            print(f"\n[BruteForce] ✅ Best combination: {best_params}")
            print(f"[BruteForce] ✅ Best {target_metric}: {best_score:.8f}")
        else:
            print("\n[BruteForce] ❌ No valid combination found that satisfies constraints.")

        return best_params, best_score

    def run(self, c_file_path, target_metric):
        results_dir = "results"
        if os.path.exists(results_dir):
            print("[Workflow] Clearing previous results...")
            shutil.rmtree(results_dir)

        # Run frontend ONCE to produce output/main.bc
        success = self.compiler_frontend.compile(c_file_path)
        if not success:
            print("[Workflow] Compilation failed — aborting.")
            exit(1)

        # Derive .bc path in output dir
        base_name = os.path.splitext(os.path.basename(c_file_path))[0]
        bc_path = os.path.join("output", base_name + ".bc")

        # return self.greedy_parameter_search(bc_path, target_metric)
        return self.brute_force_search(bc_path, target_metric)
