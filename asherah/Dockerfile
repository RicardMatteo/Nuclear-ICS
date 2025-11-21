FROM ubuntu:20.04

# Éviter les prompts interactifs
ENV DEBIAN_FRONTEND=noninteractive

# Installation des dépendances système
RUN apt-get update && apt-get install -y \
    python3.8 \
    python3-pip \
    git \
    build-essential \
    libmodbus-dev \
    wget \
    sudo \
    && rm -rf /var/lib/apt/lists/*

# Créer le ramdisk
RUN mkdir -p /ramdisk && chmod 755 /ramdisk

# Cloner le repository mbans
WORKDIR /opt
RUN git clone https://github.com/ait-cs-IaaS/mbans.git
WORKDIR /opt/mbans

# Copier la bibliothèque mbclient
RUN cp DEPENDENCIES/libmbclient.so /usr/lib/ && \
    chmod 755 /usr/lib/libmbclient.so && \
    ldconfig

# Installer les requirements Python pour Ferryman
WORKDIR /opt/mbans/FERRYMAN
RUN pip3 install -r requirements.txt

# Rendre les scripts exécutables
WORKDIR /opt/mbans
RUN chmod +x asherah_npp.sh && \
    chmod +x MB_SERVER/modbus_server && \
    chmod +x SIMULATION/alpha_mbans_HIL_RPS_ON && \
    chmod +x SIMULATION/release_mbans_STANDALONE

# Copier le script de démarrage
COPY start_asherah.sh /opt/mbans/start_asherah.sh
RUN chmod +x /opt/mbans/start_asherah.sh
RUN sed -i 's/\r$//' /opt/mbans/start_asherah.sh

WORKDIR /opt/mbans

EXPOSE 502

CMD ["/opt/mbans/start_asherah.sh"]