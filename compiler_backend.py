import subprocess
import os
import json
from pathlib import Path

class ParamCompilerBackend:
    def __init__(self, config_path='config.json'):
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                self.llc_path = os.path.expanduser(config.get("llc_path", "./bin/llc"))
                self.objdump_path = os.path.expanduser(config.get("llvm_objdump_path", "./bin/llvm-objdump"))
                self.riscv_gcc = config.get("riscv_gcc", "riscv32-unknown-elf-gcc")
                self.m5ops = config.get("m5ops_object", "m5ops.o")
                self.llc_timeout = config.get("llc_timeout", 5)
        except FileNotFoundError:
            print("[ERROR] config.json not found. Using default tool paths.")
            self.llc_path = "./bin/llc"
            self.objdump_path = "./bin/llvm-objdump"
            self.riscv_gcc = "riscv32-unknown-elf-gcc"
            self.m5ops = "m5ops.o"
            self.llc_timeout = 2

    def compile(self, bc_path, parameters=None):
        output_dir = Path("output")
        base_name = Path(bc_path).stem
        asm_file = output_dir / f"{base_name}.S"
        obj_file = output_dir / f"{base_name}.o"
        disasm_file = output_dir / f"{base_name}.disasm"
        elf_file = output_dir / f"{base_name}.elf"

        output_dir.mkdir(exist_ok=True)

        try:
            print("[Backend] Converting LLVM bitcode to RISC-V assembly...")
            subprocess.run(
                [self.llc_path, bc_path, "-o", str(asm_file)] + (parameters or []),
                check=True,
                timeout=self.llc_timeout
            )

            print("[Backend] Assembling to object file...")
            subprocess.run([
                self.riscv_gcc,
                "-c", str(asm_file),
                "-o", str(obj_file)
            ], check=True)

            print("[Backend] Disassembling object file...")
            with open(disasm_file, "w") as disasm_out:
                subprocess.run([
                    self.objdump_path,
                    "-d", str(obj_file)
                ], stdout=disasm_out, check=True)

            print("[Backend] Linking object to ELF executable...")
            subprocess.run([
                self.riscv_gcc,
                str(obj_file),
                self.m5ops,
                "-o", str(elf_file)
            ], check=True)

            print(f"[Backend] Finished. ELF generated at: {elf_file}")
            return str(elf_file), {"code size": obj_file.stat().st_size}

        except subprocess.TimeoutExpired:
            print(f"[TIMEOUT] Compilation timed out with parameters: {parameters}")
            return None, {}
        except subprocess.CalledProcessError as e:
            print(f"[ERROR] Backend subprocess failed: {e}")
            return None, {}
        except FileNotFoundError as e:
            print(f"[ERROR] Tool not found: {e}")
            return None, {}
