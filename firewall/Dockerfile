FROM alpine:latest

RUN apk add --no-cache \
    iptables \
    ip6tables \
    bash \
    iproute2 \
    tcpdump

COPY firewall-rules.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/firewall-rules.sh

CMD ["/usr/local/bin/firewall-rules.sh"]