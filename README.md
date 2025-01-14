[chu3an]: https://github.com/chu3an
[control server]: https://github.com/qdm12/gluetun-wiki/blob/main/setup/advanced/control-server.md

[Explain](#explain) | [Installation](#installation) | [License](#license)

# Port Update Helper

A lightweight tool to automatically check the forwarded port from Gluetun and update the qBittorrent listening port. With this tool, you can reduce the hassle of manual updates while improving system security and stability.

> [!NOTE]
> This repo is my practice for building Docker images.
> Please excuse any imperfections.
> Be cautious if you use this in a production environment.

# Explain

1. When Gluetun port changed, `curl -X POST` to this container
2. Get new port number via Gluetun API
3. Post new port number to qBittorrent API
4. (unfinished) Check the port number regularly

![img](/assets/PortUpdateHelper.png)

## Installation

1.  Midify your gluetun setting to enable [control server]
    Add `/gluetun/auth/config.toml` with following content
    ```toml
    [[roles]]
    name = "qbittorrent"
    routes = ["GET /v1/openvpn/portforwarded", "GET /v1/publicip/ip"]
    auth = "basic"
    username = "username"
    password = "password"
    ```
    Replace `username` and `password` with your own credentials
2.  Add a enviroment variable to Gluetun
    ```yaml
    VPN_PORT_FORWARDING_UP_COMMAND=/bin/sh -c "curl -X POST 127.0.0.1:9080"
    ```
    Replace `127.0.0.1` with PortUpdateHelper ip or Docker host ip
3.  Run this container
    * Docker Compose
      ```docker-compose
      version: "3"
      services:
        gluetun:
          image: ghcr.io/chu3an/port-update-helper:latest
          container_name: port-update-helper
          ports:
            - 9080:9080
          environment:
            - QB_URL="http://127.0.0.1:8080"
            - QB_USERNAME="username"
            - QB_PASSWORD="password"
            - GT_URL="http://127.0.0.1:8000"
            - GT_USERNAME="username"
            - GT_PASSWORD="password"
      ```
    * Docker run
      ```docker-compose
      docker run -d -p 9080:9080 --name port-update-helper \
        -e QB_URL=http://127.0.0.1:8080 \
        -e QB_USERNAME=username \
        -e QB_PASSWORD=password \
        -e GT_URL=http://127.0.0.1:8000 \
        -e GT_USERNAME=username \
        -e GT_PASSWORD=password \
        ghcr.io/chu3an/port-update-helper:latest
      ```
    Replace all the ip and credentials with your own

# License

This repo is licensed under MIT license
