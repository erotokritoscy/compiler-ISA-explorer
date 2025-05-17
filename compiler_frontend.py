import subprocess
import os
import json

class CompilerFrontend:
    def __init__(self, config_path='config.json'):
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                self.clang_path = os.path.expanduser(config.get("clang_path", "./bin/clang"))
                self.include_path = config.get("riscv_include_path", "/opt/riscv/riscv32-unknown-elf/include")
        except FileNotFoundError:
            print(f"[ERROR] Config file '{config_path}' not found.")
            self.clang_path = "./bin/clang"
            self.include_path = "/opt/riscv/riscv32-unknown-elf/include"

    def compile(self, c_code_path, parameters=None):
        print(f"[CompilerFrontend] Compiling {c_code_path} to LLVM bitcode...")

        # Create output directory if it doesn't exist
        output_dir = "output"
        os.makedirs(output_dir, exist_ok=True)

        # Derive output bitcode file path
        base_name = os.path.splitext(os.path.basename(c_code_path))[0]
        bc_output = os.path.join(output_dir, base_name + ".bc")

        # Build the clang command
        cmd = [
            self.clang_path,
            "-emit-llvm",
            "-target", "riscv32",
            "-isystem", self.include_path,
            "-c", c_code_path,
            "-o", bc_output
        ]

        if parameters:
            cmd[1:1] = parameters  # insert parameters after clang path

        try:
            subprocess.run(cmd, check=True)
            print(f"[SUCCESS] Bitcode generated: {bc_output}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"[ERROR] Compilation failed with return code {e.returncode}")
            return False
        except FileNotFoundError:
            print(f"[ERROR] clang not found at '{self.clang_path}'. Check your config.")
            return False
