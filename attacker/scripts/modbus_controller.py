#!/usr/bin/env python3
"""
Interactive Modbus controller for the Asherah simulator
Allows writing to any register/coil with optional spam modes.

Compatible with pymodbus 3.8.6
"""

from pymodbus.client import ModbusTcpClient
import time
import sys
import threading

# Configuration
ASHERAH_IP = "10.100.1.10"
ASHERAH_PORT = 502

# Interesting registers for Asherah (from the lab documentation)
COILS_MAP = {
    0: "RC1_PumpOnOffCmd (Primary pump 1 ON/OFF)",
    1: "RC2_PumpOnOffCmd (Primary pump 2 ON/OFF)",
    2: "CR_SCRAMCmd (Emergency SCRAM command)",
    3: "PZ_BackupHeaterPowCmd (Pressurizer backup heater)",
    4: "AF_MakeupPumpCmd (Makeup pump command)",
    5: "SD_SafetyValveCmd (Safety valve command)",
    6: "TB_IsoValveCmd (Turbine isolation valve)",
    7: "CC_PumpOnOffCmd (Condenser pump ON/OFF)",
    8: "FW_Pump1OnOffCmd (Feedwater pump 1 ON/OFF)",
    9: "FW_Pump2OnOffCmd (Feedwater pump 2 ON/OFF)",
    10: "FW_Pump3OnOffCmd (Feedwater pump 3 ON/OFF)",
}

HOLDING_REGS_MAP = {
    0: "RC1_PumpSpeedCmd (Pump 1 speed, 0-100%)",
    1: "RC2_PumpSpeedCmd (Pump 2 speed, 0-100%)",
    2: "CR_PosCmd (Control rod position, 0-1000 steps)",
    17: "CTRL_RXPowerSetpoint (Power setpoint, 0-110%)",
    18: "CTRL_PZPressSetPoint (Pressurizer pressure setpoint, 0-18 MPa)",
}

