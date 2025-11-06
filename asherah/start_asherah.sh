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

# Créer ramdisk si nécessaire
mkdir -p /ramdisk
chmod 755 /ramdisk

# Démarrer le serveur Modbus
cd /opt/mbans/MB_SERVER
echo "Starting Modbus Server..."
./modbus_server &
MODBUS_PID=$!
sleep 3

# Démarrer le simulateur (mode standalone ou HIL selon config)
cd /opt/mbans/SIMULATION
echo "Starting Nuclear Simulator..."
if [ "$USE_PLC" = "true" ]; then
    echo "Mode: Hardware-in-the-Loop (with PLC)"
    ./alpha_mbans_HIL_RPS_ON &
    SIMULATOR_PID=$!
    sleep 3
    
    # Démarrer Ferryman pour communication PLC
    cd /opt/mbans/FERRYMAN
    echo "Starting Ferryman bridge..."
    # Modifier l'IP dans ferryman.py
    sed -i "s/192.168.1.100/${PLC_IP}/g" ferryman.py
    python3 ferryman.py &
    FERRYMAN_PID=$!
else
    echo "Mode: Standalone (no external PLC)"
    ./release_mbans_STANDALONE &
    SIMULATOR_PID=$!
fi

echo ""
echo "✓ Asherah simulator started successfully!"
echo "  - Modbus Server PID: $MODBUS_PID"
echo "  - Simulator PID: $SIMULATOR_PID"
[ -n "$FERRYMAN_PID" ] && echo "  - Ferryman PID: $FERRYMAN_PID"
echo ""
echo "Registers available at Modbus TCP port ${MODBUS_PORT}"
echo "Press Ctrl+C to stop..."

# Handler pour arrêt propre
trap "echo 'Stopping...'; kill $MODBUS_PID $SIMULATOR_PID $FERRYMAN_PID 2>/dev/null; exit 0" SIGTERM SIGINT

# Garder le container actif
wait
