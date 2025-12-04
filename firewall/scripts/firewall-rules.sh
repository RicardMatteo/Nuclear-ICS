#!/bin/bash
set -e

echo "Starting ICS Firewall..."

# Default policies
iptables -P FORWARD DROP
iptables -P INPUT ACCEPT
iptables -P OUTPUT ACCEPT

# Allow established connections
iptables -A FORWARD -m state --state ESTABLISHED,RELATED -j ACCEPT

iptables -A FORWARD -s 10.100.2.10 -d 10.100.1.0/24 -p tcp --dport 502 -j ACCEPT
iptables -A FORWARD -s 10.100.1.11 -d 10.100.1.0/24 -p tcp --dport 502 -j ACCEPT
iptables -A FORWARD -s 10.100.1.0/24 -d 10.100.2.10 -p tcp --sport 502 -j ACCEPT
iptables -A FORWARD -s 10.100.1.0/24 -d 10.100.1.11 -p tcp --sport 502 -j ACCEPT


# Allow SCADA to PLC (Modbus)
iptables -A FORWARD -s 10.100.2.10 -d 10.100.1.10 -p tcp --dport 502 -j ACCEPT

# Log dropped packets
iptables -A FORWARD -j LOG --log-prefix "FW-DROP: " --log-level 4

echo "Firewall rules applied"
# show active rules
iptables -L -n -v
# Keep container running
tail -f /dev/null