class ModbusController:
    def __init__(self):
        self.client = ModbusTcpClient(ASHERAH_IP, port=ASHERAH_PORT, timeout=5)
        self.spam_active = False
        self.spam_thread = None
        
    def connect(self):
        """Connect to Asherah Modbus server."""
        print(f"Connecting to Asherah ({ASHERAH_IP}:{ASHERAH_PORT})...")
        self.client.connect()
        
        if not self.client.connected:
            print("ERROR: Cannot connect to Asherah")
            sys.exit(1)
        print("Connected\n")
    
    def read_coil(self, address):
        """Read a single coil (binary actuator)."""
        try:
            result = self.client.read_coils(address=address, count=1, slave=1)
            if not result.isError():
                return result.bits[0]
        except Exception as e:
            print(f"WARNING: Error: {e}")
        return None
    
    def write_coil(self, address, value):
        """Write a single coil (binary actuator)."""
        try:
            result = self.client.write_coil(address=address, value=value, slave=1)
            if not result.isError():
                return True
            else:
                print(f"WARNING: Modbus error: {result}")
        except Exception as e:
            print(f"WARNING: Error: {e}")
        return False
    
    def read_holding_register(self, address):
        """Read a single holding register."""
        try:
            result = self.client.read_holding_registers(address=address, count=1, slave=1)
            if not result.isError():
                return result.registers[0]
        except Exception as e:
            print(f"WARNING: Error: {e}")
        return None
    
    def write_holding_register(self, address, value):
        """Write a single holding register."""
        try:
            result = self.client.write_register(address=address, value=value, slave=1)
            if not result.isError():
                return True
            else:
                print(f"WARNING: Modbus error: {result}")
        except Exception as e:
            print(f"WARNING: Error: {e}")
        return False
    
    def read_input_register(self, address):
        """Read a single input register (sensor reading)."""
        try:
            result = self.client.read_input_registers(address=address, count=1, slave=1)
            if not result.isError():
                return result.registers[0]
        except Exception as e:
            print(f"WARNING: Error: {e}")
        return None
    
    def spam_writer(self, reg_type, address, value, frequency):
        """Background thread to spam writes at a given frequency."""
        interval = 1.0 / frequency
        count = 0
        print(f"\nSpam started: Writing {value} to {reg_type} {address} every {interval:.2f}s")
        print("   Press 's' in main menu to stop\n")
        
        while self.spam_active:
            if reg_type == "coil":
                self.write_coil(address, value)
            elif reg_type == "holding":
                self.write_holding_register(address, value)
            
            count += 1
            if count % 10 == 0:
                print(f"  [Spam] {count} messages sent...")
            time.sleep(interval)
        
        print(f"\nSpam stopped (sent {count} messages)\n")
    
    def menu_write_coil(self):
        """Menu to write a coil (binary actuator)."""
        print("\n" + "="*70)
        print("  WRITE COIL (Binary Actuator)")
        print("="*70)
        print("\nAvailable coils:")
        for addr, desc in sorted(COILS_MAP.items()):
            current = self.read_coil(addr)
            status = f"[Current: {current}]" if current is not None else ""
            print(f"  {addr:3d} : {desc} {status}")
        
        print("\nOr enter any address (0-65535)")
        
        try:
            address = int(input("\nCoil address: "))
            value_str = input("Value (0/1 or ON/OFF): ").strip().upper()
            
            if value_str in ['1', 'ON', 'TRUE']:
                value = True
            elif value_str in ['0', 'OFF', 'FALSE']:
                value = False
            else:
                print("Invalid value")
                return
            
            mode = input("Mode (s=single, r=repeat): ").strip().lower()
            
            if mode == 's':
                if self.write_coil(address, value):
                    print(f"Coil {address} set to {value}")
                    new_val = self.read_coil(address)
                    print(f"  Verification: {new_val}")
            
            elif mode == 'r':
                freq = float(input("Frequency (Hz, ex: 1 for 1/s, 10 for 10/s): "))
                self.spam_active = True
                self.spam_thread = threading.Thread(
                    target=self.spam_writer,
                    args=("coil", address, value, freq),
                    daemon=True
                )
                self.spam_thread.start()
        
        except ValueError:
            print(" Invalid input")
    
    def menu_write_holding(self):
        """Menu to write a holding register (analog command)."""
        print("\n" + "="*70)
        print("  WRITE HOLDING REGISTER (Analog Command)")
        print("="*70)
        print("\nImportant registers:")
        for addr, desc in sorted(HOLDING_REGS_MAP.items()):
            current = self.read_holding_register(addr)
            status = f"[Current: {current}]" if current is not None else ""
            print(f"  {addr:3d} : {desc} {status}")
        
        print("\nOr enter any address (0-65535)")
        
        try:
            address = int(input("\nHolding register address: "))
            
            # Aide selon l'adresse
            if address == 17:
                print("  Power setpoint: 0-110% -> Raw value: 0-65535")
                print("  Formula: raw = (percent / 110) * 65535")
                percent = float(input("  Enter power %: "))
                value = int((percent / 110.0) * 65535)
                print(f"  → Will write raw value: {value}")
            
            elif address == 18:
                print("  Pressure setpoint: 0-18 MPa -> Raw value: 0-65535")
                print("  Formula: raw = (mpa / 18) * 65535")
                mpa = float(input("  Enter pressure (MPa): "))
                value = int((mpa / 18.0) * 65535)
                print(f"  → Will write raw value: {value}")
            
            elif address in [0, 1]:
                print("  Pump speed: 0-100% -> Raw value: 0-65535")
                print("  Formula: raw = (percent / 100) * 65535")
                percent = float(input("  Enter speed %: "))
                value = int((percent / 100.0) * 65535)
                print(f"  → Will write raw value: {value}")
            
            elif address == 2:
                print("  Rod position: 0-1000 steps -> Raw value: 0-65535")
                print("  Formula: raw = (steps / 1000) * 65535")
                steps = float(input("  Enter position (steps): "))
                value = int((steps / 1000.0) * 65535)
                print(f"  → Will write raw value: {value}")
            
            else:
                value = int(input("Raw value (0-65535): "))
            
            mode = input("Mode (s=single, r=repeat): ").strip().lower()
            
            if mode == 's':
                if self.write_holding_register(address, value):
                    print(f"HR {address} set to {value}")
                    time.sleep(0.5)
                    new_val = self.read_holding_register(address)
                    print(f"  Verification: {new_val}")
            
            elif mode == 'r':
                freq = float(input("Frequency (Hz): "))
                self.spam_active = True
                self.spam_thread = threading.Thread(
                    target=self.spam_writer,
                    args=("holding", address, value, freq),
                    daemon=True
                )
                self.spam_thread.start()
        
        except ValueError:
            print("Invalid input")
    
    def menu_read(self):
        """Menu to read registers."""
        print("\n" + "="*70)
        print("  READ REGISTERS")
        print("="*70)
        print("\n1. Read Coil (FC 01)")
        print("2. Read Discrete Input (FC 02)")
        print("3. Read Holding Register (FC 03)")
        print("4. Read Input Register (FC 04)")
        
        choice = input("\nChoice: ").strip()
        
        try:
            address = int(input("Address: "))
            count = int(input("Count (default 1): ") or "1")
            
            if choice == '1':
                result = self.client.read_coils(address=address, count=count, slave=1)
                if not result.isError():
                    print(f"\nCoils {address}-{address+count-1}: {result.bits[:count]}")
            
            elif choice == '2':
                result = self.client.read_discrete_inputs(address=address, count=count, slave=1)
                if not result.isError():
                    print(f"\nDiscrete Inputs {address}-{address+count-1}: {result.bits[:count]}")
            
            elif choice == '3':
                result = self.client.read_holding_registers(address=address, count=count, slave=1)
                if not result.isError():
                    print(f"\nHolding Registers {address}-{address+count-1}: {result.registers}")
            
            elif choice == '4':
                result = self.client.read_input_registers(address=address, count=count, slave=1)
                if not result.isError():
                    regs = result.registers
                    print(f"\nInput Registers {address}-{address+count-1}:")
                    for i, val in enumerate(regs):
                        print(f"  IR {address+i}: {val} (0x{val:04X})")
        
        except ValueError:
            print(" Invalid input")
        except Exception as e:
            print(f" Error: {e}")
    
    def stop_spam(self):
        """Stop any active spam thread."""
        if self.spam_active:
            self.spam_active = False
            if self.spam_thread:
                self.spam_thread.join(timeout=2)
            print("Spam stopped")
        else:
            print("No spam active")
    
    def main_menu(self):
        """Main interactive menu."""
        print("""
╔══════════════════════════════════════════════════════════════════════╗
║         MODBUS INTERACTIVE CONTROLLER - Asherah Reactor              ║
╚══════════════════════════════════════════════════════════════════════╝

Control the reactor by writing to actuators:
  - COILS: Binary commands (ON/OFF)
  - HOLDING REGISTERS: Analog commands (setpoints, speeds)

Monitor with:
  - INPUT REGISTERS: Sensor readings
  - DISCRETE INPUTS: Binary sensor states
""")
        
        while True:
            print("\n" + "="*70)
            print("  MAIN MENU")
            print("="*70)
            print("\n1. Write COIL (Binary actuator)")
            print("2. Write HOLDING REGISTER (Analog command)")
            print("3. Read any register type")
            print("4. Quick actions (presets)")
            print("s. Stop spam")
            print("q. Quit")
            
            choice = input("\n> ").strip().lower()
            
            if choice == '1':
                self.menu_write_coil()
            elif choice == '2':
                self.menu_write_holding()
            elif choice == '3':
                self.menu_read()
            elif choice == '4':
                self.menu_quick_actions()
            elif choice == 's':
                self.stop_spam()
            elif choice == 'q':
                self.stop_spam()
                print("\n✓ Disconnecting...\n")
                break
    
    def menu_quick_actions(self):
        """Quick predefined actions."""
        print("\n" + "="*70)
        print("  QUICK ACTIONS")
        print("="*70)
        print("\n1. Set power to 100%")
        print("2. Set power to 110% (max safe)")
        print("3. Set power to 120% (DANGEROUS)")
        print("4. Set power to 50%")
        print("5. SCRAM (emergency shutdown)")
        print("6. Stop pump 1")
        print("7. Start pump 1")
        
        choice = input("\nChoice: ").strip()
        
        if choice == '1':
            self.write_holding_register(17, int((100/110)*65535))
            print("Power setpoint -> 100%")
        
        elif choice == '2':
            self.write_holding_register(17, 65535)
            print("Power setpoint -> 110%")
        
        elif choice == '3':
            self.write_holding_register(17, int((120/110)*65535))
            print("WARNING: Power setpoint -> 120% (EXCEEDS DESIGN!)")
        
        elif choice == '4':
            self.write_holding_register(17, int((50/110)*65535))
            print("Power setpoint -> 50%")
        
        elif choice == '5':
            self.write_coil(2, True)
            print("WARNING: SCRAM ACTIVATED!")
        
        elif choice == '6':
            self.write_coil(0, False)
            print("Pump 1 stopped")
        
        elif choice == '7':
            self.write_coil(0, True)
            print("Pump 1 started")


def main():
    controller = ModbusController()
    controller.connect()
    
    try:
        controller.main_menu()
    except KeyboardInterrupt:
        print("\n\n Interrupted by user\n")
    finally:
        controller.stop_spam()
        controller.client.close()


if __name__ == "__main__":
    main()