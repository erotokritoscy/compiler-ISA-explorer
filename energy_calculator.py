#!/usr/bin/python
import sys
import re

class parse_node:
    def __init__(self, key=None, value=None, indent=0):
        self.key = key
        self.value = value
        self.indent = indent
        self.leaves = []

    def append(self, n):
        self.leaves.append(n)

    def get_tree(self, indent):
        padding = ' ' * indent * 2
        me = padding + str(self)
        kids = map(lambda x: x.get_tree(indent + 1), self.leaves)
        return me + '\n' + ''.join(kids)

    def getValue(self, key_list):
        if self.key == key_list[0]:
            if len(key_list) == 1:
                return self.value
            else:
                kids = map(lambda x: x.getValue(key_list[1:]), self.leaves)
                return ''.join(kids)
        return ''

    def __str__(self):
        return 'k: ' + str(self.key) + ' v: ' + str(self.value)

class EnergyCalculator:
    def __init__(self, data_in):
        self.debug = False
        self.name = 'mcpat:energy_calculator'
        print(f"[EnergyCalculator] Loading McPAT output: {data_in}")

        try:
            with open(data_in) as buf:
                self.root = parse_node('root', None, -1)
                trunk = [self.root]

                for line in buf:
                    indent = len(line) - len(line.lstrip())
                    equal = '=' in line
                    colon = ':' in line
                    useless = not equal and not colon
                    items = list(map(lambda x: x.strip(), line.split('=')))

                    branch = trunk[-1]

                    if useless:
                        continue
                    elif equal:
                        if len(items) > 1:
                            n = parse_node(key=items[0], value=items[1], indent=indent)
                            branch.append(n)
                            if self.debug:
                                print(f"[EnergyCalculator] Parsed leaf: {n}")
                    else:
                        while indent <= branch.indent:
                            trunk.pop()
                            branch = trunk[-1]
                        n = parse_node(key=items[0], value=None, indent=indent)
                        branch.append(n)
                        trunk.append(n)
                        if self.debug:
                            print(f"[EnergyCalculator] Parsed node: {n}")

            print("[EnergyCalculator] Tree parsing complete.")

        except Exception as e:
            print(f"[EnergyCalculator] ❌ Failed to load file: {e}")
            raise

    def get_tree(self):
        return self.root.get_tree(0)

    def getValue(self, key_list):
        full_key = ' -> '.join(key_list)
        value = self.root.getValue(['root'] + key_list)
        if value == '':
            raise ValueError(f"[EnergyCalculator] ❌ Value not found for key path: {full_key}")
        return value

    def getEnergy(self, runtime_seconds):
        print(f"[EnergyCalculator] Estimating energy with runtime: {runtime_seconds:.8f} s")

        leakage = self.getValue(['Processor:', 'Total Leakage'])
        dynamic = self.getValue(['Processor:', 'Runtime Dynamic'])

        leakage = float(re.sub(' W', '', leakage))
        dynamic = float(re.sub(' W', '', dynamic))

        print(f"[EnergyCalculator] Total Leakage: {leakage} W")
        print(f"[EnergyCalculator] Runtime Dynamic: {dynamic} W")

        energy_joules = (leakage + dynamic) * runtime_seconds

        print(f"[EnergyCalculator] Estimated Energy: {energy_joules:.6f} Joules")
        return energy_joules

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: %s <mcpat-out.txt> <runtime_in_seconds>" % sys.argv[0])
        sys.exit(1)

    mcpat_file = sys.argv[1]
    runtime = float(sys.argv[2])

    calculator = EnergyCalculator(mcpat_file)
    energy = calculator.getEnergy(runtime)

    print("Estimated Energy: %.6f Joules" % energy)
