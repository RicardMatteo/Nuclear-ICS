FROM kalilinux/kali-rolling:latest

RUN apt-get update -qq && \
    apt-get install -y \
    iproute2 \
    iputils-ping \
    nmap \
    netcat-traditional \
    python3 \
    python3-pip \
    python3-venv \
    tcpdump \
    python3-pymodbus \
    -qq && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

COPY startup.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/startup.sh

CMD ["/usr/local/bin/startup.sh"]