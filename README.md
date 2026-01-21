[chu3an]: https://github.com/chu3an
[control server]: https://github.com/qdm12/gluetun-wiki/blob/main/setup/advanced/control-server.md
[timezone]: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones#List

[Explain](#explain) | [Usage](#Usage) | [License](#license)

# Port Update Helper

A lightweight tool to automatically check the forwarded port from Gluetun and update the qBittorrent listening port. With this tool, you can reduce the hassle of manual updates while improving system security and stability.

Now powered by **FastAPI** for better performance and **Tini** for proper process management.

> [!NOTE]
> This repo is my practice for building Docker images.
> Please excuse any imperfections.
> Be cautious if you use this in a production environment.

# Explain

1. When Gluetun port changed, `curl -X POST` to this container
2. Get new port number via Gluetun API
3. Post new port number to qBittorrent API
4. Check the port number regularly (via internal cron)

![img](/assets/PortUpdateHelper.png)

## Usage

Replace the following IP address, username, and password with your own.

1.  Modify your gluetun setting to enable [control server]
    Add `/gluetun/auth/config.toml` with following content
    ```toml
    [[roles]]
    name = "qbittorrent"
    routes = ["GET /v1/portforward", "GET /v1/publicip/ip"]
    auth = "basic"
    username = "username"
    password = "password"
    ```
2.  Add a enviroment variable to Gluetun
    ```yaml
    VPN_PORT_FORWARDING_UP_COMMAND=/bin/sh -c "curl -X POST 192.168.X.X:9080"
    ```
3.  Run this container (docker-compose)
    You can use the provided `docker-compose.yaml` and `.env` file.
    
    1. Create a `.env` file (see `example.env`):
    ```ini
    QB_URL=http://192.168.X.X:8080
    QB_USERNAME=username
    QB_PASSWORD=password
    GT_URL=http://192.168.X.X:8000
    GT_USERNAME=username
    GT_PASSWORD=password
    CHK_INTERVAL=5
    TZ=Asia/Tokyo
    ```

    2. Run with docker-compose:
    ```yaml
    services:
      port-update-helper:
        image: ghcr.io/chu3an/port-update-helper:latest
        container_name: port-update-helper
        ports:
          - 9080:9080
        env_file:
          - .env
        restart: unless-stopped
    ```

    Environment Variables
    | Env         | Description | Default |
    |-------------|---|---|
    | CHK_INTERVAL | Check interval time (minutes) | 5 |
    | QB_URL      | qBittorrent URL  | |
    | QB_USERNAME | Username of qBittorrent | |
    | QB_PASSWORD | Password of qBittorrent | |
    | GT_URL      | Gluetun control server URL | |
    | GT_USERNAME | Username of Gluetun | |
    | GT_PASSWORD | Password of Gluetun | |
    | TZ          | Specify a timezone to use ([reference](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones#List)) | Asia/Tokyo |
        
# License

This repo is licensed under MIT license
