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
    apk add --no-cache tzdata curl && \
    pip install flask requests && \
    chmod +x /entrypoint && \
    chmod +x /app/routine.sh

ENV TZ=Asia/Tokyo

EXPOSE 9080

ENTRYPOINT ["/entrypoint"]
