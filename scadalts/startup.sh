#!/bin/bash
set -e

# Configure routing (as root)
echo "Configuring network routes..."
ip route add 10.100.1.0/24 via 10.100.2.254

# Verify route
if ! ip route | grep -q "10.100.1.0/24 via 10.100.2.254"; then
    echo "ERROR: Route not configured"
    exit 1
fi

# Wait for database (as root is fine)
echo "Waiting for database..."
/usr/local/bin/wait-for-it \
  --host=scada_db \
  --port=3306 \
  --timeout=60 \
  --strict

# Switch to scada user and start Tomcat
echo "Starting Tomcat as scada user..."
exec su -s /bin/bash scada -c '/usr/local/tomcat/bin/catalina.sh run'