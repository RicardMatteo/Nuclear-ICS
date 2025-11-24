#!/bin/bash

# Configuration
export PLC_IP=${PLC_IP:-172.20.0.20}
export PLC_PORT=${PLC_PORT:-502}
export MODBUS_PORT=${MODBUS_PORT:-502}

echo "========================================="
echo "  Asherah Nuclear Power Plant Simulator"
echo "========================================="
echo "Modbus Server: 0.0.0.0:${MODBUS_PORT}"
echo "PLC Target: ${PLC_IP}:${PLC_PORT}"
echo "========================================="

# Route statique
ip route add 10.100.2.0/24 via 10.100.1.254

# Create ramdisk if needed
mkdir -p /ramdisk
chmod 755 /ramdisk

# Start the Modbus server
cd /opt/mbans/MB_SERVER
echo "Starting Modbus Server..."
# The Modbus server must listen on 0.0.0.0 to be reachable from Docker
./modbus_server &
MODBUS_PID=$!
sleep 5

# Verify the server is listening
if netstat -tuln 2>/dev/null | grep -q ":502"; then
    echo "Modbus server listening on port 502"
else
    echo "Warning: Modbus server may not be listening on port 502"
fi

# Start the simulator (standalone or HIL based on configuration)
cd /opt/mbans/SIMULATION
echo "Starting Nuclear Simulator..."
if [ "$USE_PLC" = "true" ]; then
    echo "Mode: Hardware-in-the-Loop (with PLC)"
    ./alpha_mbans_HIL_RPS_ON &
    SIMULATOR_PID=$!
    sleep 3
    
    # Start Ferryman for PLC communication
    cd /opt/mbans/FERRYMAN
    echo "Starting Ferryman bridge..."
    # Update the IP in ferryman.py to match PLC target
    sed -i "s/192.168.1.100/${PLC_IP}/g" ferryman.py
    python3 ferryman.py &
    FERRYMAN_PID=$!
else
    echo "Mode: Standalone (no external PLC)"
    ./release_mbans_STANDALONE &
    SIMULATOR_PID=$!
fi

echo ""
echo "Asherah simulator started successfully!"
echo "  - Modbus Server PID: $MODBUS_PID"
echo "  - Simulator PID: $SIMULATOR_PID"
[ -n "$FERRYMAN_PID" ] && echo "  - Ferryman PID: $FERRYMAN_PID"
echo ""
echo "Registers available at Modbus TCP port ${MODBUS_PORT}"
echo "Press Ctrl+C to stop..."

# Clean shutdown handler
trap "echo 'Stopping...'; kill $MODBUS_PID $SIMULATOR_PID $FERRYMAN_PID 2>/dev/null; exit 0" SIGTERM SIGINT

# Keep the container running
wait