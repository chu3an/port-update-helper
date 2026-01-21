# Agent Guide for Port Update Helper

This repository is a lightweight tool to synchronize Gluetun's forwarded port with qBittorrent. It runs as a Docker container using FastAPI and Alpine Linux.

## 1. Development & Build Commands

### Environment Setup
- **Python Version**: 3.10+
- **Container**: Alpine Linux 3.21 based
- **Key Dependencies**: `fastapi`, `uvicorn`, `requests`, `tini`, `curl`

### Build & Run
The primary way to run the application is via Docker Compose.

```bash
# Build and start the container
docker-compose up -d --build

# View logs
docker-compose logs -f
```

### Local Development
To run locally without Docker (requires setting environment variables manually):

```bash
# Install dependencies
pip install fastapi uvicorn requests

# Run server (ensure environment variables are set, see example.env)
export QB_URL="http://localhost:8080"
export QB_USERNAME="admin"
# ... set other vars ...
uvicorn app.app:app --reload --port 9080
```

### Testing
Currently, there are no explicit unit tests.
- **Future**: If adding tests, use `pytest`.
- **Manual Verification**: Use `curl` to trigger the update endpoint.
  ```bash
  curl -X POST http://localhost:9080/
  ```

### Linting
No formal linter is configured in CI, but agents should adhere to:
- **Ruff/Flake8**: Recommended for static analysis.
  ```bash
  pip install ruff
  ruff check .
  ```

## 2. Code Style & Conventions

### General Python
- **Formatting**: Follow PEP 8.
- **Indentation**: 4 spaces.
- **Imports**: 
  1. Standard Library (`os`, `sys`, `logging`)
  2. Third-party (`fastapi`, `requests`)
  3. Local imports (if any)
- **Type Hinting**: Use Python type hints (`def foo(bar: str) -> bool:`) where helpful, especially for FastAPI endpoints.

### Naming
- **Classes**: `CamelCase` (e.g., `QBAPI`, `GTAPI`).
- **Functions/Variables**: `snake_case` (e.g., `change_port`, `get_public_ip`).
- **Constants/Env Vars**: `UPPER_CASE` (e.g., `QB_URL`, `CHK_INTERVAL`).

### Architecture & patterns
- **Single Responsibility**: `app/app.py` currently holds the main logic and API wrappers. Keep API wrappers (`QBAPI`, `GTAPI`) distinct within the file or separate if they grow too large.
- **Startup**: Use FastAPI `lifespan` context manager for initial checks (connection verification) and setup.
- **Concurrency**: Use `async def` for FastAPI route handlers. Synchronous `requests` calls are currently used inside; if high throughput is needed, migrate to `httpx` (async), but for this cron-job style tool, sync is acceptable.

### Error Handling & Logging
- **Logging**: **NEVER** use `print()`. Use the configured `log` object.
  ```python
  log.info("Message")
  log.error("Error details")
  ```
- **Failures**: 
  - On critical startup failures (env vars, connection), the application should exit (`sys.exit(1)`) to let the container restart policy handle it.
  - On runtime failures (cron update), log the error but keep the server running.
- **Safety**:
  - Always validate the port from Gluetun (ensure `port > 0`) before sending to qBittorrent.

## 3. Container & Deployment
- **PID 1**: The container uses `tini` as the entrypoint to handle signal propagation and zombie reaping.
- **Cron**: Scheduling is handled by the Alpine `crond` service started in `entrypoint`.
  - To change interval: Modify `CHK_INTERVAL` env var.
  - Implementation: `entrypoint` script generates `/etc/crontabs/root`.

## 4. Documentation
- Update `README.md` if adding new environment variables or changing the architecture.
- Keep `example.env` in sync with required environment variables.

## 5. API Reference & Data Structures

### Gluetun API
- **Endpoint**: `GET /v1/portforward`
- **Auth**: Basic Auth (if configured)
- **Expected Response**: JSON
  ```json
  {
      "port": 12345,
      ...
  }
  ```
- **Endpoint**: `GET /v1/publicip/ip`
- **Expected Response**: JSON
  ```json
  {
      "public_ip": "1.2.3.4",
      "country": "Country",
      "city": "City"
  }
  ```

### qBittorrent API (v2)
- **Login**: `POST /api/v2/auth/login` (application/x-www-form-urlencoded: `username`, `password`)
  - Success: `200 OK` body `Ok.`
- **Get Preferences**: `GET /api/v2/app/preferences`
  - Response: JSON `{"listen_port": 12345, ...}`
- **Set Preferences**: `POST /api/v2/app/setPreferences`
  - Data: `json={"listen_port": 12345}`
- **Logout**: `POST /api/v2/auth/logout` (Code uses `.../login` for logout in current implementation, verify if this needs fix in future)

## 6. Common Tasks Checklist

### Adding a New Environment Variable
1. **`app/app.py`**:
   - Add `os.getenv` call.
   - Add to `env_vars` check list in `lifespan`.
   - Update `GTAPI` or `QBAPI` init if needed.
2. **`docker-compose.yaml`**: Add to `environment` section.
3. **`dockerfile`**: Add `ENV` default if applicable (optional).
4. **`example.env`**: Add key with dummy value.
5. **`README.md`**: Update the Environment Variables table.

### Modifying the Update Logic
1. Locate `change_port()` in `app/app.py`.
2. Ensure you handle the `qb` and `gt` global instances correctly.
3. Maintain the logic: Login -> Check -> Update (if changed) -> Logout.
4. Always verify `gt_port > 0` before applying.
