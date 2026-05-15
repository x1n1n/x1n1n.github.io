#!/usr/bin/env python3
import sys

class VirtualMachine:
    def __init__(self, mem_size=0x10000):
        # Create a memory array (simulate byte-addressable memory)
        self.memory = [0] * mem_size
        # Create 8 general-purpose registers (32-bit)
        self.registers = [0] * 8
        # Use a Python list as a stack
        self.stack = []
        # Instruction pointer (we call it rip, similar to the disassembly)
        self.ip = 0
        # Comparison flags (simulate data_419124 and data_419125)
        self.flag_equal = False
        self.flag_negative = False
        # Debug mode flag
        self.debug = False

    def load_bytecode(self, filename):
        try:
            with open(filename, "rb") as f:
                bytecode = f.read()
            # Load bytecode into memory starting at address 0
            for i, byte in enumerate(bytecode):
                if i < len(self.memory):
                    self.memory[i] = byte
                else:
                    break
        except Exception as e:
            print(f"Failed to open file: {e}")
            sys.exit(1)

    def run(self):
        # Main fetch-decode-execute loop
        while self.ip < len(self.memory):
            # Check for the end of the loaded program (if we hit a zero opcode, for example)
            opcode = self.memory[self.ip]
            type_field = self.memory[self.ip + 1]
            # Operands are 16-bit values (little endian)
            operand_a = self.memory[self.ip + 2] | (self.memory[self.ip + 3] << 8)
            operand_b = self.memory[self.ip + 4] | (self.memory[self.ip + 5] << 8)
            if self.debug:
                self.print_debug(opcode, type_field, operand_a, operand_b)
            # Dispatch instruction
            self.exec_instruction(opcode, type_field, operand_a, operand_b)
            # Advance instruction pointer (each instruction is 6 bytes)
            # Note: Jump instructions will modify ip directly.
            self.ip += 6

    def exec_instruction(self, opcode, type_field, a, b):
        # Mapping opcodes to methods:
        # 0x00: exit
        # 0x01: mov, 0x02: add, 0x03: sub, 0x04: mul,
        # 0x05: xor, 0x06: or, 0x07: and, 0x08: not,
        # 0x09: push, 0x0a: pop, 0x0b: cmp,
        # 0x0c: jmp, 0x0d: je, 0x0e: jne,
        # 0x0f: jg, 0x10: jl, 0x11: syscall,
        # 0x12: wmem, 0x13: rmem.
        if opcode == 0x00:
            self.op_exit()
        elif opcode == 0x01:
            self.op_mov(type_field, a, b)
        elif opcode == 0x02:
            self.op_add(type_field, a, b)
        elif opcode == 0x03:
            self.op_sub(type_field, a, b)
        elif opcode == 0x04:
            self.op_mul(type_field, a, b)
        elif opcode == 0x05:
            self.op_xor(type_field, a, b)
        elif opcode == 0x06:
            self.op_or(type_field, a, b)
        elif opcode == 0x07:
            self.op_and(type_field, a, b)
        elif opcode == 0x08:
            self.op_not(type_field, a, b)
        elif opcode == 0x09:
            self.op_push(type_field, a, b)
        elif opcode == 0x0a:
            self.op_pop(type_field, a, b)
        elif opcode == 0x0b:
            self.op_cmp(type_field, a, b)
        elif opcode == 0x0c:
            self.op_jmp(type_field, a, b)
        elif opcode == 0x0d:
            self.op_je(type_field, a, b)
        elif opcode == 0x0e:
            self.op_jne(type_field, a, b)
        elif opcode == 0x0f:
            self.op_jg(type_field, a, b)
        elif opcode == 0x10:
            self.op_jl(type_field, a, b)
        elif opcode == 0x11:
            self.op_syscall(type_field, a, b)
        elif opcode == 0x12:
            self.op_wmem(type_field, a, b)
        elif opcode == 0x13:
            self.op_rmem(type_field, a, b)
        else:
            print("Invalid opcode encountered")
            sys.exit(1)

    # Instruction implementations

    def op_exit(self):
        # Opcode 0: exit the VM
        sys.exit(0)

    def op_mov(self, type_field, reg_index, value):
        # For demonstration, interpret type_field as:
        #   0: move from register 'value' to register 'reg_index'
        #   1: move immediate 'value' to register 'reg_index'
        if type_field == 0:
            # Move from register indicated by 'value'
            if value >= len(self.registers):
                print("Invalid source register in mov")
                sys.exit(1)
            self.registers[reg_index] = self.registers[value]
        elif type_field == 1:
            # Immediate move
            self.registers[reg_index] = value
        elif type_field == 2:
            # Move from memory address 'value' to register 'reg_index'
            if value < 0 or value >= len(self.memory):
                print("Invalid memory address in mov")
                sys.exit(1)
            self.registers[reg_index] = self.memory[value]
        elif type_field == 3:
            # Move from register 'value' to memory address 'reg_index'
            if value >= len(self.registers):
                print("Invalid register index in mov")
                sys.exit(1)
            if reg_index >= len(self.memory):
                print("Invalid memory address in mov")
                sys.exit(1)
            self.memory[reg_index] = self.registers[value]
        elif type_field == 4:
            self.memory[reg_index] = value
        elif type_field == 5:
            self.memory[reg_index] = self.memory[value]
        elif type_field == 6:
            self.registers[reg_index] = self.ip
        else:
            print("Invalid mov type")
            sys.exit(1)

    def op_add(self, type_field, reg_index, value):
        # Add: register[reg_index] += operand.
        # For now, support only immediate (type 1) and register (type 0).
        if reg_index >= len(self.registers):
            print("Invalid register index in add")
            sys.exit(1)
        if type_field == 0:
            if value >= len(self.registers):
                print("Invalid source register in add")
                sys.exit(1)
            self.registers[reg_index] += self.registers[value]
        elif type_field == 1:
            self.registers[reg_index] += value
        elif type_field == 2:
            self.registers[reg_index] += self.memory[value]
        else:
            print("Invalid add type")
            sys.exit(1)

    def op_sub(self, type_field, reg_index, value):
        if reg_index >= len(self.registers):
            print("Invalid register index in sub")
            sys.exit(1)
        if type_field == 0:
            if value >= len(self.registers):
                print("Invalid source register in sub")
                sys.exit(1)
            self.registers[reg_index] -= self.registers[value]
        elif type_field == 1:
            self.registers[reg_index] -= value
        elif type_field == 2:
            self.registers[reg_index] -= self.memory[value]
        else:
            print("Invalid sub type")
            sys.exit(1)
        if self.registers[reg_index] < 0:
            exit(0)

    def op_mul(self, type_field, reg_index, value):
        if reg_index >= len(self.registers):
            print("Invalid register index in mul")
            sys.exit(1)
        if type_field == 0:
            if value >= len(self.registers):
                print("Invalid source register in mul")
                sys.exit(1)
            self.registers[reg_index] *= self.registers[value]
        elif type_field == 1:
            self.registers[reg_index] *= value
        elif type_field == 2:
            self.registers[reg_index] *= self.memory[value]
        else:
            print("Invalid mul type")
            sys.exit(1)

    def op_xor(self, type_field, reg_index, value):
        if reg_index >= len(self.registers):
            print("Invalid register index in xor")
            sys.exit(1)
        if type_field == 0:
            if value >= len(self.registers):
                print("Invalid source register in xor")
                sys.exit(1)
            self.registers[reg_index] ^= self.registers[value]
        elif type_field == 1:
            self.registers[reg_index] ^= value
        elif type_field == 2:
            self.registers[reg_index] ^= self.memory[value]
        else:
            print("Invalid xor type")
            sys.exit(1)

    def op_or(self, type_field, reg_index, value):
        if reg_index >= len(self.registers):
            print("Invalid register index in or")
            sys.exit(1)
        if type_field == 0:
            if value >= len(self.registers):
                print("Invalid source register in or")
                sys.exit(1)
            self.registers[reg_index] |= self.registers[value]
        elif type_field == 1:
            self.registers[reg_index] |= value
        elif type_field == 2:
            self.registers[reg_index] |= self.memory[value]
        else:
            print("Invalid or type")
            sys.exit(1)

    def op_and(self, type_field, reg_index, value):
        if reg_index >= len(self.registers):
            print("Invalid register index in and")
            sys.exit(1)
        if type_field == 0:
            if value >= len(self.registers):
                print("Invalid source register in and")
                sys.exit(1)
            self.registers[reg_index] &= self.registers[value]
        elif type_field == 1:
            self.registers[reg_index] &= value
        elif type_field == 2:
            self.registers[reg_index] &= self.memory[value]
        else:
            print("Invalid and type")
            sys.exit(1)

    def op_not(self, type_field, reg_index, value):
        if reg_index >= len(self.registers):
            print("Invalid register index in not")
            sys.exit(1)
        # Just invert the bits.
        if type_field == 0:
            self.registers[reg_index] = ~self.registers[value]
        elif type_field == 1:
            self.registers[reg_index] = ~value
        elif type_field == 2:
            self.registers[reg_index] = ~self.memory[value]
        else:
            print("Invalid not type")
            sys.exit(1)

    def op_push(self, type_field, reg_index, _ignored):
        # For push, we support type 0: push register[reg_index]
        if type_field == 0:
            if reg_index >= len(self.registers):
                print("Invalid register index in push")
                sys.exit(1)
            self.stack.append(self.registers[reg_index])
        elif type_field == 1:
            # Alternatively, push an immediate value (using reg_index as the immediate)
            self.stack.append(reg_index)
        elif type_field == 2:
            # Push memory value at address reg_index
            if reg_index < 0 or reg_index >= len(self.memory):
                print("Invalid memory address in push")
                sys.exit(1)
            self.stack.append(self.memory[reg_index])
        else:
            print("Invalid push type")
            sys.exit(1)

    def op_pop(self, type_field, reg_index, _ignored):
        # For pop, we expect to pop into register[reg_index] (only type 0 supported)
        if not self.stack:
            print("Stack underflow in pop")
            sys.exit(1)
        if type_field == 0 or type_field == 1:
            if reg_index >= len(self.registers):
                print("Invalid register index in pop")
                sys.exit(1)
            self.registers[reg_index] = self.stack.pop()
        elif type_field == 2:
            # Pop into memory address reg_index
            if reg_index < 0 or reg_index >= len(self.memory):
                print("Invalid memory address in pop")
                sys.exit(1)
            self.memory[reg_index] = self.stack.pop()


    def op_cmp(self, type_field, reg_index, value):
        # Compare register[reg_index] with a value (either immediate or from another register)
        if reg_index >= len(self.registers):
            print("Invalid register index in cmp")
            sys.exit(1)
        left = self.registers[reg_index]
        if type_field == 0:
            # Compare with another register
            if value >= len(self.registers):
                print("Invalid source register in cmp")
                sys.exit(1)
            right = self.registers[value]
        elif type_field == 1:
            # Compare with immediate value
            right = value
        elif type_field == 2:
            # Compare with memory value at address 'value'
            if value < 0 or value >= len(self.memory):
                print("Invalid memory address in cmp")
                sys.exit(1)
            right = self.memory[value]
        else:
            print("Invalid cmp type")
            sys.exit(1)
        self.flag_equal = (left == right)
        self.flag_negative = (left - right) < 0

    def op_jmp(self, type_field, addr, _ignored):
        # Unconditional jump: set ip to addr
        if type_field == 0:
            self.ip = addr
        elif type_field == 1:
            # Jump to register[addr]
            if addr >= len(self.registers):
                print("Invalid register index in jmp")
                sys.exit(1)
            self.ip = self.registers[addr]
        else:
            print("Invalid jmp type")
            sys.exit(1)

    def op_je(self, _type_field, addr, _ignored):
        # Jump if equal flag is set
        if self.flag_equal:
            self.op_jmp(_type_field, addr, _ignored)
        else:
            self.ip += 6

    def op_jne(self, _type_field, addr, _ignored):
        # Jump if not equal
        if not self.flag_equal:
            self.op_jmp(_type_field, addr, _ignored)
        else:
            self.ip += 6

    def op_jg(self, _type_field, addr, _ignored):
        # Jump if greater: not equal and not negative.
        if (not self.flag_equal) and (not self.flag_negative):
            self.op_jmp(_type_field, addr, _ignored)
        else:
            self.ip += 6

    def op_jl(self, _type_field, addr, _ignored):
        # Jump if less: not equal and negative.
        if (not self.flag_equal) and (self.flag_negative):
            self.op_jmp(_type_field, addr, _ignored)
        else:
            self.ip += 6

    def op_syscall(self, _type_field, a, b):
        # Syscall: interpret 'a' as the syscall subtype.
        # a==0: getchar, store result in register 0
        # a==1: putchar from register 0
        # a==2: print registers
        # a==3: alternative debug print (here we print registers too)
        if a == 0:
            try:
                ch = sys.stdin.read(1)
                self.registers[0] = ord(ch) if ch else 0
            except Exception as e:
                self.registers[0] = 0
        elif a == 1:
            # Putchar: print character from register 0
            sys.stdout.write(chr(self.registers[0] & 0xFF))
            sys.stdout.flush()
        elif a == 2:
            self.print_registers()
        elif a == 3:
            print("weird function called")
            self.print_registers()
        else:
            print("Invalid syscall type")
            sys.exit(1)

    def op_wmem(self, type_field, addr, value):
        # Write memory: write value to memory at address 'addr'
        # For now, support immediate write (type 1) or from a register (type 0)
        if addr < 0 or addr >= len(self.memory):
            print("Invalid memory address in wmem")
            sys.exit(1)
        if type_field == 0:
            # value is register index
            if value >= len(self.registers):
                print("Invalid register index in wmem")
                sys.exit(1)
            self.memory[self.registers[addr]] = self.registers[value] & 0xFF
        elif type_field == 1:
            self.memory[self.registers[addr]] = value & 0xFF
        elif type_field == 2:
            self.memory[self.registers[addr]] = self.memory[value] & 0xFF
        else:
            print("Invalid wmem type")
            sys.exit(1)

    def op_rmem(self, type_field, reg_index, addr):
        # Read memory: read from memory at 'addr' into register[reg_index]
        if addr < 0 or addr >= len(self.memory):
            print("Invalid memory address in rmem")
            sys.exit(1)
        if reg_index >= len(self.registers):
            print("Invalid register index in rmem")
            sys.exit(1)
        if type_field == 0:
            # store the byte from memory into register
            self.registers[reg_index] = self.memory[self.registers[addr]]
        elif type_field == 1:
            # another variant could be to treat the memory value as an immediate
            self.registers[reg_index] = self.memory[addr]
        elif type_field == 2:
            self.registers[reg_index] = self.memory[self.memory[addr]]
        else:
            print("Invalid rmem type")
            sys.exit(1)

    # Debug and utility functions

    def print_registers(self):
        regs_str = " ".join(f"r{i}:{self.registers[i]:08x}" for i in range(len(self.registers)))
        print(regs_str)

    def print_debug(self, opcode, type_field, a, b):
        print(f"ip: {self.ip:04x} | opcode: {opcode:02x} | type: {type_field:02x} | a: {a:04x} | b: {b:04x}")
        self.print_registers()

def main():
    if len(sys.argv) < 2:
        print("usage: ./shrimple_vm <filename>")
        sys.exit(1)
    vm = VirtualMachine()
    # Optionally, enable debug mode if a second argument is passed.
    vm.debug = (len(sys.argv) > 2)
    print("reading bytecode...")
    vm.load_bytecode(sys.argv[1])
    print("\nmachine started")
    if vm.debug:
        print("debug mode enabled")
    vm.run()

if __name__ == "__main__":
    main()

