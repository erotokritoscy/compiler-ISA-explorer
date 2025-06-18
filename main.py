import sys
from workflow import Workflow

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python main.py <source_file.c>")
        sys.exit(1)

    c_file = sys.argv[1]

    print("Choose metric to optimize: exec time, code size, CPU area, peak power, total leakage, peak dynamic")
    metric = input("Metric: ").strip()

    workflow = Workflow()
    params, score = workflow.run(c_file, metric)
