FROM scadalts/scadalts:latest

# Create non-root user for Tomcat
RUN groupadd -r scada && useradd -r -g scada scada

# Install dependencies
RUN apt-get update -qq && \
    apt-get install -y --no-install-recommends \
    wget \
    iproute2 \
    iputils-ping \
    ca-certificates \
    -qq && \
    wget -q https://raw.githubusercontent.com/vishnubob/wait-for-it/master/wait-for-it.sh \
    -O /usr/local/bin/wait-for-it && \
    chmod +x /usr/local/bin/wait-for-it && \
    apt-get remove -y wget && \
    apt-get autoremove -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Copy startup script
COPY startup.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/startup.sh

# Set ownership for Tomcat directories
RUN chown -R scada:scada /usr/local/tomcat/logs \
    /usr/local/tomcat/temp \
    /usr/local/tomcat/work

# Stay as root - we'll switch users in startup script
CMD ["/usr/local/bin/startup.sh"]