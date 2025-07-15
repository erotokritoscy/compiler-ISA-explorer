import sys
from workflow import Workflow

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python main.py <source_file.c>")
        sys.exit(1)

    c_file = sys.argv[1]

    valid_metrics = {
        "exec time", "code size", "CPU area", "peak power", "total leakage", "peak dynamic", "energy"
    }

    print("Choose metric to optimize: exec time, code size, CPU area, peak power, total leakage, peak dynamic, energy")
    metric = input("Metric: ").strip()

    if metric not in valid_metrics:
        print(f"[ERROR] Invalid metric: '{metric}'")
        print("Valid metrics:", ", ".join(valid_metrics))
        sys.exit(1)

    workflow = Workflow()
    params, score = workflow.run(c_file, metric)
