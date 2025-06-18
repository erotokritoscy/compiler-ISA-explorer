import subprocess
import json
from pathlib import Path
import re

class PeakPowerEstimator:
    def __init__(self, config_path="config.json"):
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                self.mcpat_path = Path(config.get("mcpat_path", "~/mcpat-calib-public/mcpat")).expanduser()
                self.parser_script = Path(config.get("mcpat_parser", "Gem5McPATParser.py")).expanduser()
                self.template_xml = Path(config.get("mcpat_template", "mcpat_template.xml")).expanduser()
        except FileNotFoundError:
            print("[Power] Warning: config.json not found. Using defaults.")
            self.mcpat_path = Path("~/mcpat-calib-public/mcpat").expanduser()
            self.parser_script = Path("Gem5McPATParser.py").expanduser()
            self.template_xml = Path("mcpat_template.xml").expanduser()

    def estimate_peak_power(self, m5out_path="m5out"):
        # Cleanup previous run files
        for f in ["mcpat-in.xml", "mcpat-out.txt"]:
            path = Path(f)
            if path.exists():
                path.unlink()

        m5out = Path(m5out_path)
        config_json = m5out / "config.json"
        stats_txt = m5out / "stats.txt"
        mcpat_input = Path("mcpat-in.xml")
        mcpat_output = Path("mcpat-out.txt")

        # Step 1: Run Gem5McPATParser.py
        try:
            print("[Power] Generating mcpat-in.xml...")
            subprocess.run([
                "python3", str(self.parser_script),
                "--config", str(config_json),
                "--stats", str(stats_txt),
                "--template", str(self.template_xml)
            ], check=True)
        except subprocess.CalledProcessError:
            print("[Power] Error: McPAT input generation failed.")
            return None

        # Step 2: Run McPAT
        try:
            print("[Power] Running McPAT...")
            with mcpat_output.open("w") as f:
                subprocess.run([
                    str(self.mcpat_path / "mcpat"),
                    "-infile", str(mcpat_input),
                    "-print_level", "1"
                ], stdout=f, stderr=subprocess.STDOUT, check=True)
        except subprocess.CalledProcessError:
            print("[Power] Error: McPAT execution failed.")
            return None

        # Step 3: Parse peak power from mcpat-out.txt
        results = {}
        try:
            with mcpat_output.open("r") as f:
                for line in f:
                    if "Peak Power" in line:
                        match = re.search(r"Peak Power\s*=\s*([\d\.eE+-]+)", line)
                        if match:
                            results["peak power"] = float(match.group(1))
                    elif "Total Leakage" in line:
                        match = re.search(r"Total Leakage\s*=\s*([\d\.eE+-]+)", line)
                        if match:
                            results["total leakage"] = float(match.group(1))
                    elif "Peak Dynamic" in line:
                        match = re.search(r"Peak Dynamic\s*=\s*([\d\.eE+-]+)", line)
                        if match:
                            results["peak dynamic"] = float(match.group(1))

            if results:
                for k, v in results.items():
                    print(f"[Power] {k.capitalize()}: {v} W")
                return results
            else:
                print("[Power] No valid power entries found in McPAT output.")
                return None
        except Exception as e:
            print(f"[Power] Error parsing mcpat-out.txt: {e}")

        print("[Power] Peak Power not found in McPAT output.")
        return None


# ------------------------------
# ✅ Main function for testing
# ------------------------------
if __name__ == "__main__":
    estimator = PeakPowerEstimator()
    peak = estimator.estimate_peak_power()
    if peak is not None:
        print(f"✅ Peak Power (W): {peak}")
    else:
        print("❌ Failed to estimate peak power.")
