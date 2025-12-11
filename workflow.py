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
import pandas as pd


class Workflow:
    def __init__(self, param_file='params.txt'):
        self.compiler_frontend = CompilerFrontend()
        self.cpu_synthesis = CPUSynthesis()
        self.compiler_backend = ParamCompilerBackend()
        self.simulator = Simulator()
        self.peak_power_estimator = PeakPowerEstimator()

        # Load config
        with open("config.json") as f:
            config = json.load(f)
        self.constraints = config.get("constraints", {})

        # Load parameter list
        try:
            with open(param_file, 'r') as f:
                # Ensure parameters always begin with "-"
                self.possible_parameters = [
                    "-" + line.strip().lstrip("-")
                    for line in f
                    if line.strip()
                ]
        except FileNotFoundError:
            print(f"[ERROR] Parameter file '{param_file}' not found.")
            self.possible_parameters = []

    # ----------------------------------------------------------
    # Constraint helper
    # ----------------------------------------------------------
    def _violates_constraint(self, metric, value):
        if value is None:
            return True
        key = f"max_{metric.replace(' ', '_')}"
        limit = self.constraints.get(key)
        return limit is not None and value > limit

    # ----------------------------------------------------------
    # EVALUATE → returns (score, metrics_dict)
    # ----------------------------------------------------------
    def evaluate(self, bc_path, parameters, target_metric):
        # Step 1: Backend compile
        elf_path, asm_file = self.compiler_backend.compile(bc_path, parameters)
        if not elf_path:
            return None, None

        # Step 2: Simulate
        sim_metrics = self.simulator.simulate(elf_path)

        # Step 3: Synthesize CPU
        _, synthesize_results = self.cpu_synthesis.synthesize(parameters)
        cpu_area = synthesize_results.get("num_cells")

        # Step 4: Peak power estimation (fix: stringify params)
        param_str = " ".join(parameters) if parameters else ""
        power_metrics = self.peak_power_estimator.estimate_peak_power(parameters=param_str)
        peak_power = power_metrics.get("peak power") if power_metrics else None

        # Step 5: Energy estimation
        exec_time = sim_metrics.get("exec time")
        energy = None
        if exec_time is not None and os.path.exists("mcpat-out.txt"):
            try:
                calc = EnergyCalculator("mcpat-out.txt")
                energy = calc.getEnergy(float(exec_time))
            except Exception as e:
                print(f"[EnergyCalc] Failed: {e}")

        # Collect metrics
        metrics = {
            "exec time": sim_metrics.get("exec time"),
            "energy": energy,
            "code size": asm_file.get("code size"),
            "CPU area": cpu_area,
            "peak power": peak_power
        }

        # Check constraints
        for m, v in metrics.items():
            if self._violates_constraint(m, v):
                print(f"❌ Violates constraint: {m} = {v}")
                return None, metrics

        return metrics.get(target_metric), metrics

    # ----------------------------------------------------------
    # SAVE OUTPUTS + metrics.json
    # ----------------------------------------------------------
    def save_result_outputs(self, parameters, metrics=None, base_result_dir="results"):
        # Folder name
        if not parameters:
            name = "default"
        else:
            hash_suffix = hashlib.md5(" ".join(sorted(parameters)).encode()).hexdigest()[:6]
            name = "_".join([p.strip("-") for p in parameters]) + f"_{hash_suffix}"

        result_path = Path(base_result_dir) / name
        result_path.mkdir(parents=True, exist_ok=True)

        print(f"[Saver] Saving result → {result_path}")

        # Write metrics.json
        if metrics is not None:
            with open(result_path / "metrics.json", "w") as f:
                json.dump(metrics, f, indent=4)

        # Copy mcpat files
        for fname in ["mcpat-in.xml", "mcpat-out.txt"]:
            src = Path(fname)
            if src.exists():
                shutil.copy(src, result_path / fname)

        # Copy tool-generated directories
        for dirname in ["output", "m5out", "yosys_out"]:
            src = Path(dirname)
            dst = result_path / dirname
            if src.exists() and src.is_dir():
                shutil.copytree(src, dst, dirs_exist_ok=True)

        return result_path

    # ----------------------------------------------------------
    # Decode folder name → readable params
    # ----------------------------------------------------------
    def _decode_params_for_label(self, folder_name):
        if folder_name == "default":
            return "default"
        parts = folder_name.split("_")
        params_only = parts[:-1]  # drops the hash suffix
        return ", ".join(params_only)

    # ----------------------------------------------------------
    # Export CSV and TXT table
    # ----------------------------------------------------------
    def export_table(self, results_dir="results"):
        results = []

        # Load metrics
        for sub in Path(results_dir).glob("*"):
            metrics_file = sub / "metrics.json"
            if metrics_file.exists():
                with open(metrics_file) as f:
                    data = json.load(f)

                results.append({
                    "folder": sub.name,
                    "params": self._decode_params_for_label(sub.name),
                    **data
                })

        if not results:
            print("[Table] No metrics.json files found.")
            return

        df = pd.DataFrame(results)

        # Default first
        df["is_default"] = df["folder"].apply(lambda x: 1 if x == "default" else 0)
        df = df.sort_values(by="is_default", ascending=False).drop(columns=["is_default"])

        # Final column ordering
        ordered_cols = ["params"] + [
            c for c in df.columns if c not in ("params", "folder")
        ]
        df = df[ordered_cols]

        # -----------------------------------------
        # ⭐ FORMAT exec time and energy
        # -----------------------------------------
        def fmt(value):
            try:
                return f"{float(value):.8f}"  # 8 decimal places
            except:
                return value

        df["exec time"] = df["exec time"].apply(fmt)
        df["energy"] = df["energy"].apply(fmt)

        # -----------------------------------------

        # Save CSV
        csv_path = Path(results_dir) / "summary_table.csv"
        df.to_csv(csv_path, index=False)
        print(f"[Table] CSV exported → {csv_path}")

        # Save pretty text table
        txt_path = Path(results_dir) / "summary_table.txt"
        with open(txt_path, "w") as f:
            for _, row in df.iterrows():
                f.write(f"Params: {row['params']}\n")
                for col in df.columns:
                    if col != "params":
                        f.write(f"  {col}: {row[col]}\n")
                f.write("\n")

        print(f"[Table] Pretty text table exported → {txt_path}")

    # ----------------------------------------------------------
    # Generate all valid combinations
    # ----------------------------------------------------------
    def generate_valid_param_combinations(self, params, conflicts=[]):
        def valid(combo):
            for conflict in conflicts:
                if all(p in combo for p in conflict):
                    return False
            return True

        combos = chain.from_iterable(combinations(params, r) for r in range(len(params) + 1))
        return [list(c) for c in combos if valid(c)]

    # ----------------------------------------------------------
    # Brute-force parameter search
    # ----------------------------------------------------------
    def brute_force_search(self, bc_path, target_metric):
        print("[BruteForce] Testing combinations...")

        best_score = None
        best_params = []

        all_combos = self.generate_valid_param_combinations(self.possible_parameters)
        print(f"[BruteForce] Total combos: {len(all_combos)}")

        for combo in all_combos:
            score, metrics = self.evaluate(bc_path, combo, target_metric)
            print(f"Trying {combo} → {score}")

            # Save results ALWAYS so export_table can read them
            self.save_result_outputs(combo, metrics=metrics)

            if score is not None and (best_score is None or score < best_score):
                best_score = score
                best_params = combo
                print(f"🔥 New best: {score} with {combo}")

        if best_score is not None:
            print(f"\n[BruteForce] ✅ Best combination: {best_params}")
            print(f"[BruteForce] ✅ Best {target_metric}: {best_score:.8f}")
        else:
            print("\n[BruteForce] ❌ No valid combination found that satisfies constraints.")

        return best_params, best_score

    # ----------------------------------------------------------
    # Run the workflow
    # ----------------------------------------------------------
    def run(self, c_file_path, target_metric):
        # Reset results folder
        if os.path.exists("results"):
            shutil.rmtree("results")

        # Frontend compile
        if not self.compiler_frontend.compile(c_file_path):
            print("[Workflow] Frontend compile failed.")
            return

        base = os.path.splitext(os.path.basename(c_file_path))[0]
        bc_path = f"output/{base}.bc"

        best_params, best_score = self.brute_force_search(bc_path, target_metric)

        # Create summary tables
        self.export_table("results")

        return best_params, best_score
