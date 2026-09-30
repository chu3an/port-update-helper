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

1. A cron job triggers a synchronization at the configured interval (5 minutes by default).
2. The helper reads the forwarded port from Gluetun's control API.
3. The helper logs in to qBittorrent, updates the listening port when needed, and verifies the saved value.

An initial synchronization also runs during application startup. Startup fails with
a diagnostic error if either API cannot be reached or authenticated, allowing the
container restart policy to retry after a transient dependency failure.
The helper accepts both the legacy `200 Ok.` and newer `204 No Content`
qBittorrent Web API success responses.

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
3. Create `compose.yaml` :
    ```yaml
    services:
      port-update-helper:
        image: ghcr.io/chu3an/port-update-helper:latest
        container_name: port-update-helper
        environment:
          - QB_URL=${QB_URL}
          - QB_USERNAME=${QB_USERNAME}
          - QB_PASSWORD=${QB_PASSWORD}
          - GT_URL=${GT_URL}
          - GT_USERNAME=${GT_USERNAME}
          - GT_PASSWORD=${GT_PASSWORD}
          - CHK_INTERVAL=${CHK_INTERVAL:-5}
          - REQUEST_TIMEOUT=${REQUEST_TIMEOUT:-10}
          - TZ=${TZ:-Asia/Taipei}
        ports:
          - 9080:9080
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
| CHK_INTERVAL | Check interval time in whole minutes (1-59) | 5 |
| REQUEST_TIMEOUT | Timeout for each API request in seconds | 10 |
| QB_URL      | qBittorrent URL  | |
| QB_USERNAME | Username of qBittorrent | |
| QB_PASSWORD | Password of qBittorrent | |
| GT_URL      | Gluetun control server URL | |
| GT_USERNAME | Username of Gluetun control server | |
| GT_PASSWORD | Password of Gluetun control server | |
| TZ          | Specify a timezone to use ([reference](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones#List)) | Asia/Taipei |

## Compose startup ordering

When this helper is deployed with Gluetun and qBittorrent, use health-based
dependencies rather than the short `depends_on` syntax. The intended chain is:

1. Gluetun is healthy and `/tmp/gluetun/forwarded_port` contains a non-zero port.
2. qBittorrent starts and its WebUI healthcheck succeeds.
3. Port Update Helper starts and performs its initial synchronization.

The healthchecks belong in the three-service deployment Compose file; the
standalone Compose example above only starts this helper.
        
## License

This repo is licensed under MIT license
