#!/bin/bash

# Configuration du firewall avec filtrage MAC strict + monitoring

# MAC autorisées
ASHERAH_MAC="02:42:0a:64:01:0a"      # 10.100.1.10
SCADALTS_MAC="02:42:0a:64:02:0a"     # 10.100.2.10
ATTACKER_MAC="02:42:0a:64:02:64"     # 10.100.2.100

# Installer iptables
apk add --no-cache iptables 2>/dev/null || true

# FLUSH toutes les règles
iptables -F
iptables -X
iptables -t nat -F
iptables -t nat -X

# POLITIQUE PAR DÉFAUT : DROP
iptables -P FORWARD DROP
iptables -P INPUT DROP
iptables -P OUTPUT ACCEPT

# Loopback
iptables -A INPUT -i lo -j ACCEPT

echo '  → Configuration des règles de whitelist MAC...'

# ──────────────────────────────────────────────────────────────────────────
# WHITELIST : Asherah (MAC) → ScadaLTS
# ──────────────────────────────────────────────────────────────────────────

iptables -A FORWARD -i eth0 -o eth1 \
    -m mac --mac-source $ASHERAH_MAC \
    -d 10.100.2.10 \
    -p tcp --dport 502 \
    -j ACCEPT

echo '    ✓ Asherah → ScadaLTS (Modbus)'

# ──────────────────────────────────────────────────────────────────────────
# WHITELIST : ScadaLTS (MAC) → Asherah
# ──────────────────────────────────────────────────────────────────────────

iptables -A FORWARD -i eth1 -o eth0 \
    -m mac --mac-source $SCADALTS_MAC \
    -d 10.100.1.10 \
    -p tcp --sport 502 \
    -j ACCEPT

iptables -A FORWARD -i eth1 -o eth0 \
    -m mac --mac-source $SCADALTS_MAC \
    -d 10.100.1.10 \
    -p tcp --dport 502 \
    -j ACCEPT

echo '    ✓ ScadaLTS → Asherah (Modbus)'

# ──────────────────────────────────────────────────────────────────────────
# Connexions établies
# ──────────────────────────────────────────────────────────────────────────

iptables -A FORWARD -m state --state ESTABLISHED,RELATED -j ACCEPT

echo '    ✓ Connexions établies autorisées'

# ──────────────────────────────────────────────────────────────────────────
# BLOQUER ET LOGGER L'ATTAQUANT
# ──────────────────────────────────────────────────────────────────────────

# Logger les tentatives de l'attaquant
iptables -I FORWARD 1 \
    -m mac --mac-source $ATTACKER_MAC \
    -j LOG --log-prefix 'ATTACKER: ' --log-level 4

# Bloquer l'attaquant
iptables -I FORWARD 1 \
    -m mac --mac-source $ATTACKER_MAC \
    -j DROP

echo '    ✓ Attaquant bloqué et loggé'

# ──────────────────────────────────────────────────────────────────────────
# LOGGER TOUS LES PAQUETS BLOQUÉS (à la fin, avant policy DROP)
# ──────────────────────────────────────────────────────────────────────────

iptables -A FORWARD -j LOG --log-prefix 'FW_DROP: ' --log-level 4

echo '    ✓ Logging activé pour tous les DROP'

echo ''
echo '  ✓ Configuration terminée'
echo ''
echo '  Règles actives :'
iptables -L FORWARD -n -v --line-numbers
