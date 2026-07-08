# Configuration

Configuration is loaded from YAML and environment variables.

## Default file

`config/license-tracker.yaml` — copy from `config/license-tracker.example.yaml` if needed.

```yaml
database_backend: sqlite
sqlite:
  path: data/db/license_tracker.db
oracle:
  host: localhost
  port: 1521
  service_name: XEPDB1
  user: license_tracker
ssh:
  default_port: 22
  connect_timeout_seconds: 15
```

## Environment variables

| Variable | Description |
|----------|-------------|
| `LICENSE_TRACKER_CONFIG_PATH` | Path to a custom YAML config file |
| `LICENSE_TRACKER_ORACLE_PASSWORD` | Oracle database password |
| `LICENSE_TRACKER_POSTGRESQL_PASSWORD` | PostgreSQL database password |
| `LICENSE_TRACKER_CORS_ORIGINS` | JSON array of allowed CORS origins (Docker sets `["http://localhost:8080"]`) |
| `LICENSE_TRACKER_ECHARTS_RENDERER` | Absolute path to the directory containing `render.mjs` and its `node_modules` (defaults to `<project_root>/backend/scripts/echarts-renderer`) |

## PDF Report Chart Rendering Requirements

To render the dynamic visual compliance charts embedded in exported PDF reports, the backend requires Node.js to execute the ECharts rendering canvas helper.
- **Node.js**: Node must be present in the system's `PATH`.
- **ECharts Renderer Directory**: The directory resolved by `LICENSE_TRACKER_ECHARTS_RENDERER` (or the default path) must have its Node dependencies installed (`npm install` / `npm ci`).
- **System Graphics Libraries**: Since the ECharts renderer uses `node-canvas` under the hood, standard OS-level graphics libraries (e.g., Cairo, Pango, libpng, jpeg, gif) must be installed on the host system (automatically set up in the Docker environment).

## Database backends

| Backend | When to use |
|---------|-------------|
| `sqlite` | Local development and Docker (default) |
| `oracle` | Production Oracle deployments |
| `postgresql` | Alternative production backend |

Switch backends by editing `database_backend` in the YAML file and providing the matching connection settings and password environment variable.
