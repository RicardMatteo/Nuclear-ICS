#!/bin/bash

echo 1 > /proc/sys/net/ipv4/ip_forward

iptables -F
iptables -X
iptables -t nat -F
iptables -t nat -X

iptables -P FORWARD DROP
iptables -P INPUT DROP
iptables -P OUTPUT ACCEPT

iptables -A FORWARD -m state --state ESTABLISHED,RELATED -j ACCEPT
iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT

iptables -A INPUT -i lo -j ACCEPT

iptables -A FORWARD -i eth1 -o eth2 -m mac --mac-source 02:42:0a:64:01:0a -d 10.100.2.10 -p tcp --dport 502 -j ACCEPT
iptables -A FORWARD -i eth1 -o eth2 -m mac --mac-source 02:42:0a:64:01:0a -d 10.100.2.10 -p tcp --sport 502 -j ACCEPT
iptables -A FORWARD -i eth2 -o eth1 -m mac --mac-source 02:42:0a:64:02:0a -d 10.100.1.10 -p tcp --sport 502 -j ACCEPT
iptables -A FORWARD -i eth2 -o eth1 -m mac --mac-source 02:42:0a:64:02:0a -d 10.100.1.10 -p tcp --dport 502 -j ACCEPT

iptables -A FORWARD -m state --state ESTABLISHED,RELATED -j ACCEP

iptables -A FORWARD -j LOG --log-prefix "FW-DROP: " --log-level 4

iptables -L -n -v

tail -f /dev/null