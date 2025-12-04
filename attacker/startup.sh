#!/bin/bash

# Configure routing
if ip addr show eth0 | grep -q "10\.100\.2\."; then
    echo 'Configuring route for 10.100.1.0/24 via 10.100.2.254'
    ip route add 10.100.1.0/24 via 10.100.2.254
fi

echo 'Attacker container ready with routing configured'

# Keep container running
tail -f /dev/null