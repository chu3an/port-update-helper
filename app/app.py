import json
import logging
import os
import sys
from contextlib import asynccontextmanager
from typing import Any

import requests
from fastapi import FastAPI, Response


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=sys.stdout,
)
log = logging.getLogger("port-update-helper")


QB_URL = os.getenv("QB_URL")
QB_USERNAME = os.getenv("QB_USERNAME")
QB_PASSWORD = os.getenv("QB_PASSWORD")
GT_URL = os.getenv("GT_URL")
GT_USERNAME = os.getenv("GT_USERNAME")
GT_PASSWORD = os.getenv("GT_PASSWORD")
REQUEST_TIMEOUT = os.getenv("REQUEST_TIMEOUT", "10")


def response_summary(response: requests.Response) -> str:
    """Return a short response description without request credentials."""
    body = response.text.strip().replace("\n", " ")
    if len(body) > 200:
        body = f"{body[:200]}..."
    return f"HTTP {response.status_code}, body={body!r}"


class QBAPI:
    def __init__(
        self, url: str, username: str, password: str, timeout: float
    ) -> None:
        self.session = requests.Session()
        self.baseurl = url.rstrip("/")
        self.username = username
        self.password = password
        self.timeout = timeout

        # qBittorrent validates Origin/Referer against Host when CSRF protection
        # is enabled. Keep these aligned with the URL used for every request.
        self.session.headers.update(
            {
                "Origin": self.baseurl,
                "Referer": f"{self.baseurl}/",
                "User-Agent": "port-update-helper/2",
            }
        )

    def _request(
        self, method: str, path: str, **kwargs: Any
    ) -> requests.Response | None:
        try:
            return self.session.request(
                method,
                f"{self.baseurl}{path}",
                timeout=self.timeout,
                **kwargs,
            )
        except requests.RequestException as exc:
            log.error("qBittorrent API %s %s failed: %s", method, path, exc)
            return None

    def login(self) -> bool:
        # Do not let a stale session cookie hide an authentication failure.
        self.session.cookies.clear()
        response = self._request(
            "POST",
            "/api/v2/auth/login",
            data={"username": self.username, "password": self.password},
        )
        if response is not None:
            if response.status_code == 204:
                return True
            if response.status_code == 200 and response.text.strip() == "Ok.":
                return True

        if response is not None:
            log.error("qBittorrent login failed: %s", response_summary(response))
        return False

    def logout(self) -> bool:
        response = self._request("POST", "/api/v2/auth/logout")
        success = response is not None and response.status_code in (200, 204)
        if response is not None and not success:
            log.warning("qBittorrent logout failed: %s", response_summary(response))
        self.session.cookies.clear()
        return success

    def get_version(self) -> str | None:
        response = self._request("GET", "/api/v2/app/version")
        if response is not None and response.status_code == 200:
            return response.text.strip()
        if response is not None:
            log.error(
                "qBittorrent version check failed: %s",
                response_summary(response),
            )
        return None

    def get_port(self) -> int | None:
        response = self._request("GET", "/api/v2/app/preferences")
        if response is None:
            return None
        if response.status_code != 200:
            log.error(
                "qBittorrent preferences check failed: %s",
                response_summary(response),
            )
            return None

        try:
            return int(response.json()["listen_port"])
        except (KeyError, TypeError, ValueError) as exc:
            log.error("Invalid qBittorrent preferences response: %s", exc)
            return None

    def set_port(self, port: int) -> bool:
        response = self._request(
            "POST",
            "/api/v2/app/setPreferences",
            data={"json": json.dumps({"listen_port": port})},
        )
        if response is not None and response.status_code in (200, 204):
            return True
        if response is not None:
            log.error(
                "qBittorrent port update failed: %s",
                response_summary(response),
            )
        return False


