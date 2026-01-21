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

> [!NOTE]
> 2026 UPDATE
> This repo is also my opencode practice project
> I use opencode to replace Flask with fastapi, and fix 0 port issue

## Explain

1. Cronjob trigger with setting interval (default 5 min)
2. Get fowarded port from Gluetun API
3. Update port number to qBittorrent API

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
2. Create `.env` file (see `example.env`)
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
3. Create `docker-compose.yaml` :
    ```yaml
    services:
      port-update-helper:
        image: ghcr.io/chu3an/port-update-helper:latest
        container_name: port-update-helper
        ports:
          - 9080:9080
        env_file:
          - .env
        restart: on-failure:5
        logging:
          driver: 'json-file'
          options:
            max-size: '1M'
            max-file: '5'
    ```

Environment Variables
| Env         | Description | Default |
|-------------|---|---|
| CHK_INTERVAL | Check interval time (minutes) | 5 |
| QB_URL      | qBittorrent URL  | |
| QB_USERNAME | Username of qBittorrent | |
| QB_PASSWORD | Password of qBittorrent | |
| GT_URL      | Gluetun control server URL | |
| GT_USERNAME | Username of Gluetun control server | |
| GT_PASSWORD | Password of Gluetun control server | |
| TZ          | Specify a timezone to use ([reference](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones#List)) | Asia/Taipei |
        
## License

This repo is licensed under MIT license
