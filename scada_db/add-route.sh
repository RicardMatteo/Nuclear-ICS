#!/bin/bash
set -e

echo "[INFO] Installing iproute2 inside MySQL container..."
microdnf install -y iproute || yum install -y iproute || true

echo "[INFO] Adding static routes inside MySQL container..."

# Route to SCADA net
ip route add 10.100.2.0/24 via 10.100.3.254 || true

# Route to PLC net
ip route add 10.100.1.0/24 via 10.100.3.254 || true

echo "[INFO] Routes added successfully."
