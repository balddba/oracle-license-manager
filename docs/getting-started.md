# Getting started

The default setup uses SQLite — no database server required. The app creates `data/db/license_tracker.db` at the project root and applies migrations on startup.

## Backend

```bash
cd backend
uv sync --extra dev
uv run uvicorn license_tracker.main:app --reload --port 8000
```

### Report Charts Setup (Optional)

If you plan to export PDF reports containing visual compliance charts, Node.js and its package dependencies must be set up locally:

1. Ensure **Node.js** and **npm** are installed on your host system.
2. Install the renderer dependencies:
   ```bash
   cd backend/scripts/echarts-renderer
   npm install
   ```

## Frontend

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173). API requests are proxied to [http://localhost:8000](http://localhost:8000).

## Oracle database

To use Oracle instead of SQLite:

1. Copy `config/license-tracker.example.yaml` to `config/license-tracker.yaml`
2. Set `database_backend: oracle` and Oracle connection settings
3. Export the password:

```bash
export LICENSE_TRACKER_ORACLE_PASSWORD='your_password'
```

4. Run migrations:

```bash
cd backend
uv run alembic upgrade head
```

5. Start the API:

```bash
uv run uvicorn license_tracker.main:app --reload --port 8000
```

!!! note
    For Oracle and PostgreSQL, run `alembic upgrade head` during deployment. SQLite migrations run automatically on API startup.
