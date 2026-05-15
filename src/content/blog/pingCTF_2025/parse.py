#!/usr/bin/env python3
import sys
import argparse
from typing import List, Tuple, Optional

# Opcode mappings
OPCODES = {
    0x00: "exit",
    0x01: "mov",
    0x02: "add",
    0x03: "sub",
    0x04: "mul",
    0x05: "xor",
    0x06: "or",
    0x07: "and",
    0x08: "not",
    0x09: "push",
    0x0a: "pop",
    0x0b: "cmp",
    0x0c: "jmp",
    0x0d: "je",
    0x0e: "jne",
    0x0f: "jg",
    0x10: "jl",
    0x11: "syscall",
    0x12: "wmem",
    0x13: "rmem"
}

class Decompiler:
    def __init__(self, bytecode_file: str, output_file: str = None, pretty: bool = True):
        self.bytecode_file = bytecode_file
        self.output_file = output_file
        self.bytecode = []
        self.pretty = pretty
        self.labels = {}
        self.inst_size = 6  # Each instruction is 6 bytes

    def load_bytecode(self) -> None:
        """Load bytecode from file into memory."""
        try:
            with open(self.bytecode_file, "rb") as f:
                self.bytecode = list(f.read())
            print(f"Loaded {len(self.bytecode)} bytes from {self.bytecode_file}")
        except Exception as e:
            print(f"Failed to open file: {e}")
            sys.exit(1)

    def find_jump_targets(self) -> None:
        """Scan through bytecode to find all jump targets and create labels."""
        for i in range(0, len(self.bytecode) - 5, self.inst_size):
            opcode = self.bytecode[i]
            type_field = self.bytecode[i + 1]
            operand_a = self.bytecode[i + 2] | (self.bytecode[i + 3] << 8)
            
            # Check if this is a jump instruction with immediate addressing
            if opcode in [0x0c, 0x0d, 0x0e, 0x0f, 0x10] and type_field == 0:
                # Add target to labels dict if not register-based jump
                if operand_a not in self.labels:
                    self.labels[operand_a] = f"label_{operand_a:04x}"

    def format_operand(self, type_field: int, operand: int, register_prefix: str = "r") -> str:
        """Format operand based on type field."""
        # Different instructions have different type field interpretations
        # This is a simplified version, might need to be expanded for specific opcodes
        if type_field == 0:  # Register
            return f"{register_prefix}{operand}"
        elif type_field == 1:  # Immediate
            return f"{operand}"
        elif type_field == 2:  # Memory address operand
            return f"[{operand}]"
        elif type_field == 3:  # Register to memory
            return f"[{operand}]"
        elif type_field == 4:  # Immediate to memory
            return f"[{operand}]"
        elif type_field == 5:  # Memory to memory
            return f"[{operand}]"
        elif type_field == 6:  # Special (e.g., IP)
            return f"ip"
        else:
            return f"{operand} (unknown addressing mode {type_field})"

    def format_instruction(self, addr: int, opcode: int, type_field: int, 
                           operand_a: int, operand_b: int) -> str:
        """Format a single instruction as assembly code."""
        if opcode not in OPCODES:
            return f"; Invalid opcode: {opcode:02x}"
        
        mnemonic = OPCODES[opcode]
        label = self.labels.get(addr, "")
        label_str = f"{label}:" if label else ""
        
        # Format based on instruction type
        if opcode == 0x00:  # exit
            return f"{label_str:<12} exit"
        
        elif opcode in [0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07]:  # Binary ops
            # mov, add, sub, mul, xor, or, and
            dst = self.format_operand(0, operand_a)  # Always a register for these
            src = self.format_operand(type_field, operand_b)
            return f"{label_str:<12} {mnemonic} {dst}, {src}"
        
        elif opcode == 0x08:  # not (unary op)
            dst = self.format_operand(0, operand_a)
            src = self.format_operand(type_field, operand_b)
            return f"{label_str:<12} not {dst}, {src}"
        
        elif opcode == 0x09:  # push
            if type_field == 0:
                operand = self.format_operand(0, operand_a)
            else:
                operand = self.format_operand(type_field, operand_a)
            return f"{label_str:<12} push {operand}"
        
        elif opcode == 0x0a:  # pop
            operand = self.format_operand(0, operand_a)
            return f"{label_str:<12} pop {operand}"
        
        elif opcode == 0x0b:  # cmp
            left = self.format_operand(0, operand_a)
            right = self.format_operand(type_field, operand_b)
            return f"{label_str:<12} cmp {left}, {right}"
        
        elif opcode in [0x0c, 0x0d, 0x0e, 0x0f, 0x10]:  # Jumps
            # jmp, je, jne, jg, jl
            if type_field == 0:  # Direct jump
                target = self.labels.get(operand_a, f"0x{operand_a:04x}")
                return f"{label_str:<12} {mnemonic} {target}"
            else:  # Register jump
                reg = self.format_operand(0, operand_a)
                return f"{label_str:<12} {mnemonic} {reg}"
        
        elif opcode == 0x11:  # syscall
            return f"{label_str:<12} syscall {operand_a}"
        
        elif opcode == 0x12:  # wmem
            addr_reg = self.format_operand(0, operand_a)
            if type_field == 0:
                value = self.format_operand(0, operand_b)
            else:
                value = self.format_operand(type_field, operand_b)
            return f"{label_str:<12} wmem [{addr_reg}], {value}"
        
        elif opcode == 0x13:  # rmem
            dst_reg = self.format_operand(0, operand_a)
            if type_field == 0:
                addr = f"[{self.format_operand(0, operand_b)}]"
            else:
                addr = self.format_operand(type_field, operand_b)
            return f"{label_str:<12} rmem {dst_reg}, {addr}"
        
        else:
            return f"{label_str:<12} ; Unknown instruction {mnemonic} {type_field} {operand_a} {operand_b}"

    def decompile(self) -> List[str]:
        """Decompile bytecode into assembly instructions."""
        self.find_jump_targets()
        
        asm_lines = ["; Decompiled from bytecode file: " + self.bytecode_file,
                    "; Format: [label:] instruction operands",
                    ""]
        
        # Add labels section
        if self.pretty and self.labels:
            asm_lines.extend(["; Jump targets:", ""])
        
        # Disassemble each instruction
        for addr in range(0, len(self.bytecode) - 5, self.inst_size):
            opcode = self.bytecode[addr]
            type_field = self.bytecode[addr + 1]
            operand_a = self.bytecode[addr + 2] | (self.bytecode[addr + 3] << 8)
            operand_b = self.bytecode[addr + 4] | (self.bytecode[addr + 5] << 8)
            
            # Add address comment if pretty printing
            
            # Format and add the instruction
            asm_line = self.format_instruction(addr, opcode, type_field, operand_a, operand_b)
            asm_lines.append(asm_line)
            
            # Add empty line after each instruction if pretty printing
            if self.pretty:
                asm_lines.append("")
        
        return asm_lines

    def save_output(self, asm_lines: List[str]) -> None:
        """Save the decompiled assembly to file or print to stdout."""
        if self.output_file:
            try:
                with open(self.output_file, "w") as f:
                    f.write("\n".join(asm_lines))
                print(f"Output saved to {self.output_file}")
            except Exception as e:
                print(f"Failed to write output file: {e}")
                sys.exit(1)
        else:
            print("".join(asm_lines))

def main():
    parser = argparse.ArgumentParser(description="Decompile VM bytecode to assembly")
    parser.add_argument("input_file", help="Input bytecode file")
    parser.add_argument("-o", "--output", help="Output assembly file")
    parser.add_argument("-p", "--pretty", action="store_true", help="Enable pretty printing")
    args = parser.parse_args()

    decompiler = Decompiler(args.input_file, args.output, args.pretty)
    decompiler.load_bytecode()
    asm_lines = decompiler.decompile()
    decompiler.save_output(asm_lines)

if __name__ == "__main__":
    main()
