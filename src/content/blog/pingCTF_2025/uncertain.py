import angr
import claripy

def main():
    proj = angr.Project("uncertain", auto_load_libs=False)

    # Buffer where the flag is stored 
    buf = 0x446040  

    # Start of main logic 
    entry_point = 0x401146  

    # Address where "Correct flag!" is printed
    find_addr = 0x442622

    # Addresses to avoid (failure cases)
    avoid_addrs = [
        0x44262C,  # "Incorrect flag!"
    ]

    # Find the maximum flag offset
    max_offset = 0x20  # Based on flag+20h seen in disassembly

    # Create a symbolic flag of appropriate length
    flag_length = max_offset + 1  # 21 bytes (flag+0x20 means 0-based index)
    flag = claripy.BVS("flag", flag_length * 8, explicit_name=True)

    # Create a blank state starting at the function handling input
    state = proj.factory.blank_state(addr=entry_point, add_options={angr.options.LAZY_SOLVES})

    # Insert the symbolic flag into memory at the expected buffer location
    state.memory.store(buf, flag, endness='Iend_BE')
    state.regs.rdi = buf  # Set RDI to the flag buffer if scanf uses it

    # Apply constraints to ensure the flag is printable
    for i in range(flag_length):
        state.solver.add(flag.get_byte(i) >= 0x20)  # Space is lowest printable char
        state.solver.add(flag.get_byte(i) <= 0x7E)  # ~ is highest ASCII printable char

    # Create a simulation manager
    simgr = proj.factory.simulation_manager(state)

    # Explore the binary
    simgr.explore(find=find_addr, avoid=avoid_addrs)

    # Extract the found solution
    if simgr.found:
        found_state = simgr.found[0]
        flag_solution = found_state.solver.eval(flag, cast_to=bytes)
        print(f"[*] Found flag: {flag_solution.decode()}")
    else:
        print("[-] No valid flag found.")

if __name__ == "__main__":
    import logging
    logging.getLogger('angr.sim_manager').setLevel(logging.DEBUG)
    main()
