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

# Allow SCADA (10.100.2.10 and 10.100.1.11) to PLC network - Modbus TCP (port 502)
iptables -A FORWARD -s 10.100.2.10 -d 10.100.1.0/24 -p tcp --dport 502 -j ACCEPT
iptables -A FORWARD -s 10.100.1.11 -d 10.100.1.0/24 -p tcp --dport 502 -j ACCEPT
iptables -A FORWARD -s 10.100.1.0/24 -d 10.100.2.10 -p tcp --sport 502 -j ACCEPT
iptables -A FORWARD -s 10.100.1.0/24 -d 10.100.1.11 -p tcp --sport 502 -j ACCEPT

# Allow SCADA to database (MySQL on port 3306)
iptables -A FORWARD -s 10.100.3.11 -d 10.100.3.10 -p tcp --dport 3306 -j ACCEPT
iptables -A FORWARD -s 10.100.3.10 -d 10.100.3.11 -p tcp --sport 3306 -j ACCEPT

# Allow ICMP (ping) between Asherah and ScadaLTS - BIDIRECTIONAL
iptables -A FORWARD -s 10.100.1.10 -d 10.100.2.10 -p icmp -j ACCEPT
iptables -A FORWARD -s 10.100.2.10 -d 10.100.1.10 -p icmp -j ACCEPT

# ALLOW attacker to PLC network for testing (COMMENT OUT TO RE-ENABLE BLOCKING)
iptables -A FORWARD -s 10.100.2.100 -d 10.100.1.0/24 -j ACCEPT
iptables -A FORWARD -s 10.100.1.0/24 -d 10.100.2.100 -j ACCEPT

# BLOCK attacker (10.100.2.100) from PLC network - COMMENTED OUT FOR TESTING
# iptables -A FORWARD -s 10.100.2.100 -d 10.100.1.0/24 -j LOG --log-prefix "FW-BLOCK-ATTACKER: "
# iptables -A FORWARD -s 10.100.2.100 -d 10.100.1.0/24 -j DROP

# Allow ICMP for diagnostics (general rule - placed after specific rules)
iptables -A FORWARD -p icmp --icmp-type echo-request -j ACCEPT
iptables -A INPUT -p icmp --icmp-type echo-request -j ACCEPT

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