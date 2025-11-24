#!/bin/bash

# Configure routing
ip route add 10.100.1.0/24 via 10.100.2.254

echo 'Attacker container ready with routing configured'

# Keep container running
tail -f /dev/null