FROM python:3.10-alpine3.21
LABEL \
    org.opencontainers.image.authors="chu3an@GitHub" \
    org.opencontainers.image.title="port-update-helper" \
    org.opencontainers.image.url="https://github.com/chu3an/port-update-helper"

WORKDIR /app

RUN \
    apk add --no-cache tzdata && \
    pip install flask requests

COPY app /app
COPY entrypoint /entrypoint

ENV TZ=Asia/Tokyo
EXPOSE 9080

CMD ["/entrypoint"]