class GTAPI:
    def __init__(
        self, url: str, username: str, password: str, timeout: float
    ) -> None:
        self.session = requests.Session()
        self.url = url.rstrip("/")
        self.session.auth = (username, password)
        self.timeout = timeout

    def _get_json(self, path: str) -> dict[str, Any] | None:
        try:
            response = self.session.get(
                f"{self.url}{path}", timeout=self.timeout
            )
        except requests.RequestException as exc:
            log.error("Gluetun API GET %s failed: %s", path, exc)
            return None

        if response.status_code != 200:
            log.error(
                "Gluetun API GET %s failed: %s",
                path,
                response_summary(response),
            )
            return None

        try:
            data = response.json()
        except ValueError as exc:
            log.error("Invalid Gluetun JSON from %s: %s", path, exc)
            return None

        if not isinstance(data, dict):
            log.error("Invalid Gluetun response type from %s", path)
            return None
        return data

    def get_public_ip(self) -> dict[str, Any] | None:
        return self._get_json("/v1/publicip/ip")

    def get_forwarded_port(self) -> dict[str, Any] | None:
        return self._get_json("/v1/portforward")


qb: QBAPI | None = None
gt: GTAPI | None = None


def fail_startup(message: str) -> None:
    log.error(message)
    raise RuntimeError(message)


@asynccontextmanager
async def lifespan(app: FastAPI):
    del app
    global qb, gt

    required = {
        "QB_URL": QB_URL,
        "QB_USERNAME": QB_USERNAME,
        "QB_PASSWORD": QB_PASSWORD,
        "GT_URL": GT_URL,
        "GT_USERNAME": GT_USERNAME,
        "GT_PASSWORD": GT_PASSWORD,
    }
    missing = [name for name, value in required.items() if not value]
    if missing:
        fail_startup(f"Missing required environment variables: {', '.join(missing)}")

    try:
        timeout = float(REQUEST_TIMEOUT)
        if timeout <= 0:
            raise ValueError
    except ValueError:
        fail_startup("REQUEST_TIMEOUT must be a positive number")

    # The checks above guarantee these are strings.
    qb = QBAPI(QB_URL, QB_USERNAME, QB_PASSWORD, timeout)  # type: ignore[arg-type]
    gt = GTAPI(GT_URL, GT_USERNAME, GT_PASSWORD, timeout)  # type: ignore[arg-type]

    if not qb.login():
        fail_startup("qBittorrent login failed; check the detailed error above")

    qb_version = qb.get_version()
    qb.logout()
    if not qb_version:
        fail_startup("qBittorrent version check failed")
    log.info("qBittorrent version %s", qb_version)

    ip_data = gt.get_public_ip()
    if not ip_data:
        fail_startup("Gluetun public IP check failed")
    log.info(
        "Gluetun public IP %s (%s-%s)",
        ip_data.get("public_ip", "Unknown"),
        ip_data.get("country", "Unknown"),
        ip_data.get("city", "Unknown"),
    )

    if not change_port():
        fail_startup("Initial forwarded-port synchronization failed")

    yield


app = FastAPI(lifespan=lifespan)


def change_port() -> bool:
    if qb is None or gt is None:
        log.error("API clients are not initialized")
        return False

    port_data = gt.get_forwarded_port()
    if not port_data:
        return False

    try:
        gt_port = int(port_data["port"])
    except (KeyError, TypeError, ValueError):
        log.error("Gluetun response does not contain a valid port")
        return False

    if not 1 <= gt_port <= 65535:
        log.error("Invalid Gluetun forwarded port %s; update aborted", gt_port)
        return False
    log.info("Gluetun forwarded port %s", gt_port)

    if not qb.login():
        return False

    try:
        qb_port = qb.get_port()
        if qb_port is None:
            return False
        log.info("qBittorrent listen port %s", qb_port)

        if qb_port == gt_port:
            log.info("Port unchanged (same number)")
            return True

        if not qb.set_port(gt_port):
            return False

        verified_port = qb.get_port()
        if verified_port != gt_port:
            log.error(
                "qBittorrent port verification failed: expected %s, got %s",
                gt_port,
                verified_port,
            )
            return False

        log.info("qBittorrent listen port %s (changed and verified)", verified_port)
        return True
    finally:
        qb.logout()


@app.get("/health")
def get_health() -> Response:
    return Response(content="OK", status_code=200)


@app.post("/")
def post_change_port() -> Response:
    log.info("Received port synchronization request")
    if not change_port():
        return Response(content="Update Failed", status_code=500)
    return Response(content="OK", status_code=200)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=9080)
