#!/usr/bin/env python3
"""
Real-time monitor for the Asherah reactor
Displays values that update continuously in a terminal dashboard.

Compatible with pymodbus 3.8.6
"""

from pymodbus.client import ModbusTcpClient  # pymodbus 3.8.6
import time
import sys
import os

# Configuration
ASHERAH_IP = "10.100.1.10"
ASHERAH_PORT = 502
REFRESH_RATE = 2  # seconds

def clear_screen():
    """Clear the console screen."""
    os.system('clear' if os.name != 'nt' else 'cls')

def read_reactor_values(client):
    """Read reactor values from the Modbus server and convert registers.

    Returns a dict of values on success, or None on failure/exception.
    """
    try:
        result = client.read_input_registers(address=0, count=60, slave=1)

        if not result.isError():
            regs = result.registers
            return {
                # Core
                'power': regs[14] * 0.00183105469,
                'fuel_temp': regs[12] * 0.00152590219 - 273.15,
                'clad_temp': regs[11] * 0.00152590219 - 273.15,
                'mean_temp': regs[8] * 0.00152590219 - 273.15,
                'in_temp': regs[9] * 0.00152590219 - 273.15,
                'out_temp': regs[10] * 0.00152590219 - 273.15,
                'rx_press': regs[15] * 0.00030518509,
                'rod_pos': regs[20] * 0.01525878906,
                # Pressurizer
                'pz_press': regs[21] * 0.00030518509,
                'pz_temp': regs[22] * 0.00152590219 - 273.15,
                'pz_level': regs[23] * 0.00015259022,
                # Primary loops
                'rc1_speed': regs[1] * 0.00152590219,
                'rc2_speed': regs[5] * 0.00152590219,
                'rc1_flow': regs[2] * 0.00015259022,
                'rc2_flow': regs[6] * 0.00015259022,
            }
    except Exception:
        # Any read error returns None so the UI can show an error message.
        return None
    return None

def display_dashboard(values, iteration):
    """Display a neatly aligned terminal dashboard using a fixed inner width.

    The function builds each box using a constant inner width so borders
    and columns are aligned regardless of content length.
    """
    if not values:
        print("Cannot read values from Asherah")
        return

    clear_screen()

    BOX_WIDTH = 76
    LEFT_COL = 38
    RIGHT_COL = BOX_WIDTH - LEFT_COL

    def header(title):
        print("╔" + "=" * BOX_WIDTH + "╗")
        print("║" + title.center(BOX_WIDTH) + "║")
        print("╚" + "=" * BOX_WIDTH + "╝")

    def box_top():
        print("┌" + "─" * BOX_WIDTH + "┐")

    def box_bottom():
        print("└" + "─" * BOX_WIDTH + "┘")

    def two_col(left, right):
        # left aligned in left column, right aligned in right column
        inner = str(left).ljust(LEFT_COL) + str(right).rjust(RIGHT_COL)
        print("│" + inner + "│")

    def one_col(text):
        inner = str(text).center(BOX_WIDTH)
        print("│" + inner + "│")

    header("ASHERAH NUCLEAR REACTOR - LIVE MONITOR")
    print(f"  Update #{iteration}  |  Refresh rate: {REFRESH_RATE}s  |  Press Ctrl+C to exit")
    print()

    # Reactor Core
    box_top()
    two_col(f"Power: {values['power']:>6.1f} %", f"Rod Position: {values['rod_pos']:>6.1f} step")
    two_col(f"Fuel Temp: {values['fuel_temp']:>6.1f} °C", f"Clad Temp: {values['clad_temp']:>6.1f} °C")
    two_col(f"Mean Cool Temp: {values['mean_temp']:>6.1f} °C", f"Reactor Press: {values['rx_press']:>6.2f} MPa")
    two_col(f"Inlet Temp: {values['in_temp']:>6.1f} °C", f"Outlet Temp: {values['out_temp']:>6.1f} °C")
    box_bottom()
    print()

    # Pressurizer
    box_top()
    two_col(f"Pressure: {values['pz_press']:>6.2f} MPa", f"Temperature: {values['pz_temp']:>6.1f} °C")
    two_col(f"Level: {values['pz_level']:>6.2f} m", "")
    box_bottom()
    print()

    # Primary Loops
    box_top()
    two_col(f"Loop 1 Speed: {values['rc1_speed']:>6.1f} %", f"Loop 1 Flow: {values['rc1_flow']:>6.0f} kg/s")
    two_col(f"Loop 2 Speed: {values['rc2_speed']:>6.1f} %", f"Loop 2 Flow: {values['rc2_flow']:>6.0f} kg/s")
    box_bottom()
    print()

    # Status indicators (no emojis)
    status = []
    if values['power'] > 105:
        status.append("HIGH POWER")
    if values['fuel_temp'] > 700:
        status.append("HIGH FUEL TEMP")
    if values['rx_press'] > 16:
        status.append("HIGH PRESSURE")

    if status:
        box_top()
        one_col("WARNINGS")
        for s in status:
            two_col(s, "")
        box_bottom()
    else:
        box_top()
        one_col("All parameters within normal limits")
        box_bottom()

    print()
    print(f"  Next update in {REFRESH_RATE}s...")

def main():
    print("""
╔══════════════════════════════════════════════════════════════════════╗
║         ASHERAH REACTOR - REAL-TIME MONITORING                       ║
║         Live dashboard updating every 2 seconds                      ║
╚══════════════════════════════════════════════════════════════════════╝

This monitor displays real-time values from Asherah.
Compare with ScadaLTS to verify data accuracy.

Connecting to Asherah...
""")
    
    client = ModbusTcpClient(ASHERAH_IP, port=ASHERAH_PORT, timeout=5)
    client.connect()
    
    if not client.connected:
        print(f"Cannot connect to Asherah ({ASHERAH_IP}:{ASHERAH_PORT})")
        print("   Make sure Asherah simulator is running")
        sys.exit(1)
    
    print(f"Connected to {ASHERAH_IP}:{ASHERAH_PORT}")
    print("\nStarting monitor in 2 seconds...")
    time.sleep(2)
    
    iteration = 0
    try:
        while True:
            iteration += 1
            values = read_reactor_values(client)
            display_dashboard(values, iteration)
            time.sleep(REFRESH_RATE)
    
    except KeyboardInterrupt:
        clear_screen()
        print("\n" + "="*78)
        print("  Monitor stopped by user")
        print("="*78)
        print("\n✓ Connection closed\n")
    
    finally:
        client.close()


if __name__ == "__main__":
    main()