#!/bin/bash

# Enable IP forwarding
echo 1 > /proc/sys/net/ipv4/ip_forward

# Flush existing rules
iptables -F
iptables -X
iptables -t nat -F
iptables -t nat -X

# Default policies - DROP everything by default
iptables -P FORWARD DROP
iptables -P INPUT DROP
iptables -P OUTPUT ACCEPT

# Allow established connections
iptables -A FORWARD -m state --state ESTABLISHED,RELATED -j ACCEPT
iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT

# Allow loopback
iptables -A INPUT -i lo -j ACCEPT

# ============================================
# ICS FIREWALL RULES (UPDATED IPs!)
# ============================================

# Allow SCADA (10.100.2.10 and 10.100.1.10) to PLC network - Modbus TCP (port 502)
iptables -A FORWARD -i eth0 -o eth1 -m mac --mac-source 02:42:0a:64:01:0a -d 10.100.2.10 -p tcp --dport 502 -j ACCEPT
iptables -A FORWARD -i eth0 -o eth1 -m mac --mac-source 02:42:0a:64:01:0a -d 10.100.2.10 -p tcp --sport 502 -j ACCEPT
iptables -A FORWARD -i eth1 -o eth0 -m mac --mac-source 02:42:0a:64:02:0a -d 10.100.1.10 -p tcp --sport 502 -j ACCEPT
iptables -A FORWARD -i eth1 -o eth0 -m mac --mac-source 02:42:0a:64:02:0a -d 10.100.1.10 -p tcp --dport 502 -j ACCEPT

iptables -A FORWARD -m state --state ESTABLISHED,RELATED -j ACCEP

# Log all other dropped packets
iptables -A FORWARD -j LOG --log-prefix "FW-DROP: " --log-level 4

echo "=========================================="
echo "Firewall rules applied successfully"
echo "Firewall IPs:"
echo "  PLC Network:   10.100.1.254"
echo "  SCADA Network: 10.100.2.254"
echo "  DB Network:    10.100.3.254"
echo ""
echo "Allowed ICMP:"
echo "  10.100.1.10 <-> 10.100.2.10 (Asherah <-> ScadaLTS)"
echo "  Attacker (10.100.2.100) -> PLC Network (ALLOWED FOR TESTING)"
echo "=========================================="

# Show active rules
iptables -L -n -v

tail -f /dev/null