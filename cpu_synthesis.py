import os
import subprocess
import glob
import shutil
import json
import re
from pathlib import Path


class CPUSynthesis:
    def __init__(self):
        home = Path.home()
        self.core_dir = home / "riscv_core/core/custom"
        self.output_dir = Path("yosys_out")
        self.cpu_json = self.output_dir / "cpu.json"
        self.cpu_stats_json = self.output_dir / "cpu_stats.json"
        self.yosys_log = self.output_dir / "yosys_log.txt"

    def synthesize(self, parameters=None):
        # Step 1: Check core path
        if not self.core_dir.is_dir():
            print(f"[CPUSynthesis] Error: RISC-V core directory '{self.core_dir}' not found.")
            return "RTL", {}

        # Step 2: Find Verilog files
        verilog_files = list(self.core_dir.glob("*.v"))
        if not verilog_files:
            print(f"[CPUSynthesis] Error: No Verilog files in '{self.core_dir}'.")
            return "RTL", {}

        # Step 3: Clean and recreate output dir
        if self.output_dir.exists():
            shutil.rmtree(self.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Step 4: Convert parameters to -D defines
        defines = []
        if parameters:
            for param in parameters:
                if param.startswith("-custom-legalize-"):
                    macro = param.lstrip("-").replace("-", "_").upper()
                    defines.append(f"-D {macro}")
        defines_str = " ".join(defines)

        # Step 5: Build Yosys script
        verilog_paths = " ".join(str(f) for f in verilog_files)
        yosys_script = f"""
            read_verilog -sv {defines_str} {verilog_paths};
            hierarchy -top riscv_core;
            proc;
            opt_clean -purge;
            synth -top riscv_core -noabc;
            write_json {self.cpu_json}
        """

        try:
            # Step 6: Run synthesis
            print("[CPUSynthesis] Running Yosys synthesis...")
            subprocess.run(
                ["yosys", "-p", yosys_script],
                stdout=self.yosys_log.open("w"),
                stderr=subprocess.STDOUT,
                text=True
            )

            # Step 7: Run stat analysis
            if self.cpu_json.exists():
                subprocess.run(
                    ["yosys", "-p", f"read_json {self.cpu_json}; stat -json"],
                    stdout=self.cpu_stats_json.open("w"),
                    stderr=subprocess.STDOUT,
                    text=True
                )
            else:
                self.cpu_stats_json.write_text("Warning: cpu.json not found, skipping analysis.\n")
                return "RTL", {}

            # Step 8: Extract JSON content
            with open(self.cpu_stats_json, "r") as f:
                content = f.read()
            match = re.search(r"\{.*\}", content, re.DOTALL)
            if not match:
                print("[CPUSynthesis] No valid JSON found in stat output.")
                return "RTL", {}

            full_json = json.loads(match.group(0))
            design = full_json.get("design", {})

            # Optional: debug print
            # print(json.dumps(design, indent=2))

            return "RTL", {
                "CPU area": int(design.get("num_cells", 0)),
                "num_wires": int(design.get("num_wires", 0)),
                "num_cells": int(design.get("num_cells", 0))
            }

        except Exception as e:
            print(f"[CPUSynthesis] Exception occurred: {e}")
            return "RTL", {}
