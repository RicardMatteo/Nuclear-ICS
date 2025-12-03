FROM debian:bookworm-slim

RUN apt-get update && apt-get install -y \
    suricata \
    suricata-update \
    jq \
    tcpdump \
    net-tools \
    iproute2 \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /var/log/suricata /var/lib/suricata /etc/suricata/rules

COPY config/suricata.yaml /etc/suricata/suricata.yaml
COPY rules/*.rules /etc/suricata/rules/

RUN suricata-update || true
RUN chmod -R 755 /var/log/suricata /var/lib/suricata

WORKDIR /var/log/suricata

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD pidof suricata || exit 1

CMD ["suricata", "-c", "/etc/suricata/suricata.yaml", "-i", "br-plc", "-i", "br-scada", "-v"]