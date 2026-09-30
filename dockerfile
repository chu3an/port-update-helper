FROM python:3.10-alpine3.21
LABEL \
    org.opencontainers.image.authors="chu3an@GitHub" \
    org.opencontainers.image.title="port-update-helper" \
    org.opencontainers.image.url="https://github.com/chu3an/port-update-helper" \
    org.opencontainers.image.description="Update qBittorrent listening port in fast way with the forwarded port by Gluetun"

WORKDIR /app

COPY ./app /app
COPY entrypoint /entrypoint

RUN \
    apk add --no-cache tzdata curl tini && \
    pip install fastapi uvicorn requests && \
    chmod +x /entrypoint

ENV TZ=Asia/Taipei

EXPOSE 9080

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl --fail --silent --show-error --max-time 3 http://127.0.0.1:9080/health >/dev/null || exit 1

ENTRYPOINT ["/sbin/tini", "--", "/entrypoint"]
