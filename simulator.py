import subprocess
from pathlib import Path
import json

class Simulator:
    def __init__(self, config_path="config.json"):
        try:
            with open(config_path, "r") as f:
                config = json.load(f)
                self.gem5_path = Path(config.get("gem5_path", "~/gem5")).expanduser()
        except FileNotFoundError:
            print("[ERROR] config.json not found. Using default gem5 path.")
            self.gem5_path = Path("~/gem5").expanduser()

    def run_simulation(self, elf_path):
        output_dir = Path("output")
        elf_path = Path(elf_path)

        try:
            print("[Simulator] Running gem5 simulation...")

            subprocess.run([
                str(self.gem5_path / "build/RISCV/gem5.opt"),
                str(self.gem5_path / "configs/learning_gem5/part1/my-simple-riscv.py"),
                str(elf_path)
            ], check=True)

            print(f"[Simulator] Simulation completed. Output directory: {Path('m5out').resolve()}")
            return self.parse_stats("m5out/stats.txt")

        except subprocess.CalledProcessError as e:
            print(f"[ERROR] Simulation failed: {e}")
            return {}

    def parse_stats(self, stats_file):
        stats = {}
        capture = False

        try:
            with open(stats_file, "r") as f:
                for line in f:
                    line = line.strip()

                    if line.startswith("---------- Begin Simulation Statistics ----------"):
                        capture = True
                        continue
                    elif line.startswith("---------- End Simulation Statistics"):
                        break

                    if capture and line and not line.startswith("#") and not line.startswith("----------"):
                        parts = line.split("#")[0].strip().split()
                        if len(parts) >= 2:
                            key = parts[0]
                            value = " ".join(parts[1:])
                            stats[key] = value
        except FileNotFoundError:
            print(f"[ERROR] Stats file not found: {stats_file}")

        return stats

    def simulate(self, elf_path):
        stats = self.run_simulation(elf_path)

        # Extract specific values (adjust these based on what's available in your stats)
        return {
            "exec time": float(stats.get("simSeconds", 0)),
            "energy": float(stats.get("system.switch_cpus.numCycles", 0)),
            "peak power": float(stats.get("system.l2.overall_misses::total", 0))  # example fallback
        }
