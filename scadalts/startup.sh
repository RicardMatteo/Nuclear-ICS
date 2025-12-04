#!/bin/bash
set -e

# Configure routing (as root)
# if in 10.100.2.0/24 network, route to 10.100.1.0/24 via 10.100.2.254
if ip addr show eth0 | grep -q "10\.100\.2\."; then
    echo "Configuring route for 10.100.1.0/24 via 10.100.2.254"
    ip route add 10.100.1.0/24 via 10.100.2.254
  # Verify route
  if ! ip route | grep -q "10.100.1.0/24 via 10.100.2.254"; then
      echo "ERROR: Route not configured"
      exit 1
  fi
fi


# Wait for database (as root is fine)
echo "Waiting for database..."
/usr/local/bin/wait-for-it \
  --host=scada_db \
  --port=3306 \
  --timeout=60 \
  --strict

# Fix permissions (image overrides them at runtime)
echo "Fixing permissions on Tomcat directories..."
chown -R scada:scada /usr/local/tomcat/logs \
    /usr/local/tomcat/temp \
    /usr/local/tomcat/work

# Switch to scada user and start Tomcat
echo "Starting Tomcat as scada user..."
exec su -s /bin/bash scada -c '/usr/local/tomcat/bin/catalina.sh run'