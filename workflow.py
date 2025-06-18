import os
from compiler_frontend import CompilerFrontend
from cpu_synthesis import CPUSynthesis
from compiler_backend import ParamCompilerBackend
from simulator import Simulator
from peak_power_estimator import PeakPowerEstimator


class Workflow:
    def __init__(self, param_file='params.txt'):
        self.compiler_frontend = CompilerFrontend()
        self.cpu_synthesis = CPUSynthesis()
        self.compiler_backend = ParamCompilerBackend()
        self.simulator = Simulator()
        self.peak_power_estimator = PeakPowerEstimator()

        # Load parameters from file
        try:
            with open(param_file, 'r') as f:
                self.possible_parameters = [line.strip() for line in f if line.strip()]
        except FileNotFoundError:
            print(f"[ERROR] Parameter file '{param_file}' not found.")
            self.possible_parameters = []

    def evaluate(self, bc_path, parameters, target_metric):
        if target_metric == "code size":
            _, code_metrics = self.compiler_backend.compile(bc_path, parameters)
            return code_metrics.get(target_metric)

        elif target_metric in {"CPU area", "power", "frequency"}:
            _, cpu_metrics = self.cpu_synthesis.synthesize(parameters)
            return cpu_metrics.get(target_metric)

        elif target_metric in {"exec time", "peak power", "total leakage", "peak dynamic"}:
            elf_path, _ = self.compiler_backend.compile(bc_path, parameters)
            if not elf_path:
                return None
            # Always run the simulator to generate m5out
            sim_metrics = self.simulator.simulate(elf_path)
            if target_metric in {"peak power", "total leakage", "peak dynamic"}:
                metrics = self.peak_power_estimator.estimate_peak_power(parameters=parameters)
                return metrics.get(target_metric) if metrics else None
            return sim_metrics.get(target_metric)
        else:
            print(f"[ERROR] Unknown target metric: {target_metric}")
            return None

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

            print(f"Trying {trial_params} => {target_metric}: {trial_score:.10f}")
            if trial_score < best_score:
                print(f"✅ Keeping {param}")
                best_parameters.append(param)
                best_score = trial_score
            else:
                print(f"❌ Discarding {param}")

        print(f"\nBest parameters: {best_parameters}")
        print(f"Best {target_metric}: {best_score:.10f}")
        return best_parameters, best_score

    def run(self, c_file_path, target_metric):
        # Run frontend ONCE to produce output/main.bc
        success = self.compiler_frontend.compile(c_file_path)
        if not success:
            print("[Workflow] Compilation failed — aborting.")
            exit(1)

        # Derive .bc path in output dir
        base_name = os.path.splitext(os.path.basename(c_file_path))[0]
        bc_path = os.path.join("output", base_name + ".bc")

        return self.greedy_parameter_search(bc_path, target_metric)
